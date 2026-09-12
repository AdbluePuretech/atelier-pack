# -*- coding: utf-8 -*-
"""Debusque dans un classeur ce qui trahit une fabrication automatique.

Un pack juste mais qui « fait IA » est refuse avant d'etre lu, et le refus ne
porte jamais sur le modele : il porte sur une puce pleine, une phrase
explicative accrochee a un libelle, un onglet reste groupe. Ces defauts etaient
documentes dans deux listes en prose que **rien n'executait** - exactement le
defaut que le repo nomme par ailleurs : une affirmation portee dans un libelle
et jamais executee.

Ce module les rend mecaniques. Il ne lit que le fichier, sans Excel.

Deux natures de constat, et il ne faut pas les confondre :

  DEFAUT   la regle est objective, le constat se corrige sans discuter
  A JUGER  l'indice est probabiliste ; le module montre la cellule et se tait

Chaque seuil de ce module a ete recale sur une golden reelle, parce qu'un premier
jet cale sur des cas fabriques a la main trouve exactement ce qu'on y a seme.

La distinction n'est pas une precaution de style. Une fausse alerte est le meme
defaut qu'un faux vert : une alerte qu'on finit par ignorer ne protege plus de
rien. Chaque controle rend donc **un compte et son denominateur**, jamais un
verdict seul.
"""
import argparse
import json
import re
import sys

import openpyxl

# --- ce qu'on cherche dans du texte -------------------------------------------

PUCES = "•‣▪●◦▸►⁃⁌⁍"
CADRATINS = "—–"
TYPOGRAPHIQUES = "“”‘’«»"
DECORATIFS = "✓✔✗✘⚠⭐★☆➡→"

# Un libelle nomme une ligne. Des qu'il explique, commente ou justifie, il n'est
# plus un libelle : c'est une phrase, et une phrase dans une colonne de libelles
# est la signature la plus reconnaissable d'un modele ecrit par une machine.
EXPLICATIVES = re.compile(
    r"\b(assumed|assumption is|based on|calculated as|derived from|note that|"
    r"in order to|this (?:reflects|represents|assumes|captures)|"
    r"we (?:assume|apply|use)|please note|for simplicity|as a proxy|"
    r"i\.e\.|e\.g\.|hypothese retenue|on suppose|pour simplifier)\b", re.I)

EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")

# Le code couleur maison n'admet le bleu que sur une cellule VIDE, attendue du
# candidat. Du bleu sur une cellule pleine, c'est la convention de place - celle
# que tout generateur reproduit tout seul, et qui se lit au premier coup d'oeil.
BLEUS = ("FF0000FF", "FF0070C0", "FF0432FF", "FF1F4E79", "FF2E75B6", "FF00B0F0")
VIOLETS = ("FF7030A0", "FF800080", "FF7B2FBE", "FF9900FF")

# Un intercalaire est un separateur visuel de navigation : il ne calcule rien,
# c'est sa fonction. Il est donc legitimement creux et n'a pas a porter de volet
# fige - le juger comme un onglet de calcul rend deux fausses alertes par
# separateur, et un classeur peut en porter huit. Le corpus les exclut deja du
# compte d'onglets qui fixe le niveau ; on les exclut ici pour la meme raison.
INTERCALAIRE = re.compile(r"^[\s>«»<|\-–—=•*.~_]+$|>>|<<")

LIGNES_CREUSES = 8            # un onglet sous ce seuil ne trompe personne
COLONNES_LARGES = 20          # au-dela, une grille se fait defiler

# Une colonne de libelles se RECONNAIT a ce qu'elle porte, elle ne se suppose
# pas. Sur une golden reelle, tenir les colonnes A a D pour des libelles a rendu
# 124 fausses alertes : la colonne D y portait des reports inter-feuilles, pas
# des intitules. Mesure sur cette meme golden : la colonne C est du texte a
# 188/188, la D a 3/177.
PART_TEXTE = 0.7
ECHANTILLON = 200


