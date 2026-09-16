---
title: "Phase 2 - Batir le classeur"
description: "Les deux canaux d'acces au classeur, la chaine en six etapes de la calibration a l'Input_Sheet derivee, les invariants d'un modele livrable et la discipline de recalcul."
type: "reference"
status: "actif"
---

# Phase 2 — Batir

Le classeur n'est **jamais ecrit a la main**. Il est produit par un script, seule
facon de le refaire a l'identique quand un ancrage bouge — et un ancrage bouge
toujours.

## Les deux canaux, et pourquoi ils expliquent la moitie des pieges

Un classeur se joint de deux facons, qui ne repondent pas aux memes questions. **Se
tromper de canal ne produit aucune erreur : seulement des chiffres absents, ou des
chiffres perimes.**

| | Canal Python (`openpyxl`) | Canal Excel (COM) |
|---|---|---|
| Il lit | ce qui est **ecrit** dans les cellules | ce qu'Excel **calcule** |
| Excel doit tourner | non | oui |
| Vitesse | parcourt tout le classeur | rapide a l'unite, couteux en boucle |
| Pour | inventorier, comparer, verifier, ecrire | recalculer, valider, deboguer une formule |

**La limite qui commande tout le reste.** `openpyxl` ne calcule rien : quand il rend
la valeur d'une formule, il relit le cache qu'Excel a depose au dernier
enregistrement. Sur un fichier produit par un programme et jamais ouvert dans Excel,
ce cache est vide et tout ressort a `None` (piege 5). **Un chiffre recalcule ne
s'obtient que par le canal Excel.**

Trois regles d'ecriture, qui valent pour tout script de cette phase :

1. **Simuler avant d'ecrire.** Un script qui ecrit tourne en simulation par defaut :
   on lit le rapport, on le valide, et seulement ensuite on ecrit.
2. **Ne jamais ecrire par-dessus la source.** Une derivee se fabrique **a cote** de
   sa golden, jamais a sa place, et vers un chemin qui n'existe pas encore.
3. **Fermer Excel proprement.** Chaque objet COM libere, sinon les processus
   s'accumulent et le recalcul suivant lit un fichier verrouille.

## L'entree : le prompt build

**La phase 2 n'invente rien.** Elle implemente le **prompt build** ecrit en
[phase 1](01-concevoir.md) — le document qui porte le deal, les entites, la grille,
les mecaniques, la carte des onglets et les ancrages calibres.

C'est le sens de lecture a garder : **le prompt build construit la golden**, et le
prompt du pack en sera la silhouette, tiree en phase 4 du classeur recalcule.

Si `batir.py` doit prendre une decision de modelisation, c'est que le prompt build
est incomplet : on remonte le corriger plutot que de trancher ici. Une decision prise
dans le generateur n'est ecrite nulle part, et personne ne la retrouvera.

## La chaine en six etapes

Les trois premieres sont **specifiques au sujet** : elles s'ecrivent pour chaque
pack. C'est normal et ce n'est pas du gaspillage — c'est la partie qui porte le
metier. Les trois dernieres sont des controles, et elles ne se sautent pas.

### 1. `calibrer.py` — la resolution

Trouve les parametres qui font atteindre les ancrages, **sur une graine fixe**. C'est
ici que vivent les back-solves : quand l'enonce fixe une cible et non un taux, c'est
ce script qui resout le taux.

**Il tourne hors du classeur**, en Python. Resoudre dans Excel via des references
circulaires supplementaires ajouterait des boucles non voulues, et rendrait la
resolution invisible a la relecture.

La graine n'est pas un detail : sans elle, le generateur n'est pas deterministe et
l'etape « regenerer et differencier » de la phase 3 ne prouve plus rien.

Sa sortie est un jeu de parametres, ecrit dans un fichier, plus la verification que
chaque ancrage tombe dans sa tolerance. Le generateur ne resout rien : il consomme.

> Le fichier d'ancrages de la phase 1 est expose au reste de la chaine par un module
> a part, pour qu'**aucun autre script ne porte une valeur cible en dur**.

