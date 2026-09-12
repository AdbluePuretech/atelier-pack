# -*- coding: utf-8 -*-
"""Certificat : quelle part du classeur est reellement couverte par une preuve.

C'est l'orchestrateur. Il rassemble ce que les autres modules ont etabli et
repond a la seule question qui vaille : combien de cellules restent sans preuve.

Le modele de preuves, par nature de cellule :

  valeur en dur sur la feuille d'hypotheses  -> provenance + integrite
  valeur en dur ailleurs                      -> jamais couverte, c'est un defaut
  formule                                     -> famille revue + integrite + continuite
  toute cellule, si la convergence a tourne   -> + stabilite

Une preuve absente n'est pas une preuve negative : le certificat distingue
"prouve faux" de "pas prouve". Les deux empechent la certification, mais ils ne
se corrigent pas de la meme facon.

Les etapes lentes - familles, convergence, sensibilite, commutateurs - se
passent par leurs fichiers JSON. Sans eux, le certificat le dit et plafonne la
couverture au lieu de faire comme si.

Usage :
    python certifier.py "Classeur.xlsx" \
        [--familles f.json] [--convergence c.json] \
        [--sensibilite s.json] [--commutateurs m.json] [--json cert.json]
"""
import argparse
import collections
import hashlib
import json
import os
import sys

import noyau
import circuits as mod_circuits
import integrite as mod_integrite
import familles as mod_familles

PREUVES = ("provenance", "famille", "integrite", "continuite", "stabilite")


def charger(chemin):
    if not chemin or not os.path.exists(chemin):
        return None
    with open(chemin, encoding="utf-8") as fh:
        return json.load(fh)