def colonnes_de_libelles(ws):
    """Les colonnes dont le contenu rempli est massivement du texte."""
    trouvees = []
    hauteur = min(ws.max_row or 1, ECHANTILLON)
    for col in range(1, min(ws.max_column or 1, 8) + 1):
        remplies = txt = 0
        for r in range(1, hauteur + 1):
            v = ws.cell(row=r, column=col).value
            if v is None:
                continue
            remplies += 1
            if isinstance(v, str) and not v.startswith("="):
                txt += 1
        if remplies >= 5 and txt / remplies >= PART_TEXTE:
            trouvees.append(col)
    return tuple(trouvees)


SUSPECTS = PUCES + CADRATINS + TYPOGRAPHIQUES + DECORATIFS


def _lisible(t, largeur=80):
    """Le caractere fautif est par nature celui que la console ne sait pas ecrire.

    L'afficher tel quel faisait planter l'outil sur une console cp1252 - le
    controle mourait sur le defaut qu'il venait de trouver. On le remplace donc
    par son point de code, qui est de toute facon l'information utile : on
    cherche QUEL caractere retirer.
    """
    out = []
    for ch in t[:largeur]:
        if ch in SUSPECTS or ord(ch) > 0x2000:
            out.append(f"<U+{ord(ch):04X}>")
        else:
            out.append(ch)
    return "".join(out)


def _texte(cellule):
    v = cellule.value
    return v if isinstance(v, str) else None


def est_intercalaire(titre, nommes=()):
    return titre in nommes or bool(INTERCALAIRE.search(titre.strip()))


