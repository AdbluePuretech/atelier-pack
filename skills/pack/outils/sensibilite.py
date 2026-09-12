# -*- coding: utf-8 -*-
"""Balayage de sensibilite : le modele tient-il ailleurs que sur le jeu livre.

Une convergence constatee sur les entrees livrees ne dit rien du voisinage. Un
point fixe peut etre stable ici et osciller un cran plus loin ; une division
peut ne devenir nulle que sous une hypothese basse ; une batterie de controles
peut ne fermer que par chance.

Le controle : flexer chaque hypothese, une a la fois, recalculer pour de vrai,
et exiger trois choses de chaque configuration - aucune cellule en erreur, la
batterie de controles toujours fermee, et le recalcul qui aboutit.

Chaque flexion coute un recalcul Excel complet. Le module ne cache jamais ce
qu'il n'a pas teste : il annonce le nombre d'hypotheses existantes, le nombre
testees, et lesquelles ont ete laissees de cote.

Usage :
    python sensibilite.py "Classeur.xlsx" --batterie "22. Checks!D80" [--limite 12]
    python sensibilite.py "Classeur.xlsx" --entrees i_CarveFloor,i_Fill --amplitude 0.3
"""
import argparse
import json
import os
import sys
import time

import noyau
import rejouer


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("classeur")
    ap.add_argument("--entrees", help="liste d'adresses separees par des virgules")
    ap.add_argument("--prefixes", default="",
                    help="prefixes des plages nommees a flexer ; VIDE = toutes. "
                         "Un prefixe maison ne vaut que pour le classeur qui l'a "
                         "inspire : ailleurs il ne trouve rien et l'etape se "
                         "presente verte sans avoir rien teste.")
    ap.add_argument("--amplitude", type=float, default=0.20,
                    help="flexion relative appliquee, en plus et en moins")
    ap.add_argument("--batterie", help="adresse du total de la batterie ; trouvee toute seule si omise")
    ap.add_argument("--limite", type=int, default=0,
                    help="nombre maximal d'hypotheses testees, 0 = toutes")
    ap.add_argument("--iterations", type=int, default=500)
    ap.add_argument("--json")
    a = ap.parse_args()

    if not a.batterie:
        a.batterie = noyau.trouver_batterie(noyau.Classeur(a.classeur))
        if a.batterie:
            print(f"batterie trouvee automatiquement : {a.batterie}")
        else:
            print("aucune batterie de controles reperee - on ne surveillera "
                  "que les cellules en erreur")

    if a.entrees:
        cibles = [x.strip() for x in a.entrees.split(",") if x.strip()]
        total_dispo = len(cibles)
    else:
        prefixes = tuple(p for p in a.prefixes.split(",") if p)
        cibles = rejouer.entrees_nommees(a.classeur, prefixes)
        total_dispo = len(cibles)

    ignorees = []
    if a.limite and len(cibles) > a.limite:
        ignorees = cibles[a.limite:]
        cibles = cibles[:a.limite]

    if not cibles:
        print(f"BALAYAGE DE SENSIBILITE - {os.path.basename(a.classeur)}")
        print("\nETAPE NON FAITE : aucune hypothese candidate trouvee.")
        print("  Ce n'est PAS un resultat favorable - rien n'a ete flexe.")
        print("  Nommer les hypotheses a flexer avec --entrees, ou elargir "
              "--prefixes.")
        if a.json:
            with open(a.json, "w", encoding="utf-8") as fh:
                json.dump({"classeur": a.classeur, "etape_faite": False,
                           "motif": "aucune hypothese candidate",
                           "hypotheses_candidates": 0, "hypotheses_testees": 0},
                          fh, ensure_ascii=False, indent=1)
        return 2

    print(f"BALAYAGE DE SENSIBILITE - {os.path.basename(a.classeur)}")
    print(f"hypotheses candidates      : {total_dispo}")
    print(f"hypotheses testees         : {len(cibles)}")
    if ignorees:
        print(f"NON TESTEES ({len(ignorees)}) : {', '.join(ignorees[:14])}"
              f"{' ...' if len(ignorees) > 14 else ''}")
    print(f"flexion                    : +/- {a.amplitude:.0%}")
    print(f"configurations a rejouer   : {len(cibles) * 2}\n")

    lignes = []
    ko = 0
    for i, cible in enumerate(cibles, 1):
        for sens, coef in (("haut", 1 + a.amplitude), ("bas", 1 - a.amplitude)):
            t0 = time.time()
            R = rejouer.Rejeu(a.classeur, etiquette=f"flex{i}{sens}")
            try:
                courante = R.relever([cible]).get(cible)
                if not isinstance(courante, (int, float)) or isinstance(courante, bool):
                    print(f"  [{cible}] non numerique ({courante!r}) - ignoree")
                    R.nettoyer()
                    break
                R.poser({cible: courante * coef})
                rec = R.recalculer(iterations=a.iterations)
                if rec["code"] != 0:
                    etat = {"saine": False, "erreurs": -1, "batterie": None,
                            "echec_recalcul": rec["erreur"][:200]}
                else:
                    etat = rejouer.sante(R, a.batterie)
                dt = time.time() - t0
                marque = "OK " if etat["saine"] else "KO "
                if not etat["saine"]:
                    ko += 1
                print(f"  [{marque}] {cible:<24} {sens:<5} "
                      f"{courante:>14.6g} -> {courante * coef:<14.6g} "
                      f"erreurs={etat['erreurs']:<4} "
                      f"batterie={etat.get('batterie')}  {dt:.0f}s")
                if not etat["saine"] and etat.get("echantillon_erreurs"):
                    print(f"          {etat['echantillon_erreurs'][:3]}")
                lignes.append({"entree": cible, "sens": sens, "valeur": courante,
                               "flexee": courante * coef, **etat,
                               "secondes": round(dt, 1)})
            finally:
                R.nettoyer()

    print()
    print("=" * 72)
    if ko == 0 and lignes:
        print(f"OK : {len(lignes)} configurations rejouees, aucune ne casse le modele.")
    elif not lignes:
        print("RIEN TESTE : aucune hypothese numerique trouvee.")
    else:
        print(f"DEFAUT : {ko} configurations sur {len(lignes)} cassent le modele.")
    if ignorees:
        print(f"  Rappel : {len(ignorees)} hypotheses n'ont PAS ete testees.")

    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump({"classeur": os.path.basename(a.classeur),
                       "amplitude": a.amplitude,
                       "hypotheses_candidates": total_dispo,
                       "hypotheses_testees": len(cibles),
                       "non_testees": ignorees,
                       "configurations_ko": ko,
                       "lignes": lignes}, fh, ensure_ascii=False, indent=2)
        print(f"\necrit : {a.json}")
    return 1 if ko else 0


if __name__ == "__main__":
    sys.exit(main())
