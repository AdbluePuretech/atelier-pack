# -*- coding: utf-8 -*-
"""Releve la MISE EN PAGE d'un classeur : ce qui se voit avant de lire un chiffre.

    python mise_en_page.py "GoldenSolution - X.xlsx"
    python mise_en_page.py "Pack.zip"                     # la golden dans le zip
    python mise_en_page.py a.xlsx b.zip c.xlsx --json corpus.json --tableau

Deux packs d'un meme lot ne doivent pas se ressembler au premier coup d'oeil : une
serie de classeurs identiques signale une fabrication en serie, comme une serie
d'onglets de la meme couleur signale un classeur genere. L'outil rend la signature
de presentation d'un classeur, pour la choisir en phase 1 dans ce que le corpus
livre et pour verifier en phase 5 qu'elle ne double pas celle d'un voisin.

La signature ne lit que la forme, jamais les valeurs :

  typographie      police et corps dominants, nombre de polices
  habillage        fonds dominants, couleurs d'onglets, quadrillage, bordures
  architecture     page de garde, intercalaires, style des noms d'onglets
  grille           periodes en ligne ou en colonne, colonne des libelles, colonne
                   des unites, premiere colonne de valeurs, volet fige, ligne de tete
  nombres          formats dominants, negatifs entre parentheses, zero en tiret

Echantillon : les 250 premieres lignes et 60 premieres colonnes de chaque feuille,
assez pour une signature, pas pour un audit.
"""
import argparse
import collections
import datetime
import io
import json
import re
import sys
import zipfile
from pathlib import Path

import openpyxl
from openpyxl.utils import get_column_letter

LIGNES, COLONNES = 250, 60
HYPOTHESES = re.compile(r"^\s*input", re.I)

# L'enveloppe des standards de banque d'affaires. La mise en page varie DEDANS, jamais
# au-dela : une option que le corpus a livree n'est pas pour autant un standard IB.
POLICES_IB = ("Arial", "Calibri", "Tahoma", "Garamond", "Times New Roman", "Cambria", "Book Antiqua")
CORPS_IB = (8.0, 9.0, 10.0)
ALIGNEMENT_IB = 80            # % des onglets dates dont la premiere periode tombe dans la meme colonne
LUMINANCE_BANDEAU_IB = 110    # un bandeau de tete est sombre, encre blanche
INTERCALAIRE = re.compile(r"^[\s>«»<|\-–—=•*.~_]+$|>>|<<")
GARDE = re.compile(r"cover|contents|index|read ?me|garde|title|overview|table of", re.I)
UNITE = re.compile(r"^\s*(\(?\s*(€|\$|£|eur|usd|gbp|chf)?\s*(m|mm|bn|k|000s?|'000|thousands?|millions?)\s*\)?|%|x|#|days?|years?|bps|€/sh|\$/sh|eur m|usd m|\$m|€m|£m|0/1)\s*$", re.I)
ANNEE = re.compile(r"^(fy|cy|q[1-4]|h[12])?\s*'?(19|20)\d{2}[ab e]?$|^(19|20)\d{2}$", re.I)


def ouvrir(chemin):
    """Le classeur deux fois : la forme, et les valeurs en cache (les en-tetes de
    periode sont souvent des formules, dont seule la valeur dit qu'elles sont des dates)."""
    p = Path(chemin)
    if p.suffix.lower() == ".zip":
        with zipfile.ZipFile(p) as z:
            noms = [n for n in z.namelist() if n.lower().endswith(".xlsx")]
            gold = [n for n in noms if "golden" in n.lower()] or noms
            if not gold:
                raise SystemExit(f"{p.name} : aucun classeur")
            octets = z.read(gold[0])
        return (openpyxl.load_workbook(io.BytesIO(octets)),
                openpyxl.load_workbook(io.BytesIO(octets), data_only=True, read_only=True),
                f"{p.name}:{Path(gold[0]).name}")
    return openpyxl.load_workbook(p), openpyxl.load_workbook(p, data_only=True, read_only=True), p.name