def controler(chemin, lignes_creuses=LIGNES_CREUSES, intercalaires=(), palette="auto"):
    """Rend {cle: {"nature", "titre", "compte", "sur", "cas"}}."""
    wb = openpyxl.load_workbook(chemin, data_only=False)
    R = {}

    def poser(cle, nature, titre, cas, sur):
        R[cle] = {"nature": nature, "titre": titre,
                  "compte": len(cas), "sur": sur, "cas": cas[:40]}

    puces, cadratins, typo, decoratifs, phrases, formules_libelle = [], [], [], [], [], []
    bleus, violets, sans_gel, creux, groupes = [], [], [], [], []
    largeurs_par_defaut = []
    textes_lus = 0
    couleurs_onglets = []

    separateurs = []
    for ws in wb.worksheets:
        couleurs_onglets.append(getattr(ws.sheet_properties.tabColor, "rgb", None)
                                if ws.sheet_properties.tabColor else None)

        # Un intercalaire sort ici entierement : il est creux, sans volet fige et
        # aux largeurs par defaut PAR CONSTRUCTION, et le juger comme un onglet
        # de calcul rend trois fausses alertes par separateur - un classeur peut
        # en porter huit. Les exemptions sont comptees et affichees dans le
        # denominateur, jamais silencieuses.
        if est_intercalaire(ws.title, intercalaires):
            separateurs.append(ws.title)
            continue

        if ws.max_row and ws.max_row < lignes_creuses:
            creux.append(f"{ws.title} : {ws.max_row} ligne(s)")
        if ws.max_column and ws.max_column > COLONNES_LARGES and ws.freeze_panes is None:
            sans_gel.append(f"{ws.title} : {ws.max_column} colonnes, aucun volet fige")
        if not any(d.width for d in ws.column_dimensions.values()):
            largeurs_par_defaut.append(ws.title)

        if any((d.outlineLevel or 0) > 0 for d in ws.row_dimensions.values()) or \
           any((d.outlineLevel or 0) > 0 for d in ws.column_dimensions.values()):
            groupes.append(ws.title)

        libelles_ici = colonnes_de_libelles(ws)
        for ligne in ws.iter_rows():
            for c in ligne:
                t = _texte(c)
                if t is None:
                    if c.value is not None and c.font and c.font.color:
                        rgb = getattr(c.font.color, "rgb", None)
                        if rgb in BLEUS:
                            bleus.append(f"{ws.title}!{c.coordinate}")
                        elif rgb in VIOLETS:
                            violets.append(f"{ws.title}!{c.coordinate}")
                    continue
                if t.startswith("="):
                    if c.column in libelles_ici:
                        formules_libelle.append(f"{ws.title}!{c.coordinate}  {_lisible(t, 60)}")
                    continue
                textes_lus += 1
                ou = f"{ws.title}!{c.coordinate}"
                if any(ch in t for ch in PUCES):
                    puces.append(f"{ou}  {_lisible(t, 60)}")
                if any(ch in t for ch in CADRATINS):
                    cadratins.append(f"{ou}  {_lisible(t, 60)}")
                if any(ch in t for ch in TYPOGRAPHIQUES):
                    typo.append(f"{ou}  {_lisible(t, 60)}")
                if any(ch in t for ch in DECORATIFS) or EMOJI.search(t):
                    decoratifs.append(f"{ou}  {_lisible(t, 60)}")
                # Seul le fait d'EXPLIQUER compte. La longueur ne dit rien : sur
                # une golden reelle, le seuil de 60 caracteres attrapait 70
                # intitules de section parfaitement legitimes - « C. Customer
                # tiers - share, elasticity and cumulative discount cap » est un
                # bandeau de bloc, pas un commentaire.
                if c.column in libelles_ici and EXPLICATIVES.search(t):
                    phrases.append(f"{ou}  {_lisible(t, 80)}")
                if c.font and c.font.color:
                    rgb = getattr(c.font.color, "rgb", None)
                    if rgb in BLEUS:
                        bleus.append(ou)
                    elif rgb in VIOLETS:
                        violets.append(ou)

    n = len(wb.worksheets)
    poser("T1", "DEFAUT", "aucune puce pleine dans un libelle", puces, f"{textes_lus} textes")
    poser("T2", "DEFAUT", "aucun tiret cadratin dans un libelle", cadratins, f"{textes_lus} textes")
    poser("T3", "DEFAUT", "aucun guillemet ni apostrophe typographique", typo, f"{textes_lus} textes")
    poser("T4", "DEFAUT", "aucun symbole decoratif ni emoji", decoratifs, f"{textes_lus} textes")
    poser("T5", "A JUGER", "aucune phrase explicative dans une colonne de libelles",
          phrases, f"{textes_lus} textes")
    poser("T6", "DEFAUT", "aucun libelle ecrit en formule (piege 16 : il part avec le blank)",
          formules_libelle, f"{n} onglets")
    # La palette se deduit de la couleur dominante des entrees en dur, sauf si
    # l'appelant la nomme. La minorite est alors ce qui detonne : un classeur
    # panache melange deux conventions dont le vert et le rouge sont INVERSES,
    # donc il dit le contraire de ce qu'il montre.
    nb, nv = len(set(bleus)), len(set(violets))
    if palette in ("maison", "onyx"):
        active = palette
    elif nb == 0 and nv == 0:
        active = None
    else:
        active = "onyx" if nb >= nv else "maison"
    # Le controle n'est pas symetrique, parce que les deux palettes ne reservent
    # pas les memes couleurs. Sous ONYX le violet est la couleur des CONTROLES :
    # en trouver est normal, et les compter en intrus rendait 37 fausses alertes
    # sur une golden conforme. Sous MAISON en revanche le bleu ne designe qu'une
    # cellule que le candidat doit remplir, donc vide : du bleu sur une cellule
    # pleine est une entree ecrite dans l'autre convention.
    if active is None:
        intrus, sur = [], "aucune encre d'entree reperee"
    elif active == "onyx":
        intrus = []
        sur = (f"palette onyx, {nb} entrees bleues"
               + (f", {nv} violets (controles, legitimes)" if nv else ""))
    else:
        intrus = sorted(set(bleus))
        sur = f"palette maison, {nv} entrees violettes"
    poser("T7", "A JUGER", "l'encre des entrees suit une seule palette", intrus, sur)
    # En dessous de trois onglets, "toutes de la meme couleur" ne veut rien
    # dire : le controle rendrait une alerte sur un classeur normal, et une
    # fausse alerte est le meme defaut qu'un faux vert.
    distinctes = {c for c in couleurs_onglets if c}
    onglets = ([] if n < 3 or len(distinctes) > 1 else
               [f"{n} onglets, {len(distinctes)} couleur(s) distincte(s)"])
    poser("T8", "A JUGER", "les onglets portent des couleurs, et pas toutes la meme",
          onglets, f"{n} onglets")
    calcul = n - len(separateurs)
    sur_calcul = (f"{calcul} onglets de calcul"
                  + (f", {len(separateurs)} intercalaire(s) exempte(s)"
                     if separateurs else ""))
    poser("T9", "A JUGER", "aucun onglet a la largeur de colonne par defaut",
          largeurs_par_defaut, sur_calcul)
    poser("T10", "A JUGER", "toute feuille large porte un volet fige", sans_gel, sur_calcul)
    poser("T11", "A JUGER", "aucun onglet creux", creux, sur_calcul)
    poser("T12", "DEFAUT", "aucun groupement laisse dans le classeur", groupes, f"{n} onglets")
    wb.close()
    return R


