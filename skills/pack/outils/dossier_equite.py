"""Monte le dossier du Q&A INVERSE : chaque point perdu, et de quoi le contester.

L'audit d'equite ne verifie pas le candidat, il verifie LA RUBRIC. Il reprend
chaque point retire et le classe : perte legitime, incertaine, ou **defaut de
rubric**. La charge de la preuve s'inverse — ce n'est plus au candidat de
meriter ses points, c'est a la rubric de justifier ceux qu'elle retire.

Sur le rapport du service, l'auditeur bute regulierement sur la meme chose : il
se declare incapable de trancher parce que le dossier lui donne le chiffre
attendu sans montrer D'OU IL SORT. Ce script corrige ce manque a la source : pour
chaque perte, il joint la CELLULE et la FORMULE de la golden. Un critere dont la
formule ne se laisse pas rattacher au prompt est un defaut de rubric, et ca se
voit alors immediatement.

Sortie : un JSON pour la machine, un Markdown pour l'auditeur — humain ou modele.
"""
import json
import re
import sys
from datetime import datetime

from docx import Document
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

RUBRIC, GOLDEN, CANDIDAT, SORTIE = sys.argv[1:5]
NL = chr(10)
MOIS = dict(zip("jan feb mar apr may jun jul aug sep oct nov dec".split(), range(1, 13)))
COL = "DEFGHI"


def norm(s):
    s = str(s or "").strip().lower()
    for a, b in (("\u2019", "'"), ("\u2013", "-"), ("\u2014", "-"), ("\u00b7", "-")):
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def indexer(wb):
    idx = {}
    for ws in wb.worksheets:
        d = {}
        for r in range(1, ws.max_row + 1):
            for c in (2, 3):
                lab = ws.cell(row=r, column=c).value
                if isinstance(lab, str) and lab.strip():
                    d.setdefault(norm(lab), []).append(r)
        idx[ws.title] = d
    return idx


gv, gf = load_workbook(GOLDEN, data_only=True), load_workbook(GOLDEN, data_only=False)
cv = load_workbook(CANDIDAT, data_only=True)
IG, IC = indexer(gv), indexer(cv)


_CACHE = {}


def grille(wb, feuille):
    """Repere les colonnes d'exercice sur l'EN-TETE de la feuille elle-meme.

    On cherche, dans les douze premieres lignes : une ligne portant FY0..FY5,
    sinon une ligne d'index de periode 0..5, sinon une ligne de dates de cloture.
    Le repli sur D..I ne sert que si la feuille ne porte aucun en-tete.
    """
    cle = (id(wb), feuille)
    if cle in _CACHE:
        return _CACHE[cle]
    ws = wb[feuille]
    fin = min(ws.max_column, 200)
    grille, dates = {}, {}
    for r in range(1, min(ws.max_row, 14) + 1):
        vus = {}
        for c in range(2, fin + 1):
            v = ws.cell(row=r, column=c).value
            if isinstance(v, str) and re.fullmatch(r"FY[0-5]", v.strip()):
                vus[v.strip()] = c
        if len(vus) >= 4:
            grille = vus
            break
    if not grille:
        for r in range(1, min(ws.max_row, 14) + 1):
            vus, suite = {}, []
            for c in range(2, fin + 1):
                v = ws.cell(row=r, column=c).value
                if isinstance(v, int) and 0 <= v <= 5:
                    suite.append((v, c))
            if [x for x, _ in suite] == list(range(6)):
                vus = {f"FY{x}": c for x, c in suite}
            if vus:
                grille = vus
                break
    # les colonnes mensuelles, pour les periodes « month ending ... »
    for r in range(1, min(ws.max_row, 14) + 1):
        for c in range(2, fin + 1):
            v = ws.cell(row=r, column=c).value
            if getattr(v, "date", None):
                dates.setdefault(v.date(), c)
    _CACHE[cle] = (grille, dates)
    return _CACHE[cle]


COLONNE_UNIQUE = 4          # colonne D, la premiere colonne de donnee


def colonnes_serie(wb, feuille):
    """Les six colonnes d'exercice d'une feuille, pour un critere de trajectoire."""
    if feuille not in wb.sheetnames:
        return []
    g, _ = grille(wb, feuille)
    g = g or {f"FY{k}": 4 + k for k in range(6)}
    return [g.get(f"FY{k}") for k in range(6)]


