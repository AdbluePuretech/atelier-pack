---
title: "Phase 1 - Concevoir la tache"
description: "Du sujet au noyau dur : le budget de discrimination qui decide du score des la conception, le piege nomme, le rollout d'enonce, le niveau vise et ses deux gates, les ancrages et les tests de declenchement."
type: "reference"
status: "actif"
---

# Phase 1 — Concevoir

On ne commence pas par ouvrir Excel. On commence par savoir **ce qu'on evalue**.

Et surtout : **le score du candidat se decide ici.** Pas dans la rubric, pas au
durcissement. Une tache concue trop facile ne se rattrape par aucun outil en aval —
c'est la lecon la plus chere du corpus, et elle est chiffree en section 2.

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
de l'enonce.**

## 3. Le piege nomme, mecanique par mecanique

**Un pack en porte plusieurs.** La circularite est exigee a tous les niveaux, donc
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

## 7. Le niveau vise, et ses deux gates

Le niveau ne s'apprecie pas a l'oeil : il se **mesure par code** sur le fichier, et
deux gates le plafonnent. Il ne se confond pas avec le budget de discrimination — un
L1 bien concu discrimine mieux qu'un L3 qui n'est que volumineux.

**Gate 1 — la taille, mesuree sur le corpus.** Les planchers d'onglets qu'on lit
parfois (15 / 20 / 25) ne sont tenus par personne : mediane reelle **13 onglets en
L1 comme en L2**. Le compte d'onglets est un garde-fou, pas un discriminant.

Les bandes ci-dessous sont relevees sur **34 goldens rangees par slot**, plus le
pack d'ancrage du haut de l'echelle.

| Niveau | Onglets de calcul | Formules | Grille | Circularite |
|--------|-------------------|----------|--------|-------------|
| **L1** | **15 a 20** | ~1 300 et au-dela | annuelle ou trimestrielle | **obligatoire** |
| **L2** | **25 a 30** | ~3 200 et au-dela | annuelle ou trimestrielle | **obligatoire** |
| **L3** | **41 a 50** | **117 000 a 155 000** | **mensuelle, 145 colonnes et au-dela** | **obligatoire** |

> **Bandes fixees le 08/09/2026**, et elles sont AU-DESSUS de ce que le corpus
> livre : mediane reelle **13 onglets en L1 comme en L2**. Ce n'est donc pas une
> description, c'est une exigence — les packs existants ne la tiennent pas.
>
> **La circularite est exigee a TOUS les niveaux, et les formules doivent etre
> sophistiquees quel que soit le sujet.** L'ancienne lecture « facultative en L1 et
> L2 » etait un constat sur le corpus, pas une permission : elle ne vaut plus.

> **Decision du 08/09/2026 — l'echelle a ete comprimee.** Les anciens niveaux L4 et
> L5 disparaissent en tant qu'echelons : **L3 reprend leurs exigences.** Un pack
> slotte L3 se batit desormais au calibre de l'ancien « L4 au plafond » — 41 onglets
> de calcul, 117 349 formules, 404 colonnes et 300 iterations sur le pack de
> reference — avec le plafond de l'ancien L5, **50 onglets de calcul**, comme borne
> haute.
>
> Ce que disait l'echelle precedente est conserve ici pour memoire : L1 >= 15
> onglets, L2 >= 20, L3 >= 25, plafond L4 a 50 au-dela duquel le label basculait en
> L5, avec Mazadona = L2 et Seine = L4 comme points d'ancrage.

**Ce que les mesures apprennent, et qui vaut plus que les seuils.**

1. **L1 et L2 ne se distinguent pas par la taille** — meme mediane d'onglets. Ce qui
   les separe est la **densite** : x2,4 sur les formules. Meme squelette, plus de
   mecanique dedans.
2. **La marche vers L3 est un changement d'axe, pas un agrandissement.** La grille
   passe de ~20 colonnes a 145 et au-dela : c'est le **passage au mensuel**, et tout
   ce qui vit sur cet axe se multiplie avec lui.
