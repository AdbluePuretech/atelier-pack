"""Chaque critere de la rubric doit se rattacher a une exigence du prompt.

C'est le controle « prompt-rubric matching » du service, joue en local. Il classe
comme lui :

  FAILED   le critere demande une chose que le prompt ne demande pas du tout ;
  STRETCH  le sujet est bien dans le prompt, mais l'exigence precise du critere
           n'y est pas ecrite et ne decoule pas mecaniquement de ce qui l'est ;
  OK       une exigence du prompt le porte.

Le rattachement se fait sur le vocabulaire : un critere dont aucun mot rare ne
figure dans le prompt ne peut pas etre defendu devant l'auditeur d'equite. La
partie deterministe ne remplace pas un juge, elle lui prepare le travail en
sortant les candidats — et surtout elle ne rate jamais un onglet inexistant.
"""
import re
import sys
from collections import Counter

from docx import Document

PROMPT, RUBRIC = sys.argv[1], sys.argv[2]
INPUT = sys.argv[3] if len(sys.argv) > 3 else None

MOTS_VIDES = set("""a an the and or of to in on at by for with from as is are be been
that this these those it its their his her they them we you i not no any all each every
if then than so such but into over under out up down more most less least other another
which who whom whose what when where how why can may must shall will would should could
pass if exactly within value values line item items sheet fiscal year years total
model prompt rubric criterion criteria section point points check checks""".split())


def racine(m):
    """Racinisation minimale : le pluriel ne doit pas faire un mot different.

    « violation » et « violations » designent la meme exigence ; les compter a
    part faisait passer pour non notee une exigence que la rubric couvrait.
    """
    if len(m) > 4 and m.endswith("ies"):
        return m[:-3] + "y"
    # « es » ne se retire qu'apres une sifflante : sinon « rates » devient « rat ».
    if len(m) > 4 and m.endswith("es") and m[-3] in "sxzhio":
        return m[:-2]
    if len(m) > 3 and m.endswith("s") and not m.endswith(("ss", "us", "is")):
        return m[:-1]
    return m


def jetons(t):
    return {racine(m) for m in re.findall(r"[a-z][a-z\-]{2,}", t.lower())
            if m not in MOTS_VIDES}


pr = Document(PROMPT)
puces = [p.text.strip() for p in pr.paragraphs if p.text.strip()]
# Le candidat recoit le prompt ET l'input sheet. Une exigence portee par un
# libelle d'hypothese — le spread du cas 2, le seuil de paiement du vendor note —
# est aussi legitime qu'une puce du prompt. Ne juger que le prompt inventait des
# defauts la ou le pack est complet.
puces_prompt = list(puces)

if INPUT and INPUT.lower().endswith((".htm", ".html")):
    # Format environnement : les hypotheses ne sont plus servies dans une
    # feuille, elles sont a chercher dans un terminal. Le vocabulaire legitime
    # est donc celui du terminal - un critere qui cite "head register" ou
    # "free-freight threshold" est defendable parce que l'environnement les
    # porte, exactement comme un libelle d'Input_Sheet l'etait.
    import html as _h
    import json as _j
    brut = open(INPUT, encoding="utf-8").read()
    m = re.search(r"const ARTICLES = (\[.*?\]);\s*\nconst ", brut, re.S)
    if m:
        for a in _j.loads(m.group(1)):
            puces.append(a.get("titre", ""))
            puces += a.get("puces", [])
            puces += [re.sub(r"<[^>]+>", " ", b) for b in a.get("corps", [])]
        puces = [_h.unescape(p) for p in puces]
    else:
        puces.append(_h.unescape(re.sub(r"<[^>]+>", " ", brut)))
elif INPUT:
    from openpyxl import load_workbook
    ws = load_workbook(INPUT)["Input_Sheet"]
    for r in range(1, ws.max_row + 1):
        v = ws.cell(row=r, column=3).value
        if isinstance(v, str):
            puces.append(v)

CORPUS = jetons(" ".join(puces))
FREQ = Counter()
for p in puces:
    FREQ.update(jetons(p))

