---
title: "Les contrats de format"
description: "Le code couleur du classeur, les unites, et la facon de reprendre le format des documents au lieu de l'imiter."
type: "reference"
status: "actif"
---

# Les contrats de format

Un pack juste mais mal presente est refuse avant d'etre lu. Le format n'est pas de
la decoration : c'est ce qui fait qu'un relecteur financier reconnait un modele
professionnel en trois secondes.

## Le principe qui gouverne les deux contrats

**Le format se lit dans le document de reference, il ne s'invente pas.**

Chaque corpus a le sien. Ce qui suit decrit la **forme** d'un contrat de format et
donne celui d'un corpus reel en exemple — pas une norme universelle. Face a un
nouveau corpus : ouvrir son document d'exemple et en relever les valeurs.

**Et chaque pack prend sa propre mise en page dans ce corpus, toujours aux standards
stricts d'une banque d'affaires** (decision du 14/09/2026) : grille, architecture,
police, teinte, famille de documents. Ce contrat dit ce qui se tient partout ; ce qui
change d'un pack a l'autre, l'enveloppe IB dont rien ne sort, et le controle qui les
verifie, vivent dans **[la mise en page](mise-en-page.md)**.

---

## I. Le classeur

### Le code couleur — le point le plus souvent rate

C'est la convention de la modelisation financiere, et un relecteur la lit
immediatement. Elle porte sur **l'encre du nombre**, pas sur le fond de la cellule.

| Encre | Ce que la cellule contient |
|-------|----------------------------|
| **Violet** | un nombre en dur, sur la feuille d'hypotheses |
| **Vert** | un nombre en dur **hors** de la feuille d'hypotheses, ou un lien externe |
| **Rouge** | une formule qui atteint une autre feuille |
| **Noir** | une formule locale, et tous les libelles |
| **Bleu** | une entree attendue du candidat : la cellule reste **vide** |

Le vert est un **signal d'alerte** : il annonce une valeur en dur la ou il ne devrait
pas y en avoir. Dans une golden bien construite, il n'y en a pas.

### Il y a DEUX palettes, et le corpus dit laquelle

Le tableau ci-dessus est la palette **maison**. Une seconde existe, la convention de
marche, et **elle n'est pas une derive** : un corpus reel l'impose au candidat, en
toutes lettres, dans le bloc `Formatting Requirements` de son prompt — mesure sur
**45 prompts sur 45**.

| | palette **maison** | palette **onyx** |
|---|---|---|
| nombre en dur sur la feuille d'entree | **violet** | **bleu** |
| nombre en dur ailleurs | vert | bleu |
| lien externe | vert | **rouge** |
| formule vers une autre feuille | **rouge** | **vert** |
| formule locale, libelles | noir | noir |
| controles | noir | **violet** |

**Le vert et le rouge sont inverses entre les deux.** Se tromper de palette produit
un classeur qui a l'air soigne et qui dit le contraire de ce qu'il montre.

Les deux vivent dans le module de format, et un generateur bascule **une fois, en
tete de fichier** :

```python
import format_maison as fm
fm.palette("onyx")      # ou "maison", la valeur par defaut
```

**Relever la palette dans le prompt du corpus servi avant d'ecrire une ligne** — le
bloc `Formatting Requirements` la donne. **Pour un pack livre, c'est la convention de
marche, standard IB, et elle ne varie pas d'un pack a l'autre** : la mise en page change,
l'encre jamais. La couleur ne s'ecrit jamais a la main :
elle se deduit du contenu, ce qui rend la derive impossible par distraction.

### Police et corps

Une seule police pour tout le classeur, un seul corps, **pris dans la fiche de mise en
page du pack** parmi les polices de place : Arial, Calibri, Tahoma, Garamond, Times New
Roman, Cambria, Book Antiqua, en corps 8, 9 ou 10. Le corpus en livre d'autres (Goudy
Old Style, Rockwell, Manrope) et du corps 11 : ce ne sont pas des standards IB, on ne
les reprend pas.

```
POLICE = "Garamond"      # un exemple : la fiche de mise en page du pack decide
TAILLE = 8
```

### Les bandeaux

Une hierarchie visuelle a quatre niveaux, du plus fonce au plus clair. Les fonces
portent une encre blanche.

```
FOND_TITRE       le bandeau de tete de la feuille
FOND_SECTION     un bloc
FOND_SECONDAIRE  un sous-groupe dans un bloc
FOND_DOUX        une sous-section, et les lignes de statistiques
```

**Le piege** : deux niveaux de bleu trop proches ne se distinguent plus a l'ecran, et
la hierarchie disparait. Ecarter les valeurs franchement.