3. **En L3 la circularite n'est plus optionnelle.** Elle etait armee sur 13 goldens
   de slot L3 sur 13, contre 9 sur 10 et 9 sur 11 en dessous.
4. **On monte en ajoutant des AXES, pas des onglets** : periodes x entites x trials.
   Le pack de reference porte 145 periodes, 48 partenaires et 512 tirages.

**Gate 2 — la circularite.** « Reelles » a un sens precis : ni les boucles inertes,
ni les composantes fortement connexes du graphe. Les trois tests de
`compter_boucles.py` font foi — isolement, cycle residuel, **amplitude** — et
`iterate="1"` doit etre reellement present dans `xl/workbook.xml`.

| Boucles reelles et independantes | Plafond |
|----------------------------------|---------|
| 0 | non conforme, ne depasse pas L1, et on le signale |
| 1 a 3 | L1 |
| au-dela | echelon a fixer |

> **A fixer, et ce ne sera pas par la mesure.** L'echelon de L2 n'a pas ete rebase.
> Repere : les deux packs batis au calibre haut — Toubkal et Ravenna — portent
> **huit** boucles reelles et independantes chacun.

> **Pourquoi l'echelon superieur n'est pas mesurable sur le fichier.** On a compte
> les circuits du graphe de dependances sur quinze goldens, cinq par slot. Le
> resultat ne suit pas le niveau du tout :
>
> ```
> L1   0 · 5 · 5 · 13 · 24        mediane  5
> L2   0 · 0 · 1 ·  5 · 18        mediane  1
> L3   0 · 24 · 72 · 121 · 239    mediane 72
> ```
>
> Un L1 peut porter 24 circuits, un L2 zero. C'est exactement ce que le piege 3
> annonce : **compter les composantes fortement connexes ne mesure rien d'utile,
> parce que dans un modele integre tout finit par se toucher.**
>
> Le compte qui compte est celui des boucles **nommees, debranchables et
> discriminantes** — celles qui passent les trois tests. Ce n'est donc pas une
> propriete qu'on lit sur un classeur fini : **c'est une decision de conception**,
> prise en phase 1 et inscrite dans la sortie de phase. L'echelon de L2 se fixe,
> il ne se mesure pas.


**La difficulte reste multi-dimensionnelle**, et c'est ce qui permet a deux modeles
de domaines etrangers d'atteindre le meme niveau : l'un charge la circularite, la
structure de financement et les controles ; l'autre la multiplicite d'entites, la
decomposition des drivers et la superposition temporelle, avec une dette presque
triviale. On decide quels axes ce domaine sait charger, et on les charge a fond.

**Un dernier avertissement de lecture.** Les dossiers `L1/`, `L2/`, `L3/` sont des
**slots**, et un pack peut etre charge au-dessus du sien : Toubkal l'assume, Ravenna
vise le calibre haut dans un slot L3. Les bandes decrivent la cible, pas une
garantie.

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

Neuf choses ecrites, validees avant de passer a la construction :

```
noyau dur             une phrase, testable
niveau                bande d'onglets tenue, et les boucles nommees une par une
prompt build          la graine developpee : deal, entites, grille, mecaniques,
                      carte des onglets, ordre de resolution, ancrages calibres.
                      Test : peut-on ecrire le generateur avec ca ?
budget                part du pool en transcription <= ~37 %
piege nomme           N mecaniques, N pieges nommes : bonne reponse / erreur
                      plausible / points qui tombent
rollout d'enonce      N passes, une par mecanique, resultats lus
frontieres            ce que la tache evalue, ce qu'elle laisse aux voisines
ancrages              valeurs, tolerances, nature [M]/[S]/[D], justifications
tests de declenchement  les bandes qui disent que la tache mord
```

Sans le noyau dur, les frontieres et les ancrages, la phase 2 construit a l'aveugle
et la phase 3 n'aura rien contre quoi se verifier. Sans le budget, le piege nomme et
le rollout d'enonce, la phase 5 decouvrira un score de 81 % sur un pack fini.

---

[Retour a la skill](../SKILL.md) | [Les pieges](pieges.md) | [Phase suivante : batir](02-batir.md)
