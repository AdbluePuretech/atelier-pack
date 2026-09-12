# -*- coding: utf-8 -*-
"""L'audit de golden solution : les defauts qu'un recalcul ne montre jamais.

Un classeur peut rendre zero erreur Excel et rester faux. C'est meme le cas
dangereux : rien ne clignote. L'audit de la tache 77 « Final » a trouve, sur un
classeur a zero erreur, **61 totaux sur 180 qui n'egalaient pas la somme de la
plage qu'ils pretendaient sommer**. Aucun chiffre de sortie n'etait verifiable,
et le livrable de la tache etait precisement une reconciliation.

Ce script rejoue ce protocole. Sept familles, de la plus grave a la plus legere :

  B1  AGREGAT INCOHERENT      une cellule `=SUM(plage)` dont la valeur en cache
                              ne vaut pas la somme des valeurs de la plage. Le
                              defaut silencieux par excellence.
  M2  INTERRUPTEUR MORT       un switch ou un breaker declare, que zero formule
                              ne consulte. Le basculer n'a aucun effet : fausse
                              assurance de controle.
  N3  NOM MORT                une plage nommee que rien ne cite. Si elle porte
                              une hypothese, elle designe au candidat une
                              methode que le modele n'emploie pas.
  N5  INPUT NEUTRALISE        un input bien reference, mais annule dans la
                              formule qui le consomme (`=-In_Fee_Offset*0`).
                              Le piege classique : la reference existe, l'effet
                              non.
  M1  ONGLET QUASI INERTE     un onglet que l'aval ne consulte presque pas. Il
                              calcule, il ne sert a rien, et il coute au lecteur.
  N7  CONSTANTE EN DUR        un litteral significatif ecrit dans une formule de
                              calcul. Le spec exige zero hardcode : une valeur
                              qu'on ne peut pas changer depuis l'input sheet
                              n'est pas une hypothese, c'est une decision cachee.
  M12 SOLUTION DE COIN        un resultat d'optimisation ou de point fixe pose
                              exactement sur une borne de sa grille : l'optimum
                              est hors du domaine cherche, et la mecanique ne
                              demontre rien.

    python gs_audit.py <golden.xlsx> [--feuille Input_Sheet] [--tolere N1,N2]

Sortie : un rapport par famille, et un code de sortie non nul si une famille
DURE (B1, M2, N5) remonte quoi que ce soit. Les autres sont des avertissements :
elles demandent un arbitrage, pas une correction mecanique.
"""
import re
import sys
from collections import defaultdict

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter, column_index_from_string

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
GOLDEN = ARGS[0]
FEUILLE = ARGS[1] if len(ARGS) > 1 else "Input_Sheet"
TOLERES = set()
for i, a in enumerate(sys.argv):
    if a == "--tolere" and i + 1 < len(sys.argv):
        TOLERES = set(sys.argv[i + 1].split(","))

wf = load_workbook(GOLDEN, data_only=False)
wv = load_workbook(GOLDEN, data_only=True)

# ---- l'inventaire des formules, une fois pour toutes ------------------------
FORMULES = []          # (feuille, ligne, colonne, texte)
for ws in wf.worksheets:
    for row in ws.iter_rows():
        for c in row:
            if isinstance(c.value, str) and c.value.startswith("="):
                FORMULES.append((ws.title, c.row, c.column, c.value))
TOUT = "\n".join(f for _, _, _, f in FORMULES)
PAR_FEUILLE = defaultdict(list)
for t, _, _, f in FORMULES:
    PAR_FEUILLE[t].append(f)

NOMS = {}
for n, d in wf.defined_names.items():
    m = re.match(r"^'?([^'!]+)'?!\$?([A-Z]+)\$?(\d+)$", str(d.value))
    if m:
        NOMS[n] = (m.group(1), m.group(2), int(m.group(3)))


def libelle(feuille, ligne):
    if feuille not in wv.sheetnames:
        return ""
    return str(wv[feuille].cell(row=ligne, column=3).value or "").strip()


