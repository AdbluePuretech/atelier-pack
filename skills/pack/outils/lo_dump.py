"""Recalcule un classeur dans LibreOffice et rend toutes ses valeurs.

C'est le moteur avec lequel le service QA note : ce que LibreOffice lit fait
foi la-bas, pas ce qu'Excel a mis en cache. Le script releve d'abord le reglage
d'iteration TEL QUE LE FICHIER LE PORTE — c'est ce que verra le correcteur —
puis force un recalcul complet et exporte chaque cellule.
"""
import json
import os
import subprocess
import sys
import time

import uno
from com.sun.star.beans import PropertyValue

CHEMIN, SORTIE = os.path.abspath(sys.argv[1]), sys.argv[2]
FORCER = len(sys.argv) > 3 and sys.argv[3] == "forcer"
PORT = 2002


def contexte():
    local = uno.getComponentContext()
    resolver = local.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver", local)
    for _ in range(40):
        try:
            return resolver.resolve(
                f"uno:socket,host=localhost,port={PORT};urp;StarOffice.ComponentContext")
        except Exception:
            time.sleep(1)
    raise SystemExit("ARRET — LibreOffice n'a pas repondu sur le socket")


ctx = contexte()
bureau = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
props = (PropertyValue("Hidden", 0, True, 0), PropertyValue("UpdateDocMode", 0, 3, 0))
doc = bureau.loadComponentFromURL(uno.systemPathToFileUrl(CHEMIN), "_blank", 0, props)

etat = {"iteration_du_fichier": bool(doc.IsIterationEnabled),
        "passages": doc.IterationCount, "ecart": doc.IterationEpsilon}
if FORCER:
    doc.IsIterationEnabled = True
    doc.IterationCount = 500
    doc.IterationEpsilon = 1e-06
etat["iteration_appliquee"] = bool(doc.IsIterationEnabled)

doc.calculateAll()

valeurs, erreurs = {}, 0
for i in range(doc.Sheets.Count):
    ws = doc.Sheets.getByIndex(i)
    cur = ws.createCursor()
    cur.gotoEndOfUsedArea(False)
    a = cur.RangeAddress
    if a.EndRow < 1 and a.EndColumn < 1:
        continue
    bloc = ws.getCellRangeByPosition(0, 0, a.EndColumn, a.EndRow)
    donnees = bloc.getDataArray()
    d = {}
    for r, ligne in enumerate(donnees):
        for c, v in enumerate(ligne):
            if isinstance(v, float) and v != 0:
                d[f"{r + 1}:{c + 1}"] = v
            elif isinstance(v, str) and v.startswith(("#", "Err:")):
                d[f"{r + 1}:{c + 1}"] = v
                erreurs += 1
    valeurs[ws.Name] = d

etat["cellules_en_erreur"] = erreurs
json.dump({"etat": etat, "valeurs": valeurs}, open(SORTIE, "w"))
print(json.dumps(etat, indent=2))
doc.close(False)