def colonne(wb, feuille, periode):
    feuille = feuille_de(wb, feuille)
    if feuille is None:
        return None
    g, dates = grille(wb, feuille)
    repli = {f"FY{k}": 4 + k for k in range(6)}
    g = g or repli
    if periode == "FY0-FY5":
        return g.get("FY0")
    if re.fullmatch(r"FY[0-5]", periode):
        return g.get(periode)
    if periode in ("register", "run configuration", "every fiscal year"):
        return g.get("FY0")
    # Un bouclage de sources et emplois, un total de batterie : ces postes ne
    # vivent PAS dans la grille de periodes, ils tiennent en une colonne. Sans
    # ce jeton, le correcteur les cherche sous FY0 et ne trouve rien.
    if periode == "total":
        return COLONNE_UNIQUE
    if periode == "life of hold":
        return g.get("FY5")
    m = re.match(r"month ending (\d{1,2})-([A-Za-z]{3})-(\d{4})", periode)
    if m:
        cible = datetime(int(m.group(3)), MOIS[m.group(2).lower()], int(m.group(1))).date()
        return dates.get(cible)
    return None


def signe_seul(attendu, obtenu):
    """Meme grandeur, signe oppose : une convention d'affichage, pas une erreur."""
    if not isinstance(attendu, (int, float)) or not isinstance(obtenu, (int, float)):
        return False
    return attendu * obtenu < 0 and abs(abs(obtenu) - abs(attendu)) <= abs(attendu) * 0.01 + 1e-9


def _retenir(wb, f, lignes, col):
    """Un libelle peut coiffer un bandeau ET une ligne : on garde celle qui chiffre."""
    if col:
        chif = [r for r in lignes
                if isinstance(wb[f].cell(row=r, column=col).value, (int, float))
                or getattr(wb[f].cell(row=r, column=col).value, "year", None)]
        if chif:
            return chif[-1]
    return lignes[-1]


def feuille_de(wb, nom):
    """Retrouve une feuille meme si le candidat l'a nommee autrement.

    La rubric nomme l'onglet comme la golden le nomme — « 08. Pocket_Price_
    Waterfall ». Un candidat a le droit d'ecrire « Pocket_Price_Waterfall », et
    lui refuser ses points pour un prefixe serait noter son style, pas son
    modele.
    """
    if nom in wb.sheetnames:
        return nom
    net = lambda s: re.sub(r"^\d+\.\s*", "", str(s)).strip().lower()
    cible = net(nom)
    for s in wb.sheetnames:
        if net(s) == cible:
            return s
    return None


def par_accord(wb, feuille, poste):
    """Adresse « <bloc>, <cle de ligne> » sur les onglets a blocs repetes.

    Le meme libelle « DEN-047 » designe sa date de repricing, son taux collare ou
    son facteur de survie selon le bloc ou on le lit. Sans cette resolution en
    deux temps, un correcteur attrape la premiere ligne venue — une date la ou il
    attend un taux — et note faux un modele juste.
    """
    # Deux separateurs, pour deux besoins distincts. La virgule adresse un ACCORD
    # dans un bloc (« Phasing factor, DEN-047 »). Le double chevron adresse un
    # POSTE dont le libelle se repete d'un bloc a l'autre : « Book total »
    # apparait quatre fois sur MFN_Clause, « Fire & Life Safety » neuf fois sur
    # Cost_Build. Sans lui, le correcteur lit le premier qu'il croise et note une
    # valeur juste au mauvais endroit.
    m = re.match(r"^(.+?) >> (.+)$", poste) or re.match(r"^(.+?), (.+)$", poste)
    feuille = feuille_de(wb, feuille) if m else None
    if not m or feuille is None:
        return None
    bloc, accord = m.group(1).strip().lower(), m.group(2).strip()
    ws = wb[feuille]
    debut = None
    for r in range(1, ws.max_row + 1):
        v = str(ws.cell(row=r, column=3).value or "").strip()
        # Deux conventions de bandeau de bloc coexistent dans le corpus :
        # « 3 - Repricing dates » et « A.4  Gross price ». On accepte les deux,
        # sinon l'adressage en deux temps ne sert qu'au pack qui l'a invente.
        b2 = re.match(r"^\d+ - (.*)$", v) or re.match(r"^[A-Z]\.\d+\s+(.*)$", v)
        if b2 and b2.group(1).strip().lower().startswith(bloc):
            debut = r
            break
    if debut is None:
        return None
    for r in range(debut + 1, min(debut + 200, ws.max_row + 1)):
        if str(ws.cell(row=r, column=3).value or "").strip() == accord:
            return r
    return None