def refs(nom):
    """Le nombre de formules qui atteignent ce nom — PAR NOM OU PAR ADRESSE.

    Une plage nommee peut etre lue de deux facons : en citant son nom, ou en
    citant la cellule qu'elle designe. Ne compter que la premiere fait declarer
    morte une hypothese que des milliers de formules consultent.
    """
    p = re.compile(r"(?<![A-Za-z0-9_.])" + re.escape(nom) + r"(?![A-Za-z0-9_.])")
    n = sum(1 for _, _, _, f in FORMULES if p.search(f))
    if n or nom not in NOMS:
        return n
    fe, co, li = NOMS[nom]
    # L'adresse, avec ou sans dollars, avec ou sans quotes autour de la feuille.
    a = re.compile(r"(?<![A-Za-z0-9_])'?" + re.escape(fe) + r"'?!\$?"
                   + re.escape(co) + r"\$?" + str(li) + r"(?![0-9])")
    return sum(1 for _, _, _, f in FORMULES if a.search(f))


rapport, dur = [], 0


def bloc(code, titre, lignes, severite="DUR"):
    global dur
    rapport.append((code, titre, lignes, severite))
    if severite == "DUR":
        dur += len(lignes)


# ==========================================================================
# B1 — les agregats qui ne suivent pas leur propre formule
# ==========================================================================
# On ne teste que la forme SANS ambiguite : `=SUM(plage)` seul, sur une plage
# rectangulaire de la meme feuille. Une formule composee peut legitimement
# differer d'une somme ; celle-ci ne le peut pas.
SOMME = re.compile(r"^=SUM\((?:'?([^'!]+)'?!)?\$?([A-Z]+)\$?(\d+):\$?([A-Z]+)\$?(\d+)\)$",
                   re.I)
faux, testes = [], 0
for feuille, ligne, col, f in FORMULES:
    m = SOMME.match(f.replace(" ", ""))
    if not m:
        continue
    cible = m.group(1) or feuille
    if cible not in wv.sheetnames:
        continue
    c1, r1, c2, r2 = (column_index_from_string(m.group(2)), int(m.group(3)),
                      column_index_from_string(m.group(4)), int(m.group(5)))
    ws = wv[cible]
    total = 0.0
    for r in range(min(r1, r2), max(r1, r2) + 1):
        for c in range(min(c1, c2), max(c1, c2) + 1):
            v = ws.cell(row=r, column=c).value
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                total += v
    affiche = wv[feuille].cell(row=ligne, column=col).value
    if not isinstance(affiche, (int, float)) or isinstance(affiche, bool):
        continue
    testes += 1
    ecart = abs(affiche - total)
    if ecart > max(abs(total), abs(affiche)) * 1e-9 + 1e-6:
        faux.append("{}!{}{}  affiche {:,.4f}, la plage somme {:,.4f}  (ecart {:,.4f})"
                    .format(feuille, get_column_letter(col), ligne, affiche, total, ecart))
bloc("B1", "Agregats incoherents avec leur propre formule "
     "({} cellules =SUM(plage) testees)".format(testes), faux)

# ==========================================================================
# M2 — interrupteurs et breakers declares mais morts
# ==========================================================================
# Un switch se reconnait a son nom ou a son libelle : « (1 = ... ) », « switch »,
# « breaker », « _On », « Brk_ ». C'est la famille ou un mort coute le plus cher :
# le classeur AFFICHE un controle qui n'existe pas.
MOTIF_SW = re.compile(r"(switch|breaker|\(1\s*=|flag)", re.I)
morts_sw, morts_nom = [], []
for nom, (fe, co, li) in sorted(NOMS.items()):
    if nom in TOLERES:
        continue
    n = refs(nom)
    if n:
        continue
    lab = libelle(fe, li)
    est_sw = bool(MOTIF_SW.search(lab)) or nom.startswith("Brk_") or nom.endswith("_On")
    entree = "{:<18} {}!{}{:<5} {}".format(nom, fe, co, li, lab[:56])
    (morts_sw if est_sw else morts_nom).append(entree)
bloc("M2", "Interrupteurs et breakers declares que zero formule ne consulte", morts_sw)
bloc("N3", "Noms definis que zero formule ne cite", morts_nom, "AVERT")

