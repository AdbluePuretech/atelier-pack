# -*- coding: utf-8 -*-
"""Les sorties sont-elles economiquement possibles ?

Les neuf autres etapes verifient qu'un classeur est juste **avec lui-meme** :
il boucle, il converge, ses identites ferment, ses controles surveillent quelque
chose. Aucune ne verifie qu'il dit quelque chose de **possible**.

Un modele peut passer les vingt controles d'integrite, converger a froid, tenir
sa parite LibreOffice, et afficher une marge d'EBITDA de 340 %, un multiple
negatif ou un TRI de 900 %. Arithmetiquement irreprochable, economiquement mort.

La doctrine du metier appelle ca la **vraisemblance**, et la range dans ses
workstreams. Chez nous elle etait declaree « portee par le fichier d'ancrages » -
or les ancrages sont un document de CONCEPTION, ecrit avant la construction, et
personne ne les rejoue contre le classeur fini. Sur un classeur qu'on n'a pas
fabrique, il n'y en a meme pas.

Deux niveaux, et il ne faut pas les confondre
---------------------------------------------
**Les bornes universelles** ne demandent aucune declaration : une part qui sort
de [0, 1], un multiple negatif, un taux annualise au-dela du raisonnable. Elles
sont rares et sures, parce qu'une fausse alerte est le meme defaut qu'un faux
vert.

**Les bornes declarees** viennent d'un fichier que l'auditeur ecrit - le pendant,
cote grandeurs, des « identites imposees de l'exterieur » de l'etape 6. C'est un
module a **jugement**, pas a verdict : imposer des verites generales a un modele
particulier produit des exceptions legitimes.

Le module ne conclut jamais seul sur une borne declaree. Il montre, il compte, il
se tait.
"""
import argparse
import json
import re
import sys

import openpyxl

# --- ce qu'une cellule ANNONCE, lu dans son format de nombre ------------------

# Un « % » DANS des guillemets est un suffixe litteral : la cellule porte alors
# 85 pour 85 %, pas 0,85. Le confondre avec le vrai type pourcentage d'Excel a
# rendu quatre fausses alertes sur une golden conforme.
_LITTERAL = re.compile(r'"[^"]*"')


def est_pourcent(fmt):
    return "%" in _LITTERAL.sub("", fmt or "")


# Une ligne de CONTROLE porte un residu, pas une grandeur economique : un tie a
# -0,001 n'est pas un multiple negatif. C'est la troisieme fois que ce correctif
# s'impose - I13 et I17 le portent deja - donc c'est un reflexe, pas un cas.
MOTS_CONTROLE = ("must be nil", "violation", "controlled to nil", "tie -", "tie ",
                 "check", "residual", "residu", "target nil", "reconcil")
EST_MULTIPLE = re.compile(r'"x"|\\x|0\.0+x', re.I)

# Un libelle qui annonce une grandeur bornee. On reconnait la LIGNE par son
# intitule, comme I17 reconnait une ligne de controle par le sien.
MARGES = re.compile(r"\b(margin|marge|ratio|share|part|taux|rate|yield|"
                    r"utilisation|coverage|payout|take-?up)\b", re.I)
MULTIPLES = re.compile(r"\b(multiple|moic|mom|tvpi|dpi|rvpi|x\b)", re.I)
RENDEMENTS = re.compile(r"\b(irr|tri|xirr|return|rendement)\b", re.I)

# Les bornes universelles. Larges a dessein : elles doivent etre indiscutables.
BORNE_PART = (-1.0, 1.0)          # une part, une marge : hors de la, c'est faux
BORNE_MULTIPLE = (0.0, 25.0)      # un multiple negatif n'existe pas
BORNE_RENDEMENT = (-1.0, 3.0)     # -100 % a +300 % annualises

COLONNES_LIBELLES = (1, 2, 3, 4)


def _libelle_de_ligne(ws, ligne):
    for col in COLONNES_LIBELLES:
        v = ws.cell(row=ligne, column=col).value
        if isinstance(v, str) and v.strip() and not v.startswith("="):
            return v.strip()
    return ""