def couleur(c):
    try:
        if c is None or c.type != "rgb" or not isinstance(c.rgb, str):
            return None
        v = c.rgb.upper()
        return None if v in ("00000000", "FFFFFFFF") else v[-6:]
    except Exception:
        return None


def style_nom(noms):
    styles = collections.Counter()
    for n in noms:
        if INTERCALAIRE.search(n):
            styles["intercalaire"] += 1
        elif re.match(r"^\d+[\.\s_-]", n):
            styles["numerote"] += 1
        elif "_" in n and " " not in n:
            styles["Snake_Case"] += 1
        elif " " in n:
            styles["avec espaces"] += 1
        else:
            styles["un mot"] += 1
    return styles.most_common(1)[0][0] if styles else "-"


def est_periode(v):
    if isinstance(v, (datetime.date, datetime.datetime)):
        return True
    if isinstance(v, (int, float)) and not isinstance(v, bool) and 1990 <= v <= 2100 and float(v).is_integer():
        return True
    return isinstance(v, str) and bool(ANNEE.match(v.strip()))


def signature(chemin):
    wb, wv, nom = ouvrir(chemin)
    polices, corps, fonds, formats = collections.Counter(), collections.Counter(), collections.Counter(), collections.Counter()
    col_libelles, col_unites, col_valeurs, volets, tetes = (collections.Counter() for _ in range(5))
    orient = collections.Counter()
    bordures = cellules = negatifs_par = zero_tiret = numeriques = 0
    quadrillage = onglets_couleur = 0
    tab_couleurs = collections.Counter()
    encre_durs, encre_liens, encre_locales = collections.Counter(), collections.Counter(), collections.Counter()
    alignement = collections.Counter()
    calc = [ws for ws in wb.worksheets if not INTERCALAIRE.search(ws.title)]

    for ws in wb.worksheets:
        tc = couleur(ws.sheet_properties.tabColor) if ws.sheet_properties.tabColor is not None else None
        if tc:
            onglets_couleur += 1
            tab_couleurs[tc] += 1
    for ws in calc:
        if ws.sheet_view.showGridLines is not False:
            quadrillage += 1
        if ws.freeze_panes:
            volets[ws.freeze_panes] += 1
        par_ligne, par_col = collections.Counter(), collections.Counter()
        debut_ligne = {}
        textes_col, unites_col, valeurs_col = collections.Counter(), collections.Counter(), collections.Counter()
        premiere_ligne = None
        for row in ws.iter_rows(min_row=1, max_row=min(ws.max_row, LIGNES), max_col=min(ws.max_column, COLONNES)):
            for c in row:
                v = c.value
                if v is None:
                    continue
                cellules += 1
                if premiere_ligne is None:
                    premiere_ligne = c.row
                f = c.font
                if f is not None:
                    if f.name:
                        polices[f.name] += 1
                    if f.sz:
                        corps[float(f.sz)] += 1
                teinte = famille_couleur(couleur(f.color) or "000000") if f is not None and f.color is not None else "noir"
                if isinstance(v, (int, float)) and not isinstance(v, bool) and HYPOTHESES.search(ws.title):
                    encre_durs[teinte] += 1
                elif isinstance(v, str) and v.startswith("="):
                    (encre_liens if "!" in v else encre_locales)[teinte] += 1
                fill = c.fill
                if fill is not None and fill.fill_type == "solid":
                    fc = couleur(fill.fgColor)
                    if fc:
                        fonds[fc] += 1
                b = c.border
                if b is not None and any(getattr(b, s).style for s in ("top", "bottom", "left", "right")):
                    bordures += 1
                if isinstance(v, str) and v.startswith("="):
                    valeurs_col[c.column] += 1
                    numeriques += 1
                    nf = c.number_format or "General"
                    formats[nf] += 1
                    if "(" in nf and ";" in nf:
                        negatifs_par += 1
                    if re.search(r';\s*"?-"?\s*$|;\s*"?\s*-\s*"?\s*;', nf) or nf.count(";") >= 2 and "-" in nf.split(";")[2]:
                        zero_tiret += 1
                elif isinstance(v, str):
                    if UNITE.match(v):
                        unites_col[c.column] += 1
                    elif est_periode(v):
                        par_ligne[c.row] += 1
                        par_col[c.column] += 1
                        debut_ligne[c.row] = min(debut_ligne.get(c.row, c.column), c.column)
                    elif len(v) > 2:
                        textes_col[c.column] += 1
                elif est_periode(v):
                    par_ligne[c.row] += 1
                    par_col[c.column] += 1
                    debut_ligne[c.row] = min(debut_ligne.get(c.row, c.column), c.column)
        if textes_col:
            col_libelles[textes_col.most_common(1)[0][0]] += 1
        if unites_col and unites_col.most_common(1)[0][1] >= 3:
            col_unites[unites_col.most_common(1)[0][0]] += 1
        if valeurs_col:
            col_valeurs[min(valeurs_col)] += 1
        if premiere_ligne:
            tetes[premiere_ligne] += 1
        for row in wv[ws.title].iter_rows(min_row=1, max_row=min(ws.max_row, LIGNES), max_col=min(ws.max_column, COLONNES)):
            for c in row:
                v = getattr(c, "value", None)
                coord = (getattr(c, "row", None), getattr(c, "column", None))
                if v is None or coord[0] is None:
                    continue
                if isinstance(ws.cell(*coord).value, str) and ws.cell(*coord).value.startswith("=") and est_periode(v):
                    par_ligne[coord[0]] += 1
                    par_col[coord[1]] += 1
                    debut_ligne[coord[0]] = min(debut_ligne.get(coord[0], coord[1]), coord[1])
        ml = max(par_ligne.values(), default=0)
        mc = max(par_col.values(), default=0)
        if max(ml, mc) >= 4:
            orient["en ligne" if ml >= mc else "en colonne"] += 1
        # la regle IB : sur chaque onglet date, la premiere periode tombe dans la meme colonne
        if ml >= 4 and ml >= mc and not HYPOTHESES.search(ws.title):
            ligne_dates = max(par_ligne, key=lambda r: par_ligne[r])
            alignement[debut_ligne[ligne_dates]] += 1

    n = max(len(calc), 1)
    top = lambda c, k=1: [x for x, _ in c.most_common(k)]
    lettre = lambda c: get_column_letter(top(c)[0]) if c else "-"
    return {
        "classeur": nom,
        "onglets": len(wb.worksheets),
        "police": top(polices)[0] if polices else "-",
        "polices": len(polices),
        "corps": top(corps)[0] if corps else None,
        "fonds_dominants": top(fonds, 4),
        "fonds_distincts": len(fonds),
        "onglets_colores_pct": round(100 * onglets_couleur / max(len(wb.worksheets), 1)),
        "couleurs_onglets": len(tab_couleurs),
        "quadrillage_pct": round(100 * quadrillage / n),
        "bordures_pct": round(100 * bordures / max(cellules, 1)),
        "page_de_garde": bool(wb.worksheets and GARDE.search(wb.worksheets[0].title)),
        "intercalaires": sum(1 for ws in wb.worksheets if INTERCALAIRE.search(ws.title)),
        "noms_onglets": style_nom([ws.title for ws in wb.worksheets]),
        "periodes": top(orient)[0] if orient else "-",
        "colonne_libelles": lettre(col_libelles),
        "colonne_unites": lettre(col_unites),
        "premiere_colonne_valeurs": lettre(col_valeurs),
        "volet_fige": top(volets)[0] if volets else "aucun",
        "ligne_de_tete": top(tetes)[0] if tetes else None,
        "format_dominant": top(formats)[0] if formats else "-",
        "negatifs_parentheses_pct": round(100 * negatifs_par / max(numeriques, 1)),
        "colonnes_alignees_pct": (round(100 * max(alignement.values()) / sum(alignement.values()))
                                  if alignement else None),      # None : aucun onglet date lu
        "encre_entrees": top(encre_durs)[0] if encre_durs else "-",
        "encre_liens_feuilles": top(encre_liens)[0] if encre_liens else "-",
        "encre_formules_locales": top(encre_locales)[0] if encre_locales else "-",
        "zero_tiret_pct": round(100 * zero_tiret / max(numeriques, 1)),
    }


