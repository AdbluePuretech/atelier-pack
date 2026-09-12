---
title: "Phase 4 - Enoncer et noter : le prompt, la rubric, et l autotest"
description: "Criteres atomiques tires des valeurs recalculees, pool et poids, gates et penalites armees, le protocole de notation, et l'autotest a 100 %."
type: "reference"
status: "actif"
---

# Phase 4 — Enoncer et noter

Deux documents sortent d'ici, et **dans cet ordre** : le prompt fixe ce qu'on
demande, la rubric mesure ce qui a ete demande. Les ecrire separement fabrique
exactement les orphelines que la tracabilite de la phase 5 ira trouver.

## Le prompt du pack : le tirer du build

**Ce n'est pas le prompt build.** Celui-la a servi a construire la golden et ne sort
jamais du dossier de travail. Ce qu'on ecrit ici en est la **silhouette** : meme
squelette — la carte des onglets, les lignes de sortie exigees — **chair retiree**.
Ce qui disparait est la methode : comment la valeur se calcule, quel parametre a ete
resolu, contre quelle cible.

**Son test d'acceptation** n'est pas « pas de formules, sept pages » — ce sont des
contraintes de forme. C'est celui-ci :

> **Un analyst competent doit pouvoir reproduire le modele avec ce prompt et l'input
> sheet, et rien d'autre.**

C'est ce document qui genere l'**AI Output**, donc c'est lui, et lui seul, qui porte
le seuil du corpus. Le prompt build n'est note par personne.

Son ossature — la carte des onglets, les mecaniques annoncees — a ete posee en
phase 1, parce que c'est elle que le generateur implemente. Ce qui se termine ici,
c'est tout ce qui ne pouvait pas s'ecrire avant la golden recalculee : les
conventions d'affichage reellement employees, le regime de calcul reellement arme,
et la liste des sorties telle que le classeur la porte.

Le squelette en neuf blocs et les six regles : **[le contrat du
prompt](contrat-prompt.md)**. Trois d'entre elles se ratent souvent :

- **au plus sept pages** — mediane du corpus 6,5 ;
- **le bloc `Xlsx Output` / `Formatting Requirements`**, present dans 45 prompts
  sur 45, et celui qu'on oublie en ecrivant un pack neuf ;
- **aucune formule** : le prompt dit quoi produire, jamais comment.

```
python outils/verifier_prompt.py "Prompt - <Pack>.docx"
```

> **Sortie** : `controles en echec : 0`. C'est la porte du prompt, et elle se
> franchit avant d'ecrire une ligne de rubric — une rubric ecrite sur un enonce
> qui bougera encore est une rubric a refaire.

## La rubric

La rubric n'est pas un resume du prompt. C'est **l'instrument de mesure** : chaque
ligne est un test que la copie passe ou rate.

**Le lecteur vise est un VP, un Director ou un Executive Director**, pas un analyste
junior. La rubric doit etre assez complexe et assez juste pour saturer a ce
niveau-la.

> **Les regles d'ecriture sont contractuelles** et vivent dans
> **[le contrat de la rubric](contrat-rubric.md)** : criteres autoportants,
> ponderation et bande du `+1`, constantes en configuration, gates, penalites,
> couverture du formatting, et les deux seuls changements que le prompt a le droit
> de recevoir. Ce qui suit en donne la logique ; **le contrat fait foi.**

## La regle qui prime

**Chaque valeur de la rubric est lue dans le classeur recalcule, jamais ecrite de
memoire.**

Une valeur recopiee depuis une note, un message ou un calcul mental sera fausse a la
troisieme decimale, et fera perdre des points a une copie juste. La rubric se
**genere** depuis le classeur, ou se verifie contre lui ligne a ligne.

## Un critere

```
[+2] 08. Pocket_Price_Waterfall — Pocket price, F01 · T1 · Band A — FY0 — 0.526 (EUR per unit)
```

Quatre parties, dans cet ordre : **le poids**, **la feuille**, **le poste et la
periode**, **la valeur attendue avec son unite**.

Les proprietes qui comptent :