def controler(chemin, bornes=None, limite_cas=25):
    """Rend une liste de constats. `bornes` : [{poste, min, max, unite}]."""
    wb = openpyxl.load_workbook(chemin, data_only=True)
    hors_part, hors_mult, hors_rdt, declarees = [], [], [], []
    lus = 0
    exemptes = [0]
    bornes = bornes or []

    for ws in wb.worksheets:
        for ligne in ws.iter_rows():
            if not ligne:
                continue
            lib = _libelle_de_ligne(ws, ligne[0].row)
            if not lib:
                continue
            for c in ligne:
                v = c.value
                if not isinstance(v, (int, float)) or isinstance(v, bool):
                    continue
                if v != v or v in (float("inf"), float("-inf")):
                    continue
                fmt = c.number_format or ""
                lus += 1
                ou = f"{ws.title}!{c.coordinate}"
                if any(m in lib.lower() for m in MOTS_CONTROLE):
                    exemptes[0] += 1
                    continue
                # Une part se reconnait a son FORMAT (%) et a son libelle.
                if est_pourcent(fmt) and MARGES.search(lib):
                    if not (BORNE_PART[0] <= v <= BORNE_PART[1]):
                        hors_part.append(f"{ou}  {lib[:44]}  {v:.4g}")
                elif MULTIPLES.search(lib) and (EST_MULTIPLE.search(fmt) or "x" in fmt.lower()):
                    if not (BORNE_MULTIPLE[0] <= v <= BORNE_MULTIPLE[1]):
                        hors_mult.append(f"{ou}  {lib[:44]}  {v:.4g}")
                elif RENDEMENTS.search(lib) and est_pourcent(fmt):
                    if not (BORNE_RENDEMENT[0] <= v <= BORNE_RENDEMENT[1]):
                        hors_rdt.append(f"{ou}  {lib[:44]}  {v:.4g}")
                for b in bornes:
                    if b.get("poste", "").lower() in lib.lower():
                        lo, hi = b.get("min"), b.get("max")
                        if (lo is not None and v < lo) or (hi is not None and v > hi):
                            declarees.append(
                                f"{ou}  {lib[:40]}  {v:.6g}  hors [{lo}, {hi}]")
    wb.close()

    R = [
        ("V1", "DEFAUT", "aucune part ni marge hors de [-100 %, +100 %]",
         hors_part, f"{lus} valeurs lues, {exemptes[0]} sur lignes de controle exemptees"),
        ("V2", "DEFAUT", "aucun multiple negatif ni au-dela de 25x",
         hors_mult, f"{lus} valeurs lues"),
        ("V3", "DEFAUT", "aucun rendement annualise hors de [-100 %, +300 %]",
         hors_rdt, f"{lus} valeurs lues"),
        ("V4", "A JUGER", "les bornes declarees tiennent",
         declarees, f"{len(bornes)} borne(s) declaree(s)"
                    + ("" if bornes else " - AUCUNE, l'etape ne prouve rien")),
    ]
    return [{"cle": k, "nature": n, "titre": t, "compte": len(c),
             "sur": s, "cas": c[:limite_cas]} for k, n, t, c, s in R]


TEMOIN = [("Gross margin", "0.0%", 3.4, True), ("Gross margin", "0.0%", 0.42, False),
          ("Exit multiple", chr(39) + chr(39) + chr(39), -1.2, True),
          ("Net IRR", "0.0%", 9.0, True)]
TEMOIN[2] = ("Exit multiple", '0.00"x"', -1.2, True)


def autotest():
    """Un controle qui n'a rien lu rend vert : on lui donne des cas connus."""
    for lib, fmt, v, doit_crier in TEMOIN:
        if MARGES.search(lib) and est_pourcent(fmt):
            crie = not (BORNE_PART[0] <= v <= BORNE_PART[1])
        elif MULTIPLES.search(lib):
            crie = not (BORNE_MULTIPLE[0] <= v <= BORNE_MULTIPLE[1])
        elif RENDEMENTS.search(lib) and est_pourcent(fmt):
            crie = not (BORNE_RENDEMENT[0] <= v <= BORNE_RENDEMENT[1])
        else:
            raise SystemExit(f"ARRET - le controle ne reconnait plus {lib!r}")
        if crie != doit_crier:
            raise SystemExit(f"ARRET - le controle est casse sur {lib!r} = {v}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("classeur")
    ap.add_argument("--bornes", help="fichier JSON : [{poste, min, max}]")
    ap.add_argument("--detail", action="store_true")
    ap.add_argument("--json")
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass
    autotest()

    bornes = []
    if a.bornes:
        with open(a.bornes, encoding="utf-8") as fh:
            bornes = json.load(fh)

    R = controler(a.classeur, bornes)
    print(f"VRAISEMBLANCE - {a.classeur}\n")
    durs = 0
    for d in R:
        dur = d["nature"] == "DEFAUT" and d["compte"]
        durs += d["compte"] if dur else 0
        etat = "OK  " if not d["compte"] else ("FAUT" if dur else "JUGE")
        print(f"  [{etat}] {d['cle']:<3} {d['titre']:<52} {d['compte']:>5}   sur {d['sur']}")
    if not bornes:
        print("\n  Aucune borne declaree : V4 n'a rien essaye. Ce n'est PAS un"
              "\n  resultat favorable - ecrire un fichier de bornes pour que"
              "\n  l'etape prouve quelque chose.")
    print(f"\n  INVRAISEMBLANCES : {durs}")
    if a.detail:
        for d in R:
            if d["compte"]:
                print(f"\n--- {d['cle']} {d['titre']}  ({d['nature']}, {d['compte']})")
                for c in d["cas"]:
                    print(f"      {c}")
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(R, fh, ensure_ascii=False, indent=1)
    return 1 if durs else 0


if __name__ == "__main__":
    sys.exit(main())