### 2. `batir.py` — l'ecriture

Ecrit le classeur, **un module par famille d'onglets**, depuis les parametres
calibres. Il ne prend **aucune** decision de modelisation : toutes ont ete prises
avant.

Il importe le module de format maison plutot que d'ecrire ses propres couleurs et
largeurs — sinon deux modeles divergent et le format cesse d'etre un contrat. Voir
[les contrats de format](contrats-format.md).

### 3. `caler.py` — l'aller-retour Excel

L'etape que la premiere version de cette phase ignorait, et sans laquelle rien ne
tombe juste : recalculer dans Excel, **caler les entrees residuelles sur les
ancrages**, et **figer les snapshots de circularite**.

Un modele circulaire ne converge pas au premier passage, et certaines entrees ne
peuvent etre resolues qu'une fois le classeur calcule. Le calage boucle jusqu'a ce
que les ancrages tiennent sur les valeurs **calculees par Excel**, pas sur celles
que Python croyait produire.

### 4. `tester.py` — les tests de declenchement

Passe sur les valeurs en cache **les tests de declenchement ecrits en phase 1**.

> Le script ne s'arrete pas quand les nombres bouclent. Il s'arrete quand la tache
> mord.

Un pack dont les ancrages tombent juste et dont aucun test ne mord est un pack
facile qui a l'air fini. C'est ici qu'on le decouvre, pas au rollout.

### 5. `outils/amplitude_boucles.py` — une boucle est-elle discriminante ?

```
python outils/amplitude_boucles.py "<classeur>" --rubric "<rubric.txt>"
```

**Cet outil est portable** : il ne sait rien du sujet. Il repere les interrupteurs
**a ce qu'ils VALENT** — 0 ou 1 — et non a un prefixe de nom, bascule chacun,
recalcule par le vrai Excel et **renote le classeur contre sa rubric**. L'amplitude
d'une boucle est le nombre de points qu'elle coute quand on la coupe.


C'est la seule question qui compte sur une circularite, et le test d'isolement n'y
repond pas. Un residu qui converge dit que la boucle **se ferme**, pas qu'elle
**deplace** quoi que ce soit.

Le script coupe chaque breaker, recalcule, et compare **un panier de valeurs
notees**.

> **Une boucle qui ne bouge aucune valeur au-dela de la tolerance de la rubric est
> decorative.**

C'est strictement plus fort que le test d'isolement du piege 3 : celui-la demande que
la boucle deplace *une* valeur, celui-ci qu'elle deplace une valeur **que la rubric
note**. Une boucle decorative gonfle le compte de circularites sans rien apporter au
budget de discrimination de la phase 1.

### 6. `recalculer_python.py` — le chemin de tete, rejoue ailleurs

Rejoue **en Python** le chemin de tete — revenu, EBITDA, dette nette, sortie,
multiple, TRI — et le diffe au classeur.

Il attrape le defaut qu'aucun recalcul sans erreur ne peut voir : **la formule qui
calcule autre chose que ce que son intitule annonce, avec un controle qui partage la
meme erreur et ferme donc a zero.** C'est la version phase 2 de la regle
d'independance qui gouverne la phase 3 : un controle ne vaut que s'il est independant
de ce qu'il controle.

## Les invariants

Ces regles valent pour tout pack, quel que soit le sujet. Elles sont verifiables, et
elles doivent l'etre a chaque build.

### Aucune valeur en dur hors de l'input sheet

Toute hypothese vit dans la feuille d'hypotheses, et **une seule fois**. Une valeur
recopiee dans une formule ailleurs est une hypothese fantome : le candidat ne peut
pas la connaitre, et elle ne bougera pas quand on changera l'original.

Verifiable : compter les litteraux numeriques hors de l'input sheet. Le compte doit
etre nul, aux exceptions structurelles pres (un `0` d'initialisation, un `1` de
normalisation) qui se justifient une par une. **Ventiler par valeur distincte** et
non par cellule : douze constantes reparties sur 4 000 cellules, c'est douze choses a
tracer, pas 4 000.

