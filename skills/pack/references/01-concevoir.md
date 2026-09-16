---
title: "Phase 1 - Concevoir la tache"
description: "Du sujet au noyau dur : le budget de discrimination qui decide du score des la conception, le piege nomme, le rollout d'enonce, le niveau vise lu dans les onglets et non a leur nombre, les ancrages et les tests de declenchement."
type: "reference"
status: "actif"
---

# Phase 1 — Concevoir

On ne commence pas par ouvrir Excel. On commence par savoir **ce qu'on evalue**.

Et surtout : **le score du candidat se decide ici.** Pas dans la rubric, pas au
durcissement. Une tache concue trop facile ne se rattrape par aucun outil en aval —
c'est la lecon la plus chere du corpus, et elle est chiffree en section 2.

## 0. Avant d'ecrire : developper avec l'auteur, et tenir la graine

**On ne rend pas une conception toute faite.** A toute demande de pack neuf, de noyau a
refaire ou de durcissement de fond, la phase s'ouvre par un **brainstorming avec
l'auteur** : partir des erreurs reellement commises par les candidats du lot, developper
les pistes une par une — leur mecanisme, pourquoi elles mordent, leur risque d'equite —
et poser **une seule question par message**. La conception ne s'ecrit qu'apres son
accord, et seulement sur ce qu'il a retenu.

> Decision du 16/09/2026 : une conception complete, ecrite des la demande d'un noyau
> « beaucoup plus etoffe », a ete renvoyee au brouillon. Le noyau est le jugement de
> metier de l'auteur ; un document ecrit sans lui le met devant un fait accompli.

**La graine est un contrat.** Elle vient de la liste de taches validee avec l'expert et
les labs : un pack qui en deborde n'est plus la tache commandee, meme s'il est plus
difficile. Avant d'ajouter une mecanique, une entree ou une sortie, **la rattacher a une
ligne de la graine** (Inputs, Outputs, Modeling points) ; ce qui ne s'y rattache pas ne
rentre pas, meme pour durcir. La difficulte se cherche dans la facon de resoudre ce que
la graine demande, pas dans de nouveaux sujets. La conception porte une **table de
tracabilite graine -> pack**.

> Decision du 14/09/2026, apres une phase 1 qui avait ajoute a la graine une election
> fiscale, un impot de vente, un DCF et des rendements de preteurs : « reste sur le
> prompt que je t'ai donne au depart, ca doit pas changer ».

## 1. Le noyau dur

Une tache d'evaluation n'a d'interet que si un modele competent peut echouer
dessus pour une raison interessante. Le **noyau dur**, c'est la mecanique precise
qui separe un bon modele d'un modele moyen.

Un noyau dur se formule en une phrase et se teste : *si le modele rate ca, il rate
la tache ; s'il reussit ca, le reste suit*.

Exemples de noyaux durs, du plus faible au plus fort :

| Noyau | Ce qu'il teste | Valeur |
|-------|----------------|--------|
| Batir un compte de resultat sur dix ans | de la saisie | faible |
| Reconstituer un cascade de remises | de la lecture d'enonce | moyenne |
| **Resoudre des taux depuis une cible de fuite, poste apres poste, chacun sur la base laissee par le precedent** | de la comprehension d'un mecanisme | **forte** |

Le bon noyau dur est presque toujours **une resolution**, pas un calcul : quelque
chose que l'enonce ne donne pas et qu'il faut deduire.

La forme la plus discriminante du corpus, nommee par la doctrine Onyx : **un terme
commercial auto-referentiel, calcule sur le nombre qu'il fait bouger.**

Treize formes eprouvees, rangees en quatre familles, chacune avec son piege nomme et
son aval mesure : **[le catalogue des mecaniques
discriminantes](mecaniques-discriminantes.md)**. On y choisit **trois ou quatre
mecaniques de familles differentes** — quatre auto-references de la meme famille
testent une seule competence quatre fois, et leurs points tombent ensemble. Un plafond
d'indexation qui s'applique au carnet de cloture, que l'ecretage lui-meme deplace :

```
A = min(U, c x (B0 + A))     et quand le plafond mord :  A = c x B0 / (1 - c)
```

## 2. Le budget de discrimination

C'est la lecture qui decide du score, et elle est arithmetique — pas une impression.

**Le constat fondateur.** Le premier AI output de Denali a note **162 / 200 = 81 %**
contre un pack fini : quinze gates passees, aucune penalite declenchee. Le
decoupage a montre ou etaient partis les points.

