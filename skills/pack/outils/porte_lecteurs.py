# -*- coding: utf-8 -*-
"""Les lecteurs des portes : lancer un outil de la skill et tirer de sa sortie UNE ligne.

Chaque outil imprime son resultat a sa facon. Une porte ne peut rien bloquer tant
qu'elle ne sait pas lire ce resultat : ce module fait la traduction, un lecteur par
outil, vers la ligne standard (lu, ecarts, verdict).

La regle qui gouverne tous les lecteurs est celle de la skill : un controle qui n'a
rien lu rend vert. Donc `lu == 0` n'est jamais VERT, et un motif attendu absent de la
sortie est un ROUGE « sortie illisible », jamais un zero ecart suppose.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

ICI = Path(__file__).resolve().parent

VERT, ROUGE, NON_FAIT = "VERT", "ROUGE", "NON FAIT"


@dataclass
class Ligne:
    id: str
    libelle: str
    lu: int = 0
    ecarts: int = 0
    verdict: str = ROUGE
    detail: str = ""
    fichiers: list = field(default_factory=list)

    def dict(self):
        return dict(id=self.id, libelle=self.libelle, lu=self.lu, ecarts=self.ecarts,
                    verdict=self.verdict, detail=self.detail, fichiers=[str(f) for f in self.fichiers])


def juger(id, libelle, lu, ecarts, detail="", fichiers=()):
    """Le verdict ne se declare pas, il se deduit : rien lu ou un ecart = ROUGE."""
    if lu is None:
        return Ligne(id, libelle, 0, 0, ROUGE, "sortie illisible : " + detail, list(fichiers))
    if lu <= 0:
        return Ligne(id, libelle, 0, ecarts or 0, ROUGE, "rien lu" + (" : " + detail if detail else ""), list(fichiers))
    return Ligne(id, libelle, lu, ecarts, VERT if ecarts == 0 else ROUGE, detail, list(fichiers))


def non_fait(id, libelle, raison, fichiers=()):
    return Ligne(id, libelle, 0, 0, NON_FAIT, raison, list(fichiers))


def lancer(args, cwd=None, timeout=3600):
    """Lance une commande et rend (code, sortie). Une commande introuvable rend (None, message)."""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    try:
        r = subprocess.run(args, cwd=cwd, capture_output=True, timeout=timeout, env=env,
                           shell=isinstance(args, str))
    except FileNotFoundError as e:
        return None, str(e)
    except subprocess.TimeoutExpired:
        return None, f"delai depasse ({timeout} s)"
    sortie = (r.stdout or b"").decode("utf-8", errors="replace") + (r.stderr or b"").decode("utf-8", errors="replace")
    return r.returncode, sortie


def outil(nom, *args, timeout=3600):
    return lancer([sys.executable, str(ICI / nom), *[str(a) for a in args]], timeout=timeout)


def nombre(motif, texte, groupe=1):
    m = re.search(motif, texte)
    return int(float(m.group(groupe).replace(",", "").replace(" ", ""))) if m else None


def fin(sortie, n=600):
    return sortie.strip()[-n:].replace("\n", " / ")


def excel_present():
    if os.name != "nt":
        return False
    code, sortie = lancer(["powershell", "-NoProfile", "-Command",
                           "if (Get-ItemProperty 'Registry::HKEY_CLASSES_ROOT\\Excel.Application' -ErrorAction SilentlyContinue) { 'oui' } else { 'non' }"],
                          timeout=60)
    return code == 0 and "oui" in sortie


def libreoffice_present():
    return Path(r"C:\Program Files\LibreOffice\program\soffice.exe").exists()


# ---- les lecteurs, un par outil ---------------------------------------------

def compter_boucles(id, golden, minimum, detail_min=""):
    code, s = outil("compter_boucles.py", golden)
    reelles = nombre(r"MECANIQUES CIRCULAIRES REELLES\s*:\s*(\d+)", s)
    formules = nombre(r"formules\s*:\s*([\d,]+)", s)
    if reelles is None:
        return juger(id, "boucles reelles", None, 0, fin(s), [golden])
    return juger(id, "boucles reelles", formules, max(0, minimum - reelles),
                 f"{reelles} mecanique(s) reelle(s), minimum {minimum}{detail_min}", [golden])


def inputs_morts(id, golden):
    code, s = outil("inputs_morts.py", golden)
    if "ARRET" in s:
        return juger(id, "hypotheses mortes", None, 0, fin(s), [golden])
    conso = nombre(r"hypotheses consommees\s*:\s*(\d+)", s)
    mortes = nombre(r"HYPOTHESES MORTES\s*:\s*(\d+)", s)
    colonne = re.search(r"libelles\s*:\s*colonne (\w+)", s)
    if conso is None or mortes is None:
        return juger(id, "hypotheses mortes", None, 0, fin(s), [golden])
    return juger(id, "hypotheses mortes", conso + mortes, mortes + (1 if conso == 0 else 0),
                 f"{conso} consommee(s), {mortes} morte(s), libelles en {colonne.group(1) if colonne else '?'}", [golden])


def formules_sures(id, golden):
    code, s = outil("formules_sures.py", golden)
    vues = nombre(r"fonctions distinctes employees\s*:\s*(\d+)", s)
    if vues is None:
        return juger(id, "formules sures", None, 0, fin(s), [golden])
    fautives = 0 if "AUCUNE" in s else (nombre(r"FONCTIONS HORS PORTEE\s*:\s*(\d+)", s) or 0)
    return juger(id, "formules sures", vues, fautives, f"{fautives} fonction(s) hors portee sur {vues}", [golden])


RANG = {"L1": 1, "L2": 2, "L3": 3}


def niveau(id, golden, vise):
    code, s = outil("niveau.py", golden)
    logiques = nombre(r"logiques distinctes\s*:\s*([\d,]+)", s)
    m = re.search(r"NIVEAU TENU SUR LE FICHIER\s*:\s*(L[123]|aucun)", s)
    if logiques is None or not m:
        return juger(id, "niveau tenu", None, 0, fin(s), [golden])
    tenu = m.group(1)
    ok = RANG.get(tenu, 0) >= RANG.get(vise, 9)
    return juger(id, "niveau tenu", logiques, 0 if ok else 1, f"tenu {tenu}, vise {vise}, {logiques} logiques", [golden])


def _mise_en_page(id, libelle, args, fichiers, premier_du_lot):
    code, s = outil("mise_en_page.py", *args)
    ib = len(re.findall(r"HORS STANDARD IB", s))
    if premier_du_lot:
        m = re.search(r"STANDARDS IB\s*:\s*(tenus|(\d+) ecart)", s)
        if not m:
            return juger(id, libelle, None, 0, fin(s), fichiers)
        ecarts = 0 if m.group(1) == "tenus" else int(m.group(2))
        return juger(id, libelle, 1, ecarts, f"premier pack du lot, declare ; {ecarts} ecart(s) IB", fichiers)
    if "RIEN COMPARE" in s:
        return juger(id, libelle, 0, ib, "aucun classeur du lot lu", fichiers)
    m = re.search(r"(\d+) classeurs compares, (\d+) trop proches", s)
    if not m:
        return juger(id, libelle, None, 0, fin(s), fichiers)
    lus, proches = int(m.group(1)), int(m.group(2))
    return juger(id, libelle, lus, proches + ib, f"{lus} compare(s), {proches} trop proche(s), {ib} ecart(s) IB", fichiers)


def mise_en_page(id, golden, lot, premier_du_lot):
    if premier_du_lot:
        return _mise_en_page(id, "mise en page", [golden], [golden], True)
    return _mise_en_page(id, "mise en page", [golden, "--contre", lot], [golden], False)


def fiche(id, conception):
    code, s = outil("mise_en_page.py", "--fiche", conception)
    m = re.search(r"FICHE\s*:\s*(\d+) axe\(s\) lus, (\d+) hors options", s)
    if not m:
        return juger(id, "fiche de mise en page", None, 0, fin(s), [conception])
    hors = re.findall(r"(?:HORS OPTIONS|AXE MANQUANT) : ([^\n]+)", s)
    return juger(id, "fiche de mise en page", int(m.group(1)), int(m.group(2)),
                 "; ".join(hors) if hors else f"{m.group(1)} axes dans les options admises", [conception])


def distance_fiche(id, conception, lot, premier_du_lot):
    if premier_du_lot:
        return juger(id, "distance de la fiche au lot", 1, 0, "premier pack du lot, declare", [conception])
    code, s = outil("mise_en_page.py", "--fiche", conception, "--contre", lot)
    if "RIEN COMPARE" in s:
        return juger(id, "distance de la fiche au lot", 0, 0, "aucun classeur du lot lu", [conception])
    c = re.search(r"(\d+) classeurs compares, (\d+) trop proches", s)
    if not c:
        return juger(id, "distance de la fiche au lot", None, 0, fin(s), [conception])
    lus, proches = int(c.group(1)), int(c.group(2))
    return juger(id, "distance de la fiche au lot", lus, proches, f"{lus} compare(s), {proches} trop proche(s)", [conception])


def verifier_prompt(id, prompt):
    code, s = outil("verifier_prompt.py", prompt)
    lus = len(re.findall(r"\[(OK  |FAUT)\]", s))
    echecs = nombre(r"controles en echec\s*:\s*(\d+)", s)
    if echecs is None:
        return juger(id, "contrat du prompt", None, 0, fin(s), [prompt])
    return juger(id, "contrat du prompt", lus, echecs, f"{echecs} controle(s) en echec sur {lus}", [prompt])


def verifier_rubric(id, rubric):
    code, s = outil("verifier_rubric.py", rubric)
    lus = len(re.findall(r"\[(OK  |FAUT|JUGE)\]", s))
    total = nombre(r"VIOLATIONS DE CONTRAT\s*:\s*(\d+)", s)
    if total is None:
        return juger(id, "contrat de la rubric", None, 0, fin(s), [rubric])
    return juger(id, "contrat de la rubric", lus, total, f"{total} violation(s) sur {lus} regles", [rubric])


def noter(id, classeur, rubric_source, libelle="la golden re-note 100 %"):
    code, s = outil("noter.py", classeur, "--rubric", rubric_source)
    m = re.search(r"VALEUR\s*:\s*([\d.]+)\s*/\s*([\d.]+) points", s)
    nr = nombre(r"non resolus[^:]*:\s*[\d.]+ points sur (\d+) criteres", s)
    if not m:
        return juger(id, libelle, None, 0, fin(s), [classeur, rubric_source])
    gagne, pool = float(m.group(1)), float(m.group(2))
    ecarts = (0 if abs(gagne - pool) < 1e-9 else 1) + (nr or 0)
    return juger(id, libelle, int(round(pool)), ecarts,
                 f"{gagne:g} / {pool:g} points, {nr or 0} critere(s) non resolu(s)", [classeur, rubric_source])


def score_de(classeur, rubric_source):
    """Le pourcentage que noter.py donne a un classeur, ou None."""
    code, s = outil("noter.py", classeur, "--rubric", rubric_source)
    m = re.search(r"VALEUR\s*:\s*([\d.]+)\s*/\s*([\d.]+) points", s)
    return (float(m.group(1)) / float(m.group(2)) * 100) if m and float(m.group(2)) else None


def amplitude_boucles(id, golden, rubric_source):
    code, s = outil("amplitude_boucles.py", golden, "--rubric", rubric_source)
    if "ETAPE NON FAITE" in s:
        return juger(id, "chaque boucle notee", 0, 0, "aucun interrupteur trouve", [golden, rubric_source])
    m = re.search(r"BOUCLES DECORATIVES\s*:\s*(\d+)\s*/\s*(\d+)", s)
    if not m:
        return juger(id, "chaque boucle notee", None, 0, fin(s), [golden, rubric_source])
    inconnues = len(re.findall(r"\[\?\?\?\?\]", s))
    return juger(id, "chaque boucle notee", int(m.group(2)), int(m.group(1)) + inconnues,
                 f"{m.group(1)} decorative(s), {inconnues} non mesuree(s) sur {m.group(2)}", [golden, rubric_source])


def tracabilite(id, prompt, rubric, input_sheet=None):
    args = [prompt, rubric] + ([input_sheet] if input_sheet else [])
    code, s = outil("tracabilite.py", *args)
    crit = nombre(r"criteres examines\s*:\s*(\d+)", s)
    failed = nombre(r"FAILED (\d+)", s)
    exig = nombre(r"exigences examinees\s*:\s*(\d+)", s)
    orph = nombre(r"SANS COUVERTURE\s*:\s*(\d+)", s)
    if None in (crit, failed, exig, orph):
        return juger(id, "tracabilite prompt <-> rubric", None, 0, fin(s), [prompt, rubric])
    return juger(id, "tracabilite prompt <-> rubric", crit + exig, failed + orph,
                 f"{failed} critere(s) sans appui dans le prompt, {orph} exigence(s) non notee(s)", [prompt, rubric])


def gs_audit(id, golden):
    code, s = outil("gs_audit.py", golden)
    formules = nombre(r"formules ([\d,]+)", s)
    durs = nombre(r"VIOLATIONS DURES\s*:\s*(\d+)", s)
    if durs is None:
        return juger(id, "audit de la golden", None, 0, fin(s), [golden])
    return juger(id, "audit de la golden", formules, durs, f"{durs} violation(s) dure(s)", [golden])


def traces_ia(id, golden):
    code, s = outil("traces_ia.py", golden)
    defauts = nombre(r"defauts objectifs\s*:\s*(\d+)", s)
    lus = sum(int(x) for x in re.findall(r"sur (\d+)", s))
    if defauts is None:
        return juger(id, "traces de fabrication", None, 0, fin(s), [golden])
    return juger(id, "traces de fabrication", lus, defauts, f"{defauts} defaut(s) objectif(s) sur {lus} elements lus", [golden])


def dossier_equite(id, rubric, golden, candidat):
    sortie = Path(tempfile.mkdtemp()) / "equite.json"
    code, s = outil("dossier_equite.py", rubric, golden, candidat, sortie)
    pool = nombre(r"pool\s*:\s*([\d.]+)", s)
    douteux = nombre(r"A VERIFIER\s*:\s*[\d.]+ points sur (\d+) criteres", s)
    signes = nombre(r"signe seul[^:]*:\s*[\d.]+ points sur (\d+) criteres", s)
    if pool is None or douteux is None or signes is None:
        return juger(id, "equite des pertes", None, 0, fin(s), [rubric, golden, candidat])
    return juger(id, "equite des pertes", pool, douteux + signes,
                 f"{douteux} perte(s) a verifier, {signes} perte(s) de signe seul", [rubric, golden, candidat])


def parite_libreoffice(id, golden):
    if not libreoffice_present():
        return non_fait(id, "parite LibreOffice", "LibreOffice absent", [golden])
    sortie = Path(tempfile.mkdtemp()) / "lo-valeurs.json"
    code, s = lancer(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                      str(ICI / "parite_libreoffice.ps1"), "-Chemin", str(golden), "-Sortie", str(sortie)])
    lus = nombre(r"cellules comparees\s*:\s*([\d,]+)", s)
    ecarts = nombre(r"ECARTS[^:]*:\s*(\d+)", s)
    if lus is None or ecarts is None:
        return juger(id, "parite LibreOffice", None, 0, fin(s or ""), [golden])
    return juger(id, "parite LibreOffice", lus, ecarts, f"{ecarts} ecart(s) sur {lus} cellules", [golden])


LIGNE_PACK = re.compile(r"^PORTE\s+(\S+)\s*\|\s*lu\s+(\d+)\s*\|\s*ecarts\s+(\d+)\s*\|\s*(VERT|ROUGE|NON FAIT)\s*(?:\|\s*(.*))?$", re.M)


def controle_du_pack(commande, dossier, porte):
    """Un controle propre au pack imprime une ou plusieurs lignes PORTE ; aucune = ROUGE."""
    code, s = lancer(commande, cwd=dossier)
    lignes = []
    for m in LIGNE_PACK.finditer(s):
        ident, lu, ecarts, verdict, detail = m.groups()
        l = juger(f"P{porte}.pack.{ident}", f"controle du pack : {ident}", int(lu), int(ecarts), detail or "")
        if verdict == NON_FAIT:
            l = non_fait(l.id, l.libelle, detail or "declare non fait par le controle")
        elif verdict == ROUGE and l.verdict == VERT:
            l.verdict, l.detail = ROUGE, (detail or "") + " (declare ROUGE par le controle)"
        lignes.append(l)
    if not lignes:
        lignes.append(juger(f"P{porte}.pack", f"controle du pack : {commande}", None, 0,
                            f"aucune ligne PORTE dans la sortie (code {code}) : {fin(s or '')}"))
    return lignes


def outil_present(nom):
    return shutil.which(nom) is not None
