# -*- coding: utf-8 -*-
"""Dossier de convergence : les valeurs du classeur sont-elles des valeurs.

Un classeur circulaire ne rend pas un resultat, il rend le point ou son
iteration s'est arretee. Tant qu'on n'a pas prouve que ce point est unique et
stable, une valeur en cache n'est pas une reference - c'est un souvenir de
calcul.

Le controle : recalculer le meme classeur dans plusieurs configurations qui ne
devraient RIEN changer, et comparer les 70 000 valeurs en cache une a une. Pas
d'echantillon, pas de liste choisie : tout.

La configuration la plus severe est le depart A FROID. openpyxl, en
reenregistrant un classeur charge en mode formules, laisse tomber les valeurs en
cache : Excel repart alors de zero au lieu de repartir du point fixe precedent.
Si les deux chemins arrivent au meme endroit, le point fixe ne depend pas du
chemin.

Usage :
    python convergence.py "Classeur.xlsx" [--rapide] [--tolerance 1e-9] [--json r.json]
"""
import argparse
import collections
import json
import os
import sys
import time

import openpyxl

import rejouer

# (etiquette, iterations, ecart, passes, depart_a_froid)
PLAN_COMPLET = [
    ("corpus-500x3", 500, 1e-06, 3, False),
    ("court-100x1", 100, 1e-06, 1, False),
    ("serre-1000x5", 1000, 1e-08, 5, False),
    ("froid-500x3", 500, 1e-06, 3, True),
]
PLAN_RAPIDE = [
    ("corpus-500x3", 500, 1e-06, 3, False),
    ("froid-500x3", 500, 1e-06, 3, True),
]


def toutes_les_valeurs(chemin):
    """Toute valeur numerique en cache, adressee feuille!colonne!ligne."""
    wb = openpyxl.load_workbook(chemin, read_only=True, data_only=True)
    out = {}
    for ws in wb.worksheets:
        for row in ws.iter_rows(values_only=False):
            for c in row:
                if isinstance(c.value, (int, float)) and not isinstance(c.value, bool):
                    out[(ws.title, c.row, c.column)] = c.value
    wb.close()
    return out


def comparer_tout(ref, essai, tolerance, plancher):
    """Une tolerance RELATIVE seule ne veut rien dire pres de zero : passer de
    1e-10 a -1e-10 est un ecart relatif de 200 %, et c'est du bruit flottant.
    On exige donc les deux : l'ecart doit depasser un plancher absolu ET la
    tolerance relative pour compter."""
    bougent = []
    absentes = 0
    for cle, v in ref.items():
        if cle not in essai:
            absentes += 1
            continue
        w = essai[cle]
        if isinstance(v, (int, float)) and isinstance(w, (int, float)):
            if abs(v - w) <= plancher:
                continue
        e = rejouer.ecart_relatif(v, w)
        if e > tolerance:
            bougent.append((cle, v, w, e))
    bougent.sort(key=lambda x: -x[3])
    return bougent, absentes


def autotest():
    """Un controle qui ne sait pas voir bouger une valeur rendra toujours vert.

    Trois temoins : un jeu identique ne doit rien signaler ; un jeu dont une
    valeur a bouge de 10 % doit en signaler exactement une ; et le bruit
    flottant pres de zero ne doit pas compter, sinon l'etape hurle sur tout
    classeur - passer de 1e-12 a -1e-12 est un ecart relatif de 200 %.
    """
    ref = {("f", 1, 1): 100.0, ("f", 2, 1): 1e-12, ("f", 3, 1): -5.0}
    if comparer_tout(ref, dict(ref), 1e-6, 1e-9)[0]:
        raise SystemExit("ARRET - le controle est casse : il voit bouger un jeu identique")

    bouge = dict(ref)
    bouge[("f", 1, 1)] = 110.0
    vus = comparer_tout(ref, bouge, 1e-6, 1e-9)[0]
    if len(vus) != 1:
        raise SystemExit(f"ARRET - le controle est casse : {len(vus)} ecart(s) vu(s) "
                         "la ou une seule valeur a bouge")

    bruit = dict(ref)
    bruit[("f", 2, 1)] = -1e-12
    if comparer_tout(ref, bruit, 1e-6, 1e-9)[0]:
        raise SystemExit("ARRET - le plancher absolu ne protege plus du bruit "
                         "flottant pres de zero")


