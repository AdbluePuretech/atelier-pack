---
title: "Mode d'emploi de l'atelier de packs"
description: "Installer, fabriquer un premier pack, et comprendre ce que la skill attend de vous."
type: "reference"
status: "actif"
---

# Mode d'emploi

Ce document s'adresse a quelqu'un qui n'a jamais fabrique de pack. Il se lit en dix
minutes, une seule fois.

## Ce que vous allez produire

Un **pack** est un jeu de quatre documents destines a evaluer un modele d'IA sur de
la modelisation financiere :

| Document | Ce que c'est |
|----------|--------------|
| **Prompt** | l'enonce donne au modele evalue |
| **Input sheet** | le classeur d'hypotheses qu'on lui fournit |
| **Golden solution** | le classeur de reference, celui qui a raison |
| **Rubric** | la grille de notation, tiree des valeurs de la golden |

Le modele evalue recoit le prompt et l'input sheet. Il doit produire un classeur.
La rubric mesure l'ecart entre son classeur et la golden.

**Trois documents a avoir sous la main**, parce qu'ils font foi : le
[contrat du prompt](references/contrat-prompt.md), le
[contrat de la rubric](references/contrat-rubric.md), et le
[catalogue des mecaniques discriminantes](references/mecaniques-discriminantes.md).

**Ce qui rend l'exercice difficile** n'est pas de produire ces quatre documents.
C'est de prouver qu'ils sont coherents entre eux — et surtout, de ne pas se laisser
rassurer par des controles qui ne controlent rien. C'est tout l'objet de cette
skill.

---

## 1. Installer

### Ce qu'il faut sur la machine

