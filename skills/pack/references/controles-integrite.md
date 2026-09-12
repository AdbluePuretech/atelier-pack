# Les vingt controles d'integrite

> **COPIE.** L'original vit dans la skill `audit-modele`. `/pack` en
> embarque un double parce qu'il est distribue en plugin et doit
> fonctionner seul. Corriger l'original d'abord, puis recopier.

Le balayage d'integrite est l'etape 5 de la chaine. Chaque controle rend **une
liste de cellules fautives, jamais un avis** — c'est ce qui permet de le
contester ligne par ligne au lieu de le croire.

| Cle | Controle | Gravite |
|-----|----------|---------|
| I1 | aucune valeur en dur hors de la feuille d'hypotheses | critique |
| I2 | aucun literal non trivial enfoui dans une formule | significatif |
| I3 | aucune valeur d'erreur dans le cache de calcul | critique |
| I4 | aucun masquage d'erreur — `IFERROR`, `IFNA`, `ISERROR` | critique |
| I5 | aucune fonction volatile ou indirecte — `NOW`, `RAND`, `OFFSET`, `INDIRECT` | significatif |
| I6 | aucun lien vers un classeur externe | critique |
| I7 | aucune formule ne lit une cellule vide | significatif |
| I8 | aucun nombre stocke en texte | significatif |
| I9 | aucune plage nommee inutilisee | presentationnel |
| I10 | aucune plage nommee non resolue | critique |
| I11 | rien de masque dans le classeur | significatif |
| I12 | aucune cellule fusionnee sur une zone de calcul | significatif |
| I13 | aucune plage `SUM` qui laisse une cellule du bloc dehors | critique |
| I14 | le classeur a bien ete calcule par Excel | critique |
| I15 | le cache est compatible avec les formules d'arrondi | critique |
| I16 | chaque formule porte une valeur en cache | significatif |
| I17 | aucune ligne de controle neutralisee par une multiplication par zero | critique |
| I18 | aucune hypothese posee que le modele ne lit pas | significatif |
| I19 | aucune ligne de controle saisie au lieu d'etre calculee | critique |
| I20 | aucune ligne de controle entierement constante | critique |

## La famille qui compte : I17, I19, I20

Les trois disent la meme chose par trois chemins, et **produisent le meme
resultat : un compteur de violations qui ne peut plus se declencher.**

| | Comment le controle est neutralise | Difficulte a le voir |
|---|---|---|
| **I17** | **annule** par une multiplication par zero | visible si on lit la formule |
| **I19** | **saisi** a la main au lieu d'etre calcule | se cache souvent dans UNE colonne au milieu d'une ligne de formules : la periode ou le controle n'aurait pas ferme |
| **I20** | porte une formule qui est un **literal** — `=0` | le plus retors : il passe les deux autres, parce que c'est bien une formule |

C'est cette famille qui a trouve, sur une golden reelle, dix lignes portant `=0`
la ou le generateur ecrivait un vrai compteur — une ligne **notee `[+2]` par la
rubric**, « pass if exactly 0 in all ten periods ». Dans le fichier livre elle ne
comptait rien : elle affichait zero parce qu'on le lui avait demande.

## Les trois nuances sans lesquelles le balayage ment

**I17 — `0*x` est un idiome legitime.** Il tient une dependance sans changer la
valeur : une tranche bullet qui n'amortit pas, un breaker qui gele une boucle. Ce
n'est un defaut que sur une ligne de **controle**. Le module ne signale donc que
les lignes dont le libelle annonce un controle (`must be nil`, `violation`,
`tie`, `residual`).

**I20 — un `=0` partiel est legitime.** Le defaut n'est retenu que si **aucune**
colonne de la ligne ne calcule quoi que ce soit. Un `=0` sur les periodes ou un
controle non periodique ne s'applique pas est meme la bonne facon d'eviter qu'il
lise une cellule vide.

**I18 compte par ligne, pas par cellule.** Une hypothese s'etale souvent sur
plusieurs colonnes — une valeur par cas, une colonne d'affichage a cote de la
colonne lue. Compter les cellules rendait **52 hypotheses mortes** sur une golden
qui en portait **2**, et noyait les vraies.

## I4 merite un mot

Un `IFERROR` est presque toujours un defaut dans un modele d'evaluation : il
transforme une erreur visible en valeur plausible, ce qui est exactement ce qu'un
audit cherche a empecher. Le corollaire : **I3 et I4 se lisent ensemble, jamais
l'un sans l'autre.** Un classeur qui passe I3 en portant des milliers d'`IFERROR`
passe pour la mauvaise raison.

## Ce que I14 et I15 tranchent a eux seuls

Ils separent deux defaillances opposees qu'aucun controle statique classique ne
distingue :

| | Un classeur calcule mais mal bati | Un classeur bien bati mais jamais calcule |
|---|---|---|
| I14 « calcule par Excel » | passe | **echoue** |
| I15 « cache compatible avec les `ROUND` » | passe | **echoue — 160 cellules** |
| marches dures dans un circuit | **3 637** | 0 |
| `IFERROR` | **8 699** | 0 |

Le second cas est le plus dangereux, parce qu'il s'ouvre, s'affiche, et ses
chiffres sont plausibles : ce sont ceux que le generateur Python a ecrits. Sur un
classeur circulaire c'est fatal — le point fixe de Python n'est pas celui
d'Excel.

---
Navigation : [Fabriquer un pack](../SKILL.md) | [Phase 3 - Certifier](03-certifier.md) | [Lire un resultat vert](lire-un-vert.md)
