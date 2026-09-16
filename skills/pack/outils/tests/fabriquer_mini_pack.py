# -*- coding: utf-8 -*-
"""Fabrique le mini-pack des tests des portes : un pack entier, minuscule et synthetique.

    python fabriquer_mini_pack.py <dossier>      # Windows + Excel : la golden est recalculee

Deux mecaniques (une commission calculee sur le net qu'elle reduit, donc une boucle ;
des interets sur ce net), trois ancrages, une input sheet d'un onglet, un prompt, une
rubric, un certificat, deux feuilles de score, une note d'equite. Rien n'y vient d'un
pack reel : ces fichiers partent avec la skill dans un depot public.

Le mini-pack est deja fabrique dans `mini-pack/` ; ce script sert a le refaire si son
format change.
"""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import openpyxl
from docx import Document
from openpyxl.styles import Font, PatternFill
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.workbook.properties import CalcProperties

ICI = Path(__file__).resolve().parent
OUTILS = ICI.parent
NOM = "Essai"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def golden(chemin, frais=0.02):
    wb = openpyxl.Workbook()
    wb.calculation = CalcProperties(iterate=True, iterateCount=200, iterateDelta=0.0000001, fullCalcOnLoad=True)
    bleu, vert, noir = Font(name="Arial", size=9, color="0000FF"), Font(name="Arial", size=9, color="008000"), Font(name="Arial", size=9)
    bandeau = PatternFill("solid", fgColor="1F2A36")
    inp = wb.active
    inp.title = "Input_Sheet"
    calc = wb.create_sheet("Calc")
    for ws in (inp, calc):
        ws.sheet_view.showGridLines = False
        ws["C2"], ws["C2"].font, ws["C2"].fill = ws.title, Font(name="Arial", size=9, bold=True, color="FFFFFF"), bandeau
    for i in range(5):
        calc.cell(3, 5 + i, f"FY{2026 + i}").font = noir
    for r, (lib, v) in enumerate((("Loan amount", 100), ("Fee rate", frais), ("Interest rate", 0.05), ("Loop breaker", 1)), start=4):
        inp.cell(r, 3, lib).font = noir
        c = inp.cell(r, 5, v)
        c.font, c.number_format = bleu, "#,##0.00_);(#,##0.00)"
    for r, (lib, f) in enumerate((("Net proceeds", "=Input_Sheet!$E$4-N({c}5)"),
                                  ("Fee on net proceeds", "=IF(Brk_Fee=1,Input_Sheet!$E$5*N({c}4),0)"),
                                  ("Interest on net proceeds", "=Input_Sheet!$E$6*{c}4")), start=4):
        calc.cell(r, 3, lib).font = noir
        for i, col in enumerate("EFGHI"):
            c = calc.cell(r, 5 + i, f.format(c=col))
            c.font, c.number_format = vert, "#,##0.00_);(#,##0.00)"
    dn = DefinedName("Brk_Fee", attr_text="Input_Sheet!$E$7")
    try:
        wb.defined_names["Brk_Fee"] = dn
    except TypeError:
        wb.defined_names.append(dn)
    wb.properties.creator = ""
    wb.save(chemin)


def input_sheet(chemin):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Input_Sheet"
    for r, (lib, v) in enumerate((("Loan amount", 100), ("Fee rate", 0.02), ("Interest rate", 0.05), ("Loop breaker", 1)), start=4):
        ws.cell(r, 3, lib)
        ws.cell(r, 5, v)
    wb.properties.creator = ""
    wb.save(chemin)


def docx(chemin, lignes):
    d = Document()
    for l in lignes:
        d.add_paragraph(l)
    d.core_properties.author = ""
    d.core_properties.last_modified_by = ""
    d.save(chemin)


GRAINE = """Build a model where a lender charges a fee computed on the net proceeds it reduces,
and interest accrues on those net proceeds.
Outputs: net proceeds, the fee, the interest.
"""

