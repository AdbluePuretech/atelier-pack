# -*- coding: utf-8 -*-
"""La chaine d'audit complete, en une commande.

Neuf etapes, dix commandes, chacune avec ses options : c'est beaucoup de
frottement pour un protocole qu'on veut voir applique en entier. Ce pilote les
enchaine, ecrit tous les rapports dans un meme dossier, et finit par le
certificat qui les rassemble.

Il separe ce qui coute une seconde de ce qui coute une heure :

  - la chaine STATIQUE - gel, differences, circuits, integrite, identites,
    familles - ne demande que Python et tourne en une minute. C'est le defaut ;
  - la chaine DYNAMIQUE - convergence, sensibilite, commutateurs, mutation -
    passe par le vrai Excel, une copie et un recalcul a chaque configuration.
    Elle se demande avec `--avec-excel`, et il faut compter en dizaines de
    minutes.

Aucune etape n'est sautee en silence : celles qui n'ont pas tourne sont
inscrites au journal du certificat comme travail non fait, pas comme resultat
favorable.

Usage :
    python auditer_tout.py "Classeur.xlsx" --sortie dossier/
    python auditer_tout.py "Classeur.xlsx" --sortie dossier/ --avec-excel
    python auditer_tout.py "Classeur.xlsx" --sortie dossier/ --regenere "regen.xlsx"
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time

ICI = os.path.dirname(os.path.abspath(__file__))


def empreinte(chemin):
    h = hashlib.sha256()
    with open(chemin, "rb") as fh:
        for bloc in iter(lambda: fh.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def trouver_feuille_hypotheses(chemin):
    """La feuille ou vivent les hypotheses, reconnue a ce qu'elle PORTE.

    On la cherche d'abord a son nom, puis - si aucun nom ne parle - a l'endroit
    ou pointent les plages nommees mono-cellule. Un modele range ses hypotheses
    la ou il les nomme ; c'est un indice plus sur qu'un intitule de feuille, qui
    change d'un cabinet a l'autre.
    """
    try:
        from openpyxl import load_workbook
    except ImportError:
        return None
    try:
        wb = load_workbook(chemin, read_only=False, data_only=True)
    except Exception:
        return None
    try:
        for f in wb.sheetnames:
            n = f.lower()
            if "input" in n or "assumption" in n or "hypoth" in n:
                return f
        compte = {}
        for _, dn in list(wb.defined_names.items()):
            try:
                for sh, _ref in dn.destinations:
                    compte[sh] = compte.get(sh, 0) + 1
            except Exception:
                continue
        return max(compte, key=compte.get) if compte else None
    finally:
        wb.close()


def etape(numero, titre, module, args, sortie=None, silencieux=False):
    """Lance un module et rend (code, chemin du json)."""
    cmd = [sys.executable, os.path.join(ICI, module)] + args
    if sortie:
        cmd += ["--json", sortie]
    print(f"\n{'=' * 74}")
    print(f"ETAPE {numero} - {titre}")
    print(f"{'=' * 74}")
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True)
    texte = r.stdout or ""
    if silencieux:
        for ligne in texte.splitlines():
            if any(m in ligne for m in ("OK", "DEFAUT", "FAUT", "COUVERTURE",
                                        "BLOQUANT", "controles passes", "ecart")):
                print("  " + ligne.strip())
    else:
        print(texte.rstrip())
    if r.returncode not in (0, 1) and r.stderr:
        print(f"  ERREUR : {r.stderr.strip()[:500]}")
    print(f"  [{time.time() - t0:.0f}s]")
    return r.returncode, (sortie if sortie and os.path.exists(sortie) else None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("classeur")
    ap.add_argument("--sortie", default="audit", help="dossier des rapports")
    ap.add_argument("--bornes", default="",
                    help="fichier JSON de bornes de vraisemblance : "
                         "[{poste, min, max}]. Sans lui, l'etape 10 ne verifie "
                         "que les bornes universelles et le DIT.")
    ap.add_argument("--inputs", default="",
                    help="nom de la feuille d'hypotheses ; trouvee toute seule "
                         "si omise")
    ap.add_argument("--regenere", help="classeur regenere, pour l'etape 2")
    ap.add_argument("--avec-excel", action="store_true",
                    help="lance aussi convergence, sensibilite, commutateurs, mutation")
    ap.add_argument("--echantillon-mutation", type=int, default=45)
    ap.add_argument("--limite-sensibilite", type=int, default=12)
    ap.add_argument("--registre-familles",
                    help="registre de revue existant, pour le reprendre")
    a = ap.parse_args()

    os.makedirs(a.sortie, exist_ok=True)
    J = lambda n: os.path.join(a.sortie, n)

    # La feuille d'hypotheses sert a EXCLURE ses constantes du controle des
    # valeurs en dur. Un nom suppose qui ne correspond a rien ne fait pas
    # echouer l'etape : il compte les hypotheses comme autant de defauts, et
    # noie les vrais sous des milliers de faux. Sur une golden reelle, 1 802
    # hypotheses legitimes remontaient ainsi en « valeurs en dur critiques ».
    if not a.inputs:
        a.inputs = trouver_feuille_hypotheses(a.classeur) or "01. Input_Sheet"
        print(f"feuille d'hypotheses reperee : {a.inputs}")

    # --- etape 1 : geler la version ------------------------------------
    emp = empreinte(a.classeur)
    print(f"{'=' * 74}")
    print(f"ETAPE 1 - GELER LA VERSION")
    print(f"{'=' * 74}")
    print(f"  fichier   : {os.path.abspath(a.classeur)}")
    print(f"  taille    : {os.path.getsize(a.classeur):,} octets")
    print(f"  sha256    : {emp}")
    print("  A partir d'ici, ce fichier ne doit plus bouger. Si son empreinte")
    print("  change, l'audit repart de zero.")
    with open(J("00-gel.json"), "w", encoding="utf-8") as fh:
        json.dump({"chemin": os.path.abspath(a.classeur), "sha256": emp,
                   "octets": os.path.getsize(a.classeur)}, fh, indent=2)

    rapports = {}

    # --- etape 2 : regenerer et differencier -----------------------------
    if a.regenere:
        _, p = etape(2, "REGENERER ET DIFFERENCIER", "differencier.py",
                     [a.classeur, a.regenere], J("02-differences.json"))
        rapports["differences"] = p
    else:
        print(f"\n{'=' * 74}\nETAPE 2 - REGENERER ET DIFFERENCIER : NON FAITE")
        print(f"{'=' * 74}")
        print("  Aucun classeur regenere fourni. Si ce modele est produit par un")
        print("  script, le relancer vers un fichier temporaire et repasser avec")
        print("  --regenere : c'est la preuve la moins chere du protocole, et la")
        print("  seule qui dise si le fichier livre a ete retouche a la main.")

    # --- chaine statique ---------------------------------------------------
    _, p = etape(4, "CIRCUITS", "circuits.py", [a.classeur], J("04-circuits.json"),
                 silencieux=True)
    rapports["circuits"] = p
    _, p = etape(5, "INTEGRITE", "integrite.py",
                 [a.classeur] + (["--inputs", a.inputs] if a.inputs else []),
                 J("05-integrite.json"))
    rapports["integrite"] = p
    _, p = etape(6, "IDENTITES IMPOSEES", "identites.py", [a.classeur],
                 J("06-identites.json"))
    rapports["identites"] = p
    reg = a.registre_familles or J("07-familles.json")
    # Etape 10 : la seule qui ne demande pas si le classeur est juste avec
    # lui-meme, mais s'il dit quelque chose de POSSIBLE. Statique, une seconde.
    _, p = etape(10, "VRAISEMBLANCE", "vraisemblance.py",
                 [a.classeur] + (["--bornes", a.bornes] if getattr(a, "bornes", None) else []),
                 J("09-vraisemblance.json"))
    rapports["vraisemblance"] = p

    _, _ = etape(7, "FAMILLES DE FORMULES", "familles.py",
                 [a.classeur, "--registre", reg])
    rapports["familles"] = reg if os.path.exists(reg) else None

    # --- chaine dynamique ----------------------------------------------------
    if a.avec_excel:
        _, p = etape(3, "CONVERGENCE", "convergence.py", [a.classeur, "--rapide"],
                     J("03-convergence.json"))
        rapports["convergence"] = p
        _, p = etape(8, "SENSIBILITE", "sensibilite.py",
                     [a.classeur, "--limite", str(a.limite_sensibilite)],
                     J("08-sensibilite.json"))
        rapports["sensibilite"] = p
        _, p = etape(8, "COMMUTATEURS", "commutateurs.py", [a.classeur],
                     J("08-commutateurs.json"))
        rapports["commutateurs"] = p
        _, p = etape(9, "MUTATION", "mutation.py",
                     [a.classeur, "--echantillon", str(a.echantillon_mutation)],
                     J("09-mutation.json"), silencieux=True)
        rapports["mutation"] = p
    else:
        print(f"\n{'=' * 74}")
        print("ETAPES 3, 8 ET 9 - CONVERGENCE, SENSIBILITE, COMMUTATEURS, MUTATION")
        print("NON FAITES : elles demandent Excel. Relancer avec --avec-excel.")
        print(f"{'=' * 74}")

    # --- le certificat --------------------------------------------------------
    args = [a.classeur, "--inputs", a.inputs]
    for cle, option in (("familles", "--familles"), ("convergence", "--convergence"),
                        ("sensibilite", "--sensibilite"),
                        ("commutateurs", "--commutateurs"),
                        ("identites", "--identites"), ("mutation", "--mutation"),
                        ("vraisemblance", "--vraisemblance"),
                        ("differences", "--differences")):
        if rapports.get(cle):
            args += [option, rapports[cle]]
    code, _ = etape("finale", "CERTIFICAT", "certifier.py", args, J("10-certificat.json"))

    print(f"\nrapports ecrits dans : {os.path.abspath(a.sortie)}")
    for f in sorted(os.listdir(a.sortie)):
        print(f"    {f}")
    return code


if __name__ == "__main__":
    sys.exit(main())