C'est la trouvaille la plus frequente des audits de reproductibilite : **la constante
posee sur un onglet de calcul, absente du prompt comme de l'input sheet.**

### Toute hypothese fournie doit etre consommee

Une hypothese qui figure dans l'input sheet et que le modele n'utilise jamais est un
leurre involontaire : le candidat va chercher ou la brancher, et perdre du temps.

Verifiable : `outils/inputs_morts.py`.

### L'iteration est armee dans le fichier

**Le modele EST circulaire** — c'est une exigence de tous les niveaux depuis le
08/09/2026, quel que soit le sujet. La question n'est donc pas de savoir s'il faut
armer l'iteration, mais de verifier qu'elle l'est.

Le calcul iteratif doit etre arme **dans le classeur**,
pas dans l'application de celui qui l'ouvre. Et le controle se refait **apres le
dernier enregistrement**, parce qu'Excel reecrit ce reglage (piege 4).

### Chaque boucle porte un interrupteur nomme

Une mecanique circulaire sans interrupteur ne peut ni etre testee, ni etre
diagnostiquee. Chaque boucle a le sien, plus un interrupteur general.

Verifiable, et **il faut les trois tests** :

```
python outils/compter_boucles.py "<classeur>"

  isolement : couper les autres, la mecanique tourne encore
  residuel  : tous coupes, 0 cellule auto-referente
  amplitude : coupee, elle deplace une valeur NOTEE au-dela de sa tolerance
```

Les deux premiers disent que la boucle existe (piege 3). Le troisieme dit qu'elle
sert.

> **Ce compteur a ete corrige le 09/09/2026, et il rendait un verdict faux.** Sur une
> golden dont toute la tache repose sur la circularite, il annoncait
> **« mecaniques circulaires reelles : 0 »** et une fuite de 49 cellules. Trois
> causes, toutes de la meme famille :
>
> - il cherchait les interrupteurs a un **libelle** commencant par « Breaker » : il
>   en trouvait **un** la ou le classeur en porte **six**. Un interrupteur se
>   reconnait a ce qu'il **vaut** — 0 ou 1 — comme dans `commutateurs.py` ;
> - il ne cherchait la citation que par **adresse avec dollars**, jamais par nom ni
>   sans dollars. Une formule qui ecrit `Brk_Master` echappait a la coupure, donc
>   « couper » ne coupait rien (piege 15) ;
> - il comptait deux fois le meme interrupteur — par libelle et par plage nommee —
>   ce qui faisait paraitre chaque exemplaire inerte, puisque couper « tous les
>   autres » coupait aussi son jumeau.
>
> Apres correction : fuite residuelle **49 -> 0**, verdict **0 -> 1**. Le compteur
> gouverne la gate de niveau : tant qu'il rendait zero, tout pack etait « non
> conforme, ne depasse pas L1 ».
>
> **Deux corrections de plus le 14/09/2026, sur Cobalt**, qui rendait « 0 » sur quatre
> boucles reelles :
>
> - **l'interrupteur general** cite dans chaque formule de boucle
>   (`IF(Brk_All*Brk_X=1,...)`) etait coupe avec « tous les autres » pendant l'isolement,
>   donc toutes les boucles tombaient. Il se reconnait desormais a ce qu'il coupe tous
>   les cycles a lui seul quand les autres n'en coupent qu'une partie, et il n'est plus
>   coupe pendant l'isolement ;
> - **la citation se cherchait sans borne** : `Input_Sheet!$E$10` reconnaissait
>   `$E$100` a `$E$109`, si bien que couper un interrupteur tranchait des formules
>   etrangeres a sa boucle.
>
> Cote generateur, une regle en sort : **isoler le terme de boucle dans sa propre
> cellule**. L'outil retire tous les arcs d'une formule qui cite l'interrupteur ; si cette
> formule porte aussi le chemin commun des autres boucles, couper la sienne les coupe
> toutes.

### Toute reponse dans un circuit est continue