def main():
    autotest()
    ap = argparse.ArgumentParser()
    ap.add_argument("classeur")
    ap.add_argument("--rapide", action="store_true",
                    help="deux configurations au lieu de quatre")
    ap.add_argument("--tolerance", type=float, default=1e-09)
    ap.add_argument("--plancher", type=float, default=1e-08,
                    help="ecart absolu en dessous duquel on ne compte pas")
    ap.add_argument("--garder", action="store_true", help="ne pas effacer les copies")
    ap.add_argument("--json")
    a = ap.parse_args()

    plan = PLAN_RAPIDE if a.rapide else PLAN_COMPLET
    print(f"DOSSIER DE CONVERGENCE - {os.path.basename(a.classeur)}")
    print(f"reference : les valeurs en cache du fichier livre")
    reference = toutes_les_valeurs(a.classeur)
    print(f"valeurs numeriques en cache : {len(reference):,}")
    print(f"tolerance : ecart absolu > {a.plancher:g} ET relatif > {a.tolerance:g}")
    print(f"{len(plan)} configurations a rejouer, chacune passe par le vrai Excel\n")

    resultats = []
    verdict = 0
    for etiquette, it, ec, pa, froid in plan:
        t0 = time.time()
        print(f"  [{etiquette}] iterations={it} ecart={ec:g} passes={pa}"
              f"{' DEPART A FROID' if froid else ''} ...", flush=True)
        R = rejouer.Rejeu(a.classeur, etiquette=etiquette)
        if froid:
            R.poser({})          # relecture-reecriture : le cache tombe
        rec = R.recalculer(iterations=it, ecart=ec, passes=pa)
        if rec["code"] != 0:
            print(f"      ECHEC DU RECALCUL (code {rec['code']})")
            print(f"      {rec['erreur'][:400]}")
            resultats.append({"configuration": etiquette, "recalcul": "echec",
                              "detail": rec["erreur"][:400]})
            verdict = 2
            if not a.garder:
                R.nettoyer()
            continue

        essai = toutes_les_valeurs(R.chemin)
        bougent, absentes = comparer_tout(reference, essai, a.tolerance, a.plancher)
        err = R.erreurs()
        dt = time.time() - t0

        par_feuille = collections.Counter(c[0][0] for c in bougent)
        pire = bougent[0][3] if bougent else 0.0
        print(f"      {len(bougent):>7,} valeurs bougent sur {len(reference):,}"
              f"   pire ecart relatif {pire:.2e}"
              f"   erreurs {len(err)}   {dt:.0f}s")
        if bougent:
            for f, n in par_feuille.most_common(5):
                print(f"          {f:<32} {n:>7,}")
            for cle, v, w, e in bougent[:3]:
                print(f"          {cle[0]}!{cle[2]}:{cle[1]}  {v!r} -> {w!r}  ({e:.2e})")
            verdict = max(verdict, 1)
        if err:
            print(f"      CELLULES EN ERREUR : {err[:3]}")
            verdict = 2

        resultats.append({
            "configuration": etiquette,
            "iterations": it, "ecart": ec, "passes": pa, "depart_a_froid": froid,
            "valeurs_comparees": len(reference),
            "valeurs_qui_bougent": len(bougent),
            "absentes": absentes,
            "pire_ecart_relatif": pire,
            "cellules_en_erreur": len(err),
            "par_feuille": dict(par_feuille.most_common(10)),
            "echantillon": [{"cellule": f"{c[0]}!{c[2]}:{c[1]}", "reference": v,
                             "essai": w, "ecart": e} for c, v, w, e in bougent[:25]],
            "secondes": round(dt, 1),
        })
        if not a.garder:
            R.nettoyer()

    print()
    print("=" * 72)
    if verdict == 0:
        print("OK : le point fixe ne depend ni du nombre d'iterations ni du")
        print("     point de depart. Les valeurs en cache sont des valeurs.")
    elif verdict == 1:
        print("DEFAUT : des valeurs bougent d'une configuration a l'autre.")
        print("         Tant que ces ecarts ne sont pas expliques, une valeur en")
        print("         cache n'est pas une reference opposable.")
    else:
        print("BLOQUANT : un recalcul a echoue ou a produit des erreurs.")

    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump({"classeur": os.path.basename(a.classeur),
                       "tolerance": a.tolerance,
                       "valeurs_de_reference": len(reference),
                       "verdict": verdict,
                       "configurations": resultats}, fh, ensure_ascii=False, indent=2)
        print(f"\necrit : {a.json}")
    return verdict


if __name__ == "__main__":
    sys.exit(main())
