---
title: "La mise en page du pack"
description: "Chaque pack sa mise en page, toujours dans les standards stricts de banque d'affaires : l'enveloppe IB qui ne se negocie pas, les axes qui varient dedans, la fiche decidee en phase 1, les familles de documents, et le controle contre les packs deja livres du lot."
type: "reference"
status: "actif"
---

# La mise en page : chaque pack la sienne, toujours aux standards IB

**Decision du 14/09/2026 : deux packs ne se presentent pas de la meme facon, et aucun ne
sort des standards d'une banque d'affaires.** Pas seulement les couleurs : la grille,
l'architecture du classeur, la typographie, la forme des documents. Mais la variete se
choisit **a l'interieur d'une enveloppe IB stricte**, jamais au-dela. Le [contrat de
format](contrats-format.md) dit comment un pack doit etre tenu ; cette page dit comment
chacun se distingue de ses voisins sans cesser d'etre un modele de banque.

## Pourquoi

**Une serie de classeurs identiques signale une fabrication en serie**, exactement comme
une serie d'onglets de la meme couleur signale un classeur genere. Et c'est ce que nous
livrions : mesures le 14/09/2026, les quatre packs du lot RX — Gdansk, Cobalt, Sarrasin,
Livorno — ne different entre eux sur **aucun axe de structure**. Libelles en C, valeurs
des D, colonne d'unites, page de garde, intercalaires, noms en `Snake_Case`, volet fige :
tout est pareil ; seules la police et la teinte changent.

**Et ce que le corpus livre n'est pas pour autant un standard.** Sur 66 goldens, **21
seulement** tiennent l'enveloppe ci-dessous. Les ecarts : liens entre feuilles laisses a
l'encre noire (22 goldens), fond vif, magenta ou jaune pur (12), police de fantaisie (11 :
Goudy Old Style, Rockwell, Manrope, Univers Light...), plusieurs polices dans le classeur
(10), premiere periode qui change de colonne d'un onglet a l'autre (10), bandeau clair
sans niveau sombre (7), quadrillage visible (5), corps 11 (5), periodes en colonne (4). On reprend
donc les options du corpus **filtrees par l'enveloppe**, pas le corpus tel quel.

## L'enveloppe IB : ce qui ne varie jamais

| Regle | Ce qu'on tient | Controle |
|-------|----------------|----------|
| **Encre** | convention de place : **bleu** pour un nombre en dur, **noir** pour une formule locale, **vert** pour un lien vers une autre feuille, **rouge** pour un lien externe. Elle ne change pas d'un pack a l'autre et s'ecrit dans `Formatting Requirements` | `mise_en_page.py`, `traces_ia.py` |
| **Police** | une seule dans tout le classeur, prise parmi les polices de place : Arial, Calibri, Tahoma, Garamond, Times New Roman, Cambria, Book Antiqua | `mise_en_page.py` |
| **Corps** | 8, 9 ou 10. Le 11 est le defaut d'Excel : il dit que personne n'a mis le classeur en forme | `mise_en_page.py` |
| **Temps** | les periodes courent de gauche a droite, et **la premiere periode tombe dans la meme colonne sur chaque onglet date** (80 % au moins) | `mise_en_page.py` |
| **Bandeau et fonds** | un niveau de tete sombre et sobre, encre blanche ; les fonds clairs pour les sous-niveaux et les cellules d'entree (jaune pale) ; aucun fond vif, ni magenta ni jaune pur | `mise_en_page.py` |
| **Quadrillage** | masque sur tous les onglets | `mise_en_page.py` |
| **Nombres** | negatifs entre parentheses, zero en tiret, unite affichee (colonne d'unites ou bandeau d'unite), meme nombre de decimales pour une meme grandeur | `mise_en_page.py` pour les deux premiers |
| **Hygiene** | libelles a gauche, nombres a droite, totaux sous filet, aucune cellule fusionnee dans une zone de calcul, aucune trace de fabrication | `traces_ia.py`, relecture |
| **Documents** | l'ossature du [contrat du prompt](contrat-prompt.md), les regles du [contrat de la rubric](contrat-rubric.md), des sections de rubric en style de titre (piege 2) | `verifier_prompt.py`, `verifier_rubric.py` |

