---
title: "Phase 5 - Verifier le pack avant livraison"
description: "Les six controles du QA, les questions qu'un evaluateur posera, et le rollout qui mesure la difficulte reelle."
type: "reference"
status: "actif"
---

# Phase 5 — Verifier

Le pack est complet. Il s'agit maintenant de le mettre en echec **avant** que
quelqu'un d'autre ne le fasse.

Derriere tous les controles qui suivent, **un seul critere de fond** :

> **Un associe doit pouvoir recreer le modele avec le prompt et l'input sheet, et
> rien d'autre.**

Le service qui recoit le pack pose quatre questions, et **une seule reponse negative
suffit a le renvoyer** : tout ce qui est donne sert-il ; la rubric ne demande-t-elle
que ce que le prompt demande ; la golden re-note-t-elle 100 % **dans le moteur du
correcteur** ; un modele de frontiere arrive-t-il ou on l'attend. La cinquieme est
la notre, et c'est celle qui protege le pack : **chaque point retire est-il
defendable ?**

## Les six controles

Chacun rend un compte. **Un vert sans compte ne vaut rien** — c'est le mode de
defaillance principal de cette phase (pieges 1 et 2).

### 1. Les formules sont evaluables

```
python outils/formules_sures.py "<golden>"
```

Refuse toute fonction hors du sous-ensemble que le correcteur sait evaluer. Sortie
attendue : `0 fonction refusee`, et **le nombre de formules examinees**.

### 2. La parite LibreOffice

```
powershell -File outils/parite_libreoffice.ps1 -Classeur "<golden>"
python outils/lo_parite.py "<golden>"
```

Recalcule sous LibreOffice et compare au cache Excel, cellule par cellule. Sortie
attendue : `0 divergence`, et le nombre de cellules comparees. **Verifier que les
dates sont dans le perimetre compare** : c'est la divergence la plus silencieuse
(piege 7).

**Le service recalcule sous LibreOffice, pas sous Excel.** Ce n'est pas un detail de
confort : un pack du corpus a vu sa propre golden notee **53 / 200** pour cette
seule raison, sur un modele juste. Deux consequences :

- n'employer que des fonctions anciennes — c'est le controle 1 ;
- **un modele circulaire doit porter le reglage d'iteration DANS LE FICHIER.**
  LibreOffice le lit a l'ouverture ; s'il est absent, **toute la boucle rend
  `Err:522`**.

### 3. La tracabilite prompt ↔ rubric

> Le prompt lui-meme a ete controle en phase 4 contre
> [son contrat](contrat-prompt.md) — sept pages, bloc de format, carte des onglets,
> aucune formule. Si on entre directement en phase 5 sur un pack qu'on n'a pas
> ecrit, lancer `outils/verifier_prompt.py` d'abord : ce controle-ci suppose un
> enonce conforme.

```
python outils/tracabilite.py "<prompt.txt>" "<rubric.txt>"
```

Deux sens, tous les deux fautifs :

- Un critere note **qui ne trace vers aucune exigence du prompt** : on note quelque
  chose qu'on n'a pas demande. Le service classe ces cas en `Failed`, `Stretch` et
  `Unrelated`.
- Une exigence du prompt **qu'aucun critere ne mesure** : on demande quelque chose
  qu'on ne note pas.

### 4. Les hypotheses mortes

```
python outils/inputs_morts.py "<input sheet>" "<golden>"
```

Toute hypothese fournie doit etre consommee. Sortie attendue : `0 hypothese morte`.

**La raison est plus grave que la perte de temps du candidat.** Une hypothese
laissee dans l'input sheet apres que le moteur qui la lisait a change n'est pas du
poids mort : elle **DESIGNE** au candidat la construction qu'on attend precisement
qu'il evite — et l'audit d'equite lui donnera raison de l'avoir suivie. C'est un
defaut de pack, pas une maladresse de candidat.

### 5. L'audit de la golden

```
python outils/gs_audit.py "<golden>"
```

Les defauts qu'un recalcul ne montre jamais : liens externes, feuilles masquees,
plages nommees cassees, controles tautologiques, cellules qui ne peuvent pas
echouer.

**C'est le controle qui trouve les faux verts.** Un controle code en dur a zero, ou
qui soustrait une cellule a elle-meme, passe tous les autres tests.

