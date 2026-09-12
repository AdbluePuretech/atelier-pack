"""Refuse toute fonction Excel que le correcteur ne sait pas evaluer.

Le service QA recalcule les classeurs sous LIBREOFFICE, pas sous Excel. Une
fonction moderne d'Excel — `LET`, `LAMBDA`, `XLOOKUP`, les tableaux dynamiques —
y rend `#NAME?`, et le pack se fait demolir sur un modele parfaitement juste :
c'est ce qui a coule un pack du corpus, dont la golden a note 53 / 200 sur sa
propre rubric pour cette seule raison.

Le controle est deterministe et sans faux positif : il lit les formules, pas les
valeurs. A lancer AVANT tout televersement, et idealement en fin de build.
"""
import re
import sys
import zipfile
from collections import Counter

# Ce que LibreOffice Calc n'evalue pas, ou pas de la meme facon.
FONCTION = re.compile(r"\b([A-Z][A-Z0-9.]*)\s*\(")
FORMULE = re.compile(r"<f[^>]*>([^<]*)</f>")

INTERDITES = {
    "LET", "LAMBDA", "XLOOKUP", "XMATCH", "FILTER", "SORT", "SORTBY", "UNIQUE",
    "SEQUENCE", "RANDARRAY", "TEXTJOIN", "TEXTSPLIT", "TEXTBEFORE", "TEXTAFTER",
    "IFS", "SWITCH", "MAXIFS", "MINIFS", "CONCAT", "TAKE", "DROP", "CHOOSECOLS",
    "CHOOSEROWS", "HSTACK", "VSTACK", "EXPAND", "TOCOL", "TOROW", "WRAPCOLS",
    "WRAPROWS", "BYROW", "BYCOL", "MAP", "REDUCE", "SCAN", "MAKEARRAY",
    "ARRAYTOTEXT", "VALUETOTEXT", "GROUPBY", "PIVOTBY", "PERCENTOF", "IMAGE",
}


def controler(chemin):
    """Lit les formules dans le XML brut du .xlsx, sans passer par openpyxl.

    On ne cherche que des noms de fonctions : ouvrir le classeur avec openpyxl
    pour ca coute des dizaines de secondes sur un modele de 30 000 formules, et
    fait echouer un balayage de parc sur le seul temps de chargement.
    """
    vues, fautives = Counter(), {}
    with zipfile.ZipFile(chemin) as z:
        feuilles = {}
        try:
            wbx = z.read("xl/workbook.xml").decode("utf-8", "replace")
            for i, m in enumerate(re.finditer(r'<sheet[^>]*name="([^"]*)"', wbx), 1):
                feuilles[f"sheet{i}.xml"] = m.group(1)
        except KeyError:
            pass
        for nom in z.namelist():
            if not re.fullmatch(r"xl/worksheets/sheet\d+\.xml", nom):
                continue
            titre = feuilles.get(nom.rsplit("/", 1)[1], nom)
            xml = z.read(nom).decode("utf-8", "replace")
            # Excel ecrit des formules PARTAGEES : `<f t="shared" si="0"/>`, sans
                # contenu ni balise fermante. Le texte ne vit que dans la cellule
                # maitresse du groupe — ce qui suffit pour reperer une fonction, mais
                # une expression gourmande avale tout jusqu'au prochain `</f>`.
                # Le contenu d'une formule ne porte jamais de `<` : il est echappe.
            # Excel ecrit des formules PARTAGEES : `<f t="shared" si="0"/>`, sans
            # contenu ni balise fermante. Le texte ne vit que dans la cellule maitresse
            # du groupe, ce qui suffit pour reperer une fonction — mais une expression
            # gourmande avalerait tout jusqu'au prochain `</f>`. Le contenu d'une
            # formule ne porte jamais de `<` : il est echappe en `&lt;`.
            for mf in FORMULE.finditer(xml):
                for m in re.finditer(FONCTION, mf.group(1)):
                    nomf = m.group(1)
                    vues[nomf] += 1
                    if nomf in INTERDITES:
                        fautives.setdefault(nomf, []).append(titre)
    return vues, {k: sorted(set(v)) for k, v in fautives.items()}


TEMOIN = '<f>=LET(x,1,x)+SUM(A1:A2)</f><f t="shared" si="0"/><f>=IF(A1&gt;0,1,0)</f>'


def autotest():
    """Le controle doit savoir reconnaitre un cas fautif, sinon il ne prouve rien."""
    noms = [m.group(1) for mf in FORMULE.finditer(TEMOIN)
            for m in FONCTION.finditer(mf.group(1))]
    attendu = {"LET", "SUM", "IF"}
    if set(noms) != attendu:
        raise SystemExit(f"ARRET — le controle est casse : il lit {set(noms)} "
                         f"la ou il doit lire {attendu}")


if __name__ == "__main__":
    autotest()
    vues, fautives = controler(sys.argv[1])
    print(f"  fonctions distinctes employees : {len(vues)}")
    if not fautives:
        print("  fonctions hors portee de LibreOffice : AUCUNE")
        raise SystemExit(0)
    print(f"  FONCTIONS HORS PORTEE : {len(fautives)}")
    for nom, ou in sorted(fautives.items()):
        print(f"    {nom:<14} sur les onglets : {', '.join(ou[:5])}")
    raise SystemExit(1)