| Ce qui etait note | Ce qu'un modele frontiere a rendu |
|---|---|
| Le moteur par contrat — calendrier date, exercice clos au 30 septembre, collar contrat par contrat, pont run-rate/phase | **116 / 122 = 95 %** |
| La chaine financiere, separee par des conventions que le prompt ne tranchait pas | 33 / 68 = 49 % |
| Le formatting | 12 / 14 |

Deux conclusions, et elles gouvernent toute la phase :

> **Le moteur ne discrimine pas.** Un modele frontiere absorbe la complexite
> mecanique. Ce qui le separait n'etait que de l'ambiguite d'enonce — et
> **ce n'est pas de la competence.**

> **La rubric seule ne peut pas ramener le score a 40 % : elle ne mesure que ce que
> le prompt demande.**

### Les trois regimes de rendement

| Nature du point | Ce que rend un modele frontiere |
|---|---|
| **Transcription** — appliquer une regle enoncee, meme complexe | ~95 % |
| **Convention non tranchee** — le prompt laisse le choix | ~50 %, et c'est une perte **fabriquee** |
| **Aval d'une resolution ratee** | ~0-15 %, parce que l'erreur se propage |

### Le calcul

Le pool fait 200 points. Sous 45 % = **au plus 90 points gagnes**. Soit `T` la part
du pool qui vit derriere de la transcription, le reste derriere une resolution :

```
0,95 x T  +  0,15 x (1 - T)  <=  0,45
0,80 x T                     <=  0,30
                          T  <=  37 %
```

> **Au plus ~37 % du pool peut vivre derriere de la transcription. Il faut au moins
> 120 des 200 points en aval d'une resolution que le modele rate.**

**Verification sur Denali**, avec ses trois regimes reels :

```
0,95 x (122/200) + 0,49 x (68/200) + 0,86 x (14/200)  =  0,81
```

81 %, exactement le score constate. Le modele de lecture tient.

C'est une quantite **estimable des la phase 1**, parce que le pool suit la structure
du modele : on sait deja quelles sections on va ouvrir, et lesquelles ne sont que du
cablage.

### Ce qui n'achete pas de difficulte

- **Le volume.** Des onglets, des periodes, des lignes en plus : absorbes a 95 %.
- **L'ambiguite d'enonce.** Elle fait bien baisser le score, mais toute perte de ce
  type est une perte **fabriquee** au sens du dossier d'equite — donc un defaut du
  pack, a corriger avant livraison.

Un seul levier tient : **une resolution auto-referentielle avec beaucoup d'aval.**
Et le corollaire de toujours : **la difficulte legitime vient du mecanisme, jamais
de l'enonce.** Depuis le 16/09/2026, cet aval se construit **par modules
independants**, jamais en cascade : voir ci-dessous.

### Des difficultes independantes, pas une cascade

**Decision du 16/09/2026.** Un noyau en tete de chaine dont une seule erreur fait tomber
~80 % de la rubric penalise la meme faute plusieurs fois. C'est un defaut d'equite, meme
quand c'est le levier le plus sur pour passer sous 45 % : « il faut que ce soit
independant, pas des rubrics avec trop d'elements en cascade ».

Le calcul de la section precedente comptait l'aval d'une resolution ratee a 0-15 %. Avec
des difficultes **independantes**, chacune reussie seule avec une probabilite `p`, il
devient :

```
0,95 x T  +  p x (1 - T)  <=  0,45
chaque difficulte ratee seule ~70 % du temps, p ~ 0,30 :
0,65 x T                  <=  0,15
                       T  <=  23 %
```

> **La transcription tient sous ~20 % du pool, et chaque difficulte doit etre ratee
> seule environ sept fois sur dix.** Le plafond de ~37 % ne valait que pour la lecture
> en cascade ; il reste ecrit plus haut parce qu'il explique Denali.

Le contrat de la rubric note des valeurs isolees contre la golden : il ne peut pas noter
« sur les chiffres du candidat ». **L'independance se construit donc dans la tache** :

- **une valeur notee = une mecanique**, lue sur des donnees fournies, en deux etapes au
  plus ;
- **les valeurs terminales** (un total, la decision finale) a un ou deux criteres ;
- **des marges larges sur les decisions**, pour qu'une erreur faite ailleurs ne les
  retourne pas ;