# Les axes qui se voient au premier coup d'oeil. Deux classeurs se comparent axe par
# axe ; les axes de STRUCTURE comptent a part, parce qu'une palette differente sur une
# grille identique reste le meme classeur repeint.
STRUCTURE = ("colonne_libelles", "premiere_colonne_valeurs", "page_de_garde",
             "intercalaires_oui", "noms_onglets", "colonne_unites_oui", "volet_oui")
HABILLAGE = ("police", "corps", "fond_titre", "onglets_colores_oui")
# Ce que le corpus ne fait jamais varier (66 goldens sur 66 sans quadrillage, 65 sur 66
# avec les negatifs entre parentheses) : ce ne sont pas des axes, ce sont des invariants.
INVARIANTS = {"quadrillage_oui": False, "negatifs_parentheses_oui": True, "periodes": "en ligne"}


def axes(s):
    return {
        "periodes": s["periodes"], "colonne_libelles": s["colonne_libelles"],
        "premiere_colonne_valeurs": s["premiere_colonne_valeurs"], "page_de_garde": s["page_de_garde"],
        "intercalaires_oui": s["intercalaires"] > 0, "noms_onglets": s["noms_onglets"],
        "colonne_unites_oui": s["colonne_unites"] != "-", "volet_oui": s["volet_fige"] != "aucun",
        "police": s["police"], "corps": s["corps"],
        "fond_titre": famille_couleur(min(s["fonds_dominants"], key=luminance) if s["fonds_dominants"] else "-"),
        "quadrillage_oui": s["quadrillage_pct"] >= 50, "onglets_colores_oui": s["onglets_colores_pct"] >= 50,
        "negatifs_parentheses_oui": s["negatifs_parentheses_pct"] >= 50,
    }


