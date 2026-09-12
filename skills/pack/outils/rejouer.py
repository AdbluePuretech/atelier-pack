# -*- coding: utf-8 -*-
"""Rejouer un classeur : ecrire des entrees, recalculer pour de vrai, relever
des sorties.

Machinerie partagee par les trois controles dynamiques - convergence,
sensibilite, commutateurs. Ils font tous la meme chose : poser des entrees,
recalculer, relever des sorties, comparer. Seul change ce qu'on pose et ce qu'on
attend.

Deux regles non negociables :

  - on travaille TOUJOURS sur une copie. Le classeur audite est gele (etape 1
    du protocole) et un audit qui modifie sa cible ne prouve rien ;
  - le recalcul passe par le VRAI Excel. openpyxl ne calcule pas : il relit un
    cache. Rejouer un classeur circulaire sans Excel ne dit rien du tout.
"""
import os
import re
import shutil
import subprocess
import tempfile

import openpyxl
from openpyxl.utils import get_column_letter, column_index_from_string

def _recalculateur():
    """Le script de recalcul, resolu au premier chemin qui existe vraiment.

    Trois raisons a cette prudence plutot qu'un chemin en dur :

    - la skill est auto-portante et porte son `recalculer.ps1` dans `outils/`,
      alors que le depot le range dans `systeme/scripts/excel/`. Un chemin fige
      marchait d'un cote et pointait dans le vide de l'autre -- et un chemin
      mort ne se voyait pas : chaque etape dynamique rendait simplement
      "recalcul : echec", donc aucune certification, sans dire pourquoi ;
    - un classeur circulaire genere par openpyxl a besoin d'un recalcul qui
      AMORCE la boucle avant de la fermer, sinon Excel rend #VALUE! partout.
      Un pack peut donc fournir le sien.

    Priorite : la variable d'environnement PACK_RECALCUL, puis le voisin
    immediat, puis l'emplacement du depot.
    """
    ici = os.path.dirname(os.path.abspath(__file__))
    candidats = [os.environ.get("PACK_RECALCUL"),
                 os.path.join(ici, "recalculer.ps1"),
                 os.path.join(ici, "..", "excel", "recalculer.ps1")]
    for c in candidats:
        if c and os.path.isfile(c):
            return os.path.abspath(c)
    raise FileNotFoundError(
        "Aucun script de recalcul trouve. Poser PACK_RECALCUL sur le chemin "
        "voulu, ou deposer recalculer.ps1 a cote de rejouer.py.")


RECALC = _recalculateur()


def _poseur():
    """Le script d'ecriture par Excel, resolu comme le recalculateur.

    Rendu None plutot que leve : sans Excel, `poser()` retombe sur l'ecriture
    openpyxl, degradee mais fonctionnelle sur un petit classeur.
    """
    ici = os.path.dirname(os.path.abspath(__file__))
    for c in (os.environ.get("PACK_POSER"),
              os.path.join(ici, "poser.ps1"),
              os.path.join(ici, "..", "excel", "poser.ps1")):
        if c and os.path.isfile(c):
            return os.path.abspath(c)
    return None


POSER = _poseur()

_A1 = re.compile(r"^(?:'([^']+)'|([^!]+))!\$?([A-Z]{1,3})\$?([0-9]+)$")