def trouver(idx, wb, feuille, poste, col):
    """Rend (feuille, ligne). Exact d'abord, puis approche sur les jetons.

    Sans l'etape approchee, un modele juste qui nomme sa ligne « Scale-back
    factor carried back to the run-rate roll » la ou la rubric dit « ... applied
    to every capped agreement » est compte faux. C'est le correcteur qui echoue,
    pas le candidat.
    """
    r = par_accord(wb, feuille, poste)
    if r is not None:
        return feuille_de(wb, feuille), r, "bloc/accord"
    cible, jt = norm(poste), set(norm(poste).split())
    ordre = ([feuille] if feuille in idx else []) + [s for s in idx if s != feuille]
    for f in ordre:
        if cible in idx[f]:
            return f, _retenir(wb, f, idx[f][cible], col), "exact"
    scores = []
    for f in ordre:
        for lab, lignes in idx[f].items():
            j = set(lab.split())
            if j:
                scores.append((len(jt & j) / max(len(jt | j), 1), f, lignes))
    scores.sort(key=lambda x: -x[0])
    if not scores:
        return None, None, "poste introuvable"
    premier = scores[0]
    second = scores[1][0] if len(scores) > 1 else 0.0
    if premier[0] < 0.6:
        return None, None, "poste introuvable"
    if premier[0] - second < 0.12:
        return None, None, f"appariement ambigu ({premier[0]:.0%} contre {second:.0%})"
    _, f, lignes = premier
    return f, _retenir(wb, f, lignes, col), f"approche {premier[0]:.0%}"


def reussi(corps, attendu, obtenu):
    """Applique le test que le critere ANNONCE, pas un test maison.

    Reduire la comparaison au numerique declarait perdues toutes les dates, y
    compris identiques, et ignorait les tolerances ecrites dans le critere. Un
    dossier qui invente des pertes fait rater les vraies a l'auditeur.
    """
    if hasattr(attendu, "year"):
        return hasattr(obtenu, "year") and obtenu.date() == attendu.date()
    if not isinstance(attendu, (int, float)) or not isinstance(obtenu, (int, float)):
        return False
    if "pass if exactly" in corps or "pass if 0 in every" in corps:
        return abs(obtenu - attendu) < 1e-6
    m = re.search(r"within ±([\d\.]+)(pp|x|)", corps)
    if m:
        marge = float(m.group(1)) / (100 if m.group(2) == "pp" else 1)
        return abs(obtenu - attendu) <= marge + 1e-9
    return abs(obtenu - attendu) <= abs(attendu) * 0.01 + 1e-9


def ref(feuille, ligne, col):
    return f"{feuille}!{get_column_letter(col)}{ligne}" if feuille and col else None


doc = Document(RUBRIC)
section, pertes, total, perdu, douteux, signes = None, [], 0, 0, 0, 0
for p in doc.paragraphs:
    t = p.text.strip()
    if p.style.name == "Heading 1" and t.startswith("Section "):
        section = t
        continue
    m = re.match(r"^\[\+(\d+)\]\s+(.*)$", t)
    if not m or section is None:
        continue
    poids, corps = int(m.group(1)), m.group(2)
    total += poids
    # « Sourcing — » rejoint « Method — » et « Formatting — » : ce sont des
    # conditions de CONSTRUCTION, qui se jugent sur le classeur et non en lisant
    # une cellule. Les classer en valeur revenait a chercher un poste nomme
    # « sheet 01. Input_Sheet is BUILT by the model... » dans la golden, a ne pas
    # le trouver, et a compter l'echec de la recherche comme une incertitude.
    genre = ("gate" if " gate — " in corps else
             "methode" if corps.startswith(("Method —", "Formatting —", "Sourcing —"))
             else "valeur")
    if genre != "valeur":
        # Une condition de construction ne se lit pas dans une cellule : elle part
        # telle quelle a l'auditeur, qui juge sur le classeur.
        pertes.append({"section": section, "poids": poids, "genre": genre,
                       "critere": corps, "verdict_attendu": "a juger sur le classeur"})
        continue
    parts = [x.strip() for x in corps.split(" — ")]
    feuille, poste, periode = parts[0].split("/")[0].strip(), parts[1], parts[2]
    cg = colonne(gv, feuille, periode)
    fg, rg, _ = trouver(IG, gv, feuille, poste, cg)
    cc = colonne(cv, feuille, periode)
    fc, rc, appar = trouver(IC, cv, feuille, poste, cc)
    if fc and fc != feuille:
        cc = colonne(cv, fc, periode) or cc
    attendu = gv[fg].cell(row=rg, column=cg).value if fg and cg else None
    obtenu = cv[fc].cell(row=rc, column=cc).value if fc and cc else None
    if periode == "FY0-FY5":
        cg6, cc6 = colonnes_serie(gv, fg or feuille), colonnes_serie(cv, fc or feuille)
        att6 = [gv[fg].cell(row=rg, column=c).value if fg and c else None for c in cg6]
        obt6 = [cv[fc].cell(row=rc, column=c).value if fc and c else None for c in cc6]
        ok = all(reussi(corps, a_, o_) for a_, o_ in zip(att6, obt6))
        # on rapporte le PREMIER exercice qui decroche : c'est la ou la
        # trajectoire part, et c'est ce qu'un correcteur doit pouvoir montrer.
        for k, (a_, o_) in enumerate(zip(att6, obt6)):
            if not reussi(corps, a_, o_):
                attendu, obtenu = a_, o_
                cg = cg6[k]
                cc = cc6[k]
                break
    else:
        ok = reussi(corps, attendu, obtenu)
    if ok:
        continue
    # Un poste qu'on n'a pas su localiser n'est PAS une perte : c'est une
    # incertitude du correcteur. Les confondre revient a noter son propre echec
    # de recherche au debit du candidat.
    localise = bool(fc and cc) and obtenu is not None
    if signe_seul(attendu, obtenu):
        signes += poids
    elif localise:
        perdu += poids
    else:
        douteux += poids
    pertes.append({
        "section": section, "poids": poids, "critere": corps,
        "genre": ("signe" if signe_seul(attendu, obtenu)
                  else "valeur" if localise else "a_verifier"),
        "golden": {"cellule": ref(fg, rg, cg),
                   "valeur": attendu,
                   "formule": gf[fg].cell(row=rg, column=cg).value if fg and cg else None},
        "candidat": {"cellule": ref(fc, rc, cc), "valeur": obtenu,
                     "appariement": appar,
                     "motif": "poste introuvable dans le classeur du candidat" if not fc
                              else "periode introuvable" if not cc else "valeur hors tolerance"},
    })

