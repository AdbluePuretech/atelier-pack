# -*- coding: utf-8 -*-
"""Une boucle de circularite est-elle discriminante, ou decorative ?

C'est la seule question qui compte sur une circularite, et le test d'isolement n'y
repond pas : un residu qui converge dit que la boucle **se ferme**, pas qu'elle
**deplace** quoi que ce soit.

  isolement   couper les autres, la mecanique tourne encore     -> elle EXISTE
  residuel    tout couper, 0 cellule auto-referente             -> elle est NOMMEE
  amplitude   la basculer deplace une valeur NOTEE              -> elle SERT

Ce module fait le troisieme. Il bascule chaque interrupteur, recalcule par le vrai
Excel, renote le classeur contre sa rubric, et compare.

  **Une boucle qui ne coute aucun point quand on la bascule est decorative.**

Elle gonfle le compte de circularites sans rien apporter au budget de
discrimination : le candidat qui l'ignore ne perd rien.

Pourquoi la rubric comme etalon
-------------------------------
On pourrait comparer toutes les valeurs du classeur. Ce serait plus large et moins
utile : ce qui compte n'est pas qu'une valeur bouge, c'est qu'une valeur **notee**
bouge au-dela de la tolerance que la rubric lui accorde. C'est la rubric qui definit
ce que « deplacer » veut dire.

Ce module ne sait rien du sujet. On lui donne un classeur, sa rubric, et il rend un
compte.
"""
import argparse
import json
import os
import re
import subprocess
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
for _c in (ICI, os.path.join(ICI, "..", "audit-modele"),
           os.path.join(ICI, "..", "..", "..", ".claude", "skills", "pack", "outils")):
    if os.path.isdir(_c) and _c not in sys.path:
        sys.path.insert(0, _c)

import rejouer  # noqa: E402

SCORE = re.compile(r"(\d+(?:[.,]\d+)?)\s*/\s*(\d+(?:[.,]\d+)?)\s*points", re.I)


def _noteur():
    # L'ordre compte. `noter_rubric.py` vit dans le meme dossier mais n'a PAS la
    # meme interface : le prendre par defaut faisait mourir le fils sur un
    # decodage, et l'erreur ressemblait a un probleme de rubric alors que c'etait
    # un probleme d'outil. On exige `noter.py`, qui seul accepte `--rubric`.
    for c in (os.environ.get("PACK_NOTEUR"),
              os.path.join(ICI, "noter.py"),
              os.path.join(ICI, "..", "..", "..", ".claude", "skills", "pack",
                           "outils", "noter.py"),
              os.path.join(ICI, "..", "excel", "noter.py")):
        if c and os.path.isfile(c):
            return os.path.abspath(c)
    raise FileNotFoundError(
        "Aucun noteur trouve. Poser PACK_NOTEUR sur le chemin de noter.py. "
        "Attention : noter_rubric.py n'a pas la meme interface et ne convient pas.")


def noter(classeur, rubric, timeout=900):
    """Rend (points, total) lus dans la sortie du noteur, ou (None, None)."""
    # Le noteur imprime des accents. Lance sans console, Windows le decode en
    # cp1252, le processus meurt sur l'encodage et rend un stdout VIDE - donc un
    # « aucun score » qui n'a rien a voir avec le classeur. Forcer l'UTF-8 des
    # deux cotes du tuyau.
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, _noteur(), classeur, "--rubric", rubric],
                       capture_output=True, timeout=timeout, env=env)
    sortie = (r.stdout or b"").decode("utf-8", "replace")
    erreur = (r.stderr or b"").decode("utf-8", "replace")
    m = None
    for m2 in SCORE.finditer(sortie):
        m = m2                       # le dernier score imprime est le total
    if not m:
        return None, None, (sortie[-300:] + chr(10) + erreur[-300:]).strip()
    f = lambda x: float(x.replace(",", "."))
    return f(m.group(1)), f(m.group(2)), ""


def interrupteurs(classeur, nommes=(), prefixes=()):
    """Les interrupteurs, reconnus a ce qu'ils VALENT - 0 ou 1 - pas a leur nom.

    Chercher un prefixe `br_` sur un classeur qui nomme ses breakers autrement rend
    zero, et zero se lit comme « tout va bien » alors que rien n'a ete bascule.
    """
    if nommes:
        return list(nommes)
    if prefixes:
        return rejouer.entrees_nommees(classeur, tuple(prefixes))
    valeurs = rejouer.entrees_nommees(classeur, None, valeurs=True)
    return [n for n, v in valeurs.items()
            if isinstance(v, (int, float)) and not isinstance(v, bool) and v in (0, 1)]


