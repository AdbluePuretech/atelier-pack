# -*- coding: utf-8 -*-
"""Matrice des commutateurs : tous les runs promis fonctionnent-ils.

Un prompt qui annonce des cas, des contrefactuels et des breakers
independamment activables promet autant de classeurs differents. Un seul est
livre et note - les autres n'ont souvent jamais ete ouverts. C'est la ou se
cachent les divisions par zero, les batteries qui s'ouvrent et les boucles qui
ne convergent plus.

La matrice complete est hors de portee : treize commutateurs font 8 192
combinaisons, chacune un recalcul Excel. Le module couvre donc le plan qui
attrape le plus de defauts pour le moins de temps :

  - chaque commutateur bascule SEUL, les autres au livre ;
  - tous eteints, tous allumes ;
  - les combinaisons nommees explicitement, s'il y en a.

Et il annonce toujours combien de combinaisons existent contre combien il en a
essayees. Un plan partiel qui se presente comme exhaustif ment plus qu'il
n'informe.

Usage :
    python commutateurs.py "Classeur.xlsx" --batterie "22. Checks!D80"
    python commutateurs.py "Classeur.xlsx" --commutateurs sw_Case,b_Master --combo "sw_Case=1,b_Master=0"
"""
import argparse
import json
import os
import sys
import time

import noyau
import rejouer


