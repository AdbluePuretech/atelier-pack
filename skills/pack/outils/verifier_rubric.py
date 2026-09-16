# -*- coding: utf-8 -*-
"""Controle une rubric contre son contrat d'ecriture, en .docx comme en .json.

Le contrat - les *Rubric Editing & Authoring Guidelines* - tient en une quinzaine
de regles dont une dizaine sont mecaniques. Elles vivaient en prose et rien ne les
verifiait, alors que le QA du corpus designe la couche rubric comme celle ou les
defauts se concentrent : des pins ancres sur la mauvaise cellule, des tolerances
plus serrees que l'arrondi.

Ce module ne juge pas les VALEURS - `noter_rubric.py` fait ca, en rejouant la
golden contre sa rubric. Il juge la FORME, celle dont depend la gradabilite :
un critere qu'un correcteur ne sait pas localiser fait echouer un candidat juste.

Chaque controle rend un compte et son denominateur, jamais un verdict seul.

Deux formats, une seule lecture
-------------------------------
Les environnements anciens livrent la rubric en `.docx`, les recents en `.json`
derive du meme document. Les deux se ramenent a la meme forme : une liste de
(section, poids, corps).
"""
import argparse
import io
import json
import re
import sys
import zipfile

# --- les bandes du contrat ----------------------------------------------------

POIDS_ADMIS = {1, 2, 3, 4}
KEYSTONES_CIBLE = (2, 5)          # « ~3 » : on tolere 2 a 5 avant de le dire
PART_UN_CIBLE = (0.33, 0.47)
PART_UN_PLAFOND = 0.60
PENALITES_CIBLE = (5, 7)
CRITERES_GUIDE = (75, 200)
PLAFOND_PENALITE = 0.20

CRITERE = re.compile(r"^\s*\[([+\-−])\s*(\d+)\]\s*(.*)$")   # le gabarit Ostrom ecrit le vrai signe moins U+2212
POIGNEE_P = re.compile(r"\[P\d+\]")
POIGNEE_ID = re.compile(r"\[(?!P\d+\]|[+-])[A-Za-z0-9_.\-]{1,12}\]")
SECTION = re.compile(r"^\s*Section\s+([A-Z0-9]+)\s*[—–-]\s*(.+)$", re.I)
# Une gate se reconnait a sa forme de rendu - « <Nom> gate - <condition>. If not
# met, every <perimetre> criterion in this section scores 0. » - et non au seul
# mot « gate », qui vit aussi dans le corps d'un critere ordinaire et dans un
# nom de section. Compter le mot faisait voir deux gates la ou il y en a une.
GATE = re.compile(r"\bgates?\b\s*[\u2014\u2013-]|scores?\s+0\b|\bgate\b.*\bif not met\b", re.I)
# Une tolerance redite sur la ligne, alors qu'elle vit une fois en configuration.
# « 1 % » seul : un ±0.1% ou un ±11% n'est pas la tolerance par defaut redite
TOLERANCE_REDITE = re.compile(r"within\s*[±+]?\s*(?<![\d.])1\s*%|±\s*(?<![\d.])1\s*%\s*relative|(?<![\d.])1%\s*relative", re.I)
# Ce qu'un corps ne doit jamais porter : formule, identite, reference de cellule.
FUITE = re.compile(r"='?[A-Za-z0-9 _.]+'?!\$?[A-Z]{1,3}\$?\d+|\bGS\b|\bGolden\b|^\s*=|![A-Z]{1,3}\d+")
SEPARATEUR = "—"

# Le contrat admet DEUX natures de critere, et la regle du prefixe d'entite ne
# vaut que pour la premiere : un critere de VALEUR se termine par la valeur ; un
# critere STRUCTUREL enonce une revendication de construction, en phrase. Les
# confondre a rendu 58 fausses alertes sur une rubric livree parfaitement
# conforme - le meme defaut que le re-scoring automatique du QA du corpus, dont
# les 412 flags etaient en ecrasante majorite ses propres erreurs de locator.
# Un critere de VALEUR se reconnait a son dernier segment : une valeur nue, avec
# au plus son unite. Tout le reste - une revendication de construction, un atome
# de format qui cite le prompt - est une phrase, et la regle du prefixe d'entite
# ne s'y applique pas.
#
# Un premier jet tenait pour valeur tout corps finissant par un chiffre : il
# classait « expected shortfall is taken at or below P10 » en critere de valeur
# et rendait 58 fausses alertes sur une rubric conforme. C'est la faute que le QA
# du corpus a faite aussi, avec 412 flags nes de son propre locator.
VALEUR_NUE = re.compile(
    r"^[^A-Za-z]*[-+(]?\d[\d ,.\u202f]*\)?"
    r"\s*(?:%|x|bps|days|pp|pts?|[A-Z\u20ac$\u00a3]{0,4}'?0{0,3})?\s*$")