### 6. Les traces de fabrication automatique

```
python outils/traces_ia.py "<golden>" --detail
```

Un pack juste mais qui « fait IA » est **refuse avant d'etre lu**, et le refus ne
porte jamais sur le modele : il porte sur une puce pleine, une phrase explicative
accrochee a un libelle, un onglet reste groupe. Ces defauts vivaient dans des
listes en prose que rien n'executait ; ce controle les rend mecaniques.

Douze controles, en deux natures qu'il ne faut pas confondre :

| | Ce qu'ils cherchent |
|---|---|
| **DEFAUT** — objectif, se corrige sans discuter | puces pleines, tirets cadratins, guillemets et apostrophes typographiques, symboles decoratifs et emoji, libelle ecrit en formule, groupement laisse dans le classeur |
| **A JUGER** — indice probabiliste, le module montre et se tait | phrase explicative dans une colonne de libelles, **coherence de la palette d'encre**, onglets sans couleur ou tous de la meme, largeurs de colonnes par defaut, feuille large sans volet fige, onglet creux |

**La couleur ne se juge jamais dans l'absolu.** Il y a deux palettes — voir
[les contrats de format](contrats-format.md) — et un premier jet qui comptait le
bleu en defaut a rendu **651 fausses alertes sur une golden conforme a son propre
prompt**. Le controle deduit la palette du classeur, puis ne signale que ce qui la
contredit ; `--palette maison|onyx` la force. Il n'est pas symetrique : sous onyx le
violet est la couleur des **controles**, donc legitime.

**Les intercalaires sont exemptes des trois controles de forme d'onglet** — creux,
volet fige, largeurs de colonnes. Un separateur visuel de navigation ne calcule
rien : c'est sa fonction, il est creux par construction, et le juger comme un
onglet de calcul rendrait trois fausses alertes par separateur — un classeur peut
en porter huit. Ils sont reconnus a leur nom — la forme du corpus est `>>Financials`, chevrons
colles et capitale initiale seule ; `--intercalaires` les nomme explicitement sur un
classeur qui suit une autre convention.

L'exemption se lit dans le **denominateur**, jamais en silence :

```
[JUGE] T11  aucun onglet creux    1   sur 2 onglets de calcul, 2 intercalaire(s) exempte(s)
```

C'est le meme partage que celui du corpus, qui exclut deja les separateurs du
compte d'onglets fixant le niveau.

Sortie attendue : `defauts objectifs : 0`, et **le nombre de textes lus** a cote.
La separation des deux natures n'est pas une precaution de style : une fausse
alerte est le meme defaut qu'un faux vert (piege 15).