- **Atomique** : une valeur par ligne. Pas « les prix de poche sont corrects ».
- **Autoportant** : la feuille, le poste et la periode sont nommes en toutes lettres.
  Un critere se lit seul, sans renvoi a un autre (piege 13).
- **Tronque a la valeur** : pas de formule, pas de reference de cellule, pas de
  commentaire de methode. On note un resultat, pas un chemin.
- **Teste** : soit le test par defaut, soit un test enonce dans la ligne.

## Les tests

Un test par defaut, enonce **une fois** en tete de rubric et jamais repete :

> une valeur passe si elle est a moins de 1 % relatif de la valeur montree, signe
> compris.

Et des tests explicites quand le defaut ne convient pas :

| Cas | Test a ecrire |
|-----|---------------|
| Un taux resolu | `pass if within ±0.0005` |
| Un interrupteur, un compte | `pass if exactly 2` |
| Un bouclage | `pass if exactly 0 in all ten periods` |
| Un point de pourcentage | `pass if within ±0.05pp` |

**La tolerance se choisit sur la grandeur, pas sur le confort.** Un taux a quatre
decimales tolere ±0,0005 ; le tolerer a ±1 % relatif reviendrait a accepter une
erreur de methode.

## Le pool, les poids

Le pool total et sa repartition dependent du corpus : **regarder le document
d'exemple**, ne pas inventer. Les valeurs observees sur un corpus reel : **200 points
au total**, penalites **plafonnees a 20 % du pool**. Ce qui est stable :

- Les poids sont des entiers, de 1 a 4.
- **+4** un resultat integrateur de haut niveau ; **+3** une tete de chaine ou une
  gate ; **+2** un ancrage significatif ; **+1** un membre par periode, un
  sous-composant, un atome de forme.
- **La golden doit re-marquer exactement 100 %** du pool positif.

## Les gates

Une **gate** est un critere qui teste une condition de construction, pas une valeur,
et qui **garde sa section** : si la construction rate la gate, toute la section
tombe a zero.

Elle sert a empecher qu'un candidat obtienne les points d'une section en ayant fait
autre chose que ce qui etait demande — atteindre la bonne valeur par une mauvaise
methode.

Une gate se redige comme une **condition verifiable**, pas comme une intention :

> *le prix de liste livre porte le tarif du cas 2, dans lequel l'augmentation
> concedee aux trois comptes en litige est etendue par la clause de la nation la
> plus favorisee au reste du livre T1 ; l'augmentation ne s'applique qu'a partir de
> FY1 tandis que la derive tarifaire s'applique a chaque periode.*

**Les gates de propagation** sont un cas particulier utile : au lieu de tester une
propriete interne, elles testent l'accord avec une section amont. Elles disent : *un
chassis juste sur un chiffre d'affaires faux n'a pas fait la tache.*

## Les penalites

Une section de penalites sanctionne les erreurs de methode qui **atterrissent quand
meme dans la tolerance**. Sans elles, un candidat peut commettre une faute franche
et marquer les points.

Trois proprietes obligatoires :

- **Armable** : la penalite doit nommer une erreur que la gate de sa section ne
  teste pas. Une penalite qu'aucun build ne peut declencher est du remplissage.

  **La carve-out de gate est prescrite, et c'est son usage aveugle qui tue.** Une
  penalite **qui recouvre une gate** doit le dire en toutes lettres — *« not charged
  if the `<nom de section>` gate already scored 0 »*, en mots et jamais par un
  identifiant — pour ne pas facturer deux fois la meme erreur. Mais sur un pack reel,
  **les sept** penalites la portaient, y compris celles dont l'erreur ne fait pas
  tomber la gate : toutes inertes, plafond inatteignable par construction.

  Le controle qui tranche, dans les deux cas : pour chaque penalite, exhiber **un
  build qui la declenche**. Une penalite dont on ne sait pas construire le
  declencheur n'est pas armee.
- **Une seule fois** : elle tire au plus une fois, quel que soit le nombre de
  cellules touchees.
- **Plafonnee** : un plafond global, exprime en part du pool positif, empeche qu'une
  copie serieuse tombe a zero sur une erreur unique.