- **des boucles internes a un module** ; une gate ne met a zero que son module ;
- quand la graine enchaine les sorties, **noter l'aval sur des grandeurs qui ne dependent
  pas de l'amont** (ratios par dollar, effets unitaires) plutot que sur les totaux.

**Au prototype**, injecter chaque erreur nommee et verifier qu'elle ne deplace que les
criteres de son module. Cote rubric : [les criteres
independants](contrat-rubric.md#4-bis-des-criteres-independants-pas-une-cascade).

## 3. Le piege nomme, mecanique par mecanique

**Un pack en porte plusieurs.** La circularite est un prerequis a tous les niveaux, donc
un pack neuf compte au minimum trois ou quatre mecaniques discriminantes, pas une.
Ce qui suit s'ecrit pour **chacune**, separement : une mecanique dont on n'a pas
nomme le piege ne discrimine pas, meme si ses voisines le font.

Pour chaque mecanique retenue, ecrire trois lignes :

1. **la bonne reponse** ;
2. **l'erreur exacte qu'un bon modele fera** ;
3. **combien de points de rubric tombent avec cette erreur.**

Sur Denali, la ligne 2 tenait en huit mots : *le piege est de plafonner sur le
carnet d'OUVERTURE.*

**Si on ne sait pas nommer la mauvaise reponse plausible, la mecanique ne discrimine
pas** — et aucune rubric ne rattrapera ca. Si on la nomme mais que la ligne 3 rend
huit points, la mecanique est vraie et inutile : elle ne porte pas de masse.

La ligne 2 devient le libelle de la gate de section en phase 4. Elle ne se
redecouvre pas plus tard, elle s'ecrit maintenant.

## 4. Le rollout d'enonce

Le rollout de la phase 5 est le seul juge du 45 %, et il arrive quatre phases trop
tard. Denali l'a paye : pack fini, QA passe, 81 %, tout a redurcir.

**Le meme test coute cinq minutes en phase 1.** Rediger le seul paragraphe qui
enonce la mecanique, y joindre les quelques hypotheses qu'elle consomme, et demander
le nombre a un modele frontiere. Pas de golden, pas de generateur, pas de rubric.

**Une passe par mecanique, pas une pour le pack.** Une mecanique peut mordre pendant
que sa voisine ne mord pas, et c'est precisement ce que Denali a montre : son moteur
rendait 95 %, sa chaine financiere 49 %. Tester le pack en bloc aurait moyenne les
deux et cache le probleme. Le rollout d'enonce se lance sur **chaque** mecanique
retenue, et son resultat s'ecrit a cote du piege nomme correspondant.

| Ce qu'il rend | Ce que ca dit |
|---|---|
| Le bon nombre | la mecanique ne discrimine pas — **on l'apprend maintenant** |
| L'erreur qu'on avait nommee | la mecanique est bonne, et la gate est deja ecrite |
| Une autre erreur | l'enonce est ambigu — a corriger avant d'ecrire une ligne de generateur |

Le troisieme cas est le plus utile des deux derniers : il attrape en phase 1 ce que
le dossier d'equite n'attraperait qu'en phase 5, quand la correction coute un
rebuild.

## 5. Le PROMPT BUILD — et il y en a deux

**Un pack porte deux prompts, et les confondre coute la tache.**

```
graine                deux paragraphes de concept, fournis
   |  developper et complexifier   <- c'est cette phase
PROMPT BUILD          le gros. Il sert a CONSTRUIRE la golden.
   |                                  Jamais livre.
   v
golden solution       le classeur, generé depuis lui
   |  reduire         <- phase 4
PROMPT DU PACK        sept pages. Celui qu'on donnerait a un analyst
                      pour reproduire le modele. Il genere l'AI Output.
```

### Le prompt build

C'est **la sortie principale de cette phase**, et le document qui porte tout le
travail de conception. On part de la graine — quelques paragraphes qui donnent le
sujet et le niveau — et on la **developpe et complexifie** jusqu'a ce qu'un
generateur puisse etre ecrit dessus.

Il contient tout ce que la graine ne dit pas : le deal et sa structure, les entites,
la grille temporelle, les mecaniques retenues du
[catalogue](mecaniques-discriminantes.md), la carte des onglets, l'ordre de
resolution, les conventions de base, et **les ancrages calibres**.

**On le juge a une seule question : est-ce que je peux ecrire le generateur avec
ca ?** S'il manque une convention, une base de calcul ou un ordre de resolution, il
est incomplet.

> **Il ne franchit jamais la porte.** Le prompt build contient les REPONSES —
> parametres resolus, taux back-solves, cibles de design avec leurs bandes. C'est
> exactement ce que le candidat doit reconstituer. Il est de la meme famille que
> l'anchor pack : un document de travail, et le pack de reference n'en porte aucun.

> **Sa forme standardisee n'est pas dans ce depot.** Le corpus la designe par
> `STAGE 0 a §S`, et le meta-prompt qui etend une graine en build-prompt vit dans un
> Project claude.ai, pas ici. A defaut, cette phase produit le meme contenu sans le
> gabarit.

### Le prompt du pack, decide ici et ecrit plus tard

Sa **carte d'onglets** et sa **liste de sorties exigees** sont ce que le generateur
implemente : elles se posent maintenant. Mais le document lui-meme ne s'ecrit qu'en
[phase 4](04-noter.md), une fois la golden recalculee.

Son squelette, ses six regles verifiables et son plafond de sept pages :
**[le contrat du prompt](contrat-prompt.md)**.

### Le partage entre les deux EST la decision de difficulte

**Ce qui reste dans le prompt build et n'entre pas dans le prompt du pack, c'est la
tache.** C'est le budget de discrimination vu par l'autre bout :

- trop de build dans le pack -> on a donne la construction. Le modele transcrit et
  rend 95 %, comme le moteur de Denali. La tache existe encore, elle ne discrimine
  plus ;
- pas assez -> la perte devient **fabriquee**, et le dossier d'equite donne raison
  au candidat.

## 6. Les frontieres

Un corpus contient d'autres taches. Deux pieges opposes :

- **Empieter** : reprendre la mecanique centrale d'une tache voisine, ce qui rend
  les deux redondantes.
- **Se diluer** : eviter tout recouvrement au point de n'avoir plus de sujet.

La regle : **le noyau dur doit etre neuf ; le decor peut etre commun.** Un chassis
de LBO partage avec dix autres taches ne pose aucun probleme tant que ce n'est pas
lui qu'on evalue. C'est meme souhaitable : le decor rend la tache realiste sans
consommer de la difficulte.

Poser explicitement, par ecrit : *ce que cette tache evalue, et ce qu'elle laisse a
d'autres*.

## 7. Le niveau vise : il se lit DANS les onglets

**Decision du 14/09/2026 : le nombre d'onglets ne fixe plus le niveau.** Un L3 peut
tenir en dix onglets, a condition que chacun porte une difficulte et une granularite
tres elevees ; cinquante onglets de cablage restent un L1. Les bandes d'onglets du
08/09/2026 sont conservees en fin de section, pour memoire : elles ne font plus foi.

Trois mesures disaient deja que la taille ne porte pas la difficulte :

- sur l'environnement 9, **Rigel construit 23 onglets de calcul et sort a 0,92 ;
  Cardinal en construit 65 et sort a 0,31** ;
- L1 et L2 avaient la meme mediane d'onglets dans le corpus : 13 ;
- le volume — onglets, periodes, lignes — est absorbe a 95 % (section 2).

Le niveau ne se confond toujours pas avec le budget de discrimination : **le niveau dit
le calibre du modele, le budget dit le score.** Un pack de chaque niveau vise sous 45 %.

**Une golden citee en exemple ne dit rien du niveau.** Quand la graine se termine par
« take on example the Golden Solution of X », X sert **au formatting seulement** : on
n'en tire ni le calibre, ni les mecaniques, ni les boucles, ni les scenarios, ni la carte
des onglets (decision du 16/09/2026, voir [la mise en page](mise-en-page.md)). Le fond
vient de la graine et de cette grille.

### Les cinq axes

| Axe | Ce qu'il mesure | Ou il se lit |
|-----|-----------------|--------------|
| **Decisions derivees** | les branches que le candidat doit resoudre au lieu de les recevoir, chacune prouvee par un bloc de comparaison dans la golden. **Le seul axe qui a suivi le score** : zero sur les cinq packs a 0,82-0,92, quatre sur Cardinal a 0,31 | declare en phase 1 ; invisible dans les formules |
| **Boucles reelles** | nommees, debranchables, discriminantes | `compter_boucles.py`, `amplitude_boucles.py` |
| **Granularite** | l'unite atomique ou chaque ligne porte ses propres termes (contrat, lot, creance, locataire, tranche), croisee avec le grain temporel | declaree ; les hypotheses consommees de `niveau.py` |
| **Densite logique** | le nombre de logiques differentes, au total et par onglet : une ligne recopiee sur 60 colonnes compte une fois, deux contrats aux termes differents comptent deux fois | `niveau.py` |
| **Sophistication** | la part des logiques qui portent une condition, une comparaison, une recherche, une date ou une imbrication | `niveau.py` |

### La grille

| | L1 | L2 | L3 |
|---|----|----|----|
| Decisions derivees | **≥ 1** | **≥ 2**, dont une qui change l'enjeu de la suivante | **≥ 4**, dont une chaine de trois |
| Boucles reelles et independantes | **1 a 3** | **≥ 4** | **≥ 6** |
| Granularite, declaree | une unite sous l'entite, a termes propres | un registre de lignes atomiques, chacune avec ses dates, plafonds ou paliers | deux axes fins croises dans le meme onglet — lignes atomiques x grain mensuel ou date — avec des regimes qui basculent par ligne et par periode |
| Logiques distinctes | **≥ 500** | **≥ 1 500** | **≥ 3 000** |
| Logiques par onglet de calcul, mediane | **≥ 20** | **≥ 40** | **≥ 80** |
| Hypotheses consommees | **≥ 150** | **≥ 400** | **≥ 1 000** |
| Sophistication | ≥ 45 % | ≥ 45 % | ≥ 45 % |
| Part du pool en transcription, difficultes independantes | ≤ ~20 % | ≤ ~20 % | ≤ ~20 % |
| Circularite | **prerequis bloquant** | **prerequis bloquant** | **prerequis bloquant** |
| **Onglets de calcul** | **libre** | **libre** | **libre** |

**Le niveau tenu est le plus haut dont toutes les lignes sont tenues.** Une seule ligne
sous son plancher fait redescendre le pack : 3 000 logiques etalees sur cinquante onglets,
a soixante par onglet, ne font pas un L3 mais un L2 large.

```
python outils/niveau.py "<golden>" --niveau L3 --detail
```

Il rend les mesures du fichier et `NIVEAU TENU SUR LE FICHIER`. C'est un **plafond** : les
trois axes declares — decisions derivees, boucles, transcription — ne se lisent pas dans
les formules et peuvent le faire redescendre. Un pack qui tient L3 sur le fichier sans
decision derivee reste un pack facile a gros moteur, comme Icare.

**Un L3 en dix onglets, en chiffres.** 3 000 logiques sur dix onglets, c'est 300 logiques
differentes par onglet — pas 300 lignes, 300 facons de calculer. Un registre de soixante
creances a cinq termes propres, sur une grille mensuelle, avec leurs bascules de palier et
leurs dates d'effet, y suffit ; soixante fois la meme ligne n'en fournit qu'une.

### Ce que la calibration a appris

Mesure du 14/09/2026 sur treize goldens, le tableau complet dans
[le README des outils](../outils/README.md) :

1. **Le corpus livre est sous le plancher L1, partout.** Les sept goldens de
   l'environnement 9 portent 7 a 15 logiques par onglet de calcul. La grille est une
   exigence, pas une description — comme les bandes du 08/09 l'etaient deja.
2. **Nos packs batis larges tombent en L1 par la densite.** Sarrasin porte 4 531
   logiques, au-dessus du plancher L3, mais 23,5 par onglet sur 32 onglets ; Gdansk en
   porte 1 501, a 39,5 par onglet sur 30. Ils ont etale leur logique sur des onglets.
3. **La richesse des formules ne fait pas le score.** Icare porte 2 100 logiques
   sophistiquees a 95 % et sort entre 0,82 et 0,92 ; Cardinal en porte 348 et sort a
   0,31. Les decisions derivees font le score, les planchers du fichier font le calibre :
   les deux se tiennent ensemble, aucun ne remplace l'autre.
4. **Deux mesures ont ete ecartees**, et ne se reintroduisent pas : le squelette de
   formule, references neutralisees, qui confond « prix x volume » et « taux x encours » ;
   la profondeur de chaine du graphe, qui depend de la mise en page — un echeancier
   vertical la porte a 149 sur Ashford, et elle rend 11 sur Cardinal, le plus dur.

### Batir dense plutot que large

- **Un onglet par mecanique, pas par sous-etape.** Le moteur, son registre et ses
  bascules vivent ensemble. Un lien pur d'un onglet a l'autre ne compte pas comme
  logique : `niveau.py` l'exclut.
- **Descendre a la ligne atomique.** Les termes de chaque contrat, creance ou tranche
  entrent dans le calcul de sa ligne ; un sous-total ne remplace pas un registre.
- **Croiser les axes dans l'onglet** plutot que dupliquer l'onglet par scenario ou par
  entite : un bloc replique compte une fois.
- **Peu d'onglets de presentation.** Synthese, matrice et controles ne portent pas le
  niveau, et chacun tire la mediane vers le bas.

### La circularite, et ce que son compte ne dit pas

« Reelles » a un sens precis : ni les boucles inertes, ni les composantes fortement
connexes du graphe. Les trois tests de `compter_boucles.py` font foi — isolement, cycle
residuel, **amplitude** — et `iterate="1"` doit etre reellement present dans
`xl/workbook.xml`.

**Zero boucle reelle, ou moins que le plancher du niveau : la phase 1 n'est pas finie.** Le
pack ne passe pas en construction, et **aucune derogation ne se declare** — ni au nom du
sujet, ni au nom de la graine.

### Quand le sujet ne porte pas de boucle evidente

**Decision d'Amir du 16/09/2026**, sur un settlement statement de pret distressed dont la
conception avait declare zero boucle « par derogation », au motif que la graine excluait les
effets d'ordre fabriques : **les boucles sont un prerequis.**

**Lire la graine juste.** Une clause du type *« the task does not manufacture order-dependent
results unless the specified convention genuinely changes a later calculation base »*
n'interdit pas la boucle : elle interdit la boucle **sans convention qui la porte**. Des
qu'une convention ecrite dans les pieces fait dependre une base de son propre resultat, la
boucle est admise — c'est meme la doctrine Onyx, un terme commercial calcule sur le nombre
qu'il fait bouger.

**Ou chercher**, dans les pieces du dossier plutot que dans la mecanique :

- une **somme fixe imputee aux interets courus sur le montant qu'elle rembourse** (un
  remboursement partiel « accompagne des interets courus sur le montant rembourse ») ;
