---
title: "Les outils portables de fabrication d'un pack"
description: "Les vingt-six verificateurs qui ne savent rien du sujet et marchent sur n'importe quel pack ou n'importe quel classeur."
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
