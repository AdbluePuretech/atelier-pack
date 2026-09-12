---
title: "Les pieges de fabrication d'un pack"
description: "Les seize facons dont un pack passe au vert en etant faux, et ce qui les revele."
type: "reference"
status: "actif"
---

# Les pieges de fabrication d'un pack

Chacun de ces pieges s'est produit reellement. Aucun n'a ete trouve par le controle
cense le detecter : tous ont ete trouves **parce qu'on a demande au controle ce
qu'il avait compte**.

---

## I. Les verts qui ne prouvent rien

### 1. Un controle qui n'a rien lu rend vert

Le cas archetypal. Une batterie agrege trente-neuf lignes de controle et affiche un
total de zero. Quatre de ces lignes pointaient une plage vide, parce que le controle
vivait en colonne `D` et qu'on le tirait sur la grille des periodes `E:N`. Or
`ABS(vide)` vaut zero, et l'`IFERROR` qui l'entoure ne se declenche meme pas. Ces
lignes rendaient zero **sans rien lire**, et masquaient un controle reellement en
echec.

**Ce qui le revele** : compter les lignes muettes. Une ligne dont la premiere
cellule est vide ne prouve rien.

```
=SUMPRODUCT(--(E10:E48=""))     cible : 0
```

**La regle generale** : toute batterie doit porter, hors de son propre perimetre
agrege, un compteur de ce qu'elle n'a pas lu.

### 2. Un correcteur qui n'examine aucun critere

Le harnais de Q&A du corpus repere les sections d'une rubric a leur style
`Heading 1`. Une rubric dont les titres etaient en gras — visuellement identiques —
lui a fait examiner **zero critere**, et il a rendu un rapport vert.

**Ce qui le revele** : le rapport doit annoncer le nombre de criteres examines. S'il
ne l'annonce pas, le faire annoncer.

### 3. Un compteur qui compte la mauvaise chose

Un modele devait porter sept mecaniques circulaires independantes. Le compteur en
annoncait sept. Trois etaient **inertes** : la formule refermait bien un cycle, mais
le coefficient qui la nourrissait etait nul, donc la boucle ne convergeait vers rien.

**Ce qui le revele** : deux tests, jamais un seul.

- **Test d'isolement** : couper les six autres mecaniques, verifier que celle-ci
  tourne encore et deplace une valeur.
- **Cycle residuel** : couper les sept, verifier qu'il ne reste **aucune** cellule
  auto-referente. Sinon il existe une boucle non nommee, donc non debranchable.

Compter les composantes fortement connexes du graphe de dependances ne mesure rien
d'utile : dans un modele integre, tout finit par se toucher.

---

## II. Excel ne conserve pas ce qu'on croit

### 4. Excel reecrit les reglages d'iteration du fichier

