---
title: "Catalogue des mecaniques discriminantes"
description: "Les formes d'auto-reference qui font echouer un modele frontiere, chacune avec son piege nomme, son aval typique et le pack ou elle a ete mesuree."
type: "reference"
status: "actif"
---

# Catalogue des mecaniques discriminantes

**Un modele frontiere absorbe la complexite mecanique.** Mesure sur un pack reel :
calendrier date, exercice clos au 30 septembre, collar contrat par contrat, pont
run-rate — **116 points sur 122, 95 %**. Le volume, les onglets, les periodes ne
coutent rien a un bon modele.

Ce qui le fait echouer est d'une autre nature, et ce catalogue le rassemble. Chaque
entree vient d'un pack livre ou construit ; aucune n'est inventee.

> **Comment s'en servir.** Choisir trois ou quatre mecaniques, de familles
> differentes. Pour chacune, ecrire son **piege nomme** et lancer **une passe de
> rollout d'enonce** — [phase 1, sections 3 et 4](01-concevoir.md). Une mecanique
> dont le modele frontiere sort la bonne reponse se remplace **maintenant**, pas au
> rollout final.

## Ce qui fait qu'une mecanique discrimine

Trois conditions, et il les faut toutes :

1. **La valeur se resout, elle ne se lit pas.** L'enonce donne une *cible*, pas le
   taux ; le taux se deduit.
2. **La mauvaise reponse plausible a un nom.** Si on ne sait pas l'ecrire en une
   phrase, la mecanique ne discrimine pas.
3. **L'erreur emporte beaucoup d'aval.** Une resolution ratee qui coute huit points
   est vraie et inutile.

---

## I. Les auto-references — le coeur du sujet

La doctrine Onyx nomme la plus discriminante du corpus : **un terme commercial
auto-referentiel, calcule sur le nombre qu'il fait bouger.**

### 1. Le plafond calcule sur le montant qu'il ecrete

Une hausse agregee ne peut pas depasser `c` fois le carnet de **cloture** de son
sous-carnet — or l'ecretage deplace ce carnet.

```
A = min(U, c x (B0 + A))     et quand le plafond mord :  A = c x B0 / (1 - c)
```

- **Ce qu'elle exige** : reconnaitre le point fixe, enumerer les deux regimes,
  valider chacun par son residu, reporter un code de regime.
- **Le piege nomme** : *plafonner sur le carnet d'OUVERTURE.*
- **L'aval** : toute la chaine de prix, donc les sections en dessous.
- **Ou** : indexation contractuelle, revalorisation tarifaire, MSA cap.
- **Mesure** : forme fermee, donc **pas de seconde circularite** — la tache reste au
  niveau vise.

### 2. La base de calcul qui inclut son propre resultat

Une base d'emprunt apres ecretage de concentration : la limite depend de la base, la
base depend de la limite.

- **Ce qu'elle exige** : enumerer les **ensembles actifs candidats** — huit sur un
  pack reel — et **valider le point fixe de chacun**, puis reporter le regime
  contraignant et son residu.
- **Le piege nomme** : *appliquer le plafond de concentration a l'avance brute, en
  une passe.*
- **L'aval** : la disponibilite de ligne par vehicule, donc les tirages, donc les
  interets, donc les rendements.
- **Ou** : borrowing base, covenant a definition circulaire, ratio de levier.

### 3. Le sweep qui se boucle sur le solde qu'il alimente

Tresorerie -> interets -> flux libre -> remboursement -> tresorerie. La famille de
boucles la plus banale, et c'est son defaut : **elle ne discrimine que si elle
touche autre chose que la dette.**

- **Le piege nomme** : *calculer les interets sur le solde d'ouverture pour casser la
  boucle.*
- **A savoir** : « des circularites toutes branchees sur la dette » figure parmi ce
  qui trahit une fabrication automatique. En prendre plusieurs, et **hors dette** :
  commissions sur encours contre bilan, PIK contre dette, portage de couverture.

### 4. La reprise sur ce qui a deja ete distribue

Un clawback interimaire : une depreciation tardive retroagit sur du carry deja
encaisse, donc appelle un complement d'escrow, qui modifie les flux nets.

- **Ce qu'elle exige** : le loss netting, le true-up, et un contrefactuel qui montre
  ce que la mecanique a coute.
- **Le piege nomme** : *traiter le carry encaisse comme acquis.*
- **L'aval** : les rendements nets, l'escrow, la cascade entiere.
- **Ou** : waterfall americain deal-by-deal, earn-out avec reprise, bonus malus.
- **Note** : **auto-referentiel par construction** — la circularite vient du sujet,
  sans artifice greffe. C'est la forme la plus propre.

---

## II. Les sequences — l'ordre EST la difficulte

### 5. Le back-solve poste apres poste

L'enonce fixe une **cible** — chaque poste de remise doit representer tel pourcentage
du prix de liste — et non le taux. Mais chaque poste s'applique sur le prix que les
precedents ont deja produit.

- **Le piege nomme** : *resoudre les postes simultanement.* Les taux obtenus ont
  l'air justes et sont faux.
- **L'aval** : le prix de poche, donc toute la cascade et les marges.
- **Ou** : cascade de remises, empilement de retenues, waterfall de frais.

### 6. Le water-filling d'un plafond partage

