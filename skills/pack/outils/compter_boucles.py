"""Compte les boucles INDEPENDANTES d'un classeur.

    python systeme/scripts/eiger/compter_boucles.py "classeur.xlsx"

Le nombre brut de composantes fortement connexes ne veut rien dire : une meme
mecanique repliquee sur dix colonnes en produit dix. Ce qui compte est le nombre
de SIGNATURES distinctes — l'ensemble des feuilles et des lignes traversees —
parce que c'est lui que la gate du repo mesure sous le nom de « boucles reelles
et independantes ».
"""
from __future__ import annotations

import argparse
import collections
import re
import sys
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.utils import column_index_from_string as ci, get_column_letter as CL

sys.setrecursionlimit(400000)

REF = re.compile(r"(?:'([^']+)'!|(\b[A-Za-z_][A-Za-z0-9_.]*)!)?"
                 r"(\$?[A-Z]{1,3}\$?\d{1,6})(?::(\$?[A-Z]{1,3}\$?\d{1,6}))?")
TXT = re.compile(r'"[^"]*"')


def graphe(wb):
    feuilles = {w.title for w in wb.worksheets}
    g = {}
    for w in wb.worksheets:
        for row in w.iter_rows():
            for cell in row:
                v = cell.value
                if not (isinstance(v, str) and v.startswith("=")):
                    continue
                out = []
                for m in REF.finditer(TXT.sub('""', v)):
                    f = m.group(1) or m.group(2) or w.title
                    if f not in feuilles:
                        continue
                    a, b = m.group(3).replace("$", ""), m.group(4)
                    ca, ra = re.match(r"([A-Z]+)(\d+)", a).groups()
                    if b is None:
                        out.append((f, ci(ca), int(ra)))
                    else:
                        cb, rb = re.match(r"([A-Z]+)(\d+)", b.replace("$", "")).groups()
                        for col in range(ci(ca), ci(cb) + 1):
                            for lig in range(int(ra), int(rb) + 1):
                                out.append((f, col, lig))
                g[(w.title, cell.column, cell.row)] = out
    return g


def composantes(g):
    idx, low, sur, pile, cpt, scc = {}, {}, set(), [], [0], []
    for dep in g:
        if dep in idx:
            continue
        trav = [(dep, iter(g.get(dep, [])))]
        idx[dep] = low[dep] = cpt[0]; cpt[0] += 1
        pile.append(dep); sur.add(dep)
        while trav:
            n, it = trav[-1]
            avance = False
            for v in it:
                if v not in idx:
                    idx[v] = low[v] = cpt[0]; cpt[0] += 1
                    pile.append(v); sur.add(v)
                    trav.append((v, iter(g.get(v, []))))
                    avance = True
                    break
                elif v in sur:
                    low[n] = min(low[n], idx[v])
            if not avance:
                trav.pop()
                if trav:
                    low[trav[-1][0]] = min(low[trav[-1][0]], low[n])
                if low[n] == idx[n]:
                    comp = []
                    while True:
                        w_ = pile.pop(); sur.discard(w_); comp.append(w_)
                        if w_ == n:
                            break
                    if len(comp) > 1 or n in g.get(n, []):
                        scc.append(comp)
    return scc


def cellules_en_cycle(g):
    return {c for comp in composantes(g) for c in comp}