Un classeur circulaire doit porter le calcul iteratif **arme dans le fichier**
(`iterate`, un nombre d'iterations, un ecart maximal). En enregistrant, Excel ecrase
ces valeurs par celles de **l'application**. Un classeur livre a 200 iterations peut
repartir a 1000 sans que personne ne l'ait touche, et echouer sa propre condition de
configuration.

**Ce qui le revele** : relire `xl/workbook.xml` dans le `.xlsx` apres chaque
enregistrement, et y chercher la balise `calcPr`.

**La regle** : ce controle se refait **apres** le dernier enregistrement, jamais
avant.

### 5. Un classeur ecrit par openpyxl n'a aucune valeur en cache

openpyxl ecrit des formules, il ne calcule rien. Le fichier produit est **ingradable
en l'etat** : toute lecture de valeur rend `None`. Un correcteur qui lit ce fichier
ne trouve aucune valeur et peut le rapporter comme un zero.

**La regle** : entre la generation et toute lecture de valeur, il y a **toujours** un
recalcul par Excel. Sans exception.

### 6. openpyxl ne suit pas les renommages de feuille

Renommer une feuille via openpyxl ne reecrit **aucune** des formules qui la
referencent. Le classeur s'ouvre avec des references cassees, ou pire, garde des
renvois vers un nom qui n'existe plus.

**La regle** : les noms de feuille se fixent dans le generateur, avant la premiere
ecriture. On ne renomme pas apres coup.

### 7. LibreOffice et Excel ne calculent pas tout pareil

Le correcteur du corpus peut tourner sous LibreOffice. Certaines fonctions y
divergent, et une golden juste sous Excel peut y perdre des points.

**Ce qui le revele** : recalculer le classeur sous LibreOffice et comparer cellule
par cellule au cache Excel (`outils/lo_parite.py`). Comparer aussi **les dates** :
c'est la divergence la plus frequente et la plus silencieuse.

### 16. Un libelle ecrit en formule disparait du blank

> **Ce piege ne vaut que pour un corpus qui livre un BLANK** — la golden entiere,
> formules effacees, onglets et libelles conserves. Un corpus qui livre un
> **extrait d'`Input_Sheet`** ne le rencontre pas : il n'y a pas de squelette a
> preserver. Verifier lequel s'applique avant de chercher le defaut.

Fabriquer un blank efface les formules et garde le texte. Un libelle de ligne
construit par formule — `="Cohort "&TEXT(Yr_Base,"0")` — est une formule : il part
avec les reponses. Le candidat recoit un bloc de lignes sans nom, alors que le
prompt lui promet un blank qui « preserves every tab, section header, row label ».

Le defaut est muet. Le controle des libelles ne compare que les paires ou les DEUX
classeurs portent du texte : la ou la golden porte une formule, il ne regarde rien.
Et le cout n'est pas que de lisibilite — une rubric qui cite ces cellules en
`relevant_headers` designe alors des cellules vides dans le fichier note.

**Ce qui le revele** : dans les colonnes de libelles, relever les formules-texte de
la golden dont la cellule est vide cote blank, puis lire la valeur CALCULEE de
chacune. Un statut (`PASS`, `Base`, `Q1-22A`, `n.m.`) est une sortie du modele et
doit rester vide ; une phrase est un libelle et doit revenir.

**La regle** : dans une colonne de libelles, un libelle s'ecrit en texte, jamais en
formule. Si la golden en porte deja, le blank les recoit en dur.

---

## III. Les circuits et les solveurs

### 8. Une reponse a paliers dans un circuit fait osciller le solveur

Une elasticite appliquee par palier — un coefficient qui saute quand une variable
franchit un seuil — placee a l'interieur d'une boucle iterative empeche la
convergence : le calcul oscille entre deux etats de part et d'autre du seuil.

**La regle** : toute reponse qui vit dans un circuit doit etre **continue**. Une
interpolation lineaire entre les paliers suffit ; un test sur un seuil ne convient
pas.

### 9. Un back-solve se mene tete apres tete, jamais en bloc

Quand l'enonce fixe une **cible** — par exemple : chaque poste de remise doit
representer tel pourcentage du prix de liste — et non le taux lui-meme, le taux se
resout. Mais chaque poste s'applique sur le prix que les postes precedents ont deja
produit : les resoudre simultanement donne des taux faux qui ont l'air justes.

**La regle** : resoudre dans l'ordre ou les postes s'appliquent, chacun sur la base
que le precedent a laissee.

### 10. XIRR compte en actual/365, pas en annees pleines

Un bouclage comparait un multiple compose sur cinq ans au taux rendu par `XIRR`. Il
ne fermait jamais, d'un ecart de 0,0014. Ce n'etait pas une erreur de modele : entre
le 31-12-2025 et le 31-12-2030 il y a **1826 jours**, soit 5,00274 annees.

**La regle** : quand un controle confronte deux mesures, verifier qu'elles sont **sur
la meme base** avant de conclure a une erreur — et corriger la base, pas la
tolerance.

---

## IV. Le format et les documents

### 11. Le format ne s'imite pas, il se reprend

Une rubric reconstruite « au format » d'un exemple, en lisant son texte, produit un
document qui **ressemble** au gabarit sans en etre un : les puces ne sont plus des
puces, la police n'est plus la meme, les styles portent d'autres noms. Le service
qui recoit le document voit immediatement que ce n'est pas le format demande, et les
outils qui le lisent par ses styles ne trouvent plus rien (piege 2).

**La regle** : partir du fichier d'exemple, copier **toutes** les parties du paquet
`.docx` — styles, numerotation, theme, reglages, table de polices — et ne regenerer
que le document lui-meme. C'est ce que fait `outils/txt_vers_docx.py`.

**Corollaire** : ouvrir le gabarit, ne pas se fier a sa description. Un gabarit porte
souvent trois niveaux de titre la ou on en lit deux.

### 12. Rediger en texte, convertir au dernier moment

Un `.docx` n'est ni diffable, ni greppable, ni versionnable. Ecrire le prompt et la
rubric en `.txt`, et ne produire le document qu'a la livraison. Le texte reste la
source ; le document est un artefact.

---

## V. La rubric et la notation

### 13. Un critere qui nomme la mauvaise cellule fabrique une perte fantome

Un critere qui designe un poste par un libelle ambigu — ou par le libelle d'une
ligne voisine — fait perdre des points a un candidat correct, et fausse le rollout.
Le defaut est invisible tant qu'on ne note que la golden, parce que la golden, elle,
est appariee par construction.

**Ce qui le revele** : noter un **candidat different de la golden**. Tout critere qui
ressort NON RESOLU sur un candidat credible est un critere mal adresse.

**La regle** : un critere se lit seul. Il nomme sa feuille, son poste et sa periode
en toutes lettres, sans renvoi a un autre critere.

### 14. Ne jamais rebatir un classeur retouche a la main

Des qu'un classeur genere a recu une modification manuelle, le regenerer l'ecrase.
Les corrections ulterieures se font **en place**, et la meme correction est reportee
dans le generateur pour qu'un futur rebuild ne regresse pas.

**La regle** : generateur et livre divergent des la premiere retouche manuelle.
Tenir les deux a jour, ou ne plus jamais rebuild.

### 15. Une fausse alerte est le meme defaut qu'un faux vert

L'audit d'une golden a annonce **douze interrupteurs morts** — des breakers
qu'aucune formule ne consulterait. Verification faite, l'un d'eux etait cite par
**2 391 formules**. Le controle ne cherchait que la citation par **nom defini**,
alors que ce classeur adresse ses hypotheses **par cellule**.

C'est le symetrique du piege 1. La ou un controle aveugle rassure a tort, celui-ci
alarme a tort — et une alerte qu'on finit par ignorer ne protege plus de rien.

**Ce qui le revele** : la meme question que partout ailleurs. *Qu'est-ce que ce
controle a regarde ?* Un compte de zero se verifie dans les deux sens : zero parce
qu'il n'y a rien, ou zero parce qu'on cherchait au mauvais endroit.

**La regle** : un controle qui cherche une reference doit connaitre **toutes** les
facons de la formuler — par nom, par adresse, avec ou sans dollars, avec ou sans
guillemets autour du nom de feuille.

---

## Le reflexe qui les couvre tous

Avant d'accepter un resultat, se demander : **qu'est-ce que ce controle a
effectivement lu ?** S'il ne sait pas le dire, il ne prouve rien. Le faire compter,
puis confronter son compte a ce qu'on attendait.

---

[Retour a la skill](../SKILL.md)
