# -*- coding: utf-8 -*-
"""Note un candidat contre la rubric, en resolvant SES conventions de nommage.

Le correcteur generique refuse un appariement ambigu, ce qui est la bonne
prudence : accrocher la mauvaise ligne fabrique une perte inexistante. Mais un
candidat qui ecrit « 1. Tier discount » la ou la rubric dit « Tier discount -
solved rate », ou « F01 | T1 | Band A » la ou elle dit « F01 · T1 · Band A »,
n'a pas fait d'erreur de modele : il a fait un autre choix de libelle.

Ce script rattrape ces conventions, puis applique a chaque critere le test que
la rubric enonce pour lui. Ce qu'il ne trouve toujours pas reste NON RESOLU, et
n'est jamais compte comme une perte.
"""
from __future__ import annotations

import pathlib
import re
import sys
from collections import defaultdict

from openpyxl import load_workbook

RUBRIC = ""        # renseigne par la ligne de commande
PER: list[str] = []  # relevees dans la rubric, jamais supposees


def periodes_de(chemin):
    """Releve les periodes citees par la rubric, et les remet dans l'ordre.

    Le script ne connait pas le calendrier du pack : il le LIT. Un libelle de
    periode s'ecrit FY suivi d'un indice, parfois suffixe A pour un exercice
    passe et E pour un exercice estime. C'est l'indice qui donne l'ordre, pas
    l'ordre d'apparition dans le texte.
    """
    texte = pathlib.Path(chemin).read_text(encoding="utf8")
    vues = set(re.findall(r"\bFY-?\d+[AE]?\b", texte))
    if not vues:
        return []
    par_indice = {}
    for p in vues:
        par_indice[int(re.match(r"FY(-?\d+)", p).group(1))] = p
    # Le calendrier est CONTINU : une periode qu'aucun critere ne cite existe
    # quand meme dans le classeur. Ne pas la combler decalerait toutes les
    # suivantes dans le repli positionnel des feuilles sans en-tete.
    for i in range(min(par_indice), max(par_indice) + 1):
        par_indice.setdefault(i, "FY" + str(i))
    return [par_indice[i] for i in sorted(par_indice)]

net = lambda s: re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()
sans_num = lambda s: re.sub(r"^\s*\d+\.\s*", "", str(s)).strip()


def colonnes(ws):
    """Rend {periode: colonne}, lue sur l'en-tete, jamais supposee."""
    for r in range(1, 12):
        vals = {}
        for c in range(1, ws.max_column + 1):
            v = ws.cell(row=r, column=c).value
            if isinstance(v, str) and v.strip() in PER:
                vals[v.strip()] = c
        if len(vals) >= 5:
            return vals
    return {}


def feuille(wb, nom):
    if nom in wb.sheetnames:
        return nom
    c = net(re.sub(r"^\d+\.\s*", "", nom))
    for s in wb.sheetnames:
        if net(re.sub(r"^\d+\.\s*", "", s)) == c:
            return s
    return None


def lignes(ws):
    out = []
    for r in range(1, ws.max_row + 1):
        for col in (3, 2):
            v = ws.cell(row=r, column=col).value
            if isinstance(v, str) and v.strip():
                out.append((r, v.strip()))
                break
    return out


def trouver(ws, poste):
    """Exact d'abord, puis « bloc, cle », puis approche avec marge."""
    tab = lignes(ws)
    cible = net(poste)
    for r, lab in tab:
        if net(sans_num(lab)) == cible:
            return r, "exact"
    # adressage « <bloc>, <cle> » : on cadre le bloc, on cherche la cle dedans
    m = re.match(r"^(.+?), (.+)$", poste)
    if m:
        bloc, cle = net(m.group(1)), net(m.group(2))
        debut = None
        for r, lab in tab:
            l = net(re.sub(r"^[A-Z]\.\d*\s*", "", lab))
            if l.startswith(bloc):
                debut = r
            elif debut and net(lab) == cle:
                return r, "bloc/cle"
    T = set(cible.split())
    # Passe par CONTENANCE : le candidat abrege. « 1. Tier discount » est
    # entierement contenu dans « Tier discount - solved rate », donc il le
    # designe. Quand plusieurs lignes le sont — le taux resolu et le taux
    # effectif portent le meme nom — on tranche sur le BLOC qui les coiffe,
    # en le confrontant aux mots que le libelle du candidat n'a pas repris.
    reste = T - set()
    bloc_en_cours, contenus = "", []
    for r, lab in tab:
        m2 = re.match(r"^([A-Z])\.\s*(.*)$", lab)
        if m2 and len(net(m2.group(2)).split()) > 2:
            bloc_en_cours = net(m2.group(2))
        C = set(net(sans_num(lab)).split())
        if len(C) >= 2 and C <= T:
            contenus.append((len(C), len(set(bloc_en_cours.split()) & (T - C)), r))
    if contenus:
        contenus.sort(reverse=True)
        if len(contenus) == 1 or contenus[0][:2] > contenus[1][:2]:
            return contenus[0][2], "contenance"
    meilleurs = []
    for r, lab in tab:
        j = set(net(sans_num(lab)).split())
        if j:
            meilleurs.append((len(T & j) / max(len(T | j), 1), r))
    meilleurs.sort(reverse=True)
    if meilleurs and meilleurs[0][0] >= 0.55 and (
            len(meilleurs) < 2 or meilleurs[0][0] - meilleurs[1][0] >= 0.10):
        return meilleurs[0][1], f"approche {meilleurs[0][0]:.0%}"
    return None, "introuvable"


