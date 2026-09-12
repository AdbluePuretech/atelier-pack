# La methode d'un fonds de PE

> **COPIE.** L'original vit dans la skill `audit-modele`. `/pack` en
> embarque un double parce qu'il est distribue en plugin et doit
> fonctionner seul. Corriger l'original d'abord, puis recopier.

Comment le metier audite un modele, et ce qui transpose a nos classeurs.

## Le cadre

Un sponsor n'audite pas son modele en interne. Sur un LBO avec de la dette
senior, les banques arrangeuses **exigent un model audit** en condition
prealable au closing. C'est un workstream de due diligence a part entiere,
commande a une maison specialisee - Operis, Mazars, Grant Thornton, BDO, les
Big Four. Deux a quatre semaines.

Ca ne finit jamais par "le modele est parfait". Ca finit par une **lettre
d'assurance negative** - rien n'a ete porte a notre connaissance - et un
**issues log** ou chaque point est grade, corrige, re-teste, signe. C'est la
forme a imiter : un audit rend des constats traces, pas un avis.

## Les neuf workstreams

| # | Workstream | Ce qu'il fait | Transposition |
|---|------------|---------------|---------------|
| 1 | **Gel de version** | un fichier nomme, empreinte prise, aucune modif pendant l'audit | direct - etape 1 |
| 2 | **Tie-out des inputs** | chaque valeur en dur remonte a un document : SPA, contrat de credit, note fiscale, business plan | direct - et nos packs font mieux que la moyenne du marche, avec la colonne de source et le fichier d'ancrages |
| 3 | **Revue des formules uniques** | reduire le classeur a ses formules distinctes et les lire toutes | direct - etape 5, c'est le coeur du metier |
| 4 | **Balayage d'integrite** | dur dans une formule, ancrage manquant, #REF, liens externes, feuilles masquees, plages SUM qui debordent, decalage d'une periode, conventions de signe, unites melangees, nombre en texte, IFERROR | direct - etape 4, outille |
| 5 | **Revue logique contre les documents** | la cascade de dette correspond-elle au contrat, la grille de sweep au term sheet, l'impot a la note fiscale | transpose en : le classeur implemente-t-il le prompt, et la rubric mesure-t-elle ce qu'il fait |
| 6 | **Sensibilites et stress** | flexer chaque input sur sa plage et sur les cas extremes ; aucune erreur, aucun controle rompu | direct - etape 6 |
| 7 | **Recalcul independant** | un second modelisateur refait les sorties cles a part et reconcilie | transpose en : recalculer les valeurs notees depuis les ancrages, par un autre chemin que le generateur |
| 8 | **Vraisemblance** | les sorties tiennent-elles face aux comparables | deja porte par le fichier d'ancrages, qui distingue observation de marche, choix de montage et cible de design |
| 9 | **Issues log** | rien n'est clos sans re-test | direct - la forme du rendu |

## Le point ou ca ne transpose pas

Le model audit **interdit les references circulaires**. FAST, Operis, la plupart
des comites de credit : une circularite se casse par algebre ou par macro,
jamais par calcul iteratif. La raison est exactement la notre : **un classeur
dont les valeurs dependent de l'historique de calcul n'est pas auditable**.

Nos packs inversent cette regle, et volontairement - la circularite est le
produit, c'est elle qui rend la tache difficile.

Le substitut n'est donc pas de supprimer la circularite, c'est de **prouver la
convergence** : le point fixe est unique et stable, on retombe sur les memes
valeurs a froid, a differents comptes d'iteration, sous les deux moteurs. C'est
l'etape 2, et c'est la seule qui peut invalider un pack entier - parce que si le
point fixe depend du chemin, les valeurs de la rubric ne sont pas des valeurs.

## Ce que le metier ne sait pas faire et nous si

Un auditeur humain reprend un classeur ecrit a la main : il ne peut que le lire.
Quand le classeur est **genere par un script**, on dispose d'une preuve qu'il
n'aura jamais : **regenerer et differencier**. Tout ecart entre le fichier livre
et le fichier reconstruit est soit une retouche manuelle, soit un generateur non
deterministe - et les deux sont des constats, pas des impressions.

Cette preuve liquide en une passe la question qui coute le plus cher a un
auditeur : est-ce que quelqu'un a ecrase une cellule au milieu d'une serie.

---
Navigation : [Fabriquer un pack](../SKILL.md) | [Phase 3 - Certifier](03-certifier.md) | [Moteur d'audit](../../../../systeme/scripts/audit-modele/README.md)