## Les deux sorties de phase

C'est le controle qui donne son sens a tout le reste.

```
python outils/noter.py "<golden>" --rubric "<rubric.txt>"

  VALEUR : 152 / 152 points  (100.0%)
```

**La golden doit marquer 100 % de sa propre rubric.** En dessous, ce n'est pas le
classeur qui a un probleme : c'est la rubric qui nomme une mauvaise cellule, arrondit
mal, ou pose une tolerance impossible.

**Ce que cet autotest teste vraiment n'est pas l'egalite des nombres** — elle est
acquise, puisque la rubric est generee depuis la golden. C'est que **chaque critere
soit localisable et non ambigu**. Les deux defauts sortis du premier passage sur un
pack reel n'auraient jamais fait echouer un controle du classeur :

| Le defaut | Ce qu'il coute |
|---|---|
| une colonne de periode **posee en dur et decalee d'un cran** — le critere porte la valeur de FY0 sous le nom de FY1 | fait echouer un candidat juste |
| un critere « point-in-time » sur une feuille-registre de quinze colonnes, ou **rien ne dit laquelle lire** | fait diverger deux correcteurs |

Et le corollaire, souvent oublie : un critere qui ressort **NON RESOLU** est aussi
grave qu'un critere en echec. Il veut dire que le correcteur n'a pas trouve la ligne
— donc qu'un candidat ne la trouvera pas non plus.

## Le protocole de notation

Ecrire la rubric et **noter avec** sont deux gestes, et le second a ses regles. Elles
valent aussi bien pour l'autotest que pour le rollout de la phase 5.

- **Noter sur les valeurs en cache**, `data_only=True`, **sans recalculer**. Le
  classeur note ne doit pas bouger pendant qu'on le note.
- **Le calcul iteratif doit etre arme AVANT l'ouverture** — typiquement 300 a 1000
  iterations, ecart maximal `1e-07` a `1e-09`. Ouvert sans cela, Excel signale les
  references circulaires et **met les cellules auto-referentes a zero** : on note
  alors un classeur qu'on vient de casser.
- **Grader critere par critere, strictement, sans accorder le benefice du doute.** Un
  correcteur indulgent ne mesure rien : il rend le pack incapable de discriminer, ce
  que la phase 1 avait justement cherche a eviter.
- Et la consigne qui fait la difference : **« sans utiliser ta memoire ».** On note
  ce que le fichier contient, pas ce qu'on croit y avoir mis. C'est la meme regle
  qu'en tete de phase, vue depuis l'autre bout.

## Le document

**Le format de sortie de la rubric depend du corpus, et il a change.** Mesure sur
un corpus reel, sans aucun melange :

| Environnements | Format de la rubric livree |
|---|---|
| les plus anciens | `.docx` — 26 packs |
| les plus recents | **`.json`** — 19 packs |

**Relever le format du corpus servi avant d'ecrire.** Une rubric `.docx` livree la
ou le loader attend du `.json` est rejetee sans que le contenu soit regarde, et la
conversion depuis un gabarit Word ne s'applique qu'a la premiere moitie du tableau.

Dans les deux cas la source reste le texte : un `.docx` comme un `.json` n'est ni
diffable ni greppable a la main, et le document est un artefact de livraison
(piege 12).

> **`txt_vers_docx.py` ne sert qu'aux corpus qui livrent en Word.** Il part d'un
> gabarit `.docx` et en copie toutes les parties — styles, numerotation, theme,
> table de polices. Sur un corpus qui livre sa rubric en `.json`, il n'a rien a
> faire : c'est le `.docx` **source** qui reste l'artefact faisant foi, et le
> `.json` en est derive.

Quand la sortie est un `.docx` :

```
python outils/txt_vers_docx.py "Rubric - X.txt" "Rubric - X.docx" --gabarit <nom>
```

Le format se **reprend** du gabarit, il ne s'imite pas (piege 11). Voir
**[les contrats de format](contrats-format.md)**.

---

[Retour a la skill](../SKILL.md) | [Les pieges](pieges.md) | [Phase suivante : verifier](05-verifier.md)