def hors_standard_ib(s):
    """Ce qui sort des standards d'une banque d'affaires, et pourquoi."""
    out = []
    if s["police"] not in POLICES_IB:
        out.append(f"police {s['police']} : hors des polices de place ({', '.join(POLICES_IB)})")
    if s["polices"] > 1:
        out.append(f"{s['polices']} polices : une seule par classeur")
    if s["corps"] not in CORPS_IB:
        out.append(f"corps {s['corps']} : 8 a 10 (11 est le defaut d'Excel)")
    if s["periodes"] != "en ligne":
        out.append(f"periodes {s['periodes']} : le temps court de gauche a droite")
    if s["quadrillage_pct"] > 0:
        out.append(f"quadrillage visible sur {s['quadrillage_pct']} % des onglets")
    if s["negatifs_parentheses_pct"] < 50:
        out.append("negatifs sans parentheses")
    if s["colonnes_alignees_pct"] is not None and s["colonnes_alignees_pct"] < ALIGNEMENT_IB:
        out.append(f"premiere periode dans la meme colonne sur {s['colonnes_alignees_pct']} % des onglets dates seulement")
    fonce = min(s["fonds_dominants"], key=luminance) if s["fonds_dominants"] else None
    if fonce is None or luminance(fonce) > LUMINANCE_BANDEAU_IB:
        out.append(f"aucun bandeau sombre (fond le plus fonce : {fonce or 'aucun'})")
    vifs = [h for h in s["fonds_dominants"] if vif(h)]
    if vifs:
        out.append(f"fond vif {', '.join(vifs)} : les fonds restent sobres")
    if s["encre_entrees"] != "-" and not s["encre_entrees"].startswith("bleu "):
        out.append(f"entrees en dur a l'encre {s['encre_entrees']} : bleu")
    if s["encre_liens_feuilles"] != "-" and not s["encre_liens_feuilles"].startswith("vert"):
        out.append(f"liens entre feuilles a l'encre {s['encre_liens_feuilles']} : vert")
    if s["encre_formules_locales"] not in ("-", "noir"):
        out.append(f"formules locales a l'encre {s['encre_formules_locales']} : noir")
    return out