**Les seuils de ce controle ont ete recales sur une golden livree**, et il fallait
le faire : le premier jet, cale sur des classeurs fabriques a la main, y a rendu
**775 defauts dont 124 faux positifs** — il tenait les colonnes A a D pour des
libelles alors qu'une seule l'etait. Une colonne de libelles se **reconnait** a ce
qu'elle porte, comme un commutateur se reconnait a ce qu'il vaut. De meme, la
longueur d'un libelle ne dit rien : `C. Customer tiers - share, elasticity and
cumulative discount cap` est un bandeau de bloc, pas un commentaire. Seul le fait
d'**expliquer** compte.

La lecon vaut au-dela de cet outil : **un controle teste sur des cas qu'on a semes
soi-meme trouve exactement ce qu'on y a mis.** Le passer sur un livrable reel est
ce qui separe un controle d'une demonstration.

Le caractere fautif est affiche par son **point de code** — `<U+2022>` plutot
que la puce elle-meme — parce que c'est justement celui que la console ne sait
pas ecrire, et parce que l'information utile est de savoir lequel retirer.

## Les quatre questions

Ce sont celles qu'un evaluateur pose. Y repondre par ecrit, avec des chiffres, avant
de livrer.

1. **Un candidat peut-il atteindre ces valeurs avec le seul prompt et le seul input
   sheet ?** Si une valeur exige une information absente des deux, le pack est
   invalide — ce n'est pas de la difficulte, c'est un piege.
2. **La rubric mesure-t-elle ce que le prompt demande ?** C'est le controle 3, mais
   relu par un humain : la tracabilite automatique ne voit pas un critere qui trace
   vers la bonne exigence en la mesurant mal.
3. **Les tolerances sont-elles tenables ?** Un candidat qui suit la bonne methode
   avec des arrondis raisonnables doit passer. Le rollout le montre.
4. **Que se passe-t-il si le candidat fait le choix defendable inverse ?** S'il
   perd tout, il manque une gate ou une precision d'enonce.

## Le rollout

C'est le controle le plus revelateur, et le seul qui mesure la **difficulte reelle**.

> **Le grading de l'AI Output ne se fait pas ici.** Il se fait sur **claude.ai**, pas
> dans Claude Code. La raison est que les specifications contractuelles — la revue de
> pack, les regles de notation, l'audit de golden — vivent dans les instructions
> personnalisees des **Projects claude.ai**, et nulle part ailleurs : ni sur le
> disque, ni dans ce depot. Noter ici reviendrait a noter sans le contrat.
>
> Ce qui se fait ici : preparer le classeur a noter, verifier qu'il est lisible
> (cache plein, iteratif arme), et **exploiter** le grading une fois rendu. Le
> jugement critere par critere se rend sur claude.ai.

**Le principe** : fabriquer un candidat credible — un modele qui suit le prompt
honnetement, avec les approximations qu'un bon modele ferait — et le noter contre la
rubric.

**La facon de le fabriquer qui a fait ses preuves : degrader la golden d'un
mecanisme, un seul.** On ne fait pas tourner un modele. L'ecart avec la golden est
alors *exactement* le mecanisme retire, et le point perdu se lit sans discussion.

Le chiffre obtenu est une **borne haute** : un vrai candidat fera plus d'erreurs.
C'est l'information utile — **si quelqu'un qui a tout bon sauf ce mecanisme depasse
deja la cible, la tache ne discrimine pas assez.**

Une precaution qu'il a fallu coder : **accorder au candidat les gates qu'on ne sait
pas trancher gonfle sa note de dix-huit points**, assez pour lui faire franchir la
barre a tort. Lier chaque gate a la performance de sa propre section — une gate est
structurelle, et une section dont les valeurs s'effondrent n'a pas ete construite.

```
python outils/noter.py "<candidat>" --rubric "<rubric.txt>"
python outils/dossier_equite.py "<candidat>" "<rubric.txt>"
```

### Ce que le score veut dire

| Score obtenu | Lecture |
|--------------|---------|
| Tres au-dessus de la cible | la tache est trop facile : le noyau dur ne mord pas |
| Dans la cible | c'est ce qu'on cherche |
| Tres en-dessous | verifier **pourquoi** avant de se rejouir |

Un score bas n'est une bonne nouvelle que si les pertes viennent du **noyau dur**.
Si elles viennent d'ambiguites d'enonce ou de criteres mal adresses, la tache n'est
pas difficile : elle est mal ecrite.

### Le Q&A inverse — le dossier d'equite

C'est la cinquieme question, et **la charge de la preuve s'y inverse** :

> Ce n'est plus au candidat de meriter ses points, **c'est a la rubric de justifier
> ceux qu'elle retire.**

`dossier_equite.py` monte, pour chaque point perdu, de quoi le contester : ce que le
critere demandait, ce que le candidat a produit, **la cellule et la formule de la
golden** qui justifient l'attente, et si la perte est **legitime** (erreur de
methode) ou **fabriquee** (critere mal adresse, tolerance impossible, information
absente de l'enonce). Le classement se fait en trois etats : `ok`, `incertain`,
**`defaut de rubric`** — et un second relecteur, qui n'a pas ecrit la rubric, est le
bon juge.

**Toute perte fabriquee est un defaut du pack**, pas du candidat. Elle se corrige
avant livraison.

### Le detail qui compte

Un rollout ou tous les criteres sont resolus mais ou le score est bas, c'est un bon
signe. Un rollout avec des criteres **NON RESOLUS** signale des criteres que
personne ne peut apparier — a corriger, meme si le score global parait bon.

## La livraison

Verifier ce que contient reellement le paquet livre, membre par membre. Un pack
auquel il manque l'input sheet est incomplet, et ca ne se voit pas depuis le dossier
de travail.

Ce qui precede est une question de qualite ; ceci est une question de **conformite
mecanique**. Un pack excellent qui rate un nom de fichier est rejete par le loader de
l'environnement, **sans que le modele soit meme regarde**.

**Il n'y a pas un contrat, il y en a un par corpus, et ils ne se ressemblent pas.**
Deux contrats reels, a ne jamais confondre :

| | Corpus A — quatre fichiers | Corpus B — trois fichiers |
|---|---|---|
| La golden | `GoldenSolution - <Pack>.xlsx` | `GoldenSolution.xlsx`, **en un mot** |
| Les hypotheses | `InputSheet - <Pack>.xlsx` | `Input_Blank.xlsx`, jamais « Input Template » |
| L'enonce | `Prompt - <Pack>.docx` | `Prompt.json`, UTF-8 **sans BOM** |
| La grille | `Rubric - <Pack>.docx` | *fournie par l'ingenierie* |

Dans le corpus A, **le prompt et la rubric partent en Word**. Le `.md` ou le `.txt`
reste la source — versionnee, diffable — et la conversion se fait a la livraison
(piege 12). **L'anchor pack n'appartient pas au pack** : c'est un document de
travail, et le pack de reference n'en porte aucun.

**Ce qu'on ne livre jamais**, selon le corpus : `Rubric.json`, `config.json`,
`Inputs.pptx`, `.lo_cache.json` — l'equipe d'ingenierie les produit elle-meme.

**Relever le contrat du corpus servi, et ne jamais transposer celui d'un autre** :
appliquer le contrat a trois fichiers a un pack qui en attend quatre le fait rejeter
entier. En cas de contradiction entre le contrat de livraison et une SOP d'audit, le
contrat gagne : il decrit ce que le loader fait vraiment, et une violation fait
planter ou mal noter l'environnement quelle qu'ait ete l'intention.

### Les metadonnees partent avec le fichier

Un `.xlsx` livre porte le **nom de l'auteur, le chemin machine, le compte OneDrive et
le pointeur de co-edition**. Ils traversent la livraison sans que rien ne les
signale, et ils n'ont rien a faire chez un client.

```
python outils/nettoyer_metadonnees.py "<golden>" "<input sheet>"
```

**A lancer en dernier, apres le dernier enregistrement** : Excel les reecrit a
chaque fois qu'il touche le fichier. Nettoyer puis rouvrir revient a n'avoir rien
nettoye.

C'est la meme regle que pour `calcPr`, et pour la meme raison : **tout ce qu'Excel
reecrit en enregistrant se controle apres le dernier enregistrement, jamais avant.**

### Le dernier regard

Et **relire `calcPr` une derniere fois** : si le classeur a ete rouvert dans Excel
depuis le dernier controle, le reglage d'iteration a pu changer (piege 4).

Deux reparations qui n'apparaissent qu'a ce moment-la :

- **`#SHARED:N` a la place d'une formule.** Un generateur qui rencontre une formule
  PARTAGEE peut laisser ce marqueur dans la rubric. **Vingt rubrics du corpus en
  portent, jusqu'a 984 dans une seule.** Le laisser passer rend la rubric
  ingradable sur ces lignes.

  ```
  python outils/reparer_shared.py "<rubric.txt>" "<golden>"
  ```