- un **plafond, une commission ou une retenue calcules sur le montant net** qu'ils reduisent ;
- un **gross-up**, qui rend au beneficiaire un net apres la retenue qu'il subit ;
- une **base de compensation ou de portage qui inclut les montants regles dans le meme
  paiement** qu'elle alimente.

**Trois tests avant de retenir une boucle** :

1. **realite** : un praticien la reconnait dans le document qui la porte ;
2. **graine** : elle se rattache a une ligne de la graine ;
3. **amplitude** : coupee, elle deplace une valeur notee au-dela de **sa** tolerance. Dans
   `X = k x (B + X)`, l'amplitude vaut environ `k` : un taux de quelques dixiemes de point ne
   passe la tolerance de 1 % que si le critere est note plus finement — au cent pour un
   document qui se regle au cent.

**Le nombre se borne par le haut, jamais a zero.** « Seule la boucle economiquement
necessaire » veut dire : pas de boucle gratuite au-dela du besoin. Le plancher du niveau, lui,
se tient toujours.

> **Pourquoi le compte de boucles se decide et ne se lit pas.** On a compte les circuits
> du graphe de dependances sur quinze goldens, cinq par slot. Le resultat ne suit pas le
> niveau du tout :
>
> ```
> L1   0 · 5 · 5 · 13 · 24        mediane  5
> L2   0 · 0 · 1 ·  5 · 18        mediane  1
> L3   0 · 24 · 72 · 121 · 239    mediane 72
> ```
>
> Un L1 peut porter 24 circuits, un L2 zero. **Compter les composantes fortement
> connexes ne mesure rien d'utile, parce que dans un modele integre tout finit par se
> toucher.** Le compte qui compte est celui des boucles nommees, debranchables et
> discriminantes, celles qui passent les trois tests : **une decision de conception**,
> prise en phase 1 et inscrite dans la sortie de phase. Repere : Toubkal et Ravenna,
> batis au calibre haut, en portent huit chacun.

