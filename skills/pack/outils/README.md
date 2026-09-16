---
title: "Les outils portables de fabrication d'un pack"
description: "Les verificateurs qui ne savent rien du sujet et marchent sur n'importe quel pack ou n'importe quel classeur."
type: "reference"
status: "actif"
---

# Les outils

Le partage qui structure tout : **les outils qui verifient sont portables, les
scripts qui construisent ne le sont pas.**

Ceux-ci ne savent rien du sujet. On leur donne un chemin, ils rendent un compte. Les
scripts qui batissent — ancrages, calibrateur, generateur — s'ecrivent pour chaque
pack, parce que le metier change a chaque fois. Voir [phase 2](../references/02-batir.md).

## Recalculer

| Outil | Ce qu'il fait |
|-------|---------------|
| `recalculer.ps1` | Excel recalcule et **ecrit le cache**. Indispensable apres toute generation. |

```
powershell -File recalculer.ps1 -Chemin "<classeur>" -Iterations 200 -Ecart 1e-08
```

Rend le nombre d'erreurs. Une seule invalide le build.

## Decrire et auditer

| Outil | Ce qu'il fait |
|-------|---------------|
| `bilan_classeur.py` | decrit un classeur sans rien savoir de la golden : feuilles, blocs, volumes |
| `gs_audit.py` | les defauts qu'un recalcul ne montre jamais : liens externes, feuilles masquees, controles tautologiques |
| `vraisemblance.py` | l'etape 10 : les sorties sont-elles economiquement **possibles** ? Bornes universelles, plus les bornes que l'auditeur declare |
| `traces_ia.py` | ce qui trahit une fabrication automatique : puces pleines, phrases explicatives dans les libelles, encre bleue, groupement laisse, onglets creux |
| `compter_boucles.py` | les mecaniques circulaires, par **test d'isolement** et **cycle residuel** |
| `amplitude_boucles.py` | le troisieme test : basculer chaque interrupteur et mesurer **ce que la boucle coute en points de rubric**. Zero point = boucle decorative |
| `mise_en_page.py` | la **signature de presentation** d'un classeur — grille, architecture, police, teinte, encres, formats — ses **ecarts aux standards IB**, et, avec `--contre <dossier>`, sa distance a chaque pack deja livre du lot : 3 axes de structure et 2 d'habillage au moins |
| `niveau.py` | le **niveau lu dans les onglets**, pas a leur nombre : logiques distinctes (formules R1C1, une ligne recopiee compte une fois), logiques par onglet, sophistication, hypotheses consommees, et le niveau tenu sur le fichier contre les planchers de la grille |

### Calibration du niveau

Mesure du 14/09/2026 par `niveau.py`, sur les sept goldens de l'environnement 9 et six
packs du lot RX. Les planchers de la grille (L1 : 500 logiques, 20 par onglet, 150
hypotheses ; L2 : 1 500, 40, 400 ; L3 : 3 000, 80, 1 000 ; sophistication 45 % partout)
sont poses au-dessus du corpus : c'est une exigence, pas une description.

| Golden | Onglets de calcul | Formules | Liens purs | Logiques | Par onglet | Sophistication | Hypotheses | Score connu | Tenu sur le fichier |
|--------|------:|-------:|------:|------:|-----:|-----:|------:|------|------|
| Danube | 13 | 6 275 | 1 924 | 119 | 10 | 47,9 % | 218 | 0,82-0,92 | aucun |
| Rigel | 23 | 13 034 | 8 249 | 164 | 8 | 56,7 % | 532 | 0,92 | aucun |
| Valhalla | 16 | 14 774 | 3 492 | 227 | 12,5 | 41,4 % | 106 | 0,82-0,92 | aucun |
| Yards | 20 | 19 434 | 6 882 | 293 | 15 | 42,3 % | 464 | 0,82-0,92 | aucun |
| Cardinal | 65 | 101 389 | 1 459 | 348 | 7 | 70,4 % | 264 | **0,31** | aucun |
| Ashford | 50 | 150 455 | 44 465 | 1 145 | 9 | 79,7 % | 1 505 | - | aucun |
| Icare | 30 | 30 272 | 8 149 | 2 100 | 7 | 95,5 % | 1 151 | 0,82-0,92 | aucun |
| Cobalt | 21 | 9 765 | 2 444 | 551 | 23 | 48,3 % | 146 | - | aucun (hypotheses) |
| Livorno, golden mince | 27 | 8 685 | 1 426 | 1 909 | 18 | 76,3 % | 691 | - | aucun (par onglet) |
| Gdansk | 30 | 32 841 | 8 167 | 1 501 | 39,5 | 52,0 % | 402 | - | L1 |
| Aalborg | 30 | 35 715 | 4 968 | 2 070 | 27,5 | 64,4 % | 2 153 | - | L1 |
| Vistule | 28 | 122 188 | 3 235 | 3 013 | 33,5 | 83,3 % | 4 065 | - | L1 |
| Sarrasin | 32 | 26 689 | 6 456 | 4 531 | 23,5 | 81,2 % | 1 668 | - | L1 |

Trois lectures. **Le nombre d'onglets ne suit ni le score ni la richesse** : Cardinal, 65
onglets, porte moins de logiques que Gdansk a 30. **La richesse ne fait pas le score** :
Icare est riche et facile, Cardinal pauvre et dur, parce que le score suit les decisions
derivees, qu'aucune formule ne montre. **Nos packs batis larges tombent par la densite** :
Sarrasin tient le total d'un L3 mais etale ses logiques sur 32 onglets.

Deux versions de la mesure ont ete essayees et rejetees le meme jour : le squelette de
formule, qui tassait tout entre 87 et 407 logiques, et la profondeur du graphe, qui suit
la mise en page (149 sur Ashford, 11 sur Cardinal).