DATE_NUE = re.compile(r"^\s*(?:\d{1,2}-)?[A-Za-z]{3}-\d{2,4}\s*$|^\s*(?:FY|Q)\d{1,4}[A-Za-z]?\s*$")
PASS_IF = re.compile(r"\bpass if\b", re.I)
# Un atome de format cite la phrase du prompt qu'il fait respecter (contrat 3.4).
ATOME_FORMAT = re.compile(r"Prompt\s*:\s*[\"\u201c]|\bformatting\b|\bpresentation\b", re.I)


def est_critere_de_valeur(section, corps):
    """Vrai seulement si le corps se termine par une valeur nue."""
    if ATOME_FORMAT.search(section) or ATOME_FORMAT.search(corps):
        return False
    t = corps.strip().rstrip(".")
    # « ... — 0.526 — pass if within 1% » : la valeur est le segment d'avant.
    segments = [x.strip() for x in t.split(SEPARATEUR) if x.strip()]
    if not segments:
        return False
    if PASS_IF.search(segments[-1]) and len(segments) >= 2:
        segments = segments[:-1]
    dernier = segments[-1]
    return bool(VALEUR_NUE.match(dernier) or DATE_NUE.match(dernier))


def _lignes_docx(chemin):
    with zipfile.ZipFile(chemin) as z:
        xml = z.read("word/document.xml").decode("utf-8", "replace")
    xml = re.sub(r"</w:p>", "\n", xml)
    xml = re.sub(r"<[^>]+>", "", xml)
    for e, c in (("&amp;", "&"), ("&quot;", '"'), ("&apos;", "'"),
                 ("&lt;", "<"), ("&gt;", ">")):
        xml = xml.replace(e, c)
    return xml.split("\n")


def lire(chemin):
    """Rend (items, config, pool_declare). items = [(section, signe, poids, corps)]."""
    items, config, section = [], [], "?"
    if str(chemin).lower().endswith(".json"):
        d = json.loads(io.open(chemin, encoding="utf-8").read())
        config = list(d.get("scoring_configuration", []))
        for s in d.get("sections", []):
            nom = f"{s.get('id','?')} {s.get('name','')}".strip()
            for k in (s.get("criteria") or []):
                p = k.get("weight", 0)
                items.append((nom, "+" if p >= 0 else "-", abs(p), k.get("text", "")))
    else:
        dans_config = False
        for l in _lignes_docx(chemin):
            m = SECTION.match(l)
            if m:
                section = f"{m.group(1)} {m.group(2)}".strip()
                dans_config = False
                continue
            if re.match(r"^\s*scoring configuration", l, re.I):
                dans_config = True
                continue
            m = CRITERE.match(l)
            if m:
                dans_config = False
                items.append((section, "-" if m.group(1) == "−" else m.group(1), int(m.group(2)), m.group(3)))
            elif dans_config and l.strip():
                config.append(l.strip())
    pool = None
    for c in config:
        m = re.search(r"pool\s*=?\s*(\d+)\s*points", c, re.I)
        if m:
            pool = int(m.group(1))
    return items, config, pool


