"""Decrit un classeur de candidat, sans rien savoir de la golden.

    python systeme/scripts/qa-pack/bilan_classeur.py "AI Output.xlsx"

Le rollout ne se juge pas seulement a la note. Avant de compter les points, on
regarde ce que le candidat a REELLEMENT produit : combien d'onglets, combien de
formules, s'il a arme le calcul iteratif, s'il a laisse des cellules en erreur,
et si son classeur est circulaire du tout.

Ce script ne connait aucune structure attendue. Il lit ce qui est la, ce qui
permet de le passer sur n'importe quel candidat de n'importe quel pack.
"""
from __future__ import annotations

import argparse
import re
from collections import Counter

from openpyxl import load_workbook

ERREURS = ("#REF!", "#VALUE!", "#DIV/0!", "#NAME?", "#N/A", "#NUM!", "#NULL!", "Err:")
FONCTION = re.compile(r"(?<![A-Za-z0-9_.])([A-Z][A-Z0-9._]{1,})\s*\(")
MODERNES = {"LET", "LAMBDA", "XLOOKUP", "XMATCH", "FILTER", "SORT", "UNIQUE",
            "SEQUENCE", "TEXTJOIN", "IFS", "MAXIFS", "MINIFS", "SWITCH"}


def main(chemin):
    wf = load_workbook(chemin)
    wv = load_workbook(chemin, data_only=True)

    calc = wf.calculation
    print("=" * 78)
    print(f"BILAN DU CLASSEUR  {chemin}")
    print("=" * 78)
    print(f"  onglets                 : {len(wf.sheetnames)}")
    print(f"  calcul iteratif arme    : {bool(getattr(calc, 'iterate', False))}"
          f"   ({getattr(calc, 'iterateCount', '-')} passages,"
          f" ecart {getattr(calc, 'iterateDelta', '-')})")
    print(f"  plages nommees          : {len(wf.defined_names)}")

    total_f = total_v = err = 0
    fonctions, par_feuille, liens = Counter(), [], 0
    for ws in wf.worksheets:
        nf = nv = 0
        for row in ws.iter_rows():
            for c in row:
                v = c.value
                if isinstance(v, str) and v.startswith("="):
                    nf += 1
                    fonctions.update(FONCTION.findall(v))
                    liens += v.count("!")
                elif isinstance(v, (int, float)):
                    nv += 1
        for row in wv[ws.title].iter_rows():
            for c in row:
                if isinstance(c.value, str) and c.value.startswith(ERREURS):
                    err += 1
        total_f += nf
        total_v += nv
        par_feuille.append((ws.title, nf, nv))

    print(f"  cellules de formule     : {total_f:,}")
    print(f"  valeurs en dur          : {total_v:,}")
    print(f"  references inter-onglet : {liens:,}")
    print(f"  cellules en ERREUR      : {err}")
    hors = sorted(set(fonctions) & MODERNES)
    print(f"  fonctions hors portee de LibreOffice : {', '.join(hors) if hors else 'AUCUNE'}")
    cache = sum(1 for ws in wv.worksheets for row in ws.iter_rows()
                for c in row if isinstance(c.value, (int, float)))
    print(f"  valeurs en cache        : {cache:,}"
          + ("" if cache else "   <-- classeur JAMAIS recalcule, non gradable en l'etat"))

    print("\n  ONGLET                              formules   valeurs")
    for nom, nf, nv in par_feuille:
        print(f"    {nom[:34]:34s} {nf:>8,d}  {nv:>8,d}")

    print("\n  FONCTIONS EMPLOYEES")
    print("    " + "  ".join(f"{f}:{n}" for f, n in fonctions.most_common(18)))
    return total_f


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("classeur")
    main(ap.parse_args().classeur)