**Chaque domaine charge sa granularite a sa facon** : l'un par un registre de contrats a
termes propres, l'autre par des entites qui s'enchevetrent, un troisieme par une grille
datee au jour. Tous les axes de la grille sont exiges ; c'est la matiere qui les remplit
qui change.

**Un dernier avertissement de lecture.** Les dossiers `L1/`, `L2/`, `L3/` sont des
**slots**, et un pack peut etre charge au-dessus du sien : Toubkal l'assume, Ravenna
vise le calibre haut dans un slot L3. La grille decrit la cible, pas une garantie.

> **Conserve pour memoire, ne fait plus foi depuis le 14/09/2026.** La grille du
> 08/09/2026 fixait le niveau par la taille, sur 34 goldens rangees par slot plus le
> pack d'ancrage du haut :
>
> | Niveau | Onglets de calcul | Formules | Grille | Circularite |
> |--------|-------------------|----------|--------|-------------|
> | L1 | 15 a 20 | ~1 300 et au-dela | annuelle ou trimestrielle | obligatoire |
> | L2 | 25 a 30 | ~3 200 et au-dela | annuelle ou trimestrielle | obligatoire |
> | L3 | 41 a 50 | 117 000 a 155 000 | mensuelle, 145 colonnes et au-dela | obligatoire |
>
> Elle avait comprime l'echelle : L4 et L5 disparaissaient, L3 reprenant le calibre de
> l'ancien « L4 au plafond » (41 onglets, 117 349 formules, 404 colonnes, 300 iterations
> sur le pack de reference) avec 50 onglets de calcul pour borne haute. L'echelle d'avant
> disait L1 >= 15 onglets, L2 >= 20, L3 >= 25, plafond L4 a 50, avec Mazadona = L2 et
> Seine = L4 pour ancrages. Ses lectures restent vraies et ont nourri la grille actuelle :
> L1 et L2 ne se distinguaient que par la densite (x2,4 sur les formules), la marche vers
> L3 etait un changement d'axe (le passage au mensuel), et on monte en ajoutant des axes
> — periodes x entites x trials — pas des onglets. La gate de boucles disait « 1 a 3 :
> plafond L1 ; au-dela, echelon a fixer » ; la grille actuelle fixe cet echelon.

