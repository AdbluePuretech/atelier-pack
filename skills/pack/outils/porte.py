# -*- coding: utf-8 -*-
"""Les portes de la skill pack : une phase ne se termine que quand sa porte s'ouvre.

    python porte.py init <dossier>
    python porte.py <1|2|3|4|5|juicing> [pack.json]
    python porte.py 2 --iteration <k> [pack.json]
    python porte.py relais <porte> --decision valide|modifie|refuse --note "..." [--iteration k] [pack.json]
    python porte.py etat [pack.json]

Chaque phase decrivait sa sortie en prose, et rien n'obligeait a lancer les controles
qui la prouvent. Une porte les lance tous, rend une ligne par controle avec son compte,
et reste FERMEE tant qu'une ligne n'est pas VERTE. Un controle qui n'a rien lu n'est
jamais vert.

Le journal `portes.json`, a cote du manifeste, garde chaque porte franchie avec
l'empreinte de chaque fichier lu, et chaque relais humain. Il ne s'ecrit qu'en ajout.
Une porte dont un fichier a change depuis est PERIMEE, et toutes les suivantes avec
elle : une golden retouchee apres la certification ne garde pas son certificat.

Le protocole : references/portes.md.
"""
import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import porte_conception as pc  # noqa: E402
import porte_controles as PC  # noqa: E402
from porte_lecteurs import NON_FAIT, VERT  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ORDRE_PORTES = ["1", "2", "3", "4", "5", "juicing"]
DECISIONS = ("valide", "modifie", "refuse")


def rang(porte, iteration):
    """L'ordre dans la chaine : 1 < 2.it0 < 2.it1 < ... < 2 finale < 3 < 4 < 5 < juicing."""
    base = ORDRE_PORTES.index(porte)
    if porte == "2":
        return (base, iteration if iteration is not None else 10 ** 6)
    return (base, 0)


def nom_porte(porte, iteration):
    return f"porte {porte}" + (f", iteration {iteration}" if iteration is not None else "")


class Journal:
    def __init__(self, M):
        self.M = M
        self.chemin = M.dossier / "portes.json"
        if self.chemin.exists():
            self.d = json.loads(self.chemin.read_text(encoding="utf-8"))
        else:
            self.d = {"pack": M.nom, "evenements": []}

    @property
    def evenements(self):
        return self.d["evenements"]

    def ajouter(self, evt):
        self.evenements.append(evt)
        self.chemin.write_text(json.dumps(self.d, ensure_ascii=False, indent=1), encoding="utf-8")

    def derniere_porte(self, porte, iteration):
        for i in range(len(self.evenements) - 1, -1, -1):
            e = self.evenements[i]
            if e["type"] == "porte" and e["porte"] == porte and e.get("iteration") == iteration:
                return i, e
        return None, None

    def dernier_relais(self, porte, iteration):
        i, _ = self.derniere_porte(porte, iteration)
        for e in reversed(self.evenements[(i or 0):]):
            if e["type"] == "relais" and e["porte"] == porte and e.get("iteration") == iteration:
                return e["decision"]
        return None

    def relais_le_plus_recent(self, porte, iteration):
        """Le dernier relais de cette porte, meme si la porte a ete repassee depuis :
        un `modifie` reste en vigueur jusqu'au relais suivant."""
        for e in reversed(self.evenements):
            if e["type"] == "relais" and e["porte"] == porte and e.get("iteration") == iteration:
                return e["decision"]
        return None

    def fichiers_changes(self, evt):
        changes = []
        for cle, h in (evt.get("empreintes") or {}).items():
            rel = cle.split("#", 1)[0]
            p = Path(rel) if Path(rel).is_absolute() else self.M.dossier / rel
            if not p.exists():
                changes.append(f"{rel} (disparu)")
            elif empreinte_de(p, cle) != h:
                changes.append(rel)
        return changes

    def etat(self):
        """Pour chaque (porte, iteration) passee : derniere ouverture, peremption, relais."""
        cles = sorted({(e["porte"], e.get("iteration")) for e in self.evenements if e["type"] == "porte"},
                      key=lambda k: rang(*k))
        lignes, perimee_avant = [], None
        for porte, it in cles:
            i, e = self.derniere_porte(porte, it)
            changes = self.fichiers_changes(e) if e["ouverte"] else []
            perimee = bool(changes) or (perimee_avant is not None and e["ouverte"])
            raison = (f"{', '.join(changes)} modifie(s) depuis le {e['date'][:16]}" if changes
                      else f"{perimee_avant} perimee" if perimee else "")
            if perimee and perimee_avant is None:
                perimee_avant = nom_porte(porte, it)
            lignes.append(dict(porte=porte, iteration=it, ouverte=e["ouverte"], date=e["date"], perimee=perimee,
                               raison=raison, relais=self.dernier_relais(porte, it)))
        return lignes

    def valide(self, porte, iteration):
        """Ouverte, a jour, et relayee `valide` apres son ouverture."""
        for l in self.etat():
            if l["porte"] == porte and l["iteration"] == iteration:
                return l["ouverte"] and not l["perimee"] and l["relais"] == "valide", l
        return False, None