class Rejeu:
    """Une copie de travail du classeur, qu'on peut ecrire et recalculer."""

    def __init__(self, chemin, dossier=None, etiquette="rejeu"):
        self.origine = chemin
        base = os.path.basename(chemin)
        dossier = dossier or tempfile.mkdtemp(prefix="audit-modele-")
        os.makedirs(dossier, exist_ok=True)
        self.chemin = os.path.join(dossier, f"{etiquette} - {base}")
        shutil.copy2(chemin, self.chemin)
        self.dossier = dossier
        self.pose_degradee = False   # vrai si une ecriture est passee par openpyxl
        self.derniere_pose = ""

    # --- adressage ------------------------------------------------------

    def _resoudre(self, wb, adresse):
        """Accepte 'Feuille'!B12, Feuille!B12, ou une plage nommee mono-cellule."""
        m = _A1.match(adresse)
        if m:
            feuille = m.group(1) or m.group(2)
            return feuille, int(m.group(4)), column_index_from_string(m.group(3))
        try:
            dn = wb.defined_names[adresse]
        except (KeyError, TypeError):
            raise KeyError(f"adresse ou plage nommee inconnue : {adresse}")
        for feuille, ref in dn.destinations:
            ref = ref.replace("$", "").split(":")[0]
            mm = re.match(r"([A-Z]{1,3})([0-9]+)", ref)
            if mm:
                return feuille, int(mm.group(2)), column_index_from_string(mm.group(1))
        raise KeyError(f"plage nommee non resolue : {adresse}")

    # --- ecriture --------------------------------------------------------

    def poser(self, entrees):
        """entrees : {adresse: valeur}. Ecrit et enregistre, sans calculer.

        L'ecriture passe par le VRAI Excel, jamais par un enregistrement
        openpyxl. La raison est mesuree, pas theorique : un aller-retour
        `load_workbook` / `save` sur un classeur reel l'a fait tomber de 883 Ko
        a 447 Ko, mettant a plat 17 366 formules partagees et perdant
        `sharedStrings`, `calcChain` et les metadonnees. Le recalcul echouait
        ensuite, et l'echec etait impute au classeur audite alors qu'il venait
        de l'outil.

        openpyxl reste utilise pour RESOUDRE les adresses et relever la valeur
        d'avant - une lecture ne reecrit rien.
        """
        wb = openpyxl.load_workbook(self.chemin, data_only=False)
        poses, a_ecrire = {}, []
        try:
            for adresse, valeur in entrees.items():
                feuille, ligne, col = self._resoudre(wb, adresse)
                cellule = f"{feuille}!{get_column_letter(col)}{ligne}"
                poses[adresse] = {
                    "avant": wb[feuille].cell(row=ligne, column=col).value,
                    "apres": valeur, "cellule": cellule}
                a_ecrire.append((cellule, valeur))
        finally:
            wb.close()

        if not a_ecrire:
            return poses
        if not self._poser_par_excel(a_ecrire):
            self._poser_par_openpyxl(a_ecrire)
        return poses

    def _poser_par_excel(self, a_ecrire):
        """Vrai si Excel a pose et enregistre. Faux : l'appelant se rabat."""
        if not POSER:
            return False
        arg = ";".join(f"{cellule}={valeur}" for cellule, valeur in a_ecrire)
        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
               "-File", POSER, "-Chemin", os.path.abspath(self.chemin),
               "-Entrees", arg]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        except Exception:
            return False
        self.derniere_pose = (r.stdout or "")[-2000:]
        return r.returncode == 0

    def _poser_par_openpyxl(self, a_ecrire):
        """Repli sans Excel. Degrade : il reecrit tout le conteneur.

        Conserve parce qu'un petit classeur le supporte sans dommage et qu'une
        machine sans Office doit pouvoir faire tourner quelque chose. Il laisse
        une trace, pour qu'un resultat obtenu par ce chemin ne se lise pas
        comme un resultat obtenu par l'autre.
        """
        self.pose_degradee = True
        wb = openpyxl.load_workbook(self.chemin, data_only=False)
        try:
            for cellule, valeur in a_ecrire:
                feuille, ligne, col = self._resoudre(wb, cellule)
                wb[feuille].cell(row=ligne, column=col, value=valeur)
            wb.save(self.chemin)
        finally:
            wb.close()

    # --- calcul ----------------------------------------------------------

    def recalculer(self, iterations=500, ecart=1e-06, passes=3, timeout=1800):
        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
               "-File", os.path.abspath(RECALC),
               "-Chemin", os.path.abspath(self.chemin),
               "-Iterations", str(iterations),
               "-Ecart", str(ecart),
               "-Passes", str(passes)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {"code": r.returncode, "sortie": (r.stdout or "")[-3000:],
                "erreur": (r.stderr or "")[-1500:]}

    # --- lecture ----------------------------------------------------------

    def relever(self, adresses):
        wb = openpyxl.load_workbook(self.chemin, data_only=True)
        out = {}
        for adresse in adresses:
            try:
                feuille, ligne, col = self._resoudre(wb, adresse)
                out[adresse] = wb[feuille].cell(row=ligne, column=col).value
            except KeyError:
                out[adresse] = "<adresse inconnue>"
        wb.close()
        return out

    def erreurs(self):
        """Les cellules en erreur apres recalcul - le premier signe qu'un jeu
        d'entrees casse le modele."""
        wb = openpyxl.load_workbook(self.chemin, read_only=True, data_only=True)
        codes = ("#REF!", "#VALUE!", "#DIV/0!", "#N/A", "#NAME?",
                 "#NULL!", "#NUM!", "#SPILL!", "#CALC!")
        out = []
        for ws in wb.worksheets:
            for row in ws.iter_rows(values_only=False):
                for c in row:
                    if isinstance(c.value, str) and c.value in codes:
                        out.append(f"{ws.title}!{c.coordinate} = {c.value}")
                        if len(out) > 200:
                            wb.close()
                            return out
        wb.close()
        return out

    def nettoyer(self):
        try:
            shutil.rmtree(self.dossier, ignore_errors=True)
        except Exception:
            pass