def test_de_coupe(wb, g):
    """Une boucle est REELLE et INDEPENDANTE si couper son breaker brise un cycle
    que les autres mecaniques ne fournissent pas.

    Compter les composantes fortement connexes ne suffit pas : des qu'une boucle
    traverse le compte de resultat, elle fusionne avec toutes celles qui le
    traversent aussi, et le graphe n'en montre plus qu'une. Dans un modele
    integre la fusion est la regle, pas l'exception — c'est pourquoi le repo
    compte des MECANIQUES NOMMEES, chacune debranchable, et non des composantes.
    """
    inp = next(w for w in wb.worksheets if w.title.endswith("Input_Sheet"))
    # Un interrupteur se reconnait a ce qu'il VAUT - 0 ou 1 - et non a un libelle
    # qui commencerait par « Breaker ». Mesure sur une golden reelle : la
    # recherche par libelle en trouvait UN, la recherche par valeur en trouve
    # SIX (Brk_Master, Brk_Sweep, MFN_On, Programme_On, Restatement_On,
    # Counterfactual_On). L'outil qui decide la gate de niveau voyait donc un
    # sixieme des mecaniques, et rendait « 0 mecanique circulaire reelle » sur un
    # pack entierement bati sur sa circularite.
    #
    # C'est la meme correction que celle deja appliquee a commutateurs.py.
    breakers = {}
    for r in range(1, inp.max_row + 1):
        lib = inp.cell(row=r, column=3).value
        if isinstance(lib, str) and lib.strip().lower().startswith("breaker"):
            breakers[lib.strip()] = ["$D$" + str(r)]

    for nom in list(wb.defined_names):
        try:
            dn = wb.defined_names[nom]
            for f, ref in dn.destinations:
                if f != inp.title:
                    continue
                c = inp[ref.replace("$", "")]
                v = c.value
                if isinstance(v, (int, float)) and not isinstance(v, bool) and v in (0, 1):
                    # Deux facons de citer le meme interrupteur : par son ADRESSE
                    # et par son NOM. Ne chercher que la premiere laissait passer
                    # toutes les formules qui l'appellent par son nom - donc
                    # « couper » ne coupait rien.
                    breakers.setdefault(nom, []).extend(
                        [ref if ref.startswith("$") else "$" + ref, nom])
        except Exception:
            continue
    # Un meme interrupteur se trouve deux fois : par son libelle et par sa plage
    # nommee. Le garder en double fausse le test d'ISOLEMENT - couper « tous les
    # autres » coupe alors aussi son jumeau, et la mecanique parait inerte.
    # On fusionne par cellule visee, en gardant le nom le plus court.
    par_cellule = {}
    for nom, formes in breakers.items():
        adresse = next((f.replace("$", "") for f in formes if f.startswith("$")), nom)
        garde = par_cellule.get(adresse)
        if garde is None or len(nom) < len(garde):
            par_cellule[adresse] = nom
    fusionnes = {}
    for adresse, nom in par_cellule.items():
        formes = []
        for n, f in breakers.items():
            if next((x.replace("$", "") for x in f if x.startswith("$")), n) == adresse:
                formes.extend(f)
        fusionnes[nom] = formes
    breakers = fusionnes

    base = cellules_en_cycle(g)

    def couper(noms):
        """Neutralise toute formule citant l'un des breakers nommes.

        Une citation prend deux formes : l'adresse - `'01. Input_Sheet'!$D$18` -
        et la plage nommee - `Brk_Master`. On cherche les deux ; n'en chercher
        qu'une laissait la moitie des formules intactes.
        """
        # Piege 15 : un controle qui cherche une reference doit connaitre TOUTES
        # les facons de la formuler - par nom, par adresse, avec ou sans dollars,
        # avec ou sans guillemets autour du nom de feuille. N'en chercher qu'une
        # laissait passer les formules qui citent le breaker autrement, et le
        # cycle survivait a une coupure qui n'avait rien coupe.
        marques = []
        for n in noms:
            for forme in breakers[n]:
                if not forme.startswith("$"):
                    marques.append(forme)          # la plage nommee
                    continue
                nu = forme.replace("$", "")
                for adresse in (forme, nu):
                    marques.append("'" + inp.title + "'!" + adresse)
                    marques.append(inp.title + "!" + adresse)
        out = {}
        for cle, arcs in g.items():
            f, col, lig = cle
            v = wb[f].cell(row=lig, column=col).value
            out[cle] = [] if (isinstance(v, str)
                              and any(m in v for m in marques)) else arcs
        return out

    # Un cycle qui survit a la coupure de TOUS les breakers n'appartient a
    # aucune mecanique : c'est une fuite. Sans le soustraire, chaque breaker se
    # verrait crediter de ce residu, y compris ceux qui ne sont pas construits.
    residuel = cellules_en_cycle(couper(list(breakers)))
    sortie = []
    for nom, ancre in breakers.items():
        # On debranche TOUTES les autres mecaniques et on regarde si celle-ci
        # cree encore un cycle a elle seule. C'est la seule lecture qui resiste
        # a la fusion : couper une boucle une par une ne prouve rien tant qu'une
        # autre emprunte le meme chemin et referme le cycle a sa place.
        seule = cellules_en_cycle(couper([n for n in breakers if n != nom]))
        propre = len(seule) - len(residuel & seule)
        sortie.append((nom, propre, propre > 0))
    return base, residuel, sortie


def main(chemin):
    wb = load_workbook(chemin)
    g = graphe(wb)
    scc = composantes(g)
    sign = collections.defaultdict(list)
    for comp in scc:
        cle = (tuple(sorted({x[0] for x in comp})), tuple(sorted({x[2] for x in comp})))
        sign[cle].append(sorted({x[1] for x in comp}))
    print(f"  formules : {len(g):,}   |   composantes circulaires : {len(scc)}")
    print(f"  BOUCLES INDEPENDANTES : {len(sign)}\n")
    for i, ((feuilles, lignes), cols) in enumerate(
            sorted(sign.items(), key=lambda x: -len(x[0][1])), 1):
        etendue = f"{len(feuilles)} feuille(s)" if len(feuilles) > 1 else feuilles[0]
        print(f"  {i}. {len(cols)} exemplaire(s) · {len(lignes)} lignes · {etendue}")
        for f in feuilles:
            l = [x for x in lignes]
            print(f"       {f:32s} lignes {l[:8]}{' ...' if len(l) > 8 else ''}")
    base, residuel, res = test_de_coupe(wb, g)
    print("")
    print("  TEST D'ISOLEMENT - " + format(len(base), ",") + " cellules en cycle, toutes mecaniques actives")
    print("  cycle residuel, tous breakers coupes : " + format(len(residuel), ",")
          + (" cellules  <-- FUITE" if residuel else " cellule"))
    print("")
    reelles = 0
    for nom, seule, reelle in sorted(res, key=lambda x: -x[1]):
        etat = "REELLE" if reelle else "inerte"
        if reelle:
            reelles += 1
        print("    [" + etat + "] " + nom[:58].ljust(58)
              + format(seule, ",").rjust(8) + " cellules en cycle, elle seule")
    print("")
    print("  MECANIQUES CIRCULAIRES REELLES : " + str(reelles))
    return reelles


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("classeur", help="le classeur a examiner")
    main(ap.parse_args().classeur)