def vif(hexa):
    """Un fond sature et lumineux (magenta, jaune pur, vert pomme) ; le jaune pale des
    cellules d'entree ne l'est pas."""
    try:
        r, g, b = (int(hexa[i:i + 2], 16) / 255 for i in (0, 2, 4))
    except Exception:
        return False
    mx, mn = max(r, g, b), min(r, g, b)
    return mx > 0.85 and mx > 0 and (mx - mn) / mx > 0.75


def luminance(hexa):
    try:
        r, g, b = (int(hexa[i:i + 2], 16) for i in (0, 2, 4))
        return 0.299 * r + 0.587 * g + 0.114 * b
    except Exception:
        return 999


def famille_couleur(hexa):
    """Une teinte, pas un code : deux bleus marine voisins sont la meme identite."""
    try:
        r, g, b = (int(hexa[i:i + 2], 16) / 255 for i in (0, 2, 4))
    except Exception:
        return "-"
    mx, mn = max(r, g, b), min(r, g, b)
    if mx - mn < 0.08:
        return "gris" if mx > 0.25 else "noir"
    if mx == r:
        h = (60 * ((g - b) / (mx - mn))) % 360
    elif mx == g:
        h = 60 * ((b - r) / (mx - mn)) + 120
    else:
        h = 60 * ((r - g) / (mx - mn)) + 240
    clair = "clair" if mx > 0.8 and mn > 0.6 else "fonce"
    for borne, nom in ((20, "rouge"), (50, "orange"), (70, "jaune"), (160, "vert"), (200, "bleu-vert"),
                       (260, "bleu"), (300, "violet"), (345, "rose"), (360, "rouge")):
        if h < borne:
            return f"{nom} {clair}"
    return "-"


def distance(s1, s2):
    return distance_axes(axes(s1), axes(s2))


def distance_axes(a1, a2):
    diff = [k for k in a1 if a1[k] != a2[k] and k not in INVARIANTS]
    return {"structure": sum(k in STRUCTURE for k in diff), "habillage": sum(k in HABILLAGE for k in diff),
            "teinte": "fond_titre" in diff, "axes": diff}


# --- la fiche de la conception ----------------------------------------------------
# La porte 1 juge la mise en page AVANT que la golden existe : elle lit la fiche ecrite
# dans CONCEPTION.md, section « Fiche de mise en page », une ligne `cle: valeur` par axe,
# et la compare aux classeurs deja livres du lot comme s'il s'agissait d'une signature.
# Le bandeau se donne en hexadecimal : une teinte decrite en mots (« bleu petrole ») ne
# se compare a rien, et le generateur en aura besoin de toute facon.
OUI_NON = {"oui": True, "non": False}
OPTIONS_FICHE = {
    "colonne_libelles": ("B", "C", "D"),
    "premiere_colonne_valeurs": ("B", "D", "E", "F"),
    "noms_onglets": ("Snake_Case", "avec espaces", "un mot", "numerote"),
}
AXES_FICHE = ("page_de_garde", "intercalaires", "noms_onglets", "colonne_libelles", "premiere_colonne_valeurs",
              "colonne_unites", "volet_fige", "police", "corps", "bandeau", "onglets_colores")


def lire_fiche(chemin):
    texte = Path(chemin).read_text(encoding="utf-8")
    m = re.search(r"^##\s*Fiche de mise en page\s*$(.*?)(?=^##\s|\Z)", texte, re.M | re.S)
    valeurs = {}
    for ligne in (m.group(1) if m else "").splitlines():
        mm = re.match(r"^\s*([a-z_]+)\s*:\s*(.+?)\s*$", ligne)
        if mm:
            valeurs[mm.group(1)] = mm.group(2)
    return valeurs