def entrees_nommees(chemin, prefixes=None, valeurs=False):
    """Les plages nommees mono-cellule : les hypotheses du classeur.

    Par defaut AUCUN filtre de prefixe. Se caler sur une convention de nommage
    - i_, sw_, b_ - ne marche que sur le classeur qui l'a inspiree : un autre
    modele nommera `Brk_Master` ou `Cost_Infl` et l'outil ne trouvera rien,
    en annoncant zero hypothese au lieu d'annoncer qu'il n'a pas su chercher.

    valeurs=True retourne {nom: valeur} au lieu de la liste des noms, ce qui
    permet de reconnaitre un COMMUTATEUR a ce qu'il vaut - 0 ou 1 - plutot
    qu'a la facon dont il s'appelle.
    """
    wb = openpyxl.load_workbook(chemin, read_only=False, data_only=True)
    out = {}
    try:
        items = list(wb.defined_names.items())
    except AttributeError:
        items = [(d.name, d) for d in wb.defined_names.definedName]
    for nom, dn in items:
        if prefixes and not nom.startswith(tuple(prefixes)):
            continue
        try:
            dests = list(dn.destinations)
        except Exception:
            continue
        if len(dests) != 1:
            continue
        feuille, ref = dests[0]
        if ":" in ref:            # une plage, pas une hypothese unitaire
            continue
        v = None
        if valeurs:
            try:
                r = ref.replace("$", "")
                m = re.match(r"([A-Z]{1,3})([0-9]+)", r)
                v = wb[feuille].cell(row=int(m.group(2)),
                                     column=column_index_from_string(m.group(1))).value
            except Exception:
                v = None
        out[nom] = v
    wb.close()
    return out if valeurs else sorted(out)


def commutateurs_probables(chemin):
    """Les hypotheses qui valent 0 ou 1 : ce sont les commutateurs, quelle que
    soit la facon dont le classeur les nomme."""
    vals = entrees_nommees(chemin, valeurs=True)
    return sorted(n for n, v in vals.items()
                  if isinstance(v, (int, float)) and not isinstance(v, bool)
                  and v in (0, 1))


def sante(R, batterie=None, tolerance_batterie=1e-06):
    """L'etat d'un classeur apres recalcul : erreurs, et batterie de controles.

    Une configuration est saine si elle ne produit aucune erreur ET si la
    batterie de controles du modele ferme toujours a zero. Une batterie qui
    s'ouvre sous une hypothese flexee signale que le modele ne tient que sur
    le jeu livre.
    """
    err = R.erreurs()
    etat = {"erreurs": len(err), "echantillon_erreurs": err[:5], "batterie": None}
    if batterie:
        v = R.relever([batterie]).get(batterie)
        etat["batterie"] = v
        etat["batterie_fermee"] = isinstance(v, (int, float)) and abs(v) <= tolerance_batterie
    etat["saine"] = (etat["erreurs"] == 0) and (etat.get("batterie_fermee", True))
    return etat


def ecart_relatif(a, b):
    """Ecart relatif entre deux relevés, robuste aux zeros et aux non-nombres."""
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        d = abs(a - b)
        base = max(abs(a), abs(b))
        return d / base if base > 1e-12 else d
    return 0.0 if a == b else float("inf")


def comparer(reference, essai, tolerance=1e-09):
    """Retourne la liste des adresses qui bougent au-dela de la tolerance."""
    bougent = []
    for adresse, v in reference.items():
        w = essai.get(adresse)
        e = ecart_relatif(v, w)
        if e > tolerance:
            bougent.append({"adresse": adresse, "reference": v, "essai": w,
                            "ecart_relatif": e})
    bougent.sort(key=lambda x: -x["ecart_relatif"] if x["ecart_relatif"] != float("inf") else 0)
    return bougent