- **Une golden corrigee apres l'ecriture de la rubric.** On ne reecrit pas la
  rubric : on **rafraichit ses valeurs attendues** sur le classeur corrige, sans
  toucher aux libelles ni aux poids. Le jugement de l'auteur reste, les chiffres
  suivent.

  ```
  python outils/rafraichir_rubric.py "<rubric.txt>" "<golden corrigee>"
  ```

  **Puis on relance l'autotest** : une rubric rafraichie qui ne rend pas 100 % a
  ete rafraichie sur le mauvais classeur.

## Sortie de phase

```
formules sures        0 refusee        (sur N examinees)
parite LibreOffice    0 divergence     (sur N cellules)
tracabilite           0 orpheline dans les deux sens
hypotheses mortes     0
audit golden          0 defaut
traces IA             0 defaut objectif  (sur N textes lus)
rollout               score dans la cible, 0 critere non resolu
                      (grading rendu sur claude.ai, pas ici)
equite                0 perte fabriquee ; chaque point retire justifie par une cellule
paquet                tous les membres presents, aux noms exacts du corpus
metadonnees           nettoyees APRES le dernier enregistrement
calcPr                relu apres le dernier enregistrement
```

---

[Retour a la skill](../SKILL.md) | [Les pieges](pieges.md)