## 8. Les ancrages

Un **ancrage** est une valeur que la golden devra atteindre, decidee maintenant.

Pourquoi maintenant : un classeur genere produit des milliers de valeurs, et il est
toujours possible de se convaincre apres coup que celles qui sortent sont les
bonnes. Les ancrages empechent ca. Ils sont le contrat que le generateur doit
honorer.

Un fichier d'ancrages contient, pour chaque valeur retenue :

```
poste, periode, valeur visee, tolerance, nature, pourquoi cette valeur
```

Il s'ecrit en `ancrages.json`, au format commun a tous les packs (`id`, `mecanique`,
`poste`, `periode`, `cellule`, `valeur`, `tolerance`, `nature`, `pourquoi`) : c'est ce
format que les portes 1 et 2 lisent. La `cellule` se remplit en phase 2, quand le
classeur existe. Voir [les portes](portes.md).

Le « pourquoi » n'est pas decoratif : c'est lui qui permet, six heures plus tard, de
savoir si un ecart est un bug ou une revision legitime.

### Les trois natures

Il faut les distinguer avant de valider, parce qu'elles ne s'arbitrent pas pareil :

| Marque | Nature | Ce qu'on peut en faire |
|---|---|---|
| **[M]** | observation de marche — un comparable reel | se verifie, ne se negocie pas |
| **[S]** | structure du deal — un choix de montage | s'arbitre |
| **[D]** | **cible de design — posee pour que la tache discrimine**, pas pour ressembler au reel | se **resout** par le calibrateur |

