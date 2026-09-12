# -*- coding: utf-8 -*-
"""Comparer deux classeurs cellule par cellule.

Sur un modele **genere**, c'est la preuve qu'aucun auditeur humain ne peut
produire : on relance le generateur, et on compare son resultat au fichier
livre. Tout ecart est soit une retouche faite a la main apres generation, soit
un generateur non deterministe. Les deux sont des constats, pas des
impressions - et la question qui coute le plus cher a un auditeur, « quelqu'un
a-t-il ecrase une cellule au milieu d'une serie », se liquide en une passe.

Le module sert aussi a comparer deux versions successives d'un meme classeur :
ce qui a change entre `avant` et `apres`, et rien d'autre.

On compare les FORMULES, les valeurs en dur et les libelles - jamais les
valeurs en cache : un fichier fraichement genere n'en a pas, et leur absence
n'est pas un ecart.

Usage :
    python differencier.py "reference.xlsx" "candidat.xlsx" [--json d.json]
    python differencier.py ... --tolerance 1e-09 --max 40
"""
import argparse
import collections
import json
import os
import re
import sys

import noyau

ESPACES = re.compile(r"\s+")


def normaliser(f):
    return ESPACES.sub("", f).replace("$", "")


def comparer(ref, cand, tolerance=1e-09):
    A = noyau.Classeur(ref)
    B = noyau.Classeur(cand)

    ecarts = {"formule": [], "dur": [], "texte": [],
              "absente_du_candidat": [], "absente_de_la_reference": []}

    # --- formules ---------------------------------------------------------
    for cle, fa in A.formules.items():
        fb = B.formules.get(cle)
        if fb is None:
            if cle in B.durs or cle in B.textes:
                ecarts["formule"].append(
                    (noyau.libelle(cle), fa[:90], f"<n'est plus une formule>"))
            else:
                ecarts["absente_du_candidat"].append((noyau.libelle(cle), fa[:90]))
        elif normaliser(fa) != normaliser(fb):
            ecarts["formule"].append((noyau.libelle(cle), fa[:90], fb[:90]))
    for cle, fb in B.formules.items():
        if cle not in A.formules and cle not in A.durs and cle not in A.textes:
            ecarts["absente_de_la_reference"].append((noyau.libelle(cle), fb[:90]))

    # --- valeurs en dur ----------------------------------------------------
    for cle, va in A.durs.items():
        vb = B.durs.get(cle)
        if vb is None:
            if cle not in B.formules:
                ecarts["absente_du_candidat"].append((noyau.libelle(cle), repr(va)))
        elif isinstance(va, (int, float)) and isinstance(vb, (int, float)):
            base = max(abs(va), abs(vb), 1e-12)
            if abs(va - vb) / base > tolerance:
                ecarts["dur"].append((noyau.libelle(cle), va, vb))
        elif va != vb:
            ecarts["dur"].append((noyau.libelle(cle), va, vb))

    # --- libelles -----------------------------------------------------------
    for cle, ta in A.textes.items():
        tb = B.textes.get(cle)
        if tb is not None and ta != tb:
            ecarts["texte"].append((noyau.libelle(cle), str(ta)[:60], str(tb)[:60]))

    # --- plages nommees -------------------------------------------------------
    noms_a, noms_b = set(A.noms), set(B.noms)
    ecarts["noms_en_moins"] = sorted(noms_a - noms_b)
    ecarts["noms_en_plus"] = sorted(noms_b - noms_a)

    resume = {
        "reference": os.path.basename(ref),
        "candidat": os.path.basename(cand),
        "formules_reference": len(A.formules),
        "formules_candidat": len(B.formules),
        "durs_reference": len(A.durs),
        "durs_candidat": len(B.durs),
        "ecarts_de_formule": len(ecarts["formule"]),
        "ecarts_de_valeur_en_dur": len(ecarts["dur"]),
        "ecarts_de_libelle": len(ecarts["texte"]),
        "absentes_du_candidat": len(ecarts["absente_du_candidat"]),
        "absentes_de_la_reference": len(ecarts["absente_de_la_reference"]),
        "noms_en_moins": len(ecarts["noms_en_moins"]),
        "noms_en_plus": len(ecarts["noms_en_plus"]),
    }
    return resume, ecarts


def rapport(resume, ecarts, maxi=15):
    print(f"REFERENCE : {resume['reference']}")
    print(f"CANDIDAT  : {resume['candidat']}")
    print(f"  formules      {resume['formules_reference']:>8,} contre "
          f"{resume['formules_candidat']:>8,}")
    print(f"  valeurs dures {resume['durs_reference']:>8,} contre "
          f"{resume['durs_candidat']:>8,}")
    print()
    total = (resume["ecarts_de_formule"] + resume["ecarts_de_valeur_en_dur"]
             + resume["absentes_du_candidat"] + resume["absentes_de_la_reference"])
    for cle, lib in (("ecarts_de_formule", "formules qui different"),
                     ("ecarts_de_valeur_en_dur", "valeurs en dur qui different"),
                     ("absentes_du_candidat", "presentes ici, absentes la-bas"),
                     ("absentes_de_la_reference", "absentes ici, presentes la-bas"),
                     ("ecarts_de_libelle", "libelles qui different"),
                     ("noms_en_moins", "plages nommees perdues"),
                     ("noms_en_plus", "plages nommees ajoutees")):
        n = resume[cle]
        print(f"  {'OK  ' if not n else 'ECART'}  {lib:<34} {n:>8,}")

    for cle, lib in (("formule", "FORMULES QUI DIFFERENT"),
                     ("dur", "VALEURS EN DUR QUI DIFFERENT"),
                     ("absente_du_candidat", "ABSENTES DU CANDIDAT"),
                     ("absente_de_la_reference", "ABSENTES DE LA REFERENCE")):
        lst = ecarts[cle]
        if not lst:
            continue
        print(f"\n--- {lib} ({len(lst):,})")
        par = collections.Counter(x[0].split("!")[0] for x in lst)
        for f, n in par.most_common(8):
            print(f"      {f:<34} {n:>7,}")
        for x in lst[:maxi]:
            if len(x) == 3:
                print(f"      {x[0]:<30}")
                print(f"          ref : {x[1]}")
                print(f"          cand: {x[2]}")
            else:
                print(f"      {x[0]:<30} {x[1]}")

    print()
    if total == 0:
        print("IDENTIQUES : le candidat reproduit la reference formule pour formule.")
        print("Sur un modele genere, cela prouve qu'aucune cellule n'a ete")
        print("retouchee a la main apres generation.")
    else:
        print(f"{total:,} ecarts. Sur un modele genere, chacun est soit une")
        print("retouche manuelle, soit un generateur non deterministe.")
    return 0 if total == 0 else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reference")
    ap.add_argument("candidat")
    ap.add_argument("--tolerance", type=float, default=1e-09)
    ap.add_argument("--max", type=int, default=15)
    ap.add_argument("--json")
    a = ap.parse_args()
    resume, ecarts = comparer(a.reference, a.candidat, a.tolerance)
    code = rapport(resume, ecarts, a.max)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump({"resume": resume,
                       "ecarts": {k: v[:300] if isinstance(v, list) else v
                                  for k, v in ecarts.items()}},
                      fh, ensure_ascii=False, indent=2)
        print(f"\necrit : {a.json}")
    return code


if __name__ == "__main__":
    sys.exit(main())