| | Pourquoi | Obligatoire |
|---|---|---|
| **Python** avec `openpyxl` | lire et ecrire les classeurs | oui |
| **Microsoft Excel** | recalculer (rien d'autre ne sait le faire) | oui |
| **LibreOffice** | le controle de parite | recommande |

```
pip install openpyxl
```

Excel est indispensable et n'est remplacable par rien : c'est le seul moteur qui
calcule reellement les formules et ecrit le resultat dans le fichier. Sans lui, tout
classeur produit est vide de valeurs.

### Installer la skill

Si vous l'avez recue en dossier : le deposer dans `.claude/skills/` de votre projet,
ou dans `~/.claude/skills/` pour l'avoir partout.

Si elle est distribuee en plugin — le cas normal, parce que **les mises a jour
arrivent alors toutes seules** :

```
/plugin marketplace add <le depot que votre correspondant vous indique>
/plugin install pack
```

Voir [Les mises a jour](#5-les-mises-a-jour) plus bas.

### Deposer les deux gabarits

**C'est l'etape qu'on oublie, et sans elle rien ne marche.**

Il faut deux documents `.docx`, et **l'outil les attend a un nom precis** :

```
Rubric - Ostrom.docx           le profil « rubric »  : Title, un Heading1 par section
Prompt - Project_Madrid.docx   le profil « prompt »  : titre gras 16, paragraphe d'attaque
```

`ostrom` et `madrid` ne sont pas deux packs au choix : ce sont **deux profils de
mise en forme** codes dans l'outil, chacun lie a la structure de styles de ce
document-la. Renommer la rubric d'un autre pack ne marche pas.

Ils ne sont pas fournis avec la skill — ce sont des documents du client.
Demandez-les a la personne qui vous a transmis la skill.

**Deux facons de les brancher, et la seconde est preferable :**

```
gabarits/                          y copier les deux fichiers
PACK_GABARITS=<dossier d'exemples> ou pointer la ou ils vivent deja
```

La variable evite un doublon qui divergera de la source. Si le corpus range ses
documents d'exemple dans un dossier a lui, pointer dessus et ne rien copier.

Pourquoi c'est indispensable : le format de sortie ne s'imite pas, il se **reprend**
depuis le document d'exemple. Un format reconstitue de memoire se voit
immediatement, et les outils qui lisent ces documents par leurs styles deviennent
aveugles.

---

## 2. Fabriquer un premier pack

Ouvrez une session et dites simplement ce que vous voulez faire :

```
/pack
```

ou, plus directement :

> *Je veux monter une tache sur <votre sujet>.*

La skill enchaine cinq phases. **Chacune s'arrete et vous demande de valider avant
de continuer.** C'est voulu : les decisions qui comptent sont les votres.

**Chaque phase se ferme par une porte.** Une commande lance tous ses controles et reste
fermee tant qu'une ligne n'est pas verte avec son compte. Porte ouverte, la skill vous
montre le tableau, vous **propose** ce qui vaut un coup d'oeil — sans rien ouvrir, sauf
si vous le demandez — et attend votre decision : `valide`, `modifie` ou `refuse`. Sans
votre `valide`, la phase suivante refuse de demarrer ; et si un fichier change apres coup,
la porte devient perimee et se repasse. Le dossier du pack s'equipe au depart avec
`porte.py init`. Voir [les portes](references/portes.md).

### Phase 1 — Concevoir

On cherche le **noyau dur** : la mecanique precise qui separera un bon modele d'un
modele moyen. C'est presque toujours une **resolution** — quelque chose que l'enonce
ne donne pas et qu'il faut deduire — jamais un simple calcul.

On pose aussi les **ancrages** : les valeurs que la golden devra atteindre, decidees
*avant* de construire. Sans eux, on finit toujours par se convaincre que les valeurs
qui sortent sont les bonnes.

**Avant d'ecrire, on en parle.** La skill ne vous rend pas une conception toute faite :
elle developpe les pistes avec vous, une question a la fois, et n'ecrit que ce que vous
retenez. Et **la description de tache qu'on lui donne est un contrat** : rien n'y est
ajoute qui ne se rattache a une de ses lignes.

On y decide aussi **le budget de discrimination** : quelle part du pool de points
vit derriere de la simple transcription. Au-dela d'environ 20 %, la tache passera
au-dessus du seuil quoi qu'on fasse ensuite — un modele frontiere rend la
complexite mecanique a 95 %. Et les difficultes restent **independantes** : une seule
erreur ne doit jamais faire tomber toute la rubric.

**Le niveau se decide ici, et il ne se compte pas en onglets.** Un L3 peut tenir en
dix onglets si chacun porte une difficulte et une granularite tres elevees. Il se lit
sur cinq axes : les **decisions derivees** que le candidat doit resoudre (le seul axe
qui a suivi le score), les **boucles reelles**, la **granularite** (des lignes
atomiques qui portent chacune leurs propres termes), la **densite logique** par onglet
et la **sophistication** des formules. Les trois derniers se mesurent sur le fichier
avec `outils/niveau.py`. Les **boucles de circularite sont un prerequis a tous les
niveaux** : sans boucle reelle, pas de construction, et aucune derogation, meme quand la
graine exclut les effets d'ordre fabriques. La grille :
[le niveau vise](references/01-concevoir.md).

**On choisit trois ou quatre mecaniques, de familles differentes** — le
[catalogue](references/mecaniques-discriminantes.md) en propose treize, chacune avec
son piege. Quatre mecaniques de la meme famille testent une seule competence quatre
fois.

Puis, pour **chacune**, deux choses :

- **le piege nomme** — l'erreur exacte qu'un bon modele fera, en une phrase. Si on
  ne sait pas l'ecrire, la mecanique ne discrimine pas ;
- **une passe de rollout d'enonce** — cinq minutes : on redige le seul paragraphe
  qui enonce la mecanique, on y joint ses hypotheses, et on demande le nombre a un
  modele frontiere. S'il le sort juste, on remplace la mecanique **maintenant**.

C'est le test le plus rentable de toute la chaine. Un pack reel a ete fini, passe au
QA et note **81 %** faute de l'avoir fait : tout etait a redurcir.

> **Ce qu'on vous demandera** : le sujet, ce que la tache doit evaluer, le niveau
> vise, et le score que devrait obtenir un candidat serieux.

> **Fin de phase** : porte 1 ouverte — la conception au plan impose, les ancrages au
> format commun — et votre relais `valide`.

### Phase 2 — Batir

Trois scripts sont ecrits pour votre pack : les ancrages, un calibrateur qui resout
les parametres, et un generateur qui ecrit le classeur.

**Le classeur n'est jamais ecrit a la main.** Il est genere, parce qu'un ancrage
finit toujours par bouger et qu'il faut pouvoir tout refaire a l'identique.

**La golden se construit par iterations** : le squelette, puis une mecanique a la fois,
chacune fermee par sa petite porte et votre relais. **Vous y mettez la main quand vous
voulez.** A chaque iteration, la skill vous dit ce qui vaut un coup d'oeil et ce que la
mecanique a ajoute, et vous propose deux ou trois essais — sans ouvrir Excel, sauf si vous
le demandez. Modifiez ce que vous voulez, enregistrez, fermez, dites « fait » : chacune de
vos modifications vous est relue, et vous decidez si elle entre dans le generateur ou si
c'etait un essai. Voir [les ateliers](references/ateliers.md).

> **Fin de phase** : porte 2 ouverte — chaque iteration validee, `0 erreur`, chaque
> ancrage atteint, les boucles au plancher, le niveau tenu — et votre relais `valide`.

### Phase 3 — Certifier

`0 erreur au recalcul` est une barre basse : une golden reelle l'a franchie en
portant 8 699 `IFERROR`, 51 plages `SUM` tronquees et dix compteurs de violations
cables a `=0`. Neuf etapes posent la barre haute — gel de version, differences
contre le generateur, convergence, circuits, integrite, identites imposees,
familles de formules, sensibilite, mutation.

Cette phase **s'utilise aussi seule**, sur n'importe quel classeur qu'on n'a pas
fabrique.

> **Fin de phase** : un taux de couverture, et un issues log ou chaque etape non
> lancee est inscrite comme travail non fait — jamais comme resultat favorable. Dans un
> pack : porte 3 ouverte (couverture ≥ 95 %) et votre relais `valide`.

### Phase 4 — Enoncer et noter

**Deux documents sortent d'ici, dans cet ordre** : le prompt fixe ce qu'on demande,
la rubric mesure ce qui a ete demande. Les ecrire separement fabrique les orphelines
que la tracabilite ira trouver en phase 5.

Le prompt tient en **sept pages** et porte son bloc `Xlsx Output` /
`Formatting Requirements` — present dans 45 prompts livres sur 45, et celui qu'on
oublie. Il ne contient **aucune formule** : il dit quoi produire, jamais comment.

La rubric est ecrite **depuis les valeurs du classeur recalcule**, jamais de
memoire : une valeur recopiee sera fausse a la troisieme decimale et fera perdre des
points a une copie juste.

Puis on retourne la rubric contre la golden elle-meme.

> Les deux documents ont un contrat ecrit, et **des controles qui le verifient** :
> [le contrat du prompt](references/contrat-prompt.md) et
> [le contrat de la rubric](references/contrat-rubric.md).

> **Fin de phase** : porte 4 ouverte — `verifier_prompt.py` et `verifier_rubric.py` sans
> echec, la golden a **100 %** de sa propre rubric, chaque boucle notee — et votre relais
> `valide`. En dessous de 100 %, ce n'est pas le classeur qui est faux, c'est la rubric.

### Phase 5 — Verifier

Cinq controles automatiques, quatre questions a se poser, et le **rollout** : on
fabrique un candidat credible et on mesure ce qu'il obtient. C'est le seul moyen de
savoir si la tache est reellement difficile, ou seulement mal ecrite.

> **Fin de phase** : porte 5 ouverte — les controles au vert **avec leurs comptes**, et la
> feuille de score de l'AI Output, rendue sur claude.ai, dans la cible — et votre relais
> `valide`.

---

## 3. La seule chose a retenir

**Un controle qui n'a rien lu rend vert.**

Sur le pack qui a servi a ecrire cette skill, c'est arrive quatre fois : un QA au
vert dont trois controles sur cinq n'avaient rien lu, un compteur de boucles qui en
annoncait sept quand trois etaient mortes, une batterie aveugle sur 10 % de ses
lignes, un correcteur qui n'examinait aucun critere.

Donc, quand un outil vous annonce `0` :

> **demandez-lui ce qu'il a compte.**

`0 divergence sur 84 216 cellules` est un resultat. `0 divergence` tout court n'en
est pas un — ca peut vouloir dire qu'il n'a rien regarde.

Tous les outils de cette skill annoncent leur compte. Lisez-le.

---

## 4. Quand ca ne marche pas

| Symptome | Cause la plus frequente |
|----------|--------------------------|
| Toutes les valeurs lues valent `None` | le classeur n'a pas ete recalcule par Excel apres generation |
| Le classeur affiche des `#REF!` partout | une feuille a ete renommee apres coup |
| Le calcul ne converge pas | une reponse a paliers dans une boucle : il faut l'interpoler |
| Un controle ne ferme jamais, d'un ecart minuscule | deux mesures comparees sur des bases differentes (jours contre annees, par exemple) |
| Le document produit ne ressemble pas au gabarit | le format a ete imite au lieu d'etre repris depuis le `.docx` d'exemple |
| Le correcteur n'examine aucun critere | les titres de la rubric sont en gras au lieu d'etre un style de titre |

Le detail de chacun, avec ce qui le revele :
**[les seize pieges](references/pieges.md)**. C'est le document le plus utile du
lot ; il se lit avant de commencer, pas apres avoir echoue.

---

## 5. Les mises a jour

Si la skill a ete installee **en plugin**, les ameliorations arrivent par le meme
canal, sans rien recopier a la main :

```
/plugin                  gerer les plugins installes, et les mettre a jour
```

Le plugin est servi depuis un depot Git. Quand la personne qui le maintient y
publie une version, votre commande de mise a jour la recupere — nouveaux pieges
documentes, outils corriges, phases affinees.

**Ce qui n'est pas mis a jour automatiquement** : les deux gabarits `.docx` que vous
avez deposes dans `gabarits/`. Ils vous appartiennent, la skill n'y touche pas.

Si la skill a ete installee **en copiant un dossier**, il n'y a pas de mise a jour
automatique : il faut redemander le dossier. C'est la raison pour laquelle
l'installation en plugin est preferable.

---

## 6. Ce que la skill ne fera pas a votre place

- choisir le sujet, et verifier qu'il ne double pas une tache existante
- decider si le score obtenu au rollout est acceptable
- trancher si un defaut trouve tard se corrige ou se documente

Ces arbitrages sont le travail reel. La skill les pose au bon moment et vous donne
les chiffres pour decider ; elle ne decide pas.

---

[La skill](SKILL.md) | [Les seize pieges](references/pieges.md) | [Les outils](outils/README.md)