def controler(chemin):
    docx = not str(chemin).lower().endswith(".json")
    items, config, pool_declare = lire(chemin)
    pos = [(s, p, t) for s, sg, p, t in items if sg == "+"]
    neg = [(s, p, t) for s, sg, p, t in items if sg == "-"]
    valeurs = [(s, p, t) for s, p, t in pos if not GATE.search(t)]
    pool = sum(p for _, p, _ in pos)
    R = []

    def poser(cle, titre, fautifs, sur, nature="DEFAUT"):
        R.append({"cle": cle, "titre": titre, "nature": nature,
                  "compte": len(fautifs), "sur": sur, "cas": fautifs[:25]})

    hors = [f"{s} [+{p}] {t[:60]}" for s, p, t in pos if p not in POIDS_ADMIS]
    poser("R1", "poids dans {1,2,3,4}", hors, f"{len(pos)} criteres positifs")

    keys = [t for _, p, t in pos if p == 4]
    poser("R2", "environ 3 keystones", [] if KEYSTONES_CIBLE[0] <= len(keys) <= KEYSTONES_CIBLE[1]
          else [f"{len(keys)} keystones (+4)"], f"{len(keys)} keystones", "A JUGER")

    n1 = sum(1 for _, p, _ in pos if p == 1)
    part = n1 / len(pos) if pos else 0
    if part > PART_UN_PLAFOND:
        cas, nat = [f"part du +1 = {part:.0%}, au-dessus du plafond de 60 %"], "DEFAUT"
    elif not (PART_UN_CIBLE[0] <= part <= PART_UN_CIBLE[1]):
        cas, nat = [f"part du +1 = {part:.0%}, hors cible 33-47 %"], "A JUGER"
    else:
        cas, nat = [], "A JUGER"
    poser("R3", "part du +1 entre 33 et 47 %, plafond 60 %", cas,
          f"{n1} criteres en +1 sur {len(pos)}", nat)

    de_valeur = [(s, p, t) for s, p, t in valeurs if est_critere_de_valeur(s, t)]
    structurels = len(valeurs) - len(de_valeur)
    courts = [f"{s} [+{p}] {t[:70]}" for s, p, t in de_valeur
              if t.count(SEPARATEUR) < 3]
    poser("R4", "prefixe d'entite : entite — poste — periode — valeur", courts,
          f"{len(de_valeur)} criteres de valeur"
          + (f", {structurels} structurels exemptes" if structurels else ""))

    # Les poignees sont un artefact de RENDU : le .json derive du .docx ne les
    # porte pas. Les y chercher reprocherait au format d'etre lui-meme.
    if docx:
        ids = [f"{s} {t[:60]}" for s, p, t in pos if POIGNEE_ID.search(t)]
        poser("R5a", "aucune poignee [ID] sur un critere", ids, f"{len(pos)} criteres")
        sans_p = [f"{s} {t[:60]}" for s, p, t in neg if not POIGNEE_P.search(t)]
        poser("R5b", "chaque penalite porte sa poignee [Pn]", sans_p,
              f"{len(neg)} penalites")
    else:
        poser("R5", "poignees [ID] / [Pn]", [],
              "non applicable : le .json ne les porte pas", "A JUGER")

    redites = [f"{s} {t[:70]}" for s, p, t in valeurs if TOLERANCE_REDITE.search(t)]
    poser("R6", "la tolerance par defaut n'est jamais redite en ligne", redites,
          f"{len(valeurs)} criteres de valeur")

    if neg:
        ok = PENALITES_CIBLE[0] <= len(neg) <= PENALITES_CIBLE[1]
        cas = [] if ok else [f"{len(neg)} penalites, hors bande 5-7"]
    else:
        cas = ["aucune penalite"]
    poser("R7", "5 a 7 penalites", cas, f"{len(neg)} penalites", "A JUGER")

    par_section = {}
    for s, p, t in pos:
        if GATE.search(t):
            par_section.setdefault(s, []).append(t[:50])
    multi = [f"{s} : {len(g)} gates" for s, g in par_section.items() if len(g) > 1]
    poser("R8", "au plus une gate par section", multi,
          f"{len(par_section)} sections avec gate")

    if pool_declare is not None and pool_declare != pool:
        cas = [f"pool declare {pool_declare}, somme des poids {pool}"]
    else:
        cas = []
    poser("R9", "les points somment au pool declare", cas,
          f"pool = {pool}" + (f", declare {pool_declare}" if pool_declare else ""))

    n = len(valeurs) + len(par_section)
    poser("R10", f"{CRITERES_GUIDE[0]} a {CRITERES_GUIDE[1]} criteres notes",
          [] if CRITERES_GUIDE[0] <= n <= CRITERES_GUIDE[1] else [f"{n} criteres"],
          f"{n} criteres", "A JUGER")

    fuites = [f"{s} {t[:70]}" for s, p, t in pos if FUITE.search(t)]
    poser("R11", "aucune formule, reference de cellule ni mention de la golden",
          fuites, f"{len(pos)} criteres")
    return R, pool


TEMOIN = [("A", "+", 5, "x"), ("A", "+", 1, "Bloc — Poste — FY0 — 1"),
          ("A", "-", 2, "erreur de signe")]


def autotest():
    """Un controle qui n'a rien lu rend vert : on lui donne des cas connus."""
    if 5 in POIDS_ADMIS:
        raise SystemExit("ARRET - le controle est casse : +5 serait admis")
    if not POIGNEE_P.search("[P3] x") or POIGNEE_P.search("[+3] x"):
        raise SystemExit("ARRET - le controle est casse : poignee [Pn] mal reconnue")
    if TEMOIN[1][3].count(SEPARATEUR) < 3:
        raise SystemExit("ARRET - le controle est casse : le gabarit de corps n'a plus 3 separateurs")
    if not est_critere_de_valeur("A", "Bloc \u2014 Poste \u2014 FY0 \u2014 11,233,017"):
        raise SystemExit("ARRET - une vraie valeur n'est plus reconnue")
    if est_critere_de_valeur("A", "Bloc \u2014 expected shortfall is taken at or below P10."):
        raise SystemExit("ARRET - une phrase structurelle passe pour une valeur")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("rubric", nargs="+", help="Rubric - <Pack>.docx ou .json")
    ap.add_argument("--detail", action="store_true")
    ap.add_argument("--json")
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass
    autotest()

    total = 0
    for chemin in a.rubric:
        R, pool = controler(chemin)
        print(f"\nCONTRAT DE RUBRIC - {chemin}   (pool {pool})")
        for d in R:
            dur = d["nature"] == "DEFAUT" and d["compte"]
            total += d["compte"] if dur else 0
            etat = "OK  " if not d["compte"] else ("FAUT" if dur else "JUGE")
            print(f"  [{etat}] {d['cle']:<4} {d['titre']:<56} {d['compte']:>4}   sur {d['sur']}")
        if a.detail:
            for d in R:
                if d["compte"]:
                    print(f"\n--- {d['cle']} {d['titre']}  ({d['nature']}, {d['compte']})")
                    for c in d["cas"]:
                        print(f"      {c}")
        if a.json:
            with open(a.json, "w", encoding="utf-8") as fh:
                json.dump(R, fh, ensure_ascii=False, indent=1)
    print(f"\nVIOLATIONS DE CONTRAT : {total}")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
