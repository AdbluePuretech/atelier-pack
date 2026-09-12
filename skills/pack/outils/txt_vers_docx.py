"""Convertit un prompt ou une rubric redigee en `.txt` vers le `.docx` du corpus.

    python systeme/scripts/qa-pack/txt_vers_docx.py "Rubric - X.txt" "Rubric - X.docx" --gabarit ostrom
    python systeme/scripts/qa-pack/txt_vers_docx.py "Prompt - X.txt" "Prompt - X.docx" --gabarit madrid

On redige en `.txt` — versionnable, diffable, greppable — et on convertit au
dernier moment, parce que le harnais de Q&A reconnait les deux documents a leur
extension `.docx`.

**Le format ne s'imite pas, il se reprend.** Le script part du document
d'exemple, copie TOUTES les parties du paquet — styles, numerotation, theme,
reglages, table de polices — et ne regenere que `word/document.xml`. Ecrire ses
propres styles produit un document qui ressemble au gabarit sans en etre un :
les puces ne sont plus des puces, la police n'est plus la meme, et le service
recoit un document qui n'a pas la forme demandee.

Les deux gabarits se deposent dans `gabarits/`, ou se pointent par la
variable d'environnement `PACK_GABARITS`.

  ostrom  la rubric. Un paragraphe `Title`, un `Heading1` par section, et des
          `ListBullet` pour tout le reste. Le poids `[+N]` ouvre le critere en
          GRAS ; le corps d'une GATE est en ITALIQUE, le reste en romain.
  madrid  le prompt. Titre en gras taille 16, paragraphe d'attaque, un
          `Heading1` par grande partie, un bloc en gras italique taille 12 par
          groupe de sorties, et des `ListParagraph` numerotes pour les puces.
"""
from __future__ import annotations

import argparse
import re
import shutil
import zipfile
from pathlib import Path

# Les deux documents d'exemple du corpus. On les cherche d'abord dans le dossier
# `gabarits/` de la skill, ou il suffit de les deposer ; la variable
# d'environnement PACK_GABARITS permet de pointer ailleurs.
import os
EXEMPLES = Path(os.environ.get("PACK_GABARITS", Path(__file__).parent.parent / "gabarits"))
GABARITS = {"ostrom": EXEMPLES / "Rubric - Ostrom.docx",
            "madrid": EXEMPLES / "Prompt - Project_Madrid.docx"}

ESC = {"&": "&amp;", "<": "&lt;", ">": "&gt;"}
esc = lambda s: "".join(ESC.get(c, c) for c in s)

ARIAL = '<w:rFonts w:ascii="Arial" w:hAnsi="Arial"/>'
BLEU = '<w:color w:val="1F3864"/>'
POIDS = re.compile(r"^(\[[+\u2212-]\d+\]\s+)(.*)$")
SECTION = re.compile(r"^Section [A-Z] — ")
PARTIES_A_JETER = {"docProps/thumbnail.jpeg"}

CORE = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<cp:coreProperties '
        'xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/">'
        "<dc:title>{titre}</dc:title><dc:creator/><cp:lastModifiedBy/>"
        "</cp:coreProperties>")


def run(texte, gras=False, italique=False, taille=None, couleur=False):
    rpr = ARIAL
    if gras:
        rpr += "<w:b/>"
    rpr += "<w:i/>" if italique else '<w:i w:val="0"/>'
    if couleur:
        rpr += BLEU
    if taille:
        rpr += f'<w:sz w:val="{taille}"/>'
    espace = ' xml:space="preserve"' if texte != texte.strip() else ""
    return f"<w:r><w:rPr>{rpr}</w:rPr><w:t{espace}>{esc(texte)}</w:t></w:r>"


def para(style, runs, spacing=""):
    ppr = (f'<w:pStyle w:val="{style}"/>' if style else "") + spacing
    return f"<w:p><w:pPr>{ppr}</w:pPr>{''.join(runs)}</w:p>"


# --------------------------------------------------------------------------
def ostrom(lignes):
    """La rubric : titre, un Heading1 par section, des ListBullet ailleurs."""
    SP = '<w:spacing w:after="80" w:before="0"/>'
    out = []
    for i, l in enumerate(lignes):
        t = l.strip()
        if not t:
            continue
        if i == 0:
            out.append(para("Title", [run(t, taille="30", couleur=True)]))
        elif t == "Scoring configuration" or SECTION.match(t):
            out.append(para("Heading1", [run(t, taille="24", couleur=True)]))
        else:
            m = POIDS.match(t)
            if m:
                # Une gate enonce une condition de CONSTRUCTION, pas une valeur :
                # le gabarit la met en italique pour qu'elle se distingue a l'oeil.
                gate = " gate — " in m.group(2)
                out.append(para("ListBullet",
                                [run(m.group(1), gras=True, taille="20"),
                                 run(m.group(2), italique=gate, taille="20")], SP))
            else:
                out.append(para("ListBullet", [run(t, taille="20")], SP))
    return out


