# -*- coding: utf-8 -*-
"""Controle des circuits : ou sont les cycles, et qu'y a-t-il dedans.

Le modele porte des circularites VOULUES. La doctrine qui les rend
calculables tient en une phrase : toute reponse SITUEE DANS un circuit doit
etre continue et monotone. Une marche - IF a seuil, MIN, MAX - placee dans
un circuit fait osciller le point fixe au lieu de le faire converger, et
Excel rend alors une valeur qui depend du chemin de calcul.

Ce module tranche mecaniquement, sans avis :
  1. il calcule les composantes fortement connexes du graphe de formules ;
  2. il inventorie les reponses potentiellement discontinues ;
  3. il croise les deux. Une discontinuite DANS une composante est un defaut,
     la meme discontinuite HORS composante est un masque ou une sortie de
     reporting, donc legitime.

Usage :
    python circuits.py "Classeur.xlsx" [--json rapport.json]
"""
import argparse
import collections
import json
import re
import sys

import noyau

# Une marche vraie. Les formes lissees - 0.5*(a+b+SQRT((a-b)^2+eps)) - ne
# matchent pas, et c'est le but : ce sont elles qu'on veut voir a la place.
MARCHE = re.compile(r"\b(MAX|MIN)\s*\(", re.I)
SEUIL = re.compile(r"\bIF\s*\(", re.I)

# Un IF dont les deux branches sont des constantes et dont le test porte sur
# une comparaison est un drapeau binaire : c'est la forme la plus dangereuse
# dans un circuit, et la plus anodine en dehors.
DRAPEAU = re.compile(r"^=IF\([^,]+[<>=][^,]+,\s*[-0-9.]+\s*,\s*[-0-9.]+\s*\)$", re.I)


def _args(formule, debut):
    """Decoupe les arguments d'un appel dont la parenthese ouvre a `debut`.

    Retourne la liste des arguments bruts. Sert a isoler le TEST d'un IF :
    c'est lui, et lui seul, qui decide si la marche peut basculer.
    """
    prof = 0
    cur = []
    out = []
    dans_chaine = False
    i = debut
    while i < len(formule):
        ch = formule[i]
        if dans_chaine:
            cur.append(ch)
            if ch == '"':
                dans_chaine = False
        elif ch == '"':
            dans_chaine = True
            cur.append(ch)
        elif ch == "(":
            prof += 1
            if prof > 1:
                cur.append(ch)
        elif ch == ")":
            prof -= 1
            if prof == 0:
                out.append("".join(cur))
                return out
            cur.append(ch)
        elif ch == "," and prof == 1:
            out.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
        i += 1
    return out


def _bascule_dans_le_circuit(C, cle, formule, circuit_de, n_circuit):
    """Vrai si une marche de cette formule peut basculer PENDANT l'iteration.

    Un IF dont le test ne lit que des masques, des constantes ou des cellules
    situees hors du circuit est fige pendant l'iteration : la fonction reste
    continue en ses variables de boucle. Seul un test qui lit une cellule DU
    MEME circuit est une vraie marche.
    """
    for m in re.finditer(r"\b(IF|MAX|MIN)\s*\(", formule, re.I):
        nom = m.group(1).upper()
        args = _args(formule, m.end() - 1)
        if not args:
            continue
        # pour un IF seul le test compte ; pour MAX/MIN, tous les arguments
        a_tester = args[:1] if nom == "IF" else args
        for arg in a_tester:
            for r in C.references(cle, "=" + arg):
                if circuit_de.get(r) == n_circuit:
                    return True, nom, arg[:70]
    return False, "", ""


def entetes_periodes(C):
    """Retrouve la colonne -> libelle de periode sur une feuille periodique."""
    for feuille in ("02. Timeline_Control", "08. Pocket_Price_Waterfall"):
        if feuille not in C.feuilles:
            continue
        for (f, l, col), v in C.textes.items():
            if f != feuille or not isinstance(v, str):
                continue
            if v.strip().upper() in ("FY0", "FY-2A"):
                ligne = l
                out = {}
                for (f2, l2, c2), v2 in C.textes.items():
                    if f2 == feuille and l2 == ligne and isinstance(v2, str):
                        out[c2] = v2.strip()
                if len(out) >= 8:
                    return out
    return {}