def prerequis(J, porte, iteration, n_mecaniques):
    """Ce qui doit etre ouvert et valide avant cette porte, ou None."""
    if porte == "1":
        return None
    if porte == "2" and iteration is not None:
        avant = ("1", None) if iteration == 0 else ("2", iteration - 1)
    elif porte == "2":
        avant = ("1", None)
    else:
        precedente = ORDRE_PORTES[ORDRE_PORTES.index(porte) - 1]
        avant = (precedente, None)
    ok, l = J.valide(*avant)
    if ok:
        return None
    qui = nom_porte(*avant)
    if l is None:
        return f"{qui} jamais passee"
    if not l["ouverte"]:
        return f"{qui} fermee"
    if l["perimee"]:
        return f"{qui} perimee : {l['raison']}"
    return f"{qui} ouverte, mais sans relais valide (dernier relais : {l['relais'] or 'aucun'})"


def iterations_validees(J):
    return {l["iteration"] for l in J.etat()
            if l["porte"] == "2" and l["iteration"] is not None and l["ouverte"] and not l["perimee"] and l["relais"] == "valide"}


SANS_CELLULES = "#sans-cellules"


def empreinte_de(p, cle):
    """Les ancrages vus par la porte 1 : sans leurs cellules, que la phase 2 remplit par nature."""
    if cle.endswith(SANS_CELLULES):
        ancrages = [{k: v for k, v in a.items() if k != "cellule"} for a in pc.lire_ancrages(p)]
        return PC.hashlib.sha256(json.dumps(ancrages, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    return PC.empreinte(p)


def relatif(M, p):
    try:
        return str(Path(p).resolve().relative_to(M.dossier))
    except ValueError:
        return str(Path(p).resolve())


def empreintes(M, lignes, porte, iteration, copie=None):
    """Ce qui rend la porte perimee s'il change.

    Deux exceptions, sans lesquelles la chaine se bloquerait d'elle-meme : une iteration
    ne suit pas la golden vivante (l'iteration suivante la regenere, c'est son travail),
    elle suit sa copie figee ; la porte 1 suit les ancrages sans leurs cellules.
    """
    gold = M.chemin_de("golden")
    anc = M.chemin_de("ancrages")
    out = {}
    for l in lignes:
        for f in l.fichiers:
            p = Path(f)
            if not (p.exists() and p.is_file()):
                continue
            if iteration is not None and gold and p.resolve() == gold.resolve():
                continue
            cle = relatif(M, p)
            if (porte == "1" or iteration is not None) and anc and p.resolve() == anc.resolve():
                cle += SANS_CELLULES
            out[cle] = empreinte_de(p, cle)
    if copie is not None:
        out[relatif(M, copie)] = PC.empreinte(copie)
    return out


def afficher(lignes, titre):
    print(titre)
    largeur = max([len(l.id) for l in lignes] + [10])
    for l in lignes:
        print(f"  {l.verdict:<8} {l.id:<{largeur}}  lu {l.lu:>8}  ecarts {l.ecarts:>4}  {l.libelle} : {l.detail}")


def lancer_porte(M, porte, iteration):
    J = Journal(M)
    n = len(pc.Conception(M.chemin_de("conception")).ids()) if M.chemin_de("conception") and M.chemin_de("conception").exists() else 0
    if iteration is not None and porte != "2":
        sys.exit("REFUS : --iteration ne vaut que pour la porte 2")
    if iteration is not None and not 0 <= iteration <= n:
        sys.exit(f"REFUS : iteration {iteration} hors de 0 a {n} (la conception declare {n} mecanique(s))")
    manque = prerequis(J, porte, iteration, n)
    if manque:
        print(f"REFUS : {nom_porte(porte, iteration)} demande que la precedente soit ouverte et validee - {manque}")
        return 2
    if porte == "2":
        lignes = PC.porte_2(M, J, iteration, iterations_validees(J))
    else:
        lignes = PC.PORTES[porte](M, J)
    fermees = [l for l in lignes if l.verdict != VERT]
    ouverte = bool(lignes) and not fermees
    afficher(lignes, f"{nom_porte(porte, iteration).upper()} - {M.nom}")
    copie = None
    if ouverte and iteration is not None:
        copie = M.dossier / "build" / "iterations" / f"GS it{iteration:02d} - {M.nom}.xlsx"
        copie.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(M.chemin_de("golden"), copie)
    evt = dict(type="porte", porte=porte, iteration=iteration, date=datetime.now().isoformat(timespec="seconds"),
               ouverte=ouverte, lignes=[l.dict() for l in lignes], empreintes=empreintes(M, lignes, porte, iteration, copie))
    if copie is not None:
        evt["copie"] = relatif(M, copie)
    J.ajouter(evt)
    print()
    if ouverte:
        print(f"{nom_porte(porte, iteration).upper()} : OUVERTE ({len(lignes)} lignes vertes)")
        if iteration is not None:
            print(f"  copie de l'iteration : {evt['copie']}")
        print(f"  relais : presenter le tableau au owner, proposer ce qui vaut un coup d'oeil, puis "
              f"porte.py relais {porte}" + (f" --iteration {iteration}" if iteration is not None else "")
              + " --decision valide|modifie|refuse --note \"...\"")
        return 0
    nf = sum(1 for l in fermees if l.verdict == NON_FAIT)
    print(f"{nom_porte(porte, iteration).upper()} : FERMEE ({len(fermees)} ligne(s) : {len(fermees) - nf} rouge(s), {nf} non faite(s))")
    return 1


def relais(M, porte, iteration, decision, note):
    J = Journal(M)
    if decision not in DECISIONS:
        sys.exit(f"REFUS : decision {decision!r}, attendu {' | '.join(DECISIONS)}")
    etat = {(l["porte"], l["iteration"]): l for l in J.etat()}
    l = etat.get((porte, iteration))
    if l is None or not l["ouverte"]:
        print(f"REFUS : {nom_porte(porte, iteration)} n'est pas ouverte ; un relais ne s'inscrit que sur une porte ouverte")
        return 2
    if l["perimee"]:
        print(f"REFUS : {nom_porte(porte, iteration)} perimee ({l['raison']}) ; la repasser avant le relais")
        return 2
    J.ajouter(dict(type="relais", porte=porte, iteration=iteration, decision=decision, note=note,
                   date=datetime.now().isoformat(timespec="seconds")))
    suite = {"valide": "la suite est ouverte",
             "modifie": "relire chaque modification du owner, la reporter ou l'abandonner sur sa decision, puis repasser la porte",
             "refuse": "retour dans la phase, avec la note du owner"}[decision]
    print(f"RELAIS {decision.upper()} inscrit pour {nom_porte(porte, iteration)} : {suite}")
    return 0


def afficher_etat(M):
    J = Journal(M)
    lignes = J.etat()
    print(f"ETAT DES PORTES - {M.nom}")
    if not lignes:
        print("  aucune porte passee : commencer par la porte 1")
        return 0
    for l in lignes:
        statut = "PERIMEE" if l["perimee"] else ("OUVERTE" if l["ouverte"] else "FERMEE")
        print(f"  {nom_porte(l['porte'], l['iteration']):<24} {statut:<8} {l['date'][:16]}  relais : {l['relais'] or '-':<8} {l['raison']}")
    return 0


MANIFESTE_VIDE = {
    "nom": "<Nom>", "niveau": "L1",
    "graine": "graine.md", "conception": "CONCEPTION.md", "ancrages": "ancrages.json",
    "lot": "<dossier des packs deja livres du lot>", "premier_du_lot": False,
    "golden": "build/GoldenSolution - <Nom>.xlsx", "input_sheet": "build/InputSheet - <Nom>.xlsx",
    "certificat": "build/audit/certificat.json",
    "prompt": "build/Prompt - <Nom>.docx", "rubric": "build/Rubric - <Nom>.docx", "rubric_source": "build/rubric.txt",
    "ai_output": "<classeur de l'AI Output>", "score_ai_output": "<feuille de score claude.ai, .json>",
    "cible_score": [0, 45], "paquet": [],
    "juicing": {"rubric": "", "rubric_source": "", "score_adverse": "", "note_equite": ""},
    "controles_du_pack": {},
}


def init(dossier):
    d = Path(dossier)
    d.mkdir(parents=True, exist_ok=True)
    ecrits, gardes = [], []
    for nom, contenu in (("pack.json", json.dumps(MANIFESTE_VIDE, ensure_ascii=False, indent=2)),
                         ("CONCEPTION.md", pc.PLAN_VIDE.format(nom=d.name)),
                         ("ancrages.json", "[]\n")):
        p = d / nom
        if p.exists():
            gardes.append(nom)
            continue
        p.write_text(contenu, encoding="utf-8")
        ecrits.append(nom)
    print(f"INIT - {d}")
    print(f"  ecrits : {', '.join(ecrits) or 'aucun'}")
    print(f"  deja presents, non touches : {', '.join(gardes) or 'aucun'}")
    print("  a faire : remplir pack.json (nom, niveau, lot), deposer la graine, ecrire la conception, puis porte.py 1")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", help="init | 1 | 2 | 3 | 4 | 5 | juicing | relais | etat")
    ap.add_argument("reste", nargs="*", help="init : le dossier ; relais : la porte, puis pack.json ; sinon pack.json")
    ap.add_argument("--iteration", type=int)
    ap.add_argument("--decision")
    ap.add_argument("--note", default="")
    a = ap.parse_intermixed_args()
    if a.action == "init":
        if not a.reste:
            ap.error("init demande un dossier")
        return init(a.reste[0])
    if a.action == "relais":
        if not a.reste:
            ap.error("relais demande une porte")
        porte, reste = a.reste[0], a.reste[1:]
    else:
        porte, reste = a.action, a.reste
    try:
        M = PC.Manifeste(reste[0] if reste else "pack.json")
    except PC.ManifesteInvalide as e:
        print(f"ARRET : {e}")
        return 2
    if a.action == "etat":
        return afficher_etat(M)
    if porte not in ORDRE_PORTES:
        ap.error(f"porte inconnue : {porte}")
    if a.action == "relais":
        if not a.decision:
            ap.error("relais demande --decision valide|modifie|refuse")
        return relais(M, porte, a.iteration, a.decision, a.note)
    return lancer_porte(M, porte, a.iteration)


if __name__ == "__main__":
    sys.exit(main())
