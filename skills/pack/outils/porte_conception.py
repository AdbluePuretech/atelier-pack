# -*- coding: utf-8 -*-
"""Lire CONCEPTION.md et ancrages.json, aux formats que la porte 1 impose.

La conception etait une prose libre, differente a chaque pack : aucune porte ne
pouvait y verifier qu'une mecanique a son piege, ou que les boucles atteignent le
plancher du niveau. Le plan est desormais fixe (dix titres), et les trois listes qui
comptent — graine -> pack, mecaniques, boucles — sont des tables markdown.

Les titres se lisent sans accents ni casse : « Mécaniques et pièges » vaut
« Mecaniques et pieges ».
"""
import json
import re
import unicodedata
from pathlib import Path

TITRES = ("Graine -> pack", "Noyau dur", "Mecaniques et pieges", "Boucles", "Budget de discrimination",
          "Niveau", "Frontieres", "Fiche de mise en page", "Rollout d'enonce", "Tests de declenchement")
PLANCHER_BOUCLES = {"L1": 1, "L2": 4, "L3": 6}
BUDGET_MAX = 20
NATURES = ("M", "S", "D")


def normaliser(t):
    t = unicodedata.normalize("NFKD", str(t))
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.replace("→", "->").replace("’", "'").replace("«", "").replace("»", "")
    return re.sub(r"\s+", " ", t).strip().lower()


def sections(texte):
    out, titre, lignes = {}, None, []
    for ligne in texte.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", ligne)
        if m and not ligne.startswith("###"):
            if titre is not None:
                out[titre] = "\n".join(lignes)
            titre, lignes = normaliser(m.group(1)), []
        elif titre is not None:
            lignes.append(ligne)
    if titre is not None:
        out[titre] = "\n".join(lignes)
    return out


def table(corps):
    """La premiere table markdown du corps : une liste de dictionnaires en-tete normalise -> cellule."""
    lignes = [l.strip() for l in corps.splitlines() if l.strip().startswith("|")]
    if len(lignes) < 2:
        return []
    cellules = lambda l: [c.strip() for c in l.strip().strip("|").split("|")]
    entetes = [normaliser(c) for c in cellules(lignes[0])]
    rangs = []
    for l in lignes[1:]:
        cs = cellules(l)
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cs if c):
            continue
        rangs.append({entetes[i]: (cs[i] if i < len(cs) else "") for i in range(len(entetes))})
    return rangs


def colonne(rang, *noms):
    for n in noms:
        if normaliser(n) in rang:
            return rang[normaliser(n)].strip()
    return ""


class Conception:
    def __init__(self, chemin):
        self.chemin = Path(chemin)
        self.texte = self.chemin.read_text(encoding="utf-8")
        self.sections = sections(self.texte)

    def section(self, titre):
        return self.sections.get(normaliser(titre))

    def titres_presents(self):
        return [t for t in TITRES if self.section(t) is not None]

    def graine(self):
        return table(self.section("Graine -> pack") or "")

    def mecaniques(self):
        return table(self.section("Mecaniques et pieges") or "")

    def ids(self):
        return [colonne(r, "Id") for r in self.mecaniques() if re.fullmatch(r"M\d+", colonne(r, "Id"))]

    def boucles(self):
        return table(self.section("Boucles") or "")

    def budget(self):
        m = re.search(r"Part du pool en transcription\s*:\s*(\d+(?:[.,]\d+)?)\s*%", self.section("Budget de discrimination") or "")
        return float(m.group(1).replace(",", ".")) if m else None

    def niveau(self):
        m = re.search(r"Niveau vise\s*:\s*(L[123])", self.section("Niveau") or "", re.I)
        return m.group(1).upper() if m else None


def citation_trouvee(passage, graine_texte):
    p = normaliser(passage).strip("\"' ")
    return bool(p) and p in normaliser(graine_texte)


def lire_ancrages(chemin):
    donnees = json.loads(Path(chemin).read_text(encoding="utf-8"))
    if not isinstance(donnees, list):
        raise ValueError("ancrages.json doit etre une liste d'ancrages")
    return donnees


def defauts_ancrage(a, ids, exige_cellule):
    d = []
    ident = a.get("id", "?")
    if not isinstance(a.get("valeur"), (int, float)) or isinstance(a.get("valeur"), bool):
        d.append(f"{ident} : valeur non numerique")
    tol = a.get("tolerance") or {}
    if not (isinstance(tol.get("relative"), (int, float)) or isinstance(tol.get("absolue"), (int, float))):
        d.append(f"{ident} : tolerance relative ou absolue manquante")
    if a.get("nature") not in NATURES:
        d.append(f"{ident} : nature {a.get('nature')!r} hors M/S/D")
    if not str(a.get("pourquoi", "")).strip():
        d.append(f"{ident} : pourquoi vide")
    if a.get("mecanique") not in ids:
        d.append(f"{ident} : mecanique {a.get('mecanique')!r} absente de la conception")
    if exige_cellule and not re.fullmatch(r"'?[^!]+'?![A-Z]{1,3}\d+", str(a.get("cellule", ""))):
        d.append(f"{ident} : cellule manquante ou mal formee")
    return d


def dans_tolerance(valeur, a):
    cible, tol = a["valeur"], a.get("tolerance") or {}
    if not isinstance(valeur, (int, float)) or isinstance(valeur, bool):
        return False
    if isinstance(tol.get("absolue"), (int, float)):
        return abs(valeur - cible) <= tol["absolue"]
    rel = tol.get("relative", 0)
    return abs(valeur - cible) <= rel * abs(cible) if cible else abs(valeur) <= 1e-9


PLAN_VIDE = """# Conception - {nom}

## Graine -> pack

| Element | Nature | Passage de la graine |
|---------|--------|----------------------|
|  | mecanique / entree / sortie | citation exacte de la graine |

## Noyau dur

## Mecaniques et pieges

| Id | Mecanique | Famille | Piege nomme | Bonne reponse | Erreur plausible | Points qui tombent |
|----|-----------|---------|-------------|---------------|------------------|--------------------|
| M1 |  |  |  |  |  |  |

## Boucles

| Boucle | Interrupteur | Convention des pieces | Mecanique | Amplitude estimee |
|--------|--------------|-----------------------|-----------|-------------------|
|  |  |  | M1 |  |

## Budget de discrimination

Part du pool en transcription : NN %

## Niveau

Niveau vise : L1

## Frontieres

## Fiche de mise en page

page_de_garde: non
intercalaires: oui
noms_onglets: Snake_Case
colonne_libelles: C
premiere_colonne_valeurs: E
colonne_unites: non
volet_fige: non
police: Arial
corps: 9
bandeau: 1F2A36
onglets_colores: non
blocs:
nombres:
documents:

## Rollout d'enonce

## Tests de declenchement
"""