Un `[D]` n'est pas une donnee : c'est une cible que la phase 2 doit atteindre, et il
s'ecrit avec **une bande et ses deux bornes de rupture** — ce qui casse en dessous,
ce qui casse au-dessus. Deux exemples reels :

> **Ratio de capacite a couverture pleine — 75,5 % +/- 2** [D] : le plan de visite
> est *resolu* pour l'atteindre. A 100 % le plafond ne mord pas et la tache
> s'effondre ; a 50 % le modele ne couvre plus rien et la sortie n'a plus de sens.

> **78 comptes en zone de recouvrement** [D] : c'est le seul endroit ou l'affectation
> est un choix. En dessous de 60 le probleme disparait, au-dessus de 100 il devient
> un tri.

**Une entree calee se fournit en valeur ronde.** Mesure du 14/09/2026 : une valeur
d'entreprise fournie a 503,347 — calee pour donner a la decision des preteurs une marge de
+12,5 — a ete lue par le candidat comme « posee pour produire le resultat », et il l'a
ecrit dans ses conventions. Un chiffre a trois decimales parmi des entrees rondes designe
ou regarder et quel resultat est vise : c'est une fuite de conception. Toute entree
issue d'un `[D]` se donne **au pas des autres entrees de sa famille** ; pour tenir une
bande, bouger plusieurs entrees rondes plutot qu'une a la decimale pres, et verifier
qu'aucune sortie notee ne tombe sur un nombre rond suspect.