CONCEPTION = """# Conception - Essai

## Graine -> pack

| Element | Nature | Passage de la graine |
|---------|--------|----------------------|
| Fee on net proceeds | mecanique | a fee computed on the net proceeds it reduces |
| Interest on net proceeds | mecanique | interest accrues on those net proceeds |
| Net proceeds | sortie | Outputs: net proceeds |

## Noyau dur

La commission se calcule sur le net qu'elle reduit : un point fixe.

## Mecaniques et pieges

| Id | Mecanique | Famille | Piege nomme | Bonne reponse | Erreur plausible | Points qui tombent |
|----|-----------|---------|-------------|---------------|------------------|--------------------|
| M1 | Commission sur le net | auto-reference | commission sur le brut | 1,96 | 2,00 | fee, net |
| M2 | Interets sur le net | chaine | interets sur le brut | 4,90 | 5,00 | interest |

## Boucles

| Boucle | Interrupteur | Convention des pieces | Mecanique | Amplitude estimee |
|--------|--------------|-----------------------|-----------|-------------------|
| Commission sur le net | Brk_Fee | la commission est due sur le net verse | M1 | 0,04 |

## Budget de discrimination

Part du pool en transcription : 15 %

## Niveau

Niveau vise : L1

## Frontieres

Pas de fiscalite.

## Fiche de mise en page

page_de_garde: non
intercalaires: non
noms_onglets: Snake_Case
colonne_libelles: C
premiere_colonne_valeurs: E
colonne_unites: non
volet_fige: non
police: Arial
corps: 9
bandeau: 1F2A36
onglets_colores: non
blocs: libelle gras seul
nombres: deux decimales, negatifs (x)
documents: prompt famille C, rubric famille Ostrom

## Rollout d'enonce

M1 : une passe.

## Tests de declenchement

Commission a 0 % : la boucle disparait.
"""

ANCRAGES = [
    {"id": "A01", "mecanique": "M1", "poste": "Fee on net proceeds", "periode": "FY2026", "cellule": "Calc!E5",
     "valeur": 1.96078, "tolerance": {"relative": 0.001}, "nature": "D", "pourquoi": "la boucle converge a 2/102"},
    {"id": "A02", "mecanique": "M1", "poste": "Net proceeds", "periode": "FY2026", "cellule": "Calc!E4",
     "valeur": 98.0392, "tolerance": {"relative": 0.001}, "nature": "S", "pourquoi": "100/1,02"},
    {"id": "A03", "mecanique": "M2", "poste": "Interest on net proceeds", "periode": "FY2026", "cellule": "Calc!E6",
     "valeur": 4.90196, "tolerance": {"absolue": 0.001}, "nature": "S", "pourquoi": "5 % du net"},
]

RUBRIC = """Project Essai - Assessment Rubric

Section A — Loan (3 criteria, 5 points)
[+2] Calc — Fee on net proceeds — FY2026 — 1.961
[+2] Calc — Net proceeds — FY2030 — 98.039
[+1] Calc — Interest on net proceeds — FY2026 — 4.902
"""

RUBRIC_JUICEE = """Project Essai - Assessment Rubric (juiced)

Section A — Loan (3 criteria, 6 points)
[+4] Calc — Fee on net proceeds — FY2026 — 1.961
[+2] Calc — Net proceeds — FY2030 — 98.039
[+0] Fee gate — the fee is computed on the net proceeds it reduces. If not met, every criterion in this section scores 0.
"""