NOMBRE = re.compile(r"^\(?[−-]?[\d,]+\.?\d*\)?$")


def valeur_attendue(txt):
    t = txt.strip()
    u = ""
    m = re.match(r"^(.*?)\s*\(([^)]*)\)\s*$", t)
    if m and not NOMBRE.match(t):
        t, u = m.group(1).strip(), m.group(2)
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()").replace(",", "").replace("\u2212", "-")
    for suf in ("%", "x", "bps"):
        if t.endswith(suf):
            t = t[: -len(suf)].strip()
    try:
        v = float(t)
    except ValueError:
        return None, u
    if neg:
        v = -v
    if txt.strip().endswith("%") or u == "%":
        v /= 100.0
    return v, u


def parse():
    crits = []
    section = None
    for L in open(RUBRIC, encoding="utf8"):
        L = L.rstrip("\n")
        m = re.match(r"^Section ([A-Z]) — (.+?) \((\d+) ", L)
        if m:
            section = m.group(1)
            continue
        p = re.match(r"^\[\+(\d+)\]\s+(.*)$", L)
        if not p or section is None:
            continue
        poids, corps = int(p.group(1)), p.group(2)
        if " gate — " in corps or corps.startswith("Formatting — "):
            crits.append((section, poids, None, None, None, None, None, "construction"))
            continue
        parts = [x.strip() for x in corps.split(" — ")]
        if len(parts) < 4:
            crits.append((section, poids, None, None, None, None, None, "construction"))
            continue
        sh = parts[0].split("/")[0].strip()
        poste, per = parts[1], parts[2]
        att, unite = valeur_attendue(parts[3])
        passif = parts[4] if len(parts) > 4 else ""
        crits.append((section, poids, sh, poste, per, att, passif, "valeur"))
    return crits


def teste(obt, att, passif, per):
    if obt is None or not isinstance(obt, (int, float)):
        return None
    if "in all ten periods" in passif or per == "every fiscal year":
        return abs(obt) <= 1e-4
    m = re.search(r"exactly ([−-]?[\d.]+)", passif)
    if m:
        return abs(obt - float(m.group(1).replace("\u2212", "-"))) < 1e-9
    m = re.search(r"within ±([\d.]+)pp", passif)
    if m:
        return abs(obt - att) <= float(m.group(1)) / 100
    m = re.search(r"within ±([\d.]+)", passif)
    if m:
        return abs(obt - att) <= float(m.group(1))
    if att == 0:
        return abs(obt) < 1e-9
    return abs(obt - att) / abs(att) <= 0.01 and (obt >= 0) == (att >= 0)


def autotest():
    """Le noteur decide du 100 % de la golden : s'il se trompe de verdict, la
    rubric passe pour fausse alors qu'elle est juste, ou l'inverse.

    On lui donne des cas dont on connait la reponse : une lecture de valeur, un
    negatif entre parentheses, un pourcentage, puis les quatre formes de test
    que la rubric peut enoncer.
    """
    lectures = [("11,233,017", 11233017.0), ("(4,120.5)", -4120.5),
                ("52.6%", 0.526), ("2.64", 2.64)]
    for txt, attendu in lectures:
        v, _ = valeur_attendue(txt)
        if v is None or abs(v - attendu) > 1e-9:
            raise SystemExit(f"ARRET - le noteur lit {txt!r} comme {v!r}, "
                             f"attendu {attendu!r}")

    verdicts = [
        (100.4, 100.0, "", "FY0", True,  "1 % relatif refuse un ecart de 0,4 %"),
        (105.0, 100.0, "", "FY0", False, "1 % relatif accepte un ecart de 5 %"),
        (-100.0, 100.0, "", "FY0", False, "le signe n'est plus verifie"),
        (0.0, 3.0, "pass if exactly 0", "FY0", True, "« exactly 0 » ne passe plus"),
        (0.04, 4.2, "pass if within \u00b10.3pp", "FY0", False,
         "une bande en pp ne mord plus"),
    ]
    for obt, att, passif, per, attendu, message in verdicts:
        if teste(obt, att, passif, per) != attendu:
            raise SystemExit("ARRET - le noteur est casse : " + message)