# ==========================================================================
# N5 — inputs neutralises par une constante dans la formule consommatrice
# ==========================================================================
# `=-In_Fee_Offset*0` : la reference existe, donc N3 ne voit rien, et pourtant
# l'input est inoperant. On cherche un nom defini multiplie par un zero litteral,
# ou une formule qui cite un nom et rend une constante nulle.
NEUTRE = re.compile(r"(?<![A-Za-z0-9_.])([A-Za-z_][A-Za-z0-9_.]*)\s*\*\s*0(?![.\d])")
neutralises = []
for feuille, ligne, col, f in FORMULES:
    for m in NEUTRE.finditer(f):
        if m.group(1) in NOMS:
            neutralises.append("{}!{}{}  {}  annule dans : {}".format(
                feuille, get_column_letter(col), ligne, m.group(1), f[:80]))
    # Le zero doit etre un LITTERAL. Sans cette garde, le « 0 » final de la
    # reference « D10 » dans « =D10*Inp_PT_HVAC » se lit comme une annulation, et
    # le controle remonte vingt-cinq formules parfaitement saines.
    for m in re.finditer(r"(?<![A-Za-z0-9_.$])0\s*\*\s*([A-Za-z_][A-Za-z0-9_.]*)", f):
        if m.group(1) in NOMS:
            neutralises.append("{}!{}{}  {}  annule dans : {}".format(
                feuille, get_column_letter(col), ligne, m.group(1), f[:80]))
bloc("N5", "Inputs references mais neutralises par un zero ecrit dans la formule",
     sorted(set(neutralises)))

# ==========================================================================
# M1 — onglets que l'aval ne consulte presque pas
# ==========================================================================
CALCUL = [ws.title for ws in wf.worksheets
          if not ws.title.endswith(">>") and PAR_FEUILLE.get(ws.title)]
# Un onglet que personne ne lit n'est pas forcement inerte : un pont de programme
# ou une feuille de controles est TERMINALE par nature — elle lit tout l'amont et
# ne rend de comptes a personne. L'onglet vraiment inerte est celui que presque
# rien ne lit ET qui ne lit presque rien : il calcule dans le vide. Confondre les
# deux revient a demander la suppression des sorties.
inertes, terminaux = [], []
for t in CALCUL:
    p = re.compile(r"(?<![A-Za-z0-9_])'?" + re.escape(t) + r"'?!")
    entrant = sum(1 for f, _, _, txt in FORMULES if f != t and p.search(txt))
    if entrant > 2:
        continue
    autres = re.compile(r"(?<![A-Za-z0-9_])'?(" + "|".join(
        re.escape(x) for x in CALCUL if x != t) + r")'?!")
    sortant = sum(1 for f in PAR_FEUILLE[t] if autres.search(f))
    ligne = "{:<24} lu par l'aval {:>4} fois, cite l'amont {:>6} fois".format(
        t, entrant, sortant)
    (terminaux if sortant > 20 else inertes).append(ligne)
bloc("M1", "Onglets quasi inertes (peu lus ET ne lisant presque rien)",
     inertes, "AVERT")
bloc("M1b", "Onglets terminaux (peu lus, mais consommant tout l'amont : "
     "des sorties, pas des defauts)", terminaux, "INFO")

# ==========================================================================
# N7 — constantes significatives ecrites en dur dans les formules de calcul
# ==========================================================================
# On retire d'abord les references de cellules et les chaines, sinon « A1 » et
# « FY5 » comptent comme des nombres. Un litteral est SIGNIFICATIF s'il porte des
# decimales ou trois chiffres et plus : 0, 1, 2, 12 sont de l'arithmetique, 0,0175
# et 9,9E+99 sont des decisions cachees.
BANAL = {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12",
         "24", "100", "365", "1000"}
def est_controle(feuille, ligne):
    """Cette ligne est-elle une ligne de controle plutot que de calcul ?"""
    if "check" in feuille.lower():
        return True
    lab = str(wv[feuille].cell(row=ligne, column=3).value or "").lower()
    return bool(re.search(r"\bcheck\b|target 0|\btie[s]?\b|\bresidual\b", lab))


