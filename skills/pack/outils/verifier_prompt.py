# -*- coding: utf-8 -*-
"""Controle un prompt de pack contre le contrat observe sur le corpus.

Le prompt est le seul des quatre livrables que personne ne verifiait : la
tracabilite le compare a la rubric, le rollout le suit, la livraison exige son
nom - mais rien ne regardait ce qu'il contient.

Les regles ci-dessous ne sont pas inventees : elles sont relevees sur 45 prompts
livres du corpus.

  P1  au plus 7 pages          22 des 28 prompts dont Word a garde le compte
                               tiennent la barre ; mediane 6,5. Un prompt qui
                               s'etale noie l'enonce et se fait renvoyer.
  P2  le bloc de format        45/45 portent `Xlsx Output` et
                               `Formatting Requirements`. C'est le bloc qu'on
                               oublie, et sans lui le candidat livre un modele
                               qui ne ressemble a rien d'attendu.
  P3  la carte des onglets     45/45 portent `Sheet Contents` : le prompt EST le
                               cahier des charges du generateur.
  P4  les sorties exigees      44/45 portent `Intermediate Outputs` et
                               `Final Outputs`.
  P5  aucune formule Excel     0/45 en contiennent une. Le prompt dit QUOI
                               produire, jamais COMMENT.
  P6  la provenance            « based on the data in the Input_Sheet » : tout
                               vient de la, aucune source externe. C'est ce qui
                               separe ce corpus d'un corpus source sur documents.

Le compte de pages vit dans `docProps/app.xml`, que Word ecrit en enregistrant.
Il est parfois PERIME - quatre prompts du corpus s'y annoncent a une page et zero
mot. Quand il est absent ou incoherent, on retombe sur le nombre de mots, a
440 mots la page, mesure sur les prompts dont le compte est fiable.
"""
import argparse
import io
import re
import sys
import zipfile

PAGES_MAX = 7
MOTS_PAR_PAGE = 440

BLOCS = {
    "P2": (("Xlsx Output", "Formatting Requirements"), "le bloc de format du classeur"),
    "P3": (("Sheet Contents",), "la carte des onglets"),
    "P4": (("Intermediate Outputs", "Final Outputs"), "les sorties exigees"),
}
FORMULE = re.compile(r"=\s*(SUM|IF|INDEX|MATCH|NPV|IRR|XIRR|SUMPRODUCT|AVERAGE|MAX|MIN)\s*\(", re.I)
# Trois formulations coexistent dans le corpus pour la meme regle - « based on
# the data in », « using the inputs provided in », « from the data in ». Ne
# chercher que la premiere rendait 11 faux positifs sur 45 : le controle
# reprochait aux prompts de ne pas dire ce qu'ils disaient autrement.
PROVENANCE = re.compile(
    r"\b(based on|using|from|per|as set out in)\b[^.\n]{0,40}\bInput[_ ]?Sheet\b", re.I)


def _texte(docx):
    with zipfile.ZipFile(docx) as d:
        xml = d.read("word/document.xml").decode("utf-8", "replace")
        try:
            app = d.read("docProps/app.xml").decode("utf-8", "replace")
        except KeyError:
            app = ""
    xml = re.sub(r"</w:p>", "\n", xml)
    xml = re.sub(r"<w:tab[^>]*/>", "\t", xml)
    texte = re.sub(r"<[^>]+>", "", xml)
    for e, c in (("&amp;", "&"), ("&quot;", '"'), ("&apos;", "'"),
                 ("&lt;", "<"), ("&gt;", ">")):
        texte = texte.replace(e, c)
    pg = re.search(r"<Pages>(\d+)</Pages>", app)
    wd = re.search(r"<Words>(\d+)</Words>", app)
    return texte, (int(pg.group(1)) if pg else None), (int(wd.group(1)) if wd else None)


def controler(chemin):
    texte, pages, mots = _texte(chemin)
    mots_reels = len(texte.split())
    # Le compte de Word prime, sauf quand il se contredit lui-meme.
    source = "Word"
    if not pages or (mots is not None and mots == 0 and mots_reels > 200):
        pages = max(1, round(mots_reels / MOTS_PAR_PAGE))
        source = f"estime a {MOTS_PAR_PAGE} mots/page"

    R = []
    R.append(("P1", pages <= PAGES_MAX,
              f"au plus {PAGES_MAX} pages",
              f"{pages} page(s) ({source}), {mots_reels} mots"))
    for cle, (marqueurs, titre) in sorted(BLOCS.items()):
        absents = [m for m in marqueurs if m.lower() not in texte.lower()]
        R.append((cle, not absents, titre,
                  "present" if not absents else "MANQUE : " + ", ".join(absents)))
    trouvees = sorted({m.group(0) for m in FORMULE.finditer(texte)})
    R.append(("P5", not trouvees, "aucune formule Excel",
              "aucune" if not trouvees else f"{len(trouvees)} : " + ", ".join(trouvees[:5])))
    R.append(("P6", bool(PROVENANCE.search(texte)),
              "la provenance est enoncee",
              "enoncee" if PROVENANCE.search(texte) else "la phrase de provenance est absente"))
    return R


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("prompt", nargs="+", help="un ou plusieurs Prompt - <Pack>.docx")
    ap.add_argument("--pages", type=int, default=PAGES_MAX)
    a = ap.parse_args()
    globals()["PAGES_MAX"] = a.pages
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass

    total = 0
    for chemin in a.prompt:
        R = controler(chemin)
        rates = [r for r in R if not r[1]]
        total += len(rates)
        print(f"\n{chemin}")
        for cle, ok, titre, detail in R:
            print(f"  [{'OK  ' if ok else 'FAUT'}] {cle}  {titre:<32} {detail}")
    print(f"\n  controles en echec : {total}")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