TEMOIN_TEXTES = [
    "• Revenue",                       # T1
    "Revenue — group",                 # T2
    "Sponsor’s equity",                # T3
    "Check ✓",                         # T4
    "Revenue growth, which is assumed to decline linearly over the horizon",  # T5
]


def autotest():
    """Un controle qui n'a rien lu rend vert : on lui donne des cas connus."""
    attendus = [PUCES, CADRATINS, TYPOGRAPHIQUES, DECORATIFS]
    for t, jeu in zip(TEMOIN_TEXTES, attendus):
        if not any(ch in t for ch in jeu):
            raise SystemExit(f"ARRET - le controle est casse : {t!r} n'est plus vu")
    if not EXPLICATIVES.search(TEMOIN_TEXTES[4]):
        raise SystemExit("ARRET - le controle est casse : la phrase explicative n'est plus vue")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("classeur")
    ap.add_argument("--detail", action="store_true", help="lister les cellules fautives")
    ap.add_argument("--palette", default="auto", choices=("auto", "maison", "onyx"),
                    help="palette du corpus servi. maison : hypotheses en violet. "
                         "onyx : hypotheses en bleu, vert et rouge inverses. "
                         "auto : deduite de la couleur dominante du classeur.")
    ap.add_argument("--intercalaires", default="",
                    help="onglets separateurs, separes par des virgules. Ils sont "
                         "reconnus tout seuls a leur nom (`>>`, symboles) ; cette "
                         "option sert aux classeurs qui les nomment autrement.")
    ap.add_argument("--json")
    a = ap.parse_args()

    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass
    autotest()
    R = controler(a.classeur,
                  intercalaires=tuple(x.strip() for x in a.intercalaires.split(",") if x.strip()),
                  palette=a.palette)

    print(f"TRACES DE FABRICATION AUTOMATIQUE - {a.classeur}\n")
    defauts = 0
    for cle, d in R.items():
        etat = "OK  " if not d["compte"] else ("FAUT" if d["nature"] == "DEFAUT" else "JUGE")
        if d["compte"] and d["nature"] == "DEFAUT":
            defauts += d["compte"]
        print(f"  [{etat}] {cle:<4} {d['titre']:<62} {d['compte']:>5}   sur {d['sur']}")
    print(f"\n  defauts objectifs : {defauts}")
    if a.detail:
        for cle, d in R.items():
            if not d["compte"]:
                continue
            print(f"\n--- {cle} {d['titre']}  ({d['nature']}, {d['compte']})")
            for c in d["cas"]:
                print(f"      {c}")
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(R, fh, ensure_ascii=False, indent=1)
    return 1 if defauts else 0


if __name__ == "__main__":
    sys.exit(main())