Pas de palier, pas de saut sur seuil a l'interieur d'une boucle : le solveur
oscillerait (piege 8). Interpoler.

Nuance a ne pas rater : un `IF` dont le test ne lit que des masques, des constantes
ou des cellules **hors** du circuit est fige pendant l'iteration, donc parfaitement
legitime. Un detecteur qui ne fait pas la distinction condamne un classeur sain.

### Le classeur ne porte aucune trace de fabrication automatique

Une partie de ces traces ne se corrige pas en phase 5 : elle se **previent** ici,
parce qu'elle vient du generateur. Le code couleur s'applique tout seul quand on
importe le module de format ; un libelle s'ecrit en texte et jamais en formule ;
le groupement se retire avant d'enregistrer.

```
python outils/traces_ia.py "<classeur>"
```

Le controle appartient a la phase 5, mais le lancer a chaque build coute une
seconde et evite de decouvrir a la livraison qu'il faut regenerer.

### Les formules restent dans le sous-ensemble sur : `outils/formules_sures.py`

Le correcteur du corpus n'evalue pas toutes les fonctions Excel. Une formule qu'il
ne sait pas lire fait perdre les points de la cellule, meme juste.

## La discipline de recalcul

C'est le point ou l'on perd le plus de temps quand on l'oublie.

```
1. batir.py                 ecrit les formules, AUCUNE valeur en cache
2. recalculer.ps1           Excel calcule et enregistre le cache
3. lecture des valeurs      seulement maintenant
```

**Entre 1 et 3, il y a toujours 2.** Un classeur fraichement genere lu directement
rend `None` partout, et un outil qui lit `None` peut le rapporter comme un zero
(piege 5).

```
powershell -File outils/recalculer.ps1 -Chemin "<classeur>" -Iterations 200 -Ecart 1e-08
```

La sortie annonce le nombre d'erreurs. **Une seule erreur suffit a invalider le
build** : on ne passe pas a la suite avec des `#REF!` ou des `#DIV/0!` quelque part.

## L'`Input_Sheet` est l'onglet pivot, et l'extrait qu'on livre

Le classeur porte **un onglet `Input_Sheet` qui rassemble TOUS les inputs du
modele**. Tous les autres onglets le lisent ; aucun ne porte de valeur en dur.
C'est le pendant, cote construction, de l'invariant enonce plus haut — et les deux
sont la meme regle vue des deux bouts.

**Ce qu'on livre au candidat est cet onglet, extrait.** Mesure sur deux packs
reels : la golden porte 17 puis 48 onglets, l'input sheet livree en porte **2** —
l'intercalaire et `Input_Sheet`. Le candidat batit les 15 ou 46 autres de zero.

> **Il n'y a pas de « blank » dans ce corpus.** Un blank est un autre artefact,
> d'un autre contrat de livraison : la golden ENTIERE, formules effacees, chaque
> onglet, en-tete et libelle conserve, que le candidat remplit. C'est ce que decrit
> le piege 16, et cela ne s'applique pas ici. Ne pas confondre les deux :
> `fabriquer-blank.py` et `verifier-blank.py` servent l'autre corpus.

**Pourquoi l'extraction ne tient que si l'invariant tient.** Une constante posee sur
un onglet de calcul n'apparait pas dans l'extrait : le candidat ne peut pas la
connaitre, et rien ne le lui signale. C'est la trouvaille la plus frequente des
audits de reproductibilite, et elle se previent ici, pas en aval.

Deux proprietes a verifier sur l'extrait :

- **aucune formule qui pointe vers le MODELE.** Une input sheet porte
  legitimement des formules internes — 18 sur un pack, 50 sur un autre : des
  derivations d'hypotheses. Ce qui est interdit, c'est une formule qui atteint un
  onglet de calcul : elle donne une partie de la reponse.
- **aucun groupement** : l'input sheet se **degroupe** avant livraison. Un input
  sheet laisse groupe est l'un des signes qui trahissent immediatement une
  fabrication automatique, et il est oublie presque a chaque pack.

## Le format du classeur