def madrid(lignes):
    """Le prompt : titre, attaque, Heading1 par partie, blocs, puces numerotees.

    Le gabarit porte TROIS niveaux sous la grande partie, et les confondre se
    voit : un bloc qui coiffe des puces est en gras italique corps 12 ; un
    intitule d'onglet, sous « Sheet Contents », n'est qu'en italique et sa
    description est un paragraphe courant, pas une puce.
    """
    GRANDES = {"Intermediate Outputs", "Final Outputs", "Xlsx Output"}
    PUCE = ('<w:numPr><w:ilvl w:val="0"/><w:numId w:val="2"/></w:numPr>'
            '<w:spacing w:after="40"/>')
    BLOC = '<w:spacing w:before="160" w:after="80"/>'
    COURANT = '<w:spacing w:after="120"/>'

    groupes, cur = [], []
    for l in lignes:
        if l.strip():
            cur.append(l.strip())
        elif cur:
            groupes.append(cur); cur = []
    if cur:
        groupes.append(cur)

    out, feuilles = [], False
    for i, g in enumerate(groupes):
        tete = g[0]
        if i == 0:
            out.append(para(None, [run(tete, gras=True, taille="32")],
                            '<w:spacing w:after="200"/>'))
            continue
        if i == 1:
            # Le gabarit met tout le paragraphe d'attaque en gras.
            out.append(para(None, [run(tete, gras=True)], COURANT))
            continue
        if tete in GRANDES:
            # Le gabarit laisse le style porter la police et le corps : le
            # paragraphe de titre n'habille pas son run.
            out.append(f"<w:p><w:pPr><w:pStyle w:val=\"Heading1\"/></w:pPr>"
                       f"<w:r><w:t>{esc(tete)}</w:t></w:r></w:p>")
            continue
        if len(g) == 1 and tete.endswith("."):
            out.append(para(None, [run(tete)], COURANT))
            continue
        if feuilles and len(g) == 2:
            out.append(para(None, [run(tete, italique=True)], BLOC))
            out.append(para(None, [run(g[1])], COURANT))
            continue
        out.append(para(None, [run(tete, gras=True, italique=True, taille="24")], BLOC))
        for l in g[1:]:
            out.append(para("ListParagraph", [run(l)], PUCE))
        if tete == "Sheet Contents":
            feuilles = True
    return out


PROFILS = {"ostrom": ostrom, "madrid": madrid}


def convertir(source, cible, profil):
    gabarit = GABARITS[profil]
    if not gabarit.exists():
        raise SystemExit(f"gabarit introuvable : {gabarit}")
    lignes = Path(source).read_text(encoding="utf8").splitlines()
    corps = "".join(PROFILS[profil](lignes))
    zin = zipfile.ZipFile(gabarit)
    modele = zin.read("word/document.xml").decode("utf8")
    tete = modele[:modele.index("<w:body>") + len("<w:body>")]
    # On garde la fin du corps du gabarit : elle porte la mise en page de la
    # section (marges, format du papier), qui n'est pas du contenu.
    queue = modele[modele.rindex("<w:sectPr"):]
    doc = tete + corps + queue
    titre = lignes[0].strip() if lignes else Path(cible).stem
    with zipfile.ZipFile(cible, "w", zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            if info.filename in PARTIES_A_JETER or info.filename.endswith("/"):
                continue
            if info.filename == "word/document.xml":
                data = doc.encode("utf8")
            elif info.filename == "docProps/core.xml":
                # Ne pas expedier les metadonnees du document d'un autre client.
                data = CORE.format(titre=esc(titre)).encode("utf8")
            elif info.filename == "[Content_Types].xml":
                data = re.sub(rb'<Default Extension="jpe?g"[^/]*/>', b"",
                              zin.read(info.filename))
            elif info.filename == "_rels/.rels":
                # Retirer une partie sans retirer sa RELATION laisse un paquet
                # que Word ouvre et que python-docx refuse : le harnais tombe
                # sur une vignette qui n'existe plus.
                data = re.sub(rb'<Relationship[^>]*thumbnail[^>]*/>', b"",
                              zin.read(info.filename))
            else:
                data = zin.read(info.filename)
            zout.writestr(info.filename, data)
    zin.close()
    return len([l for l in lignes if l.strip()])


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source")
    ap.add_argument("cible")
    ap.add_argument("--gabarit", choices=sorted(PROFILS), required=True)
    a = ap.parse_args()
    n = convertir(a.source, a.cible, a.gabarit)
    print(f"{n} paragraphes ecrits dans {a.cible}  (gabarit {a.gabarit})")