def analyser(chemin):
    C = noyau.Classeur(chemin)
    adj = C.graphe()
    comps = C.composantes(adj)
    cycles = [c for c in comps if len(c) > 1]
    cycles.sort(key=len, reverse=True)

    # cellule -> numero de circuit
    circuit_de = {}
    for n, comp in enumerate(cycles, 1):
        for i in comp:
            circuit_de[C.rev_idx[i]] = n

    entetes = entetes_periodes(C)

    inventaire = []
    figees = []
    for cle, f in C.formules.items():
        est_marche = bool(MARCHE.search(f))
        est_seuil = bool(SEUIL.search(f))
        if not (est_marche or est_seuil):
            continue
        n = circuit_de.get(cle, 0)
        entree = {
            "cellule": noyau.libelle(cle),
            "feuille": cle[0],
            "periode": entetes.get(cle[2], "?"),
            "genre": "MAX/MIN" if est_marche else ("drapeau" if DRAPEAU.match(f.replace(" ", "")) else "IF"),
            "circuit": n,
            "formule": f[:160],
        }
        if n:
            bascule, quoi, test = _bascule_dans_le_circuit(C, cle, f, circuit_de, n)
            if bascule:
                entree["bascule"] = quoi
                entree["test"] = test
                inventaire.append(entree)
            else:
                figees.append(entree)
        else:
            inventaire.append(entree)

    dedans = [x for x in inventaire if x["circuit"]]
    dehors = [x for x in inventaire if not x["circuit"]]
    resume_figees = dict(collections.Counter(x["feuille"] for x in figees).most_common())

    resume = {
        "cellules_de_formule": len(C.formules),
        "arcs": sum(len(a) for a in adj),
        "circuits": [
            {
                "n": n,
                "taille": len(comp),
                "feuilles": dict(collections.Counter(C.rev_idx[i][0] for i in comp).most_common()),
                "periodes": dict(collections.Counter(
                    entetes.get(C.rev_idx[i][2], "?") for i in comp).most_common()),
            }
            for n, comp in enumerate(cycles, 1)
        ],
        "cellules_en_cycle": sum(len(c) for c in cycles),
        "discontinuites_dans_un_circuit": dedans,
        "discontinuites_hors_circuit": len(dehors),
        "hors_circuit_par_feuille": dict(
            collections.Counter(x["feuille"] for x in dehors).most_common()),
        "marches_figees_dans_un_circuit": len(figees),
        "figees_par_feuille": resume_figees,
    }
    return C, resume


def rapport(resume):
    print(f"cellules de formule        : {resume['cellules_de_formule']:>8,}")
    print(f"arcs de dependance         : {resume['arcs']:>8,}")
    print(f"cellules en cycle          : {resume['cellules_en_cycle']:>8,}")
    print(f"circuits detectes          : {len(resume['circuits']):>8}")
    print()
    for c in resume["circuits"]:
        per = ", ".join(k for k in c["periodes"] if k != "?") or "?"
        print(f"  circuit {c['n']:<2} {c['taille']:>7,} cellules   periodes : {per}")
        for f, n in list(c["feuilles"].items())[:8]:
            print(f"       {f:<32} {n:>6,}")
    print()
    dedans = resume["discontinuites_dans_un_circuit"]
    print("=" * 72)
    if dedans:
        print(f"DEFAUT : {len(dedans)} marche(s) POUVANT BASCULER pendant l'iteration")
        par = collections.Counter((x["feuille"], x.get("bascule", x["genre"])) for x in dedans)
        for (f, g), n in par.most_common():
            print(f"    {f:<32} {g:<10} {n:>6}")
        print("\n  echantillon (test qui lit une cellule du meme circuit) :")
        for x in dedans[:10]:
            print(f"    circuit {x['circuit']}  {x['cellule']:<32} test: {x.get('test','')}")
    else:
        print("OK : aucune marche ne peut basculer pendant l'iteration.")
        print("     Toute reponse situee dans un circuit y est continue.")
    print()
    print(f"  marches figees dans un circuit (test hors boucle : masque, "
          f"constante) : {resume['marches_figees_dans_un_circuit']:,}")
    print(f"      {resume['figees_par_feuille']}")
    print(f"  marches hors de tout circuit (reporting, selecteurs) : "
          f"{resume['discontinuites_hors_circuit']:,}")
    print(f"      {resume['hors_circuit_par_feuille']}")
    return 1 if dedans else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("classeur")
    ap.add_argument("--json")
    a = ap.parse_args()
    _, resume = analyser(a.classeur)
    code = rapport(resume)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(resume, fh, ensure_ascii=False, indent=2)
        print(f"\necrit : {a.json}")
    return code


if __name__ == "__main__":
    sys.exit(main())
