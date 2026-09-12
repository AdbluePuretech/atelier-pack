# -*- coding: utf-8 -*-
"""Retire d'un classeur tout ce qui identifie son auteur ou sa machine.

Le controle `L2_authoring_metadata` du service bloque la livraison si le fichier
porte un nom d'auteur, un chemin absolu, un repertoire utilisateur Windows ou un
identifiant de compte OneDrive. Et il a raison de bloquer : rien en aval ne les
retire — ni l'app de QA, ni le rollout. Ils partent chez le client.

Trois nids, et il faut les vider tous les trois :

  docProps/core.xml   `dc:creator`, `cp:lastModifiedBy`
  docProps/app.xml    `Company`, `Manager`
  xl/workbook.xml     `x15ac:absPath` — le chemin du dossier d'ou le classeur a
                      ete enregistre, glisse dans un bloc AlternateContent. C'est
                      lui qui porte le chemin du dossier utilisateur Windows et

On patche le XML en place : reecrire le classeur avec openpyxl detruirait le
cache de valeurs, et un correcteur qui recalcule ne le pardonne pas.

    python nettoyer_metadonnees.py <classeur.xlsx> [sortie.xlsx]

**A lancer EN DERNIER.** Excel reecrit `cp:lastModifiedBy`, `absPath` et le
pointeur de co-edition a CHAQUE enregistrement : purger puis recalculer remet
tout en place, et le controle rebloque. L'ordre est donc toujours corriger,
recalculer, PUIS purger.
"""
import re
import shutil
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SOURCE = sys.argv[1]
SORTIE = sys.argv[2] if len(sys.argv) > 2 else None

BALISES = ("dc:creator", "cp:lastModifiedBy", "cp:lastPrinted",
           "Company", "Manager", "dc:title", "dc:subject", "cp:keywords",
           "dc:description", "cp:category")

_BS = chr(92)
# Ce qu'on cherche, c'est une IDENTITE : un dossier utilisateur, un compte de
# stockage, un nom. Pas un identifiant de revision — `xr:revisionPtr` porte un
# documentId hexadecimal qui ne designe personne, et le confondre avec un compte
# fait echouer le controle sur un fichier propre.
SUSPECT = re.compile("(?i)([A-Z]:" + re.escape(_BS) + "Users" + re.escape(_BS)
                     + "|/Users/|d" + re.escape(".") + "docs" + re.escape(".") + "live" + re.escape(".") + "net"
                     + "|onedrive|-my" + re.escape(".") + "sharepoint" + re.escape(".") + "com)")


def nettoyer(nom, txt):
    trouve = []
    if nom in ("docProps/core.xml", "docProps/app.xml"):
        for b in BALISES:
            for m in re.finditer(r"<" + re.escape(b) + r"(\s[^>]*)?>(.*?)</" + re.escape(b) + r">", txt, re.S):
                if m.group(2).strip():
                    trouve.append(f"{nom} <{b}> = {m.group(2)[:70]!r}")
            txt = re.sub(r"<" + re.escape(b) + r"(\s[^>]*)?>.*?</" + re.escape(b) + r">",
                         lambda m: f"<{b}{m.group(1) or ''}></{b}>", txt, flags=re.S)
    if nom == "xl/workbook.xml":
        # le bloc AlternateContent qui porte absPath : on le supprime en entier,
        # Excel comme LibreOffice le regenerent sans broncher.
        for m in re.finditer(r'<mc:AlternateContent.*?</mc:AlternateContent>', txt, re.S):
            if "absPath" in m.group(0):
                chemin = re.search(r'url="([^"]*)"', m.group(0))
                trouve.append(f"{nom} absPath = {chemin.group(1)[:90]!r}" if chemin else f"{nom} absPath")
        txt = re.sub(r'<mc:AlternateContent(?:(?!</mc:AlternateContent>).)*absPath(?:(?!</mc:AlternateContent>).)*</mc:AlternateContent>',
                     "", txt, flags=re.S)
        # Le pointeur de revision de la co-edition : un documentId et un GUID de
        # session. Excel le regenere a la prochaine sauvegarde ; le laisser, c'est
        # laisser filer la trace d'un partage.
        for m in re.finditer(r'<xr:revisionPtr[^>]*/>', txt):
            trouve.append(f"{nom} xr:revisionPtr (co-edition)")
        txt = re.sub(r'<xr:revisionPtr[^>]*/>', "", txt)
    return txt, trouve


zin = zipfile.ZipFile(SOURCE)
cible = SORTIE or (SOURCE + ".nettoye")
rapport = []
with zipfile.ZipFile(cible, "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename in ("docProps/core.xml", "docProps/app.xml", "xl/workbook.xml"):
            txt, trouve = nettoyer(item.filename, data.decode("utf-8"))
            rapport += trouve
            data = txt.encode("utf-8")
        zout.writestr(item, data)
zin.close()
if not SORTIE:
    shutil.move(cible, SOURCE)
    cible = SOURCE

# controle : plus rien de suspect dans les trois nids
restes = []
z = zipfile.ZipFile(cible)
for n in ("docProps/core.xml", "docProps/app.xml", "xl/workbook.xml"):
    if n in z.namelist():
        for m in SUSPECT.finditer(z.read(n).decode("utf-8", "replace")):
            restes.append(f"{n} : ...{m.group(0)[:60]}...")

print(f"  {SOURCE}")
for r in rapport:
    print(f"     retire  {r}")
if not rapport:
    print("     (rien a retirer)")
if restes:
    print(f"     RESTE {len(restes)} trace(s) suspecte(s) :")
    for r in restes[:8]:
        print(f"        {r}")
    raise SystemExit(1)
print("     controle : aucune trace d'auteur, de chemin ou de compte")