def axes_fiche(v):
    """Les axes d'une fiche, au format de axes(), et ce qui n'y tient pas."""
    hors, manquants = [], []

    def lire(cle):
        x = v.get(cle, "").strip()
        if not x:
            manquants.append(cle)
        return x

    def oui_non(cle):
        x = lire(cle).lower()
        if x and x not in OUI_NON:
            hors.append(f"{cle} = {x} : oui ou non")
        return OUI_NON.get(x)

    ax = {k: v2 for k, v2 in INVARIANTS.items()}
    ax["page_de_garde"] = oui_non("page_de_garde")
    ax["intercalaires_oui"] = oui_non("intercalaires")
    ax["colonne_unites_oui"] = oui_non("colonne_unites")
    ax["volet_oui"] = oui_non("volet_fige")
    ax["onglets_colores_oui"] = oui_non("onglets_colores")
    for cle, options in OPTIONS_FICHE.items():
        x = lire(cle)
        if x and x not in options:
            hors.append(f"{cle} = {x} : {' | '.join(options)}")
        ax[cle] = x
    police = lire("police")
    if police and police not in POLICES_IB:
        hors.append(f"police = {police} : {' | '.join(POLICES_IB)}")
    ax["police"] = police
    corps = lire("corps")
    try:
        ax["corps"] = float(corps.replace(",", ".")) if corps else None
    except ValueError:
        ax["corps"] = None
    if corps and ax["corps"] not in CORPS_IB:
        hors.append(f"corps = {corps} : 8, 9 ou 10")
    bandeau = lire("bandeau").lstrip("#").upper()
    if bandeau:
        if not re.fullmatch(r"[0-9A-F]{6}", bandeau):
            hors.append(f"bandeau = {bandeau} : une couleur hexadecimale, 1F4E5A par exemple")
        elif luminance(bandeau) > LUMINANCE_BANDEAU_IB or vif(bandeau):
            hors.append(f"bandeau = {bandeau} : un fond sombre et sobre")
    ax["fond_titre"] = famille_couleur(bandeau) if bandeau else "-"
    return ax, hors, manquants


def main_fiche(a):
    valeurs = lire_fiche(a.fiche)
    ax, hors, manquants = axes_fiche(valeurs)
    print(f"FICHE DE MISE EN PAGE - {Path(a.fiche).name}")
    for cle in AXES_FICHE:
        print(f"  {cle:<26} {valeurs.get(cle, '-')}")
    for h in hors:
        print(f"  HORS OPTIONS : {h}")
    for m in manquants:
        print(f"  AXE MANQUANT : {m}")
    lus = len(AXES_FICHE) - len(manquants)
    print(f"FICHE : {lus} axe(s) lus, {len(hors) + len(manquants)} hors options")
    echecs = comp = 0
    if a.contre:
        for p in classeurs_du_dossier(a.contre):
            try:
                v = signature(p)
            except BaseException as e:
                print(f"  {p.name:<40} illisible ({type(e).__name__})")
                continue
            comp += 1
            dist = distance_axes(ax, axes(v))
            ok = dist["structure"] >= MIN_STRUCTURE and dist["habillage"] >= MIN_HABILLAGE and dist["teinte"]
            echecs += not ok
            print(f"  {'OK   ' if ok else 'TROP PROCHE'} {v['classeur'][:40]:<40} structure {dist['structure']}/{len(STRUCTURE)}"
                  f"  habillage {dist['habillage']}/{len(HABILLAGE)}")
        if comp == 0:
            print("RIEN COMPARE : aucun classeur lu dans le dossier. Ce n'est pas une mise en page distincte.")
        else:
            print(f"{comp} classeurs compares, {echecs} trop proches")
    sys.exit(1 if hors or manquants or echecs or (a.contre and comp == 0) else 0)


# Calibre le 14/09/2026 sur 172 paires de packs d'un meme environnement : la mediane du
# corpus differe de 3 axes de structure et de 2 d'habillage ; 43 % des paires tiennent
# ces deux planchers. Les quatre packs du lot RX, entre eux : 0 axe de structure.
MIN_STRUCTURE = 3
MIN_HABILLAGE = 2


def classeurs_du_dossier(dossier):
    d = Path(dossier)
    vus = []
    for p in sorted(d.rglob("*")):
        low = str(p).lower()
        if any(k in low for k in ("_old", "ai output", "_pack_repairs")):
            continue
        if p.suffix.lower() == ".zip" or (p.suffix.lower() == ".xlsx" and "golden" in p.name.lower()):
            vus.append(p)
    # un pack depose en zip ET en classeur ouvert ne compte qu'une fois : on garde le zip
    avec_zip = {p.parent for p in vus if p.suffix.lower() == ".zip"}
    return [p for p in vus if p.suffix.lower() == ".zip" or p.parent not in avec_zip]


