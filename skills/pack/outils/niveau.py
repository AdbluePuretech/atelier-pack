# -*- coding: utf-8 -*-
"""Mesure le niveau INTRINSEQUE d'un classeur : ce qui se passe dans les onglets,
pas combien il y en a.

    python niveau.py "GoldenSolution - X.xlsx"
    python niveau.py "GoldenSolution - X.xlsx" --niveau L3 --detail --json niveau.json

Le compte d'onglets ne dit rien de la difficulte : Rigel construit 23 onglets de
calcul et sort a 0,92, Cardinal en construit 65 et sort a 0,31. Un onglet de 10 000
cellules qui recopient la meme formule est du volume ; un onglet qui porte 300
lignes de logique differentes, chacune sur ses propres termes, est de la granularite.

L'unite est la LOGIQUE : une formule ecrite en notation relative (R1C1). Une ligne
recopiee sur 60 colonnes, un bloc replique pour neuf scenarios, un echeancier
vertical de 180 mois comptent une fois chacun. Deux lignes qui lisent des termes
differents - un contrat et son voisin, chacun avec sa date et son plafond - comptent
deux fois. C'est ce qui separe la granularite du volume.

Cinq mesures, lues dans le fichier, jamais dans le generateur :

  LOGIQUES DISTINCTES     formules R1C1 differentes, dans tout le classeur
  LOGIQUES PAR ONGLET     mediane, par onglet de calcul : la densite d'un onglet
  SOPHISTICATION          part des logiques qui portent une condition, une
                          comparaison, une recherche, une date, ou deux fonctions
                          imbriquees
  HYPOTHESES CONSOMMEES   cellules de valeur que lisent les formules : un registre
                          de 40 contrats a 6 termes en consomme 240, la meme ligne
                          repliquee 40 fois en consomme 6
  REPETITION              formules par logique : haute, c'est du volume

Deux mesures ont ete ecartees a la calibration du 14/09/2026, et il ne faut pas
les reintroduire : le squelette de formule (references neutralisees), qui confond
« prix x volume » et « taux x encours » et tasse tous les classeurs entre 87 et 407
logiques ; la profondeur de chaine du graphe, qui depend de la mise en page (un
echeancier vertical la porte a 149 sur Ashford, 11 sur Cardinal, le plus dur).

Ce que l'outil ne mesure PAS, et qui se declare en phase 1 : les decisions
derivees (le seul axe qui a suivi le score, et il est invisible dans les formules :
Cardinal n'a pas plus de logiques que les packs faciles), les boucles nommees
(compter_boucles.py, amplitude_boucles.py) et la part du pool en transcription.
Un niveau tenu sur ces cinq mesures seules n'est pas un niveau tenu.
"""
import argparse
import collections
import json
import re
import statistics
import sys
from pathlib import Path

from openpyxl.utils import column_index_from_string

sys.path.insert(0, str(Path(__file__).resolve().parent))
import noyau  # noqa: E402

INTERCALAIRE = re.compile(r"^[\s>«»<|\-–—=•*.~_]+$|>>|<<")
HYPOTHESES = re.compile(r"^\s*input", re.I)    # la feuille d'hypotheses ne calcule pas le modele
MIN_FORMULES = 20                               # sous ce seuil, un onglet ne calcule pas
FONCTION = re.compile(r"(?<![A-Za-z0-9_.])([A-Z][A-Z0-9._]*)\s*\(")
CHAINE = re.compile(r'"(?:[^"]|"")*"')
COMPARAISON = re.compile(r"<=|>=|<>|(?<![<>])[<>]|(?<=[A-Za-z0-9\])])=")
REF1 = re.compile(r"(\$?)([A-Z]{1,3})(\$?)([0-9]+)")
LIEN = re.compile(r"^=\s*[-+]?\s*(?:(?:'(?:[^']|'')+'|[A-Za-z_][A-Za-z0-9_.]*)!)?\$?[A-Z]{1,3}\$?[0-9]+\s*$")
MARQUEURS = {"IF", "IFS", "IFERROR", "SWITCH", "CHOOSE", "AND", "OR", "NOT", "MIN", "MAX",
             "MINIFS", "MAXIFS", "SUMIF", "SUMIFS", "COUNTIF", "COUNTIFS", "AVERAGEIFS",
             "INDEX", "MATCH", "XLOOKUP", "XMATCH", "LOOKUP", "VLOOKUP", "HLOOKUP", "OFFSET",
             "SUMPRODUCT", "FILTER", "EDATE", "EOMONTH", "DATE", "YEAR", "MONTH", "DAY",
             "DAYS", "YEARFRAC", "NETWORKDAYS", "WORKDAY", "DATEDIF", "WEEKDAY"}