## Ce qui varie, a l'interieur de l'enveloppe

Les options ci-dessous sont celles que le corpus livre **et** que l'enveloppe admet. Les
comptes entre parentheses portent sur les 21 goldens conformes : chaque axe y garde au
moins deux options reelles.

| Axe | Options admises | Exemples conformes |
|-----|-----------------|--------------------|
| **Colonne des libelles** | B (1) · C (18) · D (2) | B : Basel ; D : Solvo, Aphelion |
| **Premiere colonne de valeurs** | B (1) · D (15) · E (3) · F (2) | E : Caire, Zen ; F : Solvo, Goose |
| **Colonne d'unites** | avec (10) · sans (11) | avec : Solvo, Gdansk ; sans : Final, Janus |
| **Page de garde** | avec (4) · sans (17) | avec : Cobalt ; sans : Final |
| **Intercalaires** | avec (20) · sans (1) | sans : Aphelion |
| **Noms d'onglets** | `Snake_Case` (18) · avec espaces · un mot · numerotes | avec espaces : Basel ; un mot : Basalte ; numerotes : Zephyr |
| **Volet fige** | avec (8) · sans (13) | avec : Human ; sans : Caire |
| **Police** | Arial (13) · Garamond (6) · Calibri (1) · Cambria (1), plus Tahoma, Times New Roman, Book Antiqua | Garamond : Final, Caire ; Calibri : Solvo |
| **Corps** | 8 (15) · 9 (5) · 10 (1) | 9 : Livorno ; 10 : Basel |
| **Teinte du bandeau** | noir ou anthracite (14) · bleu petrole (3) · marine (2) · brun (2), toujours fonce | petrole : Solvo, Or ; marine : Human ; brun : Basel |
| **Onglets colores** | oui (3) · non (18) | oui : Gdansk |
| **Titre de bloc**, releve a l'oeil | bandeau plein · filet sous le libelle · libelle gras seul | — |
| **Numerotation des blocs**, releve a l'oeil | `A.` · `1.1` · aucune | — |

## La fiche de mise en page, decidee en phase 1

On la pose avec la carte des onglets, avant d'ecrire le generateur. Chaque ligne se prend
**dans les options admises** ; c'est la **combinaison** qui est propre au pack, jamais
une option inventee.

```
architecture   page de garde : non   intercalaires : oui   noms : avec espaces
grille         libelles en B   unites : non   valeurs des E   volet : non
blocs          titre en filet sous le libelle, numerotation 1.1
typographie    Cambria 9
habillage      bandeau bleu petrole fonce, onglets non colores
nombres        millions a une decimale, negatifs (x), zero -
encre          convention IB, ecrite dans Formatting Requirements
documents      prompt famille B, rubric famille numerotee
```

**Dans `CONCEPTION.md`, la fiche s'ecrit une cle par ligne** (`colonne_libelles: B`,
`bandeau: 1F4E5A`...), le bandeau en hexadecimal : c'est ainsi que la porte 1 la lit et la
compare au lot avant que la golden existe (`mise_en_page.py --fiche CONCEPTION.md --contre
<lot>`). Le format exact : [les portes](portes.md).

**La regle de distance.** Contre **chaque** pack deja livre du meme lot, la fiche differe
sur **au moins 3 axes de structure** (sur 7) et **2 d'habillage** (sur 4), **dont la
teinte du bandeau**. Calibrage : sur 172 paires de packs d'un meme environnement, la
mediane du corpus differe de 3 axes de structure et de 2 d'habillage, et 43 % des paires
tiennent les deux planchers. On vise au-dessus de la moyenne du corpus, pas l'exception.

