# -*- coding: utf-8 -*-
"""Registre des familles de formules : ce qu'il reste a lire pour tout couvrir.

On ne lit pas 70 000 formules. On les reduit a leurs familles structurelles -
references neutralisees, litteraux neutralises - et on lit les familles. Chaque
cellule appartient alors a une famille, et une famille revue couvre d'un coup
toutes ses cellules.

Le registre est un fichier JSON qui SURVIT d'une passe a l'autre : il porte le
statut de revue de chaque famille. Une famille inchangee garde son statut ; une
famille dont le squelette a bouge repasse a l'etat non revue, parce que ce n'est
plus la meme formule.

Usage :
    python familles.py "Classeur.xlsx"                      # etat de la revue
    python familles.py "Classeur.xlsx" --registre f.json    # cree ou met a jour
    python familles.py "Classeur.xlsx" --registre f.json --lister-a-revoir
    python familles.py "Classeur.xlsx" --registre f.json --marquer <id> --statut vue
"""
import argparse
import collections
import hashlib
import json
import os
import sys

import noyau


def identifiant(*morceaux):
    return hashlib.sha1("|".join(morceaux).encode("utf-8")).hexdigest()[:12]


EN_TETE = ("A.", "B.", "C.", "D.", "E.", "F.", "G.", "H.")


def bloc_de(C, feuille, ligne, _cache={}):
    """Le dernier en-tete de bloc au-dessus d'une ligne. C'est lui qui dit ce
    que la formule est CENSEE calculer."""
    cle = (feuille, ligne)
    if cle in _cache:
        return _cache[cle]
    for ll in range(ligne, max(ligne - 400, 0), -1):
        v = C.textes.get((feuille, ll, 3))
        if isinstance(v, str) and v.strip()[:2] in EN_TETE and len(v.strip()) > 4:
            _cache[cle] = v.strip()
            return _cache[cle]
    _cache[cle] = "(hors bloc)"
    return _cache[cle]


def recenser(chemin):
    """L'unite de revue est l'USAGE - squelette x feuille x bloc - et non le
    squelette seul.

    La premiere version groupait par squelette. C'etait faux, et cher : sur une
    golden reelle, `=X*X*X*(#-X)` servait CINQ tetes de remise differentes -
    l'une sur le prix liste, deux sur le gross, deux sur l'invoice. Le squelette
    est indifferent a la base : en verifier un usage ne dit rien des quatre
    autres, et marquer la famille « vue » couvrait 9 000 cellules dont 7 200
    n'avaient ete lues par personne.

    Le bloc, lui, porte le libelle qui dit ce que la formule est censee faire.
    C'est la plus petite unite qu'on puisse juger.
    """
    C = noyau.Classeur(chemin)
    fam = collections.defaultdict(lambda: {"cellules": 0, "exemples": []})
    for cle, f in C.formules.items():
        s = noyau.squelette(f)
        k = (s, cle[0], bloc_de(C, cle[0], cle[1]))
        e = fam[k]
        e["cellules"] += 1
        if len(e["exemples"]) < 3:
            e["exemples"].append({"cellule": noyau.libelle(cle), "formule": f[:220]})
    out = []
    for (s, feuille, bloc), e in fam.items():
        out.append({
            "id": identifiant(s, feuille, bloc),
            "squelette": s,
            "feuille": feuille,
            "bloc": bloc,
            "cellules": e["cellules"],
            "exemples": e["exemples"],
        })
    out.sort(key=lambda x: -x["cellules"])
    return C, out


def fusionner(nouvelles, chemin_registre):
    """Reprend les statuts du registre precedent, pour les familles inchangees."""
    ancien = {}
    if chemin_registre and os.path.exists(chemin_registre):
        with open(chemin_registre, encoding="utf-8") as fh:
            for e in json.load(fh).get("familles", []):
                ancien[e["id"]] = e
    reprises = perdues = 0
    for f in nouvelles:
        a = ancien.get(f["id"])
        if a and a.get("statut") and a["statut"] != "a_revoir":
            f["statut"] = a["statut"]
            f["note"] = a.get("note", "")
            reprises += 1
        else:
            f["statut"] = "a_revoir"
            f["note"] = ""
    for i, e in ancien.items():
        if e.get("statut") not in (None, "a_revoir") and i not in {x["id"] for x in nouvelles}:
            perdues += 1
    return reprises, perdues