json.dump({"pool": total, "perdu_confirme": perdu, "a_verifier": douteux, "signe_seul": signes, "pertes": pertes},
          open(SORTIE, "w", encoding="utf-8"), ensure_ascii=False, indent=2, default=str)

md = SORTIE.rsplit(".", 1)[0] + ".md"
with open(md, "w", encoding="utf-8") as f:
    nv = sum(1 for x in pertes if x["genre"] == "valeur")
    f.write("# Dossier d'equite — chaque point retire, et de quoi le contester\n\n")
    nd = sum(1 for x in pertes if x["genre"] == "a_verifier")
    entete = (
        f"Pool positif : **{total}**." + NL + NL
        + f"- Pertes **confirmees** : **{perdu}** points sur {nv} criteres. Le poste a ete"
        + f" localise dans le classeur du candidat, et sa valeur est hors tolerance." + NL
        + f"- **A verifier a la main** : {douteux} points sur {nd} criteres. Le correcteur"
        + f" n'a pas su localiser le poste : **ce n'est pas une perte, c'est une"
        + f" incertitude**, le candidat nomme peut-etre sa ligne autrement." + NL
        + f"- Criteres de construction a juger sur le classeur : {len(pertes) - nv - nd}."
        + NL + NL)
    f.write(entete)
    f.write("Pour chaque perte : le critere, la cellule et **la formule** de la golden qui\n"
            "produit la valeur attendue, et ce que porte le classeur du candidat.\n\n"
            "Verdict attendu pour chacune : `ok` (perte legitime), `incertain`, ou\n"
            "`defaut_rubric` (la rubric exige une chose que le prompt ne demande pas,\n"
            "ou que la formule de la golden ne justifie pas).\n\n")
    for i, x in enumerate(pertes, 1):
        f.write(f"## {i}. [{x['genre']}] +{x['poids']} — {x['section'][:60]}\n\n")
        f.write(f"- **Critere** : {x['critere']}\n")
        if x["genre"] == "valeur":
            g, c = x["golden"], x["candidat"]
            f.write(f"- **Golden** : `{g['cellule']}` = {g['valeur']}\n")
            f.write(f"- **Formule de la golden** : `{g['formule']}`\n")
            f.write(f"- **Candidat** : {c['cellule']} = {c['valeur']} ({c['motif']})\n")
        f.write("\n")
nv = sum(1 for x in pertes if x["genre"] == "valeur")
nd = sum(1 for x in pertes if x["genre"] == "a_verifier")
print(f"  pool                             : {total}")
print(f"  pertes CONFIRMEES                : {perdu} points sur {nv} criteres")
print(f"  poste non localise, A VERIFIER   : {douteux} points sur {nd} criteres")
ns = sum(1 for x in pertes if x["genre"] == "signe")
print(f"  signe seul (convention d'affichage) : {signes} points sur {ns} criteres")
print(f"  criteres de construction a juger : {len(pertes) - nv - nd - ns}")
print(f"  ecrit : {SORTIE}  et  {md}")