Un modele qui a l'air bricole est refuse avant meme d'etre lu. Le contrat de forme
— polices, code couleur, unites, bandeaux, largeurs — vit dans
**[les contrats de format](contrats-format.md)**.

Le point le plus souvent rate : **le code couleur des cellules**. Une entree en dur
et une formule ne se presentent pas pareil, et c'est la premiere chose qu'un
relecteur financier regarde. Il s'applique tout seul quand le generateur importe le
module de format plutot que d'ecrire ses couleurs a la main.

**La mise en page n'est pas celle du pack precedent.** Le generateur lit la fiche de
mise en page decidee en phase 1 — colonne des libelles, debut des valeurs, unites,
page de garde, intercalaires, police, bandeaux, forme des blocs — **en un seul
endroit**, et ne pose aucun style ailleurs. Recopier le `gen_base.py` d'un voisin
recopie sa grille : c'est ainsi que quatre packs du lot RX se sont retrouves
identiques sur les huit axes de structure. Voir **[la mise en page](mise-en-page.md)**.

## La golden par iterations, et les ateliers avec l'auteur

Un generateur eloigne l'auteur du modele : il ne le voit qu'une fois fini. **La golden se
construit donc par iterations courtes**, chacune fermee par une mini-porte et un relais :

| Iteration | Ce qu'elle batit | Sa porte |
|-----------|------------------|----------|
| 0, le squelette | input sheet, carte des onglets, mise en page de la fiche | `porte.py 2 --iteration 0` : cache, iteration armee |
| 1 a n | une mecanique, `M1` puis `M2`... dans l'ordre de la conception | ancrages et boucles des mecaniques batties |
| finale | la golden complete | `porte.py 2` : la sortie de phase ci-dessous |

A chaque iteration ouverte, Claude **propose** au owner ce qui vaut un coup d'oeil — la
copie `build/iterations/GS itNN` comparee a la precedente montre exactement ce que la
mecanique a ajoute — **sans ouvrir la golden**, sauf s'il le demande. S'il la retouche,
`outils/atelier.py relire` liste ses modifications cellule par cellule, et **chacune est
reportee dans le generateur ou abandonnee, sur sa decision** (`atelier.py decider`). **Pas
d'iteration suivante sans relais `valide`.** Le protocole : [les portes](portes.md).

Deux regles ne se negocient pas : **le generateur reste la source de verite** (une
modification non reportee disparait au build suivant, et on le dit), et **on n'ecrit jamais
dans un classeur ouvert**. Le protocole complet : **[les ateliers](ateliers.md)**.

## Sortie de phase

```
circularite         prerequis bloquant : au moins le plancher du niveau, quels que
                    soient le sujet et la graine ; boucles nommees
recalcul            0 erreur
ancrages            chacun atteint, dans sa tolerance, sur les valeurs CALCULEES
graine              fixe, le build est reproductible a l'identique
tests declenchement N attendus, N qui mordent
boucles             N attendues, N en isolement, 0 cycle residuel,
                    et chacune deplace une valeur notee
chemin de tete      rejoue en Python, 0 divergence avec le classeur
valeurs en dur      0 hors input sheet, ventilees par valeur distincte
hypotheses mortes   0
input sheet         extraite, 0 formule vers le modele, 0 groupement
calcPr              iteration armee, relue APRES enregistrement
niveau              outils/niveau.py : NIVEAU TENU SUR LE FICHIER = niveau vise,
                    quel que soit le nombre d'onglets
ateliers            un par mecanique, chaque modification de l'auteur reportee
                    (0 ecart apres regeneration) ou abandonnee, sur sa decision
iterations          0 a n, chacune ouverte et relayee valide
porte               porte.py 2 pack.json : OUVERTE, puis relais 2 valide
```

Tant qu'une de ces lignes n'est pas verte **avec son compte**, la phase 3 est
prematuree : ecrire une rubric sur un classeur faux, c'est ecrire une rubric fausse.

---

[Retour a la skill](../SKILL.md) | [Les pieges](pieges.md) | [Phase suivante : certifier](03-certifier.md)