def plan_de_bascule(commutateurs, etat_livre, combos):
    """(etiquette, {adresse: valeur}) pour chaque configuration a essayer."""
    plan = [("livre", {})]
    for c in commutateurs:
        v = etat_livre.get(c)
        if not isinstance(v, (int, float)):
            continue
        plan.append((f"{c}={0 if v else 1}", {c: 0 if v else 1}))
    if commutateurs:
        plan.append(("tous-eteints", {c: 0 for c in commutateurs}))
        plan.append(("tous-allumes", {c: 1 for c in commutateurs}))
    for i, combo in enumerate(combos, 1):
        poses = {}
        for morceau in combo.split(","):
            if "=" in morceau:
                k, v = morceau.split("=", 1)
                poses[k.strip()] = float(v) if "." in v else int(v)
        plan.append((f"combo{i}", poses))
    return plan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("classeur")
    ap.add_argument("--commutateurs",
                    help="liste d'adresses separees par des virgules")
    ap.add_argument("--prefixes", default="",
                    help="prefixes des plages nommees a considerer comme "
                         "commutateurs ; VIDE = on les reconnait a leur VALEUR "
                         "(0 ou 1), pas a leur nom. Un prefixe maison ne vaut "
                         "que pour le classeur qui l'a inspire.")
    ap.add_argument("--combo", action="append", default=[],
                    help='combinaison explicite, ex: "sw_Case=1,b_Master=0"')
    ap.add_argument("--batterie", help="adresse du total de la batterie ; trouvee toute seule si omise")
    ap.add_argument("--limite", type=int, default=0)
    ap.add_argument("--iterations", type=int, default=500)
    ap.add_argument("--json")
    a = ap.parse_args()

    if not a.batterie:
        a.batterie = noyau.trouver_batterie(noyau.Classeur(a.classeur))
        if a.batterie:
            print(f"batterie trouvee automatiquement : {a.batterie}")
        else:
            print("aucune batterie de controles reperee - on ne surveillera "
                  "que les cellules en erreur")

    if a.commutateurs:
        cibles = [x.strip() for x in a.commutateurs.split(",") if x.strip()]
    elif a.prefixes.strip():
        cibles = rejouer.entrees_nommees(
            a.classeur, tuple(p for p in a.prefixes.split(",") if p))
    else:
        # Un commutateur se reconnait a ce qu'il VAUT - 0 ou 1 - et non a la
        # facon dont il s'appelle. Chercher `sw_` sur un classeur qui nomme ses
        # interrupteurs `Prog_On` rend zero, et zero se lit comme « tout va
        # bien » alors que rien n'a ete bascule.
        valeurs = rejouer.entrees_nommees(a.classeur, None, valeurs=True)
        cibles = [n for n, v in valeurs.items()
                  if isinstance(v, (int, float)) and not isinstance(v, bool)
                  and v in (0, 1)]
    total_dispo = len(cibles)
    if not cibles:
        print("MATRICE DES COMMUTATEURS - "
              + os.path.basename(a.classeur))
        print("\nETAPE NON FAITE : aucun commutateur trouve.")
        print("  Ce n'est PAS un resultat favorable - aucune bascule n'a ete "
              "essayee.")
        print("  Les nommer avec --commutateurs.")
        if a.json:
            with open(a.json, "w", encoding="utf-8") as fh:
                json.dump({"classeur": a.classeur, "etape_faite": False,
                           "motif": "aucun commutateur", "commutateurs": 0,
                           "configurations_essayees": 0}, fh,
                          ensure_ascii=False, indent=1)
        return 2
    ignores = []
    if a.limite and len(cibles) > a.limite:
        ignores = cibles[a.limite:]
        cibles = cibles[:a.limite]

    sonde = rejouer.Rejeu(a.classeur, etiquette="sonde")
    etat_livre = sonde.relever(cibles) if cibles else {}
    sonde.nettoyer()

    plan = plan_de_bascule(cibles, etat_livre, a.combo)
    # Deux entrees du plan peuvent designer le MEME etat - « tous eteints »
    # vaut « X=0 » quand il n'y a qu'un commutateur deja a 1. Sans
    # dedoublonnage le taux de couverture depassait 100 %, ce qui est le genre
    # de nombre qui decredibilise tout le rapport.
    vus, unique = set(), []
    for etiquette, poses in plan:
        etat = tuple(sorted({**{c: etat_livre.get(c) for c in cibles}, **poses}.items()))
        if etat in vus:
            continue
        vus.add(etat)
        unique.append((etiquette, poses))
    plan = unique
    combinaisons_possibles = 2 ** len(cibles) if cibles else 1

    print(f"MATRICE DES COMMUTATEURS - {os.path.basename(a.classeur)}")
    print(f"commutateurs detectes      : {total_dispo}")
    if ignores:
        print(f"NON COUVERTS ({len(ignores)}) : {', '.join(ignores[:12])}")
    print(f"etat livre                 : "
          f"{ {k: v for k, v in list(etat_livre.items())[:8]} }")
    print(f"combinaisons possibles     : {combinaisons_possibles:,}")
    print(f"configurations essayees    : {len(plan)}"
          f"   ({min(100.0, len(plan) / max(combinaisons_possibles, 1) * 100):.2g} % de la matrice)")
    print()

    lignes = []
    ko = 0
    for etiquette, poses in plan:
        t0 = time.time()
        R = rejouer.Rejeu(a.classeur, etiquette=etiquette.replace("=", "_"))
        try:
            if poses:
                R.poser(poses)
            rec = R.recalculer(iterations=a.iterations)
            if rec["code"] != 0:
                etat = {"saine": False, "erreurs": -1, "batterie": None,
                        "echec_recalcul": rec["erreur"][:200]}
            else:
                etat = rejouer.sante(R, a.batterie)
            dt = time.time() - t0
            if not etat["saine"]:
                ko += 1
            print(f"  [{'OK ' if etat['saine'] else 'KO '}] {etiquette:<26} "
                  f"erreurs={etat['erreurs']:<5} batterie={etat.get('batterie')}"
                  f"   {dt:.0f}s")
            if not etat["saine"]:
                if etat.get("echec_recalcul"):
                    print(f"          recalcul : {etat['echec_recalcul'][:150]}")
                for e in etat.get("echantillon_erreurs", [])[:3]:
                    print(f"          {e}")
            lignes.append({"configuration": etiquette, "poses": poses, **etat,
                           "secondes": round(dt, 1)})
        finally:
            R.nettoyer()

    print()
    print("=" * 72)
    if ko == 0 and lignes:
        print(f"OK : {len(lignes)} configurations essayees, toutes saines.")
    else:
        print(f"DEFAUT : {ko} configurations sur {len(lignes)} cassent le modele.")
    print(f"  Couverture de la matrice : {len(plan)} sur {combinaisons_possibles:,} "
          f"combinaisons. Ce n'est PAS exhaustif.")
    if ignores:
        print(f"  {len(ignores)} commutateurs n'ont jamais ete bascules.")

    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump({"classeur": os.path.basename(a.classeur),
                       "commutateurs": total_dispo,
                       "non_couverts": ignores,
                       "combinaisons_possibles": combinaisons_possibles,
                       "configurations_essayees": len(plan),
                       "configurations_ko": ko,
                       "lignes": lignes}, fh, ensure_ascii=False, indent=2)
        print(f"\necrit : {a.json}")
    return 1 if ko else 0


if __name__ == "__main__":
    sys.exit(main())
