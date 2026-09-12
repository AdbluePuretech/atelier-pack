---
title: "Le contrat du prompt"
description: "Le squelette en neuf blocs releve sur 45 prompts livres, les six regles verifiables, et le plafond de sept pages."
type: "reference"
status: "actif"
---

# Le contrat du prompt

> **Ce contrat regit le prompt DU PACK**, celui qu'on livre — pas le **prompt
> build**, qui sert a construire la golden et ne sort jamais du dossier de travail.
> Le premier est la silhouette du second. Voir
> [la phase 1, section 5](01-concevoir.md).

Le prompt est le document que le modele evalue **lit reellement**, et c'etait le
seul des quatre livrables que rien ne verifiait : la tracabilite le compare a la
rubric, le rollout le suit, la livraison exige son nom — personne ne regardait ce
qu'il contient.

Ce qui suit n'est pas invente : c'est releve sur **45 prompts livres** d'un corpus
reel, et chaque regle porte son compte.

## Le squelette, en neuf blocs

| Bloc | Sur 45 |
|------|--------|
| Titre `Prompt - Project <Nom>: <Sujet>` | 45 |
| **Instruction** : *« Build a … model … based on the data in the Input_Sheet and to the following specifications »*, suivie du regime de calcul et des conventions d'affichage | 45 |
| **Contexte** : le deal, les entites, les montants, la grille temporelle, puis *« The defining computational features are … »* | 45 |
| `Intermediate Outputs` | 44 |
| `Final Outputs` | 44 |
| `Checks & Ties` | la plupart |
| `Xlsx Output` | **45** |
| `Formatting Requirements` | **45** |
| `Sheet Contents` — la carte onglet par onglet | **45** |

## Les six regles

### P1 — au plus sept pages

**C'est un plafond, pas une moyenne.** Mediane du corpus : 6,5 pages. Un prompt qui
s'etale noie l'enonce : des puces, et **pas le detail de la construction**.

Huit prompts du corpus le depassent, jusqu'a onze pages. Ce sont des exceptions
subies, pas un exemple a suivre.

### P2 — le bloc de format du classeur ne s'oublie pas

`Xlsx Output` puis `Formatting Requirements`, presents **dans les 45**. C'est le
bloc qu'on oublie en ecrivant un prompt neuf, et sans lui le candidat livre un
modele qui ne ressemble a rien de ce qu'on attend — puis se fait sanctionner pour
une forme qu'on ne lui avait pas demandee.

Il enonce, au minimum : pas de gridlines, le **code couleur**, une police
professionnelle, les negatifs entre parentheses et le zero en tiret, les formats de
nombre unite par unite, les en-tetes de periode avec leur ligne de dates et la
colonne de total ou de controle en tete, et les unites nommees dans le bloc
d'en-tete de chaque feuille.

> **Le code couleur est celui que le corpus impose, et il s'ecrit dans le prompt.**
> Le relever dans les documents d'exemple ; ne pas le supposer. Une golden qui ne
> suit pas le code couleur enonce dans son propre prompt se contredit elle-meme.

### P3 — `Sheet Contents` : le prompt EST le cahier des charges

La carte nominative des onglets, `Nom_Onglet — ce qu'il porte`, groupee par famille.
Presente dans les 45.

C'est la consequence structurante : **le prompt ne s'ecrit pas apres le modele.**
Sa liste d'onglets et ses sorties exigees sont ce que le generateur doit
implementer. Il se redige donc **avec la phase 1**, se stabilise en phase 2, et ne
recoit ses derniers chiffres qu'une fois la golden recalculee.

### P4 — les sorties exigees, ligne par ligne

`Intermediate Outputs` et `Final Outputs` listent **les lignes que le classeur doit
porter**, groupees par bloc, avec leur axe (`per period — month 0 to month 144`).
C'est de la que descend le pool de la rubric : sur le pack de reference,
**174 lignes d'outputs requis, 116 criteres, 200 points**.

### P5 — aucune formule

**0 prompt sur 45 contient une formule Excel.** Le prompt dit **quoi** produire,
jamais **comment**. Donner la formule, c'est supprimer la tache.

### P6 — la provenance est enoncee

Tout vient de l'`Input_Sheet`, et le prompt le dit. Trois formulations coexistent —
*« based on the data in »*, *« using the inputs provided in »*, *« from the data
in »* — et elles valent la meme chose.

C'est ce qui separe ce corpus d'un corpus **source sur documents**, ou l'enonce
renvoie a un rapport annuel ou a un extract de terminal et ou certaines valeurs sont
justement **a ne pas donner**. Les deux contrats ne se transposent pas : verifier
lequel s'applique avant d'ecrire une ligne.

## Le controle

```
python outils/verifier_prompt.py "Prompt - <Pack>.docx"
python outils/verifier_prompt.py "Prompt - <Pack>.docx" --pages 7
```

Il rend une ligne par regle, avec son compte. Le nombre de pages vient de
`docProps/app.xml`, que Word ecrit en enregistrant — il est **parfois perime**
(quatre prompts du corpus s'y annoncent a une page et zero mot), et le module
retombe alors sur le nombre de mots, a 440 mots la page.

## Ce que le prompt ne fait jamais

- **Il ne donne pas de formule** (P5).
- **Il ne designe pas le document ou se trouve la reponse**, quand la tache repose
  sur une data room : l'agent doit lire la salle et juger quelle valeur fait foi.
- **Il ne laisse pas une convention non tranchee.** Une convention que le prompt ne
  tranche pas se paie en pertes **fabriquees** au rollout : ce n'est pas de la
  difficulte, c'est de l'ambiguite, et le dossier d'equite donnera raison au
  candidat.

---

[Retour a la skill](../SKILL.md) | [Phase 1 - Concevoir](01-concevoir.md) | [Phase 4 - Noter](04-noter.md) | [Les contrats de format](contrats-format.md)