def rapport(familles, total_cellules, reprises=0, perdues=0):
    par_statut = collections.Counter(f.get("statut", "a_revoir") for f in familles)
    couvertes = sum(f["cellules"] for f in familles if f.get("statut") in ("vue", "anomalie"))
    print(f"cellules de formule        : {total_cellules:>8,}")
    print(f"USAGES (squelette x bloc)  : {len(familles):>8,}")
    print(f"  singletons               : {sum(1 for f in familles if f['cellules'] == 1):>8,}")
    print(f"  cellules par usage       : {total_cellules / max(len(familles), 1):>8.1f}")
    print()
    for s in ("vue", "anomalie", "a_revoir"):
        n = par_statut.get(s, 0)
        c = sum(f["cellules"] for f in familles if f.get("statut") == s)
        print(f"  {s:<10} {n:>5} usages     {c:>8,} cellules")
    print()
    taux = couvertes / max(total_cellules, 1) * 100
    print(f"COUVERTURE PAR LA REVUE    : {taux:>7.2f} %  "
          f"({couvertes:,} / {total_cellules:,} cellules)")
    if reprises or perdues:
        print(f"  statuts repris de la passe precedente : {reprises}")
        if perdues:
            print(f"  familles revues DISPARUES (squelette modifie) : {perdues} "
                  f"-> a relire")
    manque = [f for f in familles if f.get("statut") == "a_revoir"]
    if manque:
        print()
        print(f"  les 10 usages non revus les plus repandus "
              f"({sum(f['cellules'] for f in manque):,} cellules au total) :")
        for f in manque[:10]:
            print(f"    {f['id']}  {f['cellules']:>7,} cel.  {f['feuille'][:24]:<24} "
                  f"{f.get('bloc', '')[:44]}")
            print(f"                        {f['squelette'][:80]}")
    return taux


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("classeur")
    ap.add_argument("--registre", help="fichier JSON de suivi de la revue")
    ap.add_argument("--lister-a-revoir", action="store_true")
    ap.add_argument("--marquer", help="identifiant de famille a marquer")
    ap.add_argument("--statut", choices=["vue", "anomalie", "a_revoir"], default="vue")
    ap.add_argument("--note", default="")
    ap.add_argument("--appliquer", help="fichier JSON {id: {statut, note}} a appliquer en lot")
    a = ap.parse_args()

    C, familles = recenser(a.classeur)
    total = len(C.formules)
    reprises, perdues = fusionner(familles, a.registre)

    if a.appliquer:
        with open(a.appliquer, encoding="utf-8") as fh:
            lot = json.load(fh)
        n = 0
        for f in familles:
            e = lot.get(f["id"])
            if e:
                f["statut"] = e.get("statut", "vue")
                f["note"] = e.get("note", "")
                n += 1
        inconnus = [i for i in lot if i not in {f["id"] for f in familles}]
        print(f"{n} famille(s) marquee(s)"
              + (f" ; {len(inconnus)} identifiant(s) inconnu(s) : {inconnus[:5]}"
                 if inconnus else ""))

    if a.marquer:
        vise = [f for f in familles if f["id"] == a.marquer]
        if not vise:
            print(f"famille inconnue : {a.marquer}")
            return 2
        vise[0]["statut"] = a.statut
        vise[0]["note"] = a.note
        print(f"{a.marquer} -> {a.statut}  ({vise[0]['cellules']:,} cellules)")

    if a.lister_a_revoir:
        for f in familles:
            if f["statut"] == "a_revoir":
                print(f"\n=== {f['id']}   {f['cellules']:,} cellules   {f.get('feuille', f.get('feuilles', ''))}")
                print(f"    {f['squelette'][:200]}")
                for ex in f["exemples"]:
                    print(f"      {ex['cellule']:<34} {ex['formule'][:130]}")
        return 0

    taux = rapport(familles, total, reprises, perdues)

    if a.registre:
        with open(a.registre, "w", encoding="utf-8") as fh:
            json.dump({"classeur": os.path.basename(a.classeur),
                       "cellules_de_formule": total,
                       "couverture_revue_pct": round(taux, 2),
                       "familles": familles}, fh, ensure_ascii=False, indent=2)
        print(f"\nregistre : {a.registre}")
    return 0 if taux >= 100 else 1


if __name__ == "__main__":
    sys.exit(main())