durs, tolerances = defaultdict(list), defaultdict(list)
for feuille, ligne, col, f in FORMULES:
    if feuille == FEUILLE:          # la feuille d'hypotheses PORTE des valeurs
        continue
    net = re.sub(r'"[^"]*"', '""', f)
    net = re.sub(r"(?:'[^']+'|[A-Za-z_][A-Za-z0-9_.]*)!\$?[A-Z]+\$?\d+(?::\$?[A-Z]+\$?\d+)?",
                 " ", net)
    net = re.sub(r"(?<![A-Za-z0-9_.])\$?[A-Z]{1,3}\$?\d{1,7}(?![0-9])", " ", net)
    net = re.sub(r"[A-Za-z_][A-Za-z0-9_.]*", " ", net)
    for m in re.finditer(r"(?<![A-Za-z0-9_.$])(\d+\.\d+|\d{3,}|\d+(?:[Ee][+-]?\d+))", net):
        v = m.group(1)
        if v in BANAL:
            continue
        # Une constante dans une ligne de CALCUL est une hypothese qu'on ne peut
        # pas changer depuis l'input sheet : une decision cachee. La meme
        # constante dans une ligne de CONTROLE n'est qu'une tolerance de
        # comparaison — elle decide si le controle mord, pas ce que le modele
        # rend. Les melanger noie la premiere sous les secondes.
        cible = tolerances if est_controle(feuille, ligne) else durs
        cible[v].append("{}!{}{}".format(feuille, get_column_letter(col), ligne))


def rendre(d):
    return ["{:<14} {:>6} occurrence(s)   ex. {}".format(v, len(o), ", ".join(o[:3]))
            for v, o in sorted(d.items(), key=lambda x: -len(x[1]))]


bloc("N7", "Constantes en dur dans le CHEMIN DE CALCUL "
     "(une hypothese qu'on ne peut pas changer depuis l'input sheet)",
     rendre(durs), "AVERT")
bloc("N7b", "Constantes en dur dans les lignes de CONTROLE "
     "(tolerances de comparaison, pas des hypotheses)", rendre(tolerances), "INFO")

# ==========================================================================
# M12 — resultats de point fixe poses sur une borne de leur grille
# ==========================================================================
# Un optimiseur qui rend sa borne n'a rien optimise : l'optimum est hors du
# domaine. On repere les lignes dont le libelle annonce un resultat resolu et
# dont TOUTES les valeurs de la trajectoire valent exactement 0 ou 1.
coins = []
for ws in wv.worksheets:
    for r in range(1, ws.max_row + 1):
        lab = str(ws.cell(row=r, column=3).value or "").strip()
        if not re.search(r"\bsolved\b|\boptimal\b|\bsolution\b", lab, re.I):
            continue
        # Une ligne de controle vaut zero partout QUAND TOUT VA BIEN. La lire
        # comme une solution de coin, c'est signaler un defaut chaque fois que le
        # modele boucle correctement.
        if est_controle(ws.title, r):
            continue
        vals = [ws.cell(row=r, column=c).value for c in range(4, 10)]
        num = [v for v in vals if isinstance(v, (int, float))]
        if num and all(v in (0, 1) for v in num):
            coins.append("{}!r{}  {}  toutes les periodes a {}".format(
                ws.title, r, lab[:52], num[0]))
bloc("M12", "Resultats resolus poses sur une borne de leur grille", coins, "AVERT")

# ==========================================================================
print("=" * 78)
print("AUDIT DE LA GOLDEN — {}".format(GOLDEN))
print("=" * 78)
print("  onglets {}   formules {:,}   noms definis {}".format(
    len(wf.worksheets), len(FORMULES), len(NOMS)))
for code, titre, lignes, sev in rapport:
    marque = "[DUR]  " if sev == "DUR" else "[AVERT]"
    print("\n{} {} {} : {}".format(marque, code, titre, len(lignes)))
    for x in lignes[:25]:
        print("      " + x)
    if len(lignes) > 25:
        print("      ... et {} de plus".format(len(lignes) - 25))
print()
print("=" * 78)
print("VIOLATIONS DURES : {}".format(dur))
sys.exit(1 if dur else 0)