# Planchers fixes le 14/09/2026, au-dessus du corpus mesure (tableau dans le README des
# outils). Ils portent sur l'interieur des onglets ; le compte d'onglets n'y figure pas.
# Un L3 de 10 onglets doit donc porter ses 3 000 logiques a 300 par onglet.
BANDES = {
    "L1": {"logiques_distinctes": 500, "logiques_par_onglet": 20, "hypotheses_consommees": 150},
    "L2": {"logiques_distinctes": 1500, "logiques_par_onglet": 40, "hypotheses_consommees": 400},
    "L3": {"logiques_distinctes": 3000, "logiques_par_onglet": 80, "hypotheses_consommees": 1000},
}
SOPHISTICATION_MIN = 45                         # tous niveaux


def r1c1(cle, f, relatif=False):
    """La formule en notation relative : ce que la cellule CALCULE, pas ou elle est.

    relatif=True ignore les $ : c'est la forme d'une ligne de registre ecrite en
    absolu cellule par cellule (=Claims!$L$8, =Claims!$L$9...), qu'un generateur
    produit la ou Excel aurait recopie une reference relative."""
    l0, c0 = cle[1], cle[2]

    def rc(m):
        col_abs, col, lig_abs, lig = m.groups()
        c, l = column_index_from_string(col), int(lig)
        if relatif:
            col_abs = lig_abs = ""
        return (f"R{l}" if lig_abs else f"R[{l - l0}]") + (f"C{c}" if col_abs else f"C[{c - c0}]")

    out, pos = [], 0
    for m in noyau.JETON.finditer(f):
        if m.lastgroup not in ("qplage", "qcell", "plage", "cell"):
            continue
        out.append(f[pos:m.start()])
        t = m.group()
        coupe = t.rfind("!") + 1
        out.append(t[:coupe] + REF1.sub(rc, t[coupe:]))
        pos = m.end()
    out.append(f[pos:])
    return "".join(out)