**Quand la graine cite une golden en exemple** (« take on example the Golden Solution of
X »), X vaut **pour le formatting seulement** (decision du 16/09/2026). On en reprend la
police, le corps, les bandeaux et leurs couleurs, les encres, les formats de nombre, les
intercalaires, la disposition libelles / valeurs / periodes : la fiche se remplit sur
elle, et **elle l'emporte sur la regle de distance**, puisque l'auteur l'a choisie — une
proximite signalee par `--contre` avec X se note alors comme voulue. On n'en tire
**rien** sur le niveau, les mecaniques, les boucles, les scenarios ou la carte des
onglets.

## Les documents : des familles, pas des inventions

Tous les prompts du corpus partagent la meme ossature (`Intermediate Outputs`, `Final
Outputs`, `Xlsx Output`) ; leur **forme** se repartit en familles, et les rubrics aussi.
Releve sur 96 documents livres.

| Document | Famille | Ce qui la reconnait | Exemples |
|----------|---------|---------------------|----------|
| Prompt | **A** | titres de bloc en `Heading 1`, puces numerotees | Solvo, Fluxo, Cashly, Valhalla, Petrichor |
| Prompt | **B** | titres de bloc en `Heading 2`, puces numerotees | Icare, Yards, Ashford, Caire, Final, Dox |
| Prompt | **C** | puces simples `List Bullet` | Rigel, Cardinal, Goose, Concorde, Vantablack |
| Rubric | **Ostrom** | `Title`, sections en `Heading 1`, puces simples, Arial | Ostrom, Or, Basalte, Silex, Estuaire |
| Rubric | **numerotee** | sections en `Heading 1`, sous-sections en `Heading 2`, criteres numerotes | Gerland, Meridian, Oxbow, Ito |

Les documents suivent les memes standards que le classeur : police de place (Calibri,
Arial, Garamond, Georgia ; le corpus n'en livre pas d'autre), aucun effet decoratif.

**Deux formes a ne pas reprendre**, bien qu'elles aient ete livrees : la rubric en liste
plate sans titre de section (Rhone, Umbra), que le harnais lit mal (piege 2), et la
conversion compacte en Consolas (Lathe, Halcyon, Trieste), qui trahit un passage par un
convertisseur.

**Produire une famille, c'est reprendre son gabarit.** Le document se reconstruit depuis
le paquet Word d'un pack livre de la famille, en reutilisant ses paragraphes modeles —
comme le fait `prompt_docx.py` du pack Gdansk sur Solvo — et jamais en ecrivant des
styles. `outils/txt_vers_docx.py` ne porte pour l'instant que deux profils, Madrid et
Ostrom : une autre famille demande le convertisseur du pack, ou un profil de plus.

## Dans la chaine

| Phase | Ce que la mise en page y demande |
|-------|----------------------------------|
| [1. Concevoir](01-concevoir.md) | la fiche, prise dans les options admises, et sa distance aux packs livres du lot |
| [2. Batir](02-batir.md) | le generateur lit la fiche en un seul endroit — police, colonnes, bandeaux, forme des blocs — et ne pose aucun style ailleurs |
| [4. Enoncer et noter](04-noter.md) | `Formatting Requirements` s'ecrit depuis la fiche et l'enveloppe : colonne des libelles, debut des valeurs, unites, police, encre IB ; la rubric ne note que ce que ce bloc dit |
| [5. Verifier](05-verifier.md) | le controle ci-dessous, puis `traces_ia.py` |

```
python outils/mise_en_page.py "<golden>"                                # signature et standards IB
python outils/mise_en_page.py "<golden>" --contre "<dossier du lot>"    # standards IB et distance
```

La premiere rend la signature et `STANDARDS IB : tenus`, ou la liste des ecarts. La seconde
lit **les classeurs livres eux-memes**, pas un registre : un registre declare peut mentir,
un fichier non. Elle sort en echec au moindre ecart IB, au moindre voisin trop proche, et
quand elle n'a compare aucun classeur — **zero classeur compare n'est pas une mise en page
distincte**. Sortie attendue : aucun `HORS STANDARD IB`, et `N classeurs compares, 0 trop
proches`.

---

[Retour a la skill](../SKILL.md) | [Les contrats de format](contrats-format.md) | [Les pieges](pieges.md)