ru = Document(RUBRIC)
section = None
resultats = []
for p in ru.paragraphs:
    t = p.text.strip()
    if p.style.name == "Heading 1" and t.startswith("Section "):
        section = t
        continue
    m = re.match(r"^\[([+−-])(\d+)\]\s+(.*)$", t)
    if not m or section is None:
        continue
    signe, poids, corps = m.group(1), int(m.group(2)), m.group(3)
    genre = ("penalite" if signe != "+" else
             "gate" if " gate — " in corps else
             "methode" if corps.startswith(("Method —", "Formatting —")) else "valeur")
    # On ne juge que le VOCABULAIRE DE FOND : la feuille, le poste, la mecanique.
    # Les chiffres, les tolerances et les periodes ne sont pas dans le prompt par
    # construction, et les compter ferait du bruit.
    sujet = re.split(r" — (?:FY\d|register|life of hold|every fiscal year|month ending|run configuration)", corps)[0]
    # La phraseologie de NOTATION n'est pas une exigence : « Charged once », « If
    # not met ... scores 0 », « pass if within ... ». La laisser dans le test
    # faisait passer les huit penalites en STRETCH pour leur boilerplate, et
    # noyait les deux vrais defauts.
    for boiler in (r"Charged once\..*$", r"If not met,.*$", r"pass if.*$",
                   r"Graded on its own:.*$",
                   r"yet .*still lands within tolerance.*?\.", r"^\[P\d+\]\s*"):
        sujet = re.sub(boiler, "", sujet).strip()
    j = jetons(sujet)
    inconnus = sorted(j - CORPUS)
    rares = sorted(x for x in j & CORPUS if FREQ[x] <= 1)
    couverture = 1 - len(inconnus) / max(len(j), 1)
    etat = "FAILED" if couverture < 0.55 else "STRETCH" if couverture < 0.80 else "OK"
    resultats.append((etat, couverture, section[:1], genre, poids, corps, inconnus, rares))

# ------------------------------------------------------------------ sens inverse
# L'autre moitie du controle : une exigence du prompt que la rubric ne note nulle
# part fait travailler le candidat pour rien, et signale un pack qui demande plus
# qu'il ne mesure. On ne juge que les exigences de FOND — les puces de mise en
# forme et de structure sont couvertes en bloc par la section formatage.
VOCAB_RUBRIC = set()
for r in resultats:
    VOCAB_RUBRIC |= jetons(r[5])

orphelines = []
for texte in puces_prompt:
    j = jetons(texte)
    if len(j) < 4:
        continue
    couvert = len(j & VOCAB_RUBRIC) / len(j)
    if couvert < 0.5:
        orphelines.append((couvert, texte, sorted(j - VOCAB_RUBRIC)))

print("=" * 96)
print("TRACABILITE PROMPT -> RUBRIC")
print("=" * 96)
c = Counter(r[0] for r in resultats)
g = Counter(r[3] for r in resultats)
print(f"  criteres examines : {len(resultats)}   {dict(g)}")
print(f"  OK {c['OK']}   STRETCH {c['STRETCH']}   FAILED {c['FAILED']}")
for etat in ("FAILED", "STRETCH"):
    sel = [r for r in resultats if r[0] == etat]
    if not sel:
        continue
    print(f"\n  --- {etat} ({len(sel)}) ---")
    for _, cv, sec, genre, poids, corps, inconnus, _ in sorted(sel, key=lambda r: r[1]):
        print(f"    [{sec}] {genre:<9} +{poids}  couverture {cv:.0%}")
        print(f"        {corps[:104]}")
        print(f"        mots absents du prompt : {', '.join(inconnus[:12])}")

print()
print("=" * 96)
print("SENS INVERSE — EXIGENCES DU PROMPT QUE LA RUBRIC NE NOTE PAS")
print("=" * 96)
print(f"  exigences examinees : {len(puces_prompt)}")
print(f"  SANS COUVERTURE     : {len(orphelines)}")
for cv, texte, absents in sorted(orphelines)[:14]:
    print(f"    couverture {cv:.0%}  {texte[:96]}")
    print(f"        non repris par la rubric : {', '.join(absents[:10])}")