class Partition:
    def __init__(self):
        self.parent = {}

    def trouver(self, x):
        self.parent.setdefault(x, x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def unir(self, a, b):
        ra, rb = self.trouver(a), self.trouver(b)
        if ra != rb:
            self.parent[rb] = ra


def imbrication(corps):
    prof = pmax = 0
    for ch in corps:
        if ch == "(":
            prof += 1
            pmax = max(pmax, prof)
        elif ch == ")":
            prof -= 1
    return pmax


def sophistiquee(logique):
    corps = CHAINE.sub('""', logique[1:])
    fns = FONCTION.findall(corps)
    return (bool(set(fns) & MARQUEURS) or bool(COMPARAISON.search(corps))
            or (len(fns) >= 2 and imbrication(corps) >= 2))


def mesurer(chemin):
    C = noyau.Classeur(chemin)
    par_feuille = collections.defaultdict(list)
    for cle, f in C.formules.items():
        par_feuille[cle[0]].append((cle, f))
    hyp = {f for f in C.feuilles if HYPOTHESES.search(f) and not INTERCALAIRE.search(f)}

    # Deux cellules portent la meme logique si elles s'ecrivent pareil en R1C1
    # (une ligne recopiee, un absolu garde) OU en relatif pur (un registre ecrit
    # en absolu ligne par ligne). Les composantes de cette partition sont les logiques.
    P = Partition()
    retenues, liens, consommees = {}, 0, set()
    feuilles_calcul = []
    for feuille in C.feuilles:
        cellules = par_feuille.get(feuille, [])
        if INTERCALAIRE.search(feuille) or feuille in hyp or len(cellules) < MIN_FORMULES:
            continue
        feuilles_calcul.append(feuille)
        for cle, f in cellules:
            for ref in C.references(cle, f):
                if ref[0] in hyp or ref in C.durs or ref in C.dates:
                    consommees.add(ref)
            if LIEN.match(f):
                liens += 1
                continue
            a, b = r1c1(cle, f), r1c1(cle, f, relatif=True)
            retenues[cle] = a
            P.unir(("A", a), cle)
            P.unir(("B", b), cle)

    soph_de = collections.defaultdict(bool)
    for cle, a in retenues.items():
        r = P.trouver(cle)
        soph_de[r] = soph_de[r] or sophistiquee(a)

    onglets = []
    for feuille in feuilles_calcul:
        cles = [cle for cle, _ in par_feuille[feuille]]
        calc = [cle for cle in cles if cle in retenues]
        comps = {P.trouver(cle) for cle in calc}
        lignes = collections.Counter(cle[1] for cle in cles)
        onglets.append({
            "onglet": feuille,
            "formules": len(cles),
            "liens_purs": len(cles) - len(calc),
            "logiques_distinctes": len(comps),
            "sophistication_pct": round(100 * sum(soph_de[r] for r in comps) / max(len(comps), 1), 1),
            "repetition": round(len(calc) / max(len(comps), 1), 1),
            "largeur_max": max(lignes.values()),
        })

    toutes = {P.trouver(cle) for cle in retenues}
    n = sum(o["formules"] for o in onglets)
    return {
        "classeur": Path(chemin).name,
        "onglets_de_calcul": len(onglets),
        "formules": n,
        "liens_purs": liens,
        "logiques_distinctes": len(toutes),
        "logiques_par_onglet": round(statistics.median(o["logiques_distinctes"] for o in onglets), 1) if onglets else 0,
        "sophistication_pct": round(100 * sum(soph_de[r] for r in toutes) / max(len(toutes), 1), 1),
        "hypotheses_consommees": len(consommees),
        "repetition": round(len(retenues) / max(len(toutes), 1), 1),
        "largeur_max": max((o["largeur_max"] for o in onglets), default=0),
        "onglets": onglets,
    }


def niveau_atteint(res):
    """Le plus haut niveau dont TOUS les planchers du fichier sont tenus, ou None."""
    atteint = None
    for niveau in ("L1", "L2", "L3"):
        if all(etat == "OK" for *_, etat in juger(res, niveau)):
            atteint = niveau
    return atteint


def juger(res, niveau):
    seuils = dict(BANDES[niveau], sophistication_pct=SOPHISTICATION_MIN)
    return [(cle, seuil, res[cle], "OK" if res[cle] >= seuil else "SOUS LE PLANCHER")
            for cle, seuil in seuils.items()]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("classeur")
    ap.add_argument("--niveau", choices=sorted(BANDES), help="confronte les mesures aux planchers de ce niveau")
    ap.add_argument("--detail", action="store_true", help="une ligne par onglet de calcul")
    ap.add_argument("--json")
    a = ap.parse_args()

    res = mesurer(a.classeur)
    print(f"NIVEAU INTRINSEQUE - {res['classeur']}")
    print(f"  onglets de calcul          : {res['onglets_de_calcul']:>8}   ne fixe pas le niveau")
    print(f"  formules                   : {res['formules']:>8,}   volume")
    print(f"  liens purs                 : {res['liens_purs']:>8,}   exclus des logiques")
    print(f"  logiques distinctes        : {res['logiques_distinctes']:>8,}")
    print(f"  logiques par onglet (med.) : {res['logiques_par_onglet']:>8}")
    print(f"  sophistication             : {res['sophistication_pct']:>7} %")
    print(f"  hypotheses consommees      : {res['hypotheses_consommees']:>8,}")
    print(f"  repetition                 : {res['repetition']:>8}   formules par logique")
    print(f"  largeur de grille max      : {res['largeur_max']:>8}   colonnes")
    if res["onglets_de_calcul"] == 0:
        print("\nRIEN MESURE : aucun onglet ne porte assez de formules. Ce n'est pas un niveau bas.")
    if a.detail:
        print()
        for o in sorted(res["onglets"], key=lambda o: -o["logiques_distinctes"]):
            print(f"  {o['onglet'][:30]:<30} {o['formules']:>8,} formules {o['logiques_distinctes']:>6,} logiques "
                  f"{o['sophistication_pct']:>6} %   repetition {o['repetition']:>7}")
    atteint = niveau_atteint(res)
    res["niveau_fichier"] = atteint
    print()
    print(f"  NIVEAU TENU SUR LE FICHIER : {atteint or 'aucun - sous les planchers L1'}")
    print("  (plafond : les axes declares - decisions derivees, boucles, transcription - peuvent le baisser)")
    if a.niveau:
        verdicts = juger(res, a.niveau)
        print(f"\nPLANCHERS {a.niveau} - interieur des onglets")
        for cle, seuil, v, etat in verdicts:
            print(f"  {cle:<24} plancher {seuil:>6,}   mesure {v:>8,}   {etat}")
        print("  Hors fichier, a declarer a cote : decisions derivees, boucles nommees, part en transcription.")
        res["planchers"] = {"niveau": a.niveau, "verdicts": verdicts}
    if a.json:
        Path(a.json).write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\necrit : {a.json}")


if __name__ == "__main__":
    main()