def mesurer(classeur, rubric, cibles, iterations=500, dossier=None):
    base_pts, total, err = noter(classeur, rubric)
    if base_pts is None:
        raise SystemExit("ARRET - le noteur n'a rendu aucun score.\n" + err)

    # LE GARDE-FOU. Si la reference ne vaut pas 100 %, le correcteur ne retrouve
    # pas ses criteres dans ce classeur : basculer un interrupteur ne fera alors
    # bouger AUCUN point, et chaque boucle ressortira « decorative ». C'est le
    # symetrique exact du faux vert - un faux verdict de mort. Mesure faite : sur
    # une golden dont la reference tombait a 65 / 152, deux boucles sur deux ont
    # ete declarees decoratives a tort.
    #
    # La doctrine l'exige de toute facon : la golden re-note 100 % de sa propre
    # rubric, sinon c'est la rubric qui est fausse. Sans cela, on ne mesure rien.
    if total and base_pts < total - 1e-9:
        raise SystemExit(
            "ETAPE NON FAITE - la reference vaut {:g} / {:g}, pas 100 %.".format(base_pts, total)
            + "\n  Ce n'est PAS un resultat favorable : un correcteur qui ne retrouve"
            + "\n  pas ses criteres ne verra bouger aucun point, et toutes les boucles"
            + "\n  ressortiraient decoratives."
            + "\n  Corriger la rubric (phase 4) avant de mesurer une amplitude.")

    resultats = []
    for nom in cibles:
        r = rejouer.Rejeu(classeur, dossier=dossier, etiquette=f"amp-{nom}")
        try:
            valeurs = rejouer.entrees_nommees(classeur, None, valeurs=True)
            avant = valeurs.get(nom)
            bascule = 0 if avant == 1 else 1
            r.poser({nom: bascule})
            rec = r.recalculer(iterations=iterations)
            if rec.get("code"):
                resultats.append((nom, avant, bascule, None, None, "recalcul echoue"))
                continue
            pts, _, err2 = noter(r.chemin, rubric)
            if pts is None:
                resultats.append((nom, avant, bascule, None, None, "notation echouee"))
                continue
            resultats.append((nom, avant, bascule, pts, base_pts - pts,
                              "repli openpyxl" if r.pose_degradee else ""))
        except Exception as e:
            resultats.append((nom, None, None, None, None, f"{type(e).__name__}: {e}"))
    return base_pts, total, resultats


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("classeur")
    ap.add_argument("--rubric", required=True)
    ap.add_argument("--breakers", default="",
                    help="interrupteurs a basculer, separes par des virgules. "
                         "VIDE = tous ceux qui valent 0 ou 1.")
    ap.add_argument("--prefixes", default="",
                    help="prefixes de plages nommees. Un prefixe maison ne vaut que "
                         "pour le classeur qui l'a inspire.")
    ap.add_argument("--iterations", type=int, default=500)
    ap.add_argument("--json")
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass

    cibles = interrupteurs(
        a.classeur,
        [x.strip() for x in a.breakers.split(",") if x.strip()],
        [x.strip() for x in a.prefixes.split(",") if x.strip()])

    print(f"AMPLITUDE DES BOUCLES - {a.classeur}\n")
    if not cibles:
        print("  ETAPE NON FAITE : aucun interrupteur trouve.")
        print("  Ce n'est PAS un resultat favorable - aucune boucle n'a ete basculee.")
        print("  Les nommer avec --breakers.")
        return 2

    base, total, res = mesurer(a.classeur, a.rubric, cibles, a.iterations)
    print(f"  reference : {base:g} / {total:g} points   sur {len(cibles)} interrupteur(s)\n")
    decoratives = []
    for nom, avant, apres, pts, cout, note in res:
        if pts is None:
            print(f"  [????] {nom:<28} {note}")
            continue
        mort = cout is not None and abs(cout) < 1e-9
        if mort:
            decoratives.append(nom)
        etat = "FAUT" if mort else "OK  "
        print(f"  [{etat}] {nom:<28} {avant} -> {apres} : {pts:g} / {total:g}"
              f"   cout {cout:+g} point(s)"
              + ("   <- DECORATIVE" if mort else "")
              + (f"   ({note})" if note else ""))
    print(f"\n  BOUCLES DECORATIVES : {len(decoratives)} / {len(cibles)}")
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump({"classeur": a.classeur, "reference": base, "total": total,
                       "resultats": [list(x) for x in res],
                       "decoratives": decoratives}, fh, ensure_ascii=False, indent=1)
    return 1 if decoratives else 0


if __name__ == "__main__":
    sys.exit(main())