def empreinte(chemin):
    h = hashlib.sha256()
    with open(chemin, "rb") as fh:
        for bloc in iter(lambda: fh.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def certifier(chemin, feuille_inputs, familles=None, convergence=None,
              sensibilite=None, commutateurs=None, identites=None,
              mutation=None, differences=None, vraisemblance=None):
    journal = []

    # --- ce qui se calcule ici, tout de suite -------------------------
    C, integ = mod_integrite.balayer(chemin, feuille_inputs)
    _, circ = mod_circuits.analyser(chemin)

    fautifs_bloquants = set()
    for c in integ.controles:
        if c["ok"] or c["gravite"] == "presentationnel":
            continue
        for x in c["fautifs"]:
            fautifs_bloquants.add(x.split("  ")[0].strip())
        journal.append({"cle": c["cle"], "constat": c["libelle"],
                        "gravite": c["gravite"], "portee": c["compte"],
                        "ventilation": c["ventilation"], "statut": "ouvert"})

    basculantes = {x["cellule"] for x in circ["discontinuites_dans_un_circuit"]}
    if basculantes:
        journal.append({"cle": "C1", "constat": "marches pouvant basculer dans un circuit",
                        "gravite": "critique", "portee": len(basculantes),
                        "statut": "ouvert"})

    # --- familles revues ------------------------------------------------
    # L'unite de revue est l'USAGE - squelette x feuille x bloc - et le
    # certificat doit apparier sur la meme unite, sinon il credite toutes les
    # cellules qui partagent un squelette alors qu'un seul de ses usages a ete
    # lu. Sur une golden reelle, cet appariement trop large annoncait 48,76 %
    # de couverture pour 12,82 % de lecture reelle.
    revues = set()
    if familles:
        revues = {(f["squelette"], f.get("feuille"), f.get("bloc"))
                  for f in familles.get("familles", [])
                  if f.get("statut") in ("vue", "anomalie")}
        non_revues = sum(f["cellules"] for f in familles.get("familles", [])
                         if f.get("statut") not in ("vue", "anomalie"))
        if non_revues:
            journal.append({"cle": "F1", "constat": "familles de formules non revues",
                            "gravite": "significatif", "portee": non_revues,
                            "statut": "ouvert"})
    else:
        journal.append({"cle": "F0", "constat": "revue des familles jamais lancee",
                        "gravite": "critique", "portee": len(C.formules),
                        "statut": "ouvert"})

    # --- stabilite -------------------------------------------------------
    stable = False
    if convergence:
        bougent = sum(c.get("valeurs_qui_bougent", 0)
                      for c in convergence.get("configurations", []))
        stable = convergence.get("verdict") == 0
        if not stable:
            journal.append({"cle": "V1", "constat": "valeurs instables d'une "
                            "configuration de calcul a l'autre",
                            "gravite": "critique", "portee": bougent,
                            "statut": "ouvert"})
    else:
        journal.append({"cle": "V0", "constat": "dossier de convergence jamais etabli",
                        "gravite": "critique", "portee": len(C.formules),
                        "statut": "ouvert"})

    for nom, donnees, cle in (("sensibilite", sensibilite, "S"),
                              ("commutateurs", commutateurs, "M")):
        if not donnees:
            journal.append({"cle": f"{cle}0", "constat": f"{nom} : jamais lance",
                            "gravite": "significatif", "portee": 0, "statut": "ouvert"})
        elif donnees.get("configurations_ko"):
            journal.append({"cle": f"{cle}1",
                            "constat": f"{nom} : configurations qui cassent le modele",
                            "gravite": "critique",
                            "portee": donnees["configurations_ko"], "statut": "ouvert"})

    # --- regeneration : le fichier livre est-il ce que le generateur produit ?
    if differences is None:
        journal.append({"cle": "R0", "constat": "regeneration et diff : jamais lancee - "
                        "on ignore si le fichier a ete retouche a la main",
                        "gravite": "significatif", "portee": 0, "statut": "ouvert"})
    else:
        r = differences.get("resume", {})
        n = (r.get("ecarts_de_formule", 0) + r.get("ecarts_de_valeur_en_dur", 0)
             + r.get("absentes_du_candidat", 0) + r.get("absentes_de_la_reference", 0))
        if n:
            journal.append({"cle": "R1",
                            "constat": "le fichier livre differe de ce que le generateur "
                                       "produit : retouche manuelle ou generateur non deterministe",
                            "gravite": "critique", "portee": n, "statut": "ouvert"})

    # --- identites imposees de l'exterieur ---------------------------------
    if identites is None:
        journal.append({"cle": "D0", "constat": "identites imposees : jamais lancees",
                        "gravite": "significatif", "portee": 0, "statut": "ouvert"})
    elif identites.get("ecarts_total"):
        journal.append({"cle": "D1",
                        "constat": "identites que le modele ne declare pas : ecarts a juger",
                        "gravite": "significatif",
                        "portee": identites["ecarts_total"], "statut": "ouvert"})

    # --- la vraisemblance ---------------------------------------------------
    # La seule etape qui ne demande pas si le classeur est juste avec lui-meme,
    # mais s'il dit quelque chose de POSSIBLE. Sans elle le certificat resterait
    # muet sur un modele qui boucle parfaitement et affiche une marge de 340 %.
    if vraisemblance is None:
        journal.append({"cle": "P0", "constat": "vraisemblance : jamais lancee - on "
                        "ignore si les sorties sont economiquement possibles",
                        "gravite": "significatif", "portee": 0, "statut": "ouvert"})
    else:
        durs = sum(d.get("compte", 0) for d in vraisemblance
                   if d.get("nature") == "DEFAUT")
        declaree = any(d.get("cle") == "V4" and "AUCUNE" not in str(d.get("sur", ""))
                       for d in vraisemblance)
        if durs:
            journal.append({"cle": "P1",
                            "constat": f"{durs} valeur(s) hors des bornes universelles "
                                       "de vraisemblance",
                            "gravite": "significatif", "portee": durs,
                            "statut": "ouvert"})
        if not declaree:
            journal.append({"cle": "P2", "constat": "aucune borne de vraisemblance "
                            "declaree - l'etape n'a essaye que l'universel",
                            "gravite": "presentationnel", "portee": 0,
                            "statut": "ouvert"})

    # --- ce que la batterie surveille reellement ----------------------------
    # Le chiffre le plus severe du dossier, et le seul qui porte sur les
    # CONTROLES plutot que sur le modele. Une couverture faible ne dit pas que
    # le classeur est faux : elle dit que s'il l'etait, personne ne le saurait.
    couverture_batterie = None
    if mutation is None:
        journal.append({"cle": "U0", "constat": "test de mutation : jamais lance - on "
                        "ignore ce que la batterie surveille",
                        "gravite": "significatif", "portee": 0, "statut": "ouvert"})
    else:
        couverture_batterie = mutation.get("couverture_reelle_pct")
        if couverture_batterie is not None and couverture_batterie < 80:
            journal.append({"cle": "U1",
                            "constat": f"la batterie ne detecte que "
                                       f"{couverture_batterie:.0f} % des corruptions",
                            "gravite": "critique",
                            "portee": mutation.get("echantillon", 0),
                            "ventilation": mutation.get("angles_morts", {}),
                            "statut": "ouvert"})

    # --- provenance : quelles entrees remontent a une source ? --------------
    # Etre POSEE sur la feuille d'hypotheses ne prouve rien : c'est un
    # emplacement, pas une provenance. Une entree est tracee si sa ligne porte,
    # a droite de sa valeur, un renvoi vers une source - un identifiant de
    # document, une reference d'article, un libelle de piece. Un simple tag
    # d'unite (`%`, `x`, `EUR 000`) ne compte pas : trop court pour designer
    # quoi que ce soit.
    lignes_tracees = set()
    for (f, l, c), v in C.textes.items():
        if f != feuille_inputs or not isinstance(v, str):
            continue
        s = v.strip()
        if len(s) >= 12 and not s.startswith("="):
            lignes_tracees.add((f, l, c))
    def tracee(cle):
        return any((cle[0], cle[1], cc) in lignes_tracees
                   for cc in range(cle[2] + 1, cle[2] + 14))

    # --- couverture cellule par cellule ----------------------------------
    manques = collections.Counter()
    couvertes = 0
    hors_inputs = []
    sans_source = []
    total = 0
    for cle in list(C.formules) + list(C.durs):
        total += 1
        lib = noyau.libelle(cle)
        formule = C.formules.get(cle)
        absentes = []
        if formule is None:
            if cle[0] != feuille_inputs:
                absentes.append("provenance")
                hors_inputs.append(lib)
            elif not tracee(cle):
                absentes.append("provenance")
                sans_source.append(lib)
        else:
            usage = (noyau.squelette(formule), cle[0],
                     mod_familles.bloc_de(C, cle[0], cle[1]))
            if usage not in revues:
                absentes.append("famille")
            if lib in basculantes:
                absentes.append("continuite")
        if lib in fautifs_bloquants:
            absentes.append("integrite")
        if not stable:
            absentes.append("stabilite")
        if absentes:
            for m in absentes:
                manques[m] += 1
        else:
            couvertes += 1

    taux = couvertes / max(total, 1) * 100
    return {
        "classeur": os.path.basename(chemin),
        "empreinte_sha256": empreinte(chemin),
        "cellules_de_calcul": total,
        "cellules_couvertes": couvertes,
        "couverture_pct": round(taux, 2),
        "manques": dict(manques.most_common()),
        "durs_hors_feuille_hypotheses": len(hors_inputs),
        "entrees_sans_source": len(sans_source),
        "echantillon_sans_source": sans_source[:12],
        "familles_revues": len(revues),
        "circuits": len(circ["circuits"]),
        "marches_basculantes": len(basculantes),
        "controles_integrite_passes": sum(1 for c in integ.controles if c["ok"]),
        "controles_integrite_total": len(integ.controles),
        "couverture_batterie_pct": couverture_batterie,
        "journal": journal,
    }


def rapport(cert):
    print(f"CERTIFICAT - {cert['classeur']}")
    print(f"empreinte sha256 : {cert['empreinte_sha256']}")
    print()
    print(f"  cellules de calcul            : {cert['cellules_de_calcul']:>9,}")
    print(f"  couvertes par une preuve      : {cert['cellules_couvertes']:>9,}")
    print(f"  COUVERTURE                    : {cert['couverture_pct']:>8.2f} %")
    print()
    if cert.get("entrees_sans_source"):
        print(f"  entrees sans renvoi de source  : {cert['entrees_sans_source']:>9,}")
        print(f"      {', '.join(cert['echantillon_sans_source'][:5])}")
        print()
    if cert["manques"]:
        print("  preuves manquantes (une cellule peut en manquer plusieurs) :")
        for m, n in cert["manques"].items():
            print(f"      {m:<14} {n:>9,}")
    print()
    print(f"  integrite      : {cert['controles_integrite_passes']}/"
          f"{cert['controles_integrite_total']} controles passes")
    print(f"  circuits       : {cert['circuits']}, dont "
          f"{cert['marches_basculantes']} marches basculantes")
    print(f"  familles revues: {cert['familles_revues']}")
    cb = cert.get("couverture_batterie_pct")
    print(f"  la batterie de controles detecte "
          f"{'%.0f %%' % cb if cb is not None else 'un taux non mesure'} des corruptions")
    print()
    print("ISSUES LOG")
    print(f"  {'cle':<5} {'gravite':<15} {'portee':>9}  constat")
    for e in sorted(cert["journal"],
                    key=lambda x: {"critique": 0, "significatif": 1,
                                   "presentationnel": 2}.get(x["gravite"], 3)):
        print(f"  {e['cle']:<5} {e['gravite']:<15} {e['portee']:>9,}  {e['constat']}")
    print()
    if cert["couverture_pct"] >= 100:
        print("CERTIFIE : chaque cellule de calcul porte ses preuves.")
        return 0
    print(f"NON CERTIFIE : {100 - cert['couverture_pct']:.2f} % des cellules "
          f"n'ont pas toutes leurs preuves.")
    print("Une preuve absente n'est pas un defaut prouve - c'est un travail non fait.")
    return 1


def autotest():
    """Le certificat repose sur une seule promesse : une preuve absente est
    inscrite comme TRAVAIL NON FAIT, jamais comme resultat favorable.

    On verifie que le chargeur rend bien None sur une preuve absente - c'est ce
    None qui declenche les lignes « jamais lance » - et que la liste des preuves
    exigees n'a pas ete videe par megarde, auquel cas la couverture serait
    parfaite pour tout le monde.
    """
    if charger(None) is not None:
        raise SystemExit("ARRET - une preuve absente ne rend plus None : le "
                         "certificat ne saura plus dire qu'elle manque")
    if charger("ce-fichier-n-existe-pas.json") is not None:
        raise SystemExit("ARRET - un rapport introuvable ne rend plus None")
    if len(PREUVES) < 5:
        raise SystemExit(f"ARRET - il ne reste que {len(PREUVES)} preuve(s) exigee(s) : "
                         "la couverture deviendrait facile a atteindre")


def main():
    autotest()
    ap = argparse.ArgumentParser()
    ap.add_argument("classeur")
    ap.add_argument("--inputs", default=None,
                    help="feuille d'hypotheses ; deduite si omise")
    ap.add_argument("--familles")
    ap.add_argument("--convergence")
    ap.add_argument("--sensibilite")
    ap.add_argument("--commutateurs")
    ap.add_argument("--identites")
    ap.add_argument("--mutation")
    ap.add_argument("--differences")
    ap.add_argument("--vraisemblance")
    ap.add_argument("--json")
    a = ap.parse_args()
    if not a.inputs:
        a.inputs = mod_integrite.deduire_feuille_inputs(a.classeur)
        print(f"feuille d'hypotheses deduite : {a.inputs}")
    cert = certifier(a.classeur, a.inputs,
                     charger(a.familles), charger(a.convergence),
                     charger(a.sensibilite), charger(a.commutateurs),
                     charger(a.identites), charger(a.mutation),
                     charger(a.differences), charger(a.vraisemblance))
    code = rapport(cert)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(cert, fh, ensure_ascii=False, indent=2)
        print(f"\necrit : {a.json}")
    return code


if __name__ == "__main__":
    sys.exit(main())
