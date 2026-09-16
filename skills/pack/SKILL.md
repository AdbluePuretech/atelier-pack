---
name: pack
description: Fabriquer de bout en bout un pack de tache d'evaluation financiere - prompt, input sheet, golden solution, rubric - le certifier, le noter et le passer au QA. Porte aussi l'AUDIT d'un classeur seul, quelle que soit sa provenance. A invoquer via /pack ou quand l'utilisateur dit "fabrique une tache", "construis un pack", "monte-moi une golden solution", "ecris la rubric", "fais tourner le QA", "on livre ce pack", mais AUSSI "audite ce modele", "ce classeur est-il sans erreur", "certifie la golden", "verifie le modele de fond en comble", "cherche les erreurs dans ce classeur", "fais un model audit", ou parle de concevoir une tache d'evaluation pour un lab ; et "juice", "juicer la rubric", "juice la rubric de <pack>" (protocole de juicing).
---

# Skill : Fabriquer un pack de tache d'evaluation

> **Premiere fois ?** Lire [le mode d'emploi](MODE-EMPLOI.md) : installation,
> prerequis, ce que chaque phase attend de vous, et comment les mises a jour
> arrivent. Dix minutes, une seule fois.

Un pack, c'est quatre documents qui doivent se tenir entre eux :

| Document | Ce qu'il fait |
|----------|---------------|
| **Prompt** | ce qu'on demande au modele evalue, et rien de plus - [son contrat](references/contrat-prompt.md) |
| **Input sheet** | les hypotheses qu'on lui fournit, toutes, et rien d'autre |
| **Golden solution** | le classeur de reference, dont les valeurs font foi |
| **Rubric** | les criteres notes, tires des valeurs de la golden - [son contrat](references/contrat-rubric.md) |

> **Le contrat de la rubric decrit une REVISION** — on recoit un pack complet et une
> liste de puces de changement, on applique, on garde tout le reste. Il sert donc
> aussi bien a reprendre un pack livre qu'a en ecrire un neuf ; les cinq phases
> ci-dessous s'arretent a la livraison et ne couvrent pas ce qui revient.

> **Un cinquieme document existe, et il ne se livre pas : le PROMPT BUILD.** On
> part d'une graine de quelques paragraphes, on la developpe et on la complexifie
> jusqu'a pouvoir ecrire le generateur dessus — c'est lui qui **construit la
> golden**. Le prompt du tableau ci-dessus en est la silhouette, tiree en phase 4
> du classeur recalcule : meme squelette, methode retiree. Les confondre coute la
> tache. Voir [la phase 1, section 5](references/01-concevoir.md).

La difficulte n'est pas de les produire. Elle est de **prouver qu'ils se tiennent** :
qu'un modele qui suit le prompt a la lettre, en n'ayant que l'input sheet, peut
atteindre les valeurs de la golden, et que la rubric mesure bien ce qu'il a fait.

## La regle qui gouverne tout le reste

**Un controle qui n'a rien lu rend vert.**

C'est le mode de defaillance central de ce travail, et il s'est produit quatre fois
sur le seul pack qui a servi a ecrire cette skill : un QA au vert dont trois
controles sur cinq n'avaient rien lu, un compteur de boucles qui en annoncait sept
quand trois etaient inertes, une batterie de controles aveugle sur 10 % de ses
lignes, un correcteur qui n'examinait aucun critere.

Donc, a chaque phase : **ne jamais accepter un vert sans lui demander ce qu'il a
compte**. Un controle doit rendre un nombre — de cellules lues, de criteres
examines, de lignes appariees — et ce nombre doit etre confronte a ce qu'on
attendait. Zero examine n'est pas zero defaut.

Les seize pieges, avec ce qui les revele :
**[les pieges de fabrication](references/pieges.md)**. Le lire avant de commencer,
pas apres avoir echoue.

Et de quoi demarrer un pack neuf : **[le catalogue des mecaniques
discriminantes](references/mecaniques-discriminantes.md)** — treize formes
d'auto-reference eprouvees, chacune avec le piege exact qu'un bon modele y tombera.

## Les cinq phases

Chacune se termine par un **chiffre**, pas par une impression. Une phase ne
commence pas tant que la precedente n'a pas rendu le sien.

**Chaque phase se ferme par une porte, puis un relais.** `outils/porte.py <phase>
pack.json` lance tous les controles de la phase et reste fermee tant qu'une ligne n'est
pas verte avec son compte. Porte ouverte, Claude s'arrete : il montre le tableau,
**propose** au owner ce qui vaut un coup d'oeil sans rien ouvrir, et attend `valide`,
`modifie` ou `refuse`. La phase suivante refuse de demarrer sans relais `valide`, et une
porte dont un fichier a change depuis est perimee. Nouveau pack : `porte.py init`. Le
protocole : **[les portes](references/portes.md)**.

### 1. Concevoir - [le detail](references/01-concevoir.md)

**Elle s'ouvre par un brainstorming avec l'auteur** — les pistes developpees une par
une, une question par message, la conception ecrite seulement sur ce qu'il retient — et
**la graine est un contrat** : chaque ajout se rattache a une de ses lignes, sinon il
n'entre pas, meme pour durcir.

Du sujet au noyau dur : ce qui rend la tache difficile a reproduire, les frontieres
a ne pas franchir, le niveau vise — **lu dans les onglets, jamais a leur nombre** : un L3
peut tenir en dix onglets denses. **C'est ici que le score du candidat se decide** —
la rubric ne mesure que ce que le prompt demande, elle ne rattrape pas une tache
concue trop facile. On y pose le **budget de discrimination** (au plus ~20 % du pool
derriere de la transcription, avec des **difficultes independantes** : jamais une
cascade ou une seule erreur emporte la rubric), le **piege nomme** de chaque mecanique, et le
**fichier d'ancrages** : les valeurs que la golden devra atteindre, decidees AVANT
de construire.

**Les boucles de circularite sont un prerequis, pas un axe a arbitrer.** Tout pack en
porte, a tout niveau, au moins le plancher de sa grille (L1 : 1, L2 : 4, L3 : 6), et
chacune est reelle : nommee, debranchable, et elle deplace une valeur notee. **Aucune
derogation** : ni parce que le sujet n'en porte pas d'evidente, ni parce que la graine
exclut les effets d'ordre fabriques. On cherche alors la boucle portee par une convention
des pieces - [comment la trouver](references/01-concevoir.md#quand-le-sujet-ne-porte-pas-de-boucle-evidente).

> **Sortie** : **porte 1 ouverte, relais 1 valide** — la conception au plan impose
> (noyau, budget, pieges, boucles au moins au plancher, fiche de mise en page),
> `ancrages.json` au format commun, chaque element rattache a la graine. Zero boucle :
> la porte reste fermee.

### 2. Batir - [le detail](references/02-batir.md)

Calibrer -> batir -> caler -> tester -> amplitude des boucles -> chemin de tete
rejoue. Le classeur n'est jamais ecrit a la main : il est **genere par un script sur
une graine fixe**, seule facon de le refaire a l'identique quand un ancrage bouge. Le
calage est l'etape qu'on oublie : les ancrages doivent tomber sur les valeurs que
**Excel calcule**, pas sur celles que Python croyait produire.

**La golden se construit par iterations** : le squelette (iteration 0), puis une
mecanique par iteration, chacune fermee par sa mini-porte (`porte.py 2 --iteration k`)
et son relais. **L'auteur y met la main quand il le veut** : Claude lui propose ce qui
vaut un coup d'oeil, et si le owner retouche la golden, chaque modification est relue,
puis reportee dans le generateur ou abandonnee, sur sa decision -
[les ateliers](references/ateliers.md).

> **Sortie** : **porte 2 ouverte, relais 2 valide** — les iterations 0 a n validees,
> `0 erreur` en cache, chaque ancrage atteint, les boucles au plancher, 0 hypothese
> morte, le niveau tenu, la mise en page aux standards IB et distincte du lot.

### 3. Certifier - [le detail](references/03-certifier.md)

La phase 2 s'arrete sur `0 erreur`. C'est une barre basse : une golden reelle
l'a franchie en portant 8 699 `IFERROR`, 51 plages `SUM` tronquees et dix
compteurs de violations cables a `=0`. Neuf etapes posent la barre haute - gel,
differences contre le generateur, convergence, circuits, integrite, identites
imposees, familles, sensibilite, mutation.

```
python outils/auditer_tout.py "<golden>" --sortie audit/ --regenere "<regen>" --avec-excel
```

**Cette phase s'utilise seule**, sur n'importe quel classeur : le rendu d'un
candidat, un modele de production, une version d'archive. On entre directement
ici sans passer par les phases 1 et 2.

> **Sortie** : le taux de couverture, et un issues log ou chaque etape non
> lancee est inscrite comme travail non fait, jamais comme resultat favorable. Dans un
> pack : **porte 3 ouverte** — couverture ≥ 95 % sur la golden actuelle, aucune etape non
> faite — **et relais 3 valide**.

### 4. Enoncer et noter - [le detail](references/04-noter.md)

Deux documents, dans cet ordre. **Le prompt** se termine ici — son ossature vient de
la phase 1, ses conventions et ses sorties de la golden recalculee ; il tient en
**sept pages** et porte son bloc `Xlsx Output` / `Formatting Requirements`, present
dans 45 prompts livres sur 45. Puis **la rubric**, ecrite depuis les valeurs du
classeur recalcule, jamais de memoire, et retournee contre la golden elle-meme.

Le contrat du prompt, releve sur le corpus : [ses neuf blocs et ses six
regles](references/contrat-prompt.md).

> **Sortie** : **porte 4 ouverte, relais 4 valide** — `verifier_prompt.py` et
> `verifier_rubric.py` sans echec, la golden marque **100 %** de sa propre rubric,
> **chaque boucle coupee fait tomber au moins un critere** (`amplitude_boucles.py`), 0
> orpheline entre prompt et rubric. En dessous de 100 %, c'est la rubric qui est
> fausse, pas le classeur.

### 5. Verifier - [le detail](references/05-verifier.md)

Le QA du pack, les questions qu'un evaluateur posera, et le **rollout** : simuler un
candidat credible et mesurer ce qu'il obtient.

> **Sortie** : **porte 5 ouverte, relais 5 valide** — le QA au vert avec ses comptes, et
> la feuille de score de l'AI Output, rendue sur claude.ai contre la rubric actuelle, dans
> la cible.

### Juicer une rubric - [le protocole](references/juicer.md)

**Quand Amir demande de « juicer » une rubric**, appliquer son protocole mot pour mot : la golden
re-note exactement 100 %, un AI Output de modele frontiere tombe entre 20 et 35 % (plafond 40 %),
par la structure (points de routine retires, gates a +0 sur les mecaniques cles, keystones,
penalites de raccourci) et sous des garde-fous d'equite bloquants. Deux feuilles de score ligne a
ligne et une note d'equite sont livrees avec la rubric revisee.

> **Sortie** : **porte juicing ouverte** — golden a 100 %, adverse entre 20 et 40 %, chaque
> gate et keystone justifiee dans la note d'equite.

## Ce que cette skill ne decidera pas

Elle pose les questions au bon moment ; elle ne tranche pas a votre place :

- quelle mecanique appartient a cette tache et laquelle appartient a une tache voisine
- si le score de rollout obtenu est acceptable, ou s'il faut durcir
- si un defaut trouve tard se corrige ou se documente

Ces arbitrages sont le travail. Le reste est de l'outillage.

## Les outils

Une quarantaine d'outils portables vivent dans [`outils/`](outils/README.md) : ceux du
pack, les quatorze du moteur d'audit de la phase 3, et `porte.py` avec ses tests. Ils ne savent rien
du sujet - ils marchent sur n'importe quel pack, et pour ceux de l'audit, sur
n'importe quel classeur. Les scripts qui **construisent**
(ancrages, calibrateur, generateur) sont au contraire a ecrire pour chaque pack —
c'est normal, le sujet change a chaque fois.

## Ce qu'il faut avoir sous la main

- **Python** avec `openpyxl`, et **Excel** installe (le recalcul passe par COM).
- **LibreOffice**, pour le controle de parite. Facultatif mais recommande.
- **Les deux documents d'exemple du corpus** — un prompt et une rubric deja
  acceptes — deposes dans [`gabarits/`](gabarits/). Sans eux, le format ne peut pas
  etre repris, et un format reconstitue de memoire se voit immediatement. Voir
  [les contrats de format](references/contrats-format.md).
- **La mise en page des packs deja livres du lot** : chaque pack prend la sienne,
  grille, architecture, typographie et documents compris, et ne double aucun voisin.
  Voir [la mise en page](references/mise-en-page.md).

---

Cette skill est **auto-portante** : le dossier entier se copie dans les skills d'une
autre machine ou d'un autre compte et fonctionne tel quel, sans le reste du repo.