COLONNES_TABLEAU = [("classeur", 34), ("police", 14), ("corps", 5), ("fonds_dominants", 22), ("onglets_colores_pct", 4),
                    ("quadrillage_pct", 4), ("page_de_garde", 5), ("intercalaires", 3), ("noms_onglets", 12),
                    ("periodes", 10), ("colonne_libelles", 3), ("colonne_unites", 3), ("premiere_colonne_valeurs", 3),
                    ("volet_fige", 6), ("negatifs_parentheses_pct", 4)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("classeurs", nargs="*")
    ap.add_argument("--json")
    ap.add_argument("--tableau", action="store_true", help="une ligne par classeur")
    ap.add_argument("--contre", help="dossier des packs deja livres du meme lot : le premier classeur doit differer de "
                                     "chacun sur au moins 3 axes de structure, 2 d'habillage, dont la teinte du bandeau")
    ap.add_argument("--fiche", help="CONCEPTION.md : juger la fiche de mise en page au lieu d'un classeur")
    a = ap.parse_args()
    if a.fiche:
        main_fiche(a)
    if not a.classeurs:
        ap.error("un classeur au moins, ou --fiche")
    if a.contre:
        cible = signature(a.classeurs[0])
        cible_nom = Path(a.classeurs[0]).name
        echecs = lus = 0
        print(f"MISE EN PAGE CONTRE LE LOT - {cible['classeur']}")
        ax = axes(cible)
        ib = hors_standard_ib(cible)
        for e in ib:
            print(f"  HORS STANDARD IB : {e}")
        for k, attendu in INVARIANTS.items():
            if ax[k] != attendu:
                print(f"  INVARIANT ROMPU : {k} = {ax[k]}, le corpus ne s'en ecarte jamais")
        for p in classeurs_du_dossier(a.contre):
            if p.name == cible_nom or cible["classeur"].endswith(p.name):
                continue
            try:
                v = signature(p)
            except BaseException as e:
                print(f"  {p.name:<40} illisible ({type(e).__name__})")
                continue
            lus += 1
            dist = distance(cible, v)
            ok = dist["structure"] >= MIN_STRUCTURE and dist["habillage"] >= MIN_HABILLAGE and dist["teinte"]
            echecs += not ok
            print(f"  {'OK   ' if ok else 'TROP PROCHE'} {v['classeur'][:40]:<40} structure {dist['structure']}/{len(STRUCTURE)}"
                  f"  habillage {dist['habillage']}/{len(HABILLAGE)}  identiques : "
                  f"{', '.join(k for k in axes(cible) if k not in dist['axes'] and k not in INVARIANTS)}")
        if lus == 0:
            print("RIEN COMPARE : aucun classeur lu dans le dossier. Ce n'est pas une mise en page distincte.")
        else:
            print(f"{lus} classeurs compares, {echecs} trop proches")
        sys.exit(1 if echecs or lus == 0 or ib else 0)
    out = []
    for ch in a.classeurs:
        try:
            s = signature(ch)
        except SystemExit as e:
            print(e)
            continue
        except Exception as e:
            print(f"{Path(ch).name} : illisible ({type(e).__name__}: {e})")
            continue
        out.append(s)
        if not a.tableau:
            print(f"MISE EN PAGE - {s['classeur']}")
            for k, v in s.items():
                if k != "classeur":
                    print(f"  {k:<26} {v}")
            ib = hors_standard_ib(s)
            print(f"  STANDARDS IB : {'tenus' if not ib else str(len(ib)) + ' ecart(s)'}")
            for e in ib:
                print(f"    - {e}")
            print()
        else:
            print("  ".join(str(s[k] if not isinstance(s[k], list) else ",".join(s[k][:2]))[:w].ljust(w)
                            for k, w in COLONNES_TABLEAU), flush=True)
    if a.json:
        Path(a.json).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"ecrit : {a.json} ({len(out)} classeurs)")


if __name__ == "__main__":
    main()