Plusieurs demandeurs, un cap agrege, une ponderation de priorite : on sert par tours,
et la capacite liberee par un demandeur rassasie se redistribue au tour suivant.

- **Ce qu'elle exige** : deux tours au moins, et une **verification par inversion
  matricielle** au mois de pointe.
- **Le piege nomme** : *repartir le cap au prorata des poids en une seule passe.*
- **L'aval** : l'allocation par vehicule, donc tout ce qui en descend.

### 7. La clause de la nation la plus favorisee

Une concession accordee a trois comptes en litige s'etend par clause au reste du
livre, mais **seulement a partir d'une periode donnee**, tandis que la derive
tarifaire s'applique a chaque periode.

- **Le piege nomme** : *appliquer l'extension des la premiere periode, ou l'appliquer
  a tout le livre.*
- **L'aval** : le prix de liste livre, donc la cascade.

---

## III. Les solves sous contrainte

### 8. Le plafond de capacite qui mord et force un arbitrage

Une force de vente ne peut pas couvrir tout le carnet : le plan de visite est
**resolu** pour atteindre un ratio de couverture cible.

- **Le calibrage est la difficulte** : sur un pack reel, la cible est
  **75,5 % +/- 2**. A 100 % le plafond ne mord pas et la tache s'effondre ; a 50 % le
  modele ne couvre plus rien et la sortie n'a plus de sens.
- **Le piege nomme** : *traiter la couverture comme une donnee au lieu de la
  resoudre.*
- **Ou** : capacite commerciale, capacite industrielle, allocation de personnel.

### 9. Le re-solve declenche par un evenement date

Un evenement en milieu d'horizon rend la solution precedente invalide et force une
reaffectation.

- **Ce qu'elle exige** : que les periodes de re-solve soient **deduites**, jamais
  saisies — un seuil de declenchement les determine.
- **Le piege nomme** : *saisir en dur les periodes ou le re-solve a lieu.*
- **Mesure de calibrage** : l'evenement doit deplacer **au moins 25 comptes**, sinon
  il ne prouve rien.

### 10. Le quota descendant reconcilie a une capacite montante

Un objectif groupe se decline par territoire ; la capacite se calcule de bas en haut.
Les deux ne tombent pas juste, et l'ecart se traite.

- **Le piege nomme** : *distribuer le quota au prorata sans reconcilier.*
- **Calibrage** : le quota depasse la capacite sur 4 territoires sur 12 **avant**
  reconciliation et sur **aucun** apres.

---

## IV. Les bases et conventions — le detail qui coule un modele juste

### 11. La base temporelle

Un bouclage comparait un multiple compose sur cinq ans au taux rendu par `XIRR`. Il
ne fermait jamais, d'un ecart de 0,0014 : entre le 31-12-2025 et le 31-12-2030 il y a
**1 826 jours**, soit 5,00274 annees. `XIRR` compte en **actual/365**.

- **Le piege nomme** : *comparer un taux actual/365 a un compose en annees pleines.*
- **La regle** : quand un controle confronte deux mesures, verifier qu'elles sont
  **sur la meme base** avant de conclure a une erreur — et corriger la base, pas la
  tolerance.

### 12. La continuite dans un circuit

Une elasticite par palier, un `MAX` dur, un test de seuil place **a l'interieur**
d'une boucle iterative empeche la convergence : le calcul oscille de part et d'autre
du seuil.

- **La regle** : toute reponse qui vit dans un circuit doit etre **continue**. Une
  interpolation suffit ; la forme lissee
  `0.5*(a+b+SQRT((a-b)^2+eps))` remplace un `MAX`.
- **Nuance** : un `IF` dont le test ne lit que des masques, des constantes ou des
  cellules **hors** du circuit est fige pendant l'iteration, donc legitime.
- **Le piege nomme, cote candidat** : *placer le palier dans la boucle* — son modele
  ne converge pas, ou converge ailleurs.

### 13. Le decalage et la multi-stabilite

Un ratio calcule sur une valeur **retardee**, un plafond sur un solde d'ouverture
contre un solde de cloture.

- **Le piege nomme** : *lire la valeur de la periode courante.*
- **L'avertissement d'equite** : quand un systeme circulaire a **plusieurs solutions
  stables**, un build correct peut converger vers « la mauvaise » et echouer sans
  faute. Ce n'est pas une difficulte, c'est un defaut de pack : il se detecte a
  l'etape de convergence de la phase 3, et se corrige.

---

## Choisir un jeu, pas une mecanique

**Trois ou quatre, de familles differentes.** Un pack qui empile quatre
auto-references de la famille I teste une seule competence quatre fois ; les points
tombent ensemble et le score s'effondre d'un coup, ce qui ne discrimine pas mieux
qu'un seul critere.

Les deux packs batis au calibre haut portent **huit boucles reelles et
independantes** chacun, **dont six hors dette** pour l'un d'eux. C'est l'ordre de
grandeur.

Et le controle qui ferme la phase 2 : **une boucle qui ne deplace aucune valeur notee
au-dela de la tolerance de la rubric est decorative.** Elle gonfle le compte sans
rien apporter au budget de discrimination.

---

[Retour a la skill](../SKILL.md) | [Phase 1 - Concevoir](01-concevoir.md) | [Les pieges](pieges.md)