def main(chemin):
    wb = load_workbook(chemin, data_only=True)
    res = defaultdict(lambda: [0, 0, 0, 0, 0])   # gagne, pool, ok, echec, nonresolu
    echecs, perdus = [], []
    for sect, poids, sh, poste, per, att, passif, genre in parse():
        d = res[sect]
        d[1] += poids
        if genre == "construction":
            d[4] += 0
            continue
        f = feuille(wb, sh)
        if f is None:
            d[4] += 1
            perdus.append((sect, poids, sh, poste, "feuille absente"))
            continue
        ws = wb[f]
        r, comment = trouver(ws, poste)
        cols = colonnes(ws)
        if not cols:
            # Une feuille sans en-tete de periodes — les retours, par exemple —
            # range ses colonnes a partir de la premiere colonne de donnee.
            cols = {q: 4 + i for i, q in enumerate(PER[PER.index("FY0"):])}
        if per in ("every fiscal year", "total", "run configuration"):
            col = cols.get("FY0", 4) if per != "total" else 4
        else:
            col = cols.get(per)
        if r is None or col is None:
            d[4] += 1
            perdus.append((sect, poids, sh, poste, comment if r is None else "colonne absente"))
            continue
        if per == "every fiscal year":
            vals = [ws.cell(row=r, column=c).value for c in cols.values()]
            num = [v for v in vals if isinstance(v, (int, float))]
            obt = max((abs(v) for v in num), default=None)
        else:
            obt = ws.cell(row=r, column=col).value
        ok = teste(obt, att, passif, per)
        if ok is None:
            d[4] += 1
            perdus.append((sect, poids, sh, poste, "cellule vide"))
        elif ok:
            d[0] += poids
            d[2] += 1
        else:
            d[3] += 1
            echecs.append((sect, poids, sh, poste, per, att, obt))

    print("=" * 92)
    print("NOTE DU CANDIDAT - criteres de valeur")
    print("=" * 92)
    tg = tp = 0
    for s in sorted(res):
        g, p, ok, ec, nr = res[s]
        val = g + sum(x[1] for x in echecs if x[0] == s) + sum(x[1] for x in perdus if x[0] == s)
        tg += g; tp += val
        print(f"  Section {s} : {g:>3d} / {val:<3d} points   {ok} reussis, {ec} rates, {nr} non resolus")
    print(f"\n  VALEUR : {tg} / {tp} points  ({tg/tp:.1%})")
    print(f"  non resolus (jamais comptes en perte) : {sum(x[1] for x in perdus)} points sur {len(perdus)} criteres")
    if echecs:
        print("\n  CRITERES RATES")
        for s, poids, sh, poste, per, att, obt in echecs:
            fa = f"{att:,.4f}" if isinstance(att, float) else str(att)
            fo = f"{obt:,.4f}" if isinstance(obt, (int, float)) else str(obt)
            print(f"    [{s} +{poids}] {sh.split('. ')[-1][:22]:22s} {poste[:40]:40s} {per:6s} attendu {fa:>14s}  obtenu {fo:>14s}")
    if perdus:
        print("\n  NON RESOLUS")
        for s, poids, sh, poste, why in perdus:
            print(f"    [{s} +{poids}] {sh.split('. ')[-1][:22]:22s} {poste[:46]:46s} {why}")
    return tg, tp


if __name__ == "__main__":
    autotest()
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("classeur", help="le classeur a noter")
    ap.add_argument("--rubric", required=True, help="la rubric, en .txt")
    a = ap.parse_args()
    globals()["RUBRIC"] = a.rubric
    globals()["PER"] = periodes_de(a.rubric)
    if not PER:
        raise SystemExit("aucune periode trouvee dans la rubric : rien a noter")
    # Un correcteur annonce ce qu'il a lu AVANT de noter : un score sans compte
    # ne prouve pas qu'il a examine quoi que ce soit.
    print("  rubric   : " + pathlib.Path(a.rubric).name)
    print("  periodes : " + str(len(PER)) + " relevees - " + ", ".join(PER))
    print("  criteres : " + str(len(parse())) + " lus dans la rubric")
    print()
    main(a.classeur)