### Les formats de nombre

Ils portent l'unite. Un nombre sans format est un nombre dont on ne sait pas s'il
est en unites, en milliers ou en millions.

```
MONTANT            affiche en millions
MONTANT_MILLIERS   milliers, une decimale
PAR_ACTION         deux decimales
QUANTITE           entier
POURCENT           une decimale
```

Les negatifs se presentent **entre parentheses**, et le zero par un tiret. C'est la
convention du metier ; un signe moins fait amateur.

### Ce qui trahit une fabrication automatique

- des colonnes a la largeur par defaut
- des onglets sans couleur, ou toutes de la meme
- un volet fige oublie, ou pose au mauvais endroit
- des tirets cadratins dans les libelles la ou le corpus utilise des tirets simples
- des **puces pleines** — `•`, `●`, `▪` — la ou le corpus met un tiret simple
- des guillemets ou apostrophes **typographiques**, des symboles decoratifs, des emoji
- une **phrase explicative accrochee a un libelle** : un libelle nomme une ligne ; des
  qu'il explique ou justifie, ce n'est plus un libelle
- un groupement laisse dans le classeur
- une feuille de garde absente

Cette liste ne se relit pas a l'oeil, elle se lance :

```
python outils/traces_ia.py "<classeur>" --detail
```

### Les intercalaires

Un intercalaire est un separateur visuel de navigation. Il ne calcule rien, c'est sa
fonction : il est creux, sans volet fige et aux largeurs par defaut **par
construction**, et le controle de traces l'exempte des trois controles de forme
d'onglet en le comptant a part.

**La forme du nom :** `>>Financials`, `>>Debt`, `>>Returns`. Deux chevrons colles au
mot, et le mot en **capitale initiale seule**.

| | |
|---|---|
| ce qu'on ecrit | `>>Financials` |
| ce qu'on n'ecrit pas | `>> FINANCIALS >>` — chevrons espaces, doubles, et tout en majuscules |

La seconde forme est reconnue par le detecteur, pour ne pas crier sur un classeur
d'archive, mais ce n'est pas celle qu'on produit : les capitales et le chevron de
fermeture sont exactement le genre de surenchere qui signale une fabrication
automatique.

---

## II. Les documents

### La regle : reprendre, jamais imiter

Un `.docx` est un paquet de plusieurs parties : le document, mais aussi les styles,
la numerotation, le theme, les reglages, la table de polices. **Reecrire seulement le
document en gardant toutes les autres parties du gabarit** produit un vrai document
au bon format. Ecrire ses propres styles produit un document qui y ressemble sans en
etre un (piege 11).

C'est exactement ce que fait l'outil :

```
python outils/txt_vers_docx.py "Rubric - X.txt" "Rubric - X.docx" --gabarit <nom>
python outils/txt_vers_docx.py "Prompt - X.txt" "Prompt - X.docx" --gabarit <nom>
```

Il part du gabarit, copie toutes ses parties, et ne regenere que le contenu.

### Les gabarits

Deposer dans [`gabarits/`](../gabarits/) **un prompt et une rubric deja acceptes par
le corpus**. Sans eux, l'outil ne peut pas travailler et le format ne peut pas etre
repris.

Le dossier peut aussi etre designe par la variable d'environnement `PACK_GABARITS`.

### Lire le gabarit, pas sa description

Un gabarit porte souvent plus de niveaux qu'on ne croit en le survolant. Sur celui
qui a servi ici, le prompt en avait **trois** sous une meme grande partie :

- un bloc qui coiffe des puces : gras italique, corps 12
- un intitule d'onglet : italique seul
- sa description : paragraphe courant, **pas** une puce

Les confondre se voit immediatement. **Ouvrir le fichier et relever ses styles** ;
ne pas reconstituer sa forme depuis son texte.

### La forme d'une rubric

Deux points que le gabarit impose et qu'on retrouve rarement de soi-meme :

- **Des puces, pas des tableaux.** Un tableau se lit bien a l'ecran et se grade
  mal : le harnais du corpus attend une liste.
- **Une configuration de scoring en tete**, qui enonce **une fois pour toutes** le
  test de reussite par defaut, plutot que de le repeter a chaque ligne.

### Les styles portent du sens, pas seulement de l'apparence

Le harnais de Q&A du corpus repere les sections d'une rubric a leur style
`Heading 1`. Un titre mis en gras — visuellement identique — le rend aveugle
(piege 2). **Un titre doit etre un style de titre**, jamais du texte gras.

---

[Retour a la skill](../SKILL.md) | [Les pieges](pieges.md)