**Combien d'ancrages** : assez pour couvrir chaque mecanique au moins une fois, et
chaque agregat de tete. Une trentaine suffit ; deux cents deviennent un second
modele a maintenir.

**Les ancrages sont revisables.** Quand la construction montre qu'un ancrage etait
irrealiste, on le change — mais **explicitement**, en notant pourquoi. Ce qui est
interdit, c'est de le changer en silence pour faire passer un test.

## 9. Les tests de declenchement

Les ancrages disent quelles valeurs la golden doit atteindre. Les tests de
declenchement disent **a quelle condition la tache mord**.

> Le script ne s'arrete pas quand les nombres bouclent. Il s'arrete quand la tache
> mord.

Chacun est une bande verifiable sur la golden, pas une intention :

```
le plafond d'effectif mord sur 9 a 11 territoires sur 12, a chaque periode
l'evenement de FY3 force un re-solve qui deplace au moins 25 comptes
le covenant tient avec un headroom minimal sous 0,75x sur au moins une periode
```

Ce sont des ancrages sur **l'existence de la difficulte**. Un pack dont les nombres
bouclent et dont aucun test ne mord est un pack facile qui a l'air fini.

**Une cible fausse se corrige, la mecanique enoncee ne se deforme pas.** Sur un pack
reel, une bande demandait 150 a 300 bps la ou la mecanique du prompt en bornait le
gain a une dizaine. Elargir la mecanique pour atteindre le chiffre serait revenu a
ajuster le modele sur un nombre invente : on a garde la mecanique et corrige la
cible. Ce que le test devait prouver n'a pas change — que le mecanisme n'est pas nul.

## 10. La couverture

Avant de fixer le sujet, verifier qu'il n'est pas deja traite par le corpus. Un
sujet sature ne sera pas retenu, quelle que soit la qualite du pack.

Si un inventaire des taches existantes est disponible, le consulter. Sinon, le
demander : c'est une question qui se pose maintenant, pas apres construction.

## Sortie de phase

Ces choses ecrites, validees avant de passer a la construction. **Elles s'ecrivent dans
`CONCEPTION.md` au plan impose et dans `ancrages.json` au format commun**, que
`outils/porte.py init` pose, et la phase se ferme par **`porte.py 1 pack.json` ouverte,
puis un relais `valide` du owner** — voir [les portes](portes.md) :

```
brainstorming         les pistes developpees avec l'auteur ; la conception ne porte
                      que ce qu'il a retenu
graine -> pack        chaque mecanique, entree et sortie rattachee a une ligne de la
                      graine ; rien d'autre
noyau dur             une phrase, testable
niveau                les axes de la grille au niveau vise : decisions derivees et
                      boucles nommees une par une, granularite declaree, planchers
                      de niveau.py a atteindre. Aucune bande d'onglets.
prompt build          la graine developpee : deal, entites, grille, mecaniques,
                      carte des onglets, ordre de resolution, ancrages calibres.
                      Test : peut-on ecrire le generateur avec ca ?
boucles               prerequis : au moins le plancher du niveau, chacune avec la
                      convention des pieces qui la porte, sa forme fermee et son
                      amplitude estimee. Zero : la phase n'est pas finie.
budget                part du pool en transcription <= ~20 %, difficultes
                      independantes : chaque erreur nommee ne deplace que son module
piege nomme           N mecaniques, N pieges nommes : bonne reponse / erreur
                      plausible / points qui tombent
rollout d'enonce      N passes, une par mecanique, resultats lus
frontieres            ce que la tache evalue, ce qu'elle laisse aux voisines
ancrages              valeurs, tolerances, nature [M]/[S]/[D], justifications
tests de declenchement  les bandes qui disent que la tache mord
mise en page          la fiche (grille, architecture, typographie, habillage,
                      encre, familles de documents) et sa distance aux packs
                      deja livres du lot : voir mise-en-page.md
```

Sans le noyau dur, les frontieres et les ancrages, la phase 2 construit a l'aveugle
et la phase 3 n'aura rien contre quoi se verifier. Sans le budget, le piege nomme et
le rollout d'enonce, la phase 5 decouvrira un score de 81 % sur un pack fini.

---

[Retour a la skill](../SKILL.md) | [Les pieges](pieges.md) | [Phase suivante : batir](02-batir.md)
