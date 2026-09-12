# -*- coding: utf-8 -*-
"""Remet les valeurs attendues d'une rubric a jour sur sa golden, sans rien juger.

Quand une golden est corrigee, la rubric qui la note reste ecrite sur l'ancienne
version : ses `Values` designent des chiffres qui n'existent plus, et la golden
cesse de rendre 100 % sur sa propre rubric. Le jugement de l'auteur — les
libelles, les poids, le decoupage en sections — n'a lui aucune raison de bouger.

Ce script ne relit donc QUE les chiffres et les formules, aux plages que la
rubric designe deja. Il ne cree pas de critere, n'en supprime pas, ne renote
rien. Si une plage n'existe plus dans le classeur, il le dit et s'arrete plutot
que d'ecrire un critere muet.

    python rafraichir_rubric.py <rubric.json> <golden.xlsx> <sortie.json>
"""
import datetime
import json
import re
import sys

from openpyxl import load_workbook
from openpyxl.utils import column_index_from_string, get_column_letter

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RUBRIC, GOLDEN, SORTIE = sys.argv[1], sys.argv[2], sys.argv[3]

d = json.load(open(RUBRIC, encoding="utf-8-sig"))
R = d["Rubric"] if "Rubric" in d else d
wf = load_workbook(GOLDEN)
wv = load_workbook(GOLDEN, data_only=True)

PLAGE = re.compile(r"^'?([^'!]+)'?!\$?([A-Z]{1,3})\$?(\d+)(?::\$?([A-Z]{1,3})\$?(\d+))?$")

touches = inchanges = 0
introuvables = []
for sec, crits in R.items():
    for c in crits:
        m = PLAGE.match(c.get("cell_range", ""))
        if not m:
            introuvables.append((sec, c.get("cell_range"), "plage illisible")); continue
        nom = m.group(1)
        if nom not in wf.sheetnames:
            introuvables.append((sec, c["cell_range"], "onglet absent")); continue
        ws, wsv = wf[nom], wv[nom]
        c1, r1 = column_index_from_string(m.group(2)), int(m.group(3))
        c2, r2 = (column_index_from_string(m.group(4)), int(m.group(5))) if m.group(4) else (c1, r1)
        vals, forms = {}, {}
        for rr in range(min(r1, r2), max(r1, r2) + 1):
            for cc in range(min(c1, c2), max(c1, c2) + 1):
                coord = get_column_letter(cc) + str(rr)
                v = wsv.cell(rr, cc).value
                f = ws.cell(rr, cc).value
                if isinstance(v, (datetime.datetime, datetime.date, datetime.time)):
                    # le corpus stocke les dates en ISO 8601 ; sans cette conversion
                    # json.dump echoue et la comparaison d'idempotence est toujours fausse
                    v = v.isoformat()
                if v is not None:
                    vals[coord] = v
                if isinstance(f, str) and f.startswith("="):
                    forms[coord] = f
        if vals == (c.get("Values") or {}) and forms == (c.get("Formulae") or {}):
            inchanges += 1
            continue
        c["Values"] = vals
        c["Formulae"] = forms
        c["hasFormulae"] = bool(forms)
        touches += 1

if introuvables:
    print(f"  ARRET — {len(introuvables)} critere(s) visent une plage que la golden n'a plus :")
    for s, cr, pourquoi in introuvables[:10]:
        print(f"     {cr}  ({pourquoi})  dans « {s[:60]} »")
    raise SystemExit(1)

json.dump(d, open(SORTIE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"  criteres rafraichis : {touches}   inchanges : {inchanges}")