## Fermer une phase : les portes

| Outil | Ce qu'il fait |
|-------|---------------|
| `porte.py` | `init` equipe un dossier de pack ; `1` a `5` et `juicing` lancent la porte d'une phase, `2 --iteration k` celle d'une iteration de la golden ; `relais` inscrit la decision du owner ; `etat` montre les portes ouvertes, relayees, perimees. Tient le journal `portes.json` |
| `porte_controles.py` | le registre des portes, et les controles sans outil : cache de la golden lu dans le XML, iteration armee, ancrages atteints, input sheet extraite, certificat, feuille de score, paquet, metadonnees, decisions d'atelier |
| `porte_lecteurs.py` | un lecteur par outil de ce dossier : il le lance et tire de sa sortie une ligne `lu / ecarts / verdict` ; un motif absent rend ROUGE, jamais zero ecart suppose |
| `porte_conception.py` | lit `CONCEPTION.md` au plan impose et `ancrages.json` au format commun |
| `tests/` | `python -m unittest discover -s tests` : 48 tests sur un mini-pack synthetique, les vrais outils compris |

```
python porte.py init "<dossier du pack>"
python porte.py 2 --iteration 1 pack.json
python porte.py relais 2 --iteration 1 --decision valide --note "..." pack.json
```

Le protocole : [les portes](../references/portes.md). `mise_en_page.py --fiche
CONCEPTION.md --contre <lot>` juge la fiche de mise en page avant que la golden existe.

## Travailler avec l'auteur

| Outil | Ce qu'il fait |
|-------|---------------|
| `atelier.py` | les ateliers de la phase 2 : `preparer` une copie de travail numerotee (jamais ecrasee), `ouvrir` sur une cellule (seulement si le owner le demande), `relire` les modifications de l'auteur cellule par cellule, avec libelle de ligne, en-tete, avant, apres, et les valeurs suivies ; refuse de lire un classeur encore ouvert ; `decider` inscrit la decision du owner sur chaque modification, dans le JSON que la porte d'iteration lit |
| `atelier.ps1` | ouvre le classeur dans une **nouvelle** instance d'Excel, sur la cellule, et la laisse a l'utilisateur ; ne touche a aucune autre instance |

```
python atelier.py preparer "<golden>" --atelier "<build>/ateliers/GS atelier 03 - X.xlsx"
python atelier.py ouvrir "<copie>" --cellule "Input_Sheet!E812"
python atelier.py relire "<copie>" --reference "<golden>" --suivre "Termination!D14" --json "<build>/ateliers/it03.json"
python atelier.py decider "<build>/ateliers/it03.json" --cellule "Termination!D14" --decision reportee
```

Le protocole qui les encadre : [les ateliers](../references/ateliers.md).

## Verifier le pack

| Outil | Ce qu'il fait |
|-------|---------------|
| `formules_sures.py` | refuse toute fonction que le correcteur ne sait pas evaluer |
| `inputs_morts.py` | les hypotheses fournies que le modele ne consomme jamais |
| `tracabilite.py` | prompt ↔ rubric, dans les deux sens |
| `verifier_prompt.py` | le prompt contre son contrat : sept pages au plus, le bloc de format present, la carte des onglets, aucune formule |
| `verifier_rubric.py` | la rubric contre son contrat, en `.docx` comme en `.json` : poids, part du `+1`, prefixe d'entite, gates, penalites, poignees |
| `lo_dump.py` | recalcule sous LibreOffice et rend toutes les valeurs |
| `lo_parite.py` | compare ce recalcul au cache Excel, cellule par cellule |
| `parite_libreoffice.ps1` | enchaine les deux precedents |

## Noter

| Outil | Ce qu'il fait |
|-------|---------------|
| `noter.py` | **lit la rubric** et note un classeur contre elle, en resolvant les conventions de nommage du candidat |
| `dossier_equite.py` | pour chaque point perdu, de quoi le contester : perte legitime ou fabriquee |

```
python noter.py "<classeur>" --rubric "<rubric.txt>"
```

Sur la golden, la sortie doit etre **100 %**. Sur un candidat, elle mesure la
difficulte reelle.

## Livrer

| Outil | Ce qu'il fait |
|-------|---------------|
| `txt_vers_docx.py` | convertit un `.txt` en `.docx` **en reprenant** un gabarit du corpus |
| `nettoyer_metadonnees.py` | retire nom d'auteur, chemin machine, compte OneDrive et pointeur de co-edition. **A lancer en dernier** : Excel les reecrit a chaque enregistrement |
| `reparer_shared.py` | resout les `#SHARED:N` qu'un generateur laisse a la place d'une formule partagee |
| `rafraichir_rubric.py` | remet les valeurs attendues d'une rubric a jour sur sa golden corrigee, **sans toucher aux libelles ni aux poids** |

```
python txt_vers_docx.py "Rubric - X.txt" "Rubric - X.docx" --gabarit <nom>
```

Les gabarits vivent dans [`../gabarits/`](../gabarits/), ou a l'emplacement
designe par `PACK_GABARITS`.

## Ce qu'il faut installe

- **Python** avec `openpyxl`
- **Excel** (le recalcul passe par COM, donc Windows)
- **LibreOffice** pour la parite — facultatif, mais c'est le seul controle qui
  attrape les divergences de fonction

## La regle commune

Chacun de ces outils rend **un compte**, pas seulement un verdict. Un `0 divergence`
sans le nombre de cellules comparees ne prouve rien : il peut signifier qu'aucune
n'a ete lue. Toujours lire le compte a cote du verdict.

---

[Retour a la skill](../SKILL.md)