def main(dossier):
    d = Path(dossier)
    (d / "build" / "audit").mkdir(parents=True, exist_ok=True)
    (d / "graine.md").write_text(GRAINE, encoding="utf-8")
    (d / "CONCEPTION.md").write_text(CONCEPTION, encoding="utf-8")
    (d / "ancrages.json").write_text(json.dumps(ANCRAGES, indent=1), encoding="utf-8")
    gold = d / "build" / f"GoldenSolution - {NOM}.xlsx"
    ai = d / "build" / f"AI Output - {NOM}.xlsx"
    golden(gold)
    golden(ai, frais=0.0)
    for x in (gold, ai):
        r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                            str(OUTILS / "recalculer.ps1"), "-Chemin", str(x)], capture_output=True, text=True)
        print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr)
        subprocess.run([sys.executable, str(OUTILS / "nettoyer_metadonnees.py"), str(x)], capture_output=True)
    input_sheet(d / "build" / f"InputSheet - {NOM}.xlsx")
    docx(d / "build" / f"Prompt - {NOM}.docx", ["Prompt - Calc: Fee on net proceeds",
                                                  "Net proceeds, fee on net proceeds and interest on net proceeds, FY2026 to FY2030."])
    (d / "build" / "rubric.txt").write_text(RUBRIC, encoding="utf-8")
    docx(d / "build" / f"Rubric - {NOM}.docx", RUBRIC.splitlines())
    rub = d / "build" / f"Rubric - {NOM}.docx"
    (d / "build" / "rubric_juicee.txt").write_text(RUBRIC_JUICEE, encoding="utf-8")
    docx(d / "build" / f"Rubric - {NOM} (juicee).docx", RUBRIC_JUICEE.splitlines())
    rubj = d / "build" / f"Rubric - {NOM} (juicee).docx"
    (d / "build" / "audit" / "certificat.json").write_text(json.dumps({
        "classeur": gold.name, "empreinte_sha256": sha(gold), "cellules_de_calcul": 3, "cellules_couvertes": 3,
        "couverture_pct": 100.0, "manques": {}, "journal": []}, indent=1), encoding="utf-8")
    (d / "build" / "score_ai_output.json").write_text(json.dumps({
        "pourcentage": 20.0, "points": 1, "pool": 5, "source": "claude.ai", "date": "2026-09-17",
        "rubric_sha256": sha(rub)}, indent=1), encoding="utf-8")
    (d / "build" / "score_adverse.json").write_text(json.dumps({
        "pourcentage": 30.0, "points": 1.8, "pool": 6, "source": "claude.ai", "date": "2026-09-17",
        "rubric_sha256": sha(rubj)}, indent=1), encoding="utf-8")
    (d / "build" / "note_equite.md").write_text(
        "# Note d'equite\n\n- Fee gate : un banquier attend la commission sur le net verse.\n"
        "- Keystone fee : la valeur qui prouve le point fixe.\n", encoding="utf-8")
    (d / "pack.json").write_text(json.dumps({
        "nom": NOM, "niveau": "L1", "graine": "graine.md", "conception": "CONCEPTION.md", "ancrages": "ancrages.json",
        "lot": None, "premier_du_lot": True,
        "golden": f"build/GoldenSolution - {NOM}.xlsx", "input_sheet": f"build/InputSheet - {NOM}.xlsx",
        "certificat": "build/audit/certificat.json",
        "prompt": f"build/Prompt - {NOM}.docx", "rubric": f"build/Rubric - {NOM}.docx", "rubric_source": "build/rubric.txt",
        "ai_output": f"build/AI Output - {NOM}.xlsx", "score_ai_output": "build/score_ai_output.json",
        "cible_score": [0, 45],
        "paquet": [f"build/GoldenSolution - {NOM}.xlsx", f"build/InputSheet - {NOM}.xlsx",
                   f"build/Prompt - {NOM}.docx", f"build/Rubric - {NOM}.docx"],
        "juicing": {"rubric": f"build/Rubric - {NOM} (juicee).docx", "rubric_source": "build/rubric_juicee.txt",
                    "score_adverse": "build/score_adverse.json", "note_equite": "build/note_equite.md"},
        "controles_du_pack": {}}, indent=2, ensure_ascii=False), encoding="utf-8")
    print("mini-pack ecrit :", d)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ICI / "mini-pack")
