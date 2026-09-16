---
title: "Phase 3 - Certifier le classeur"
description: "Les neuf etapes qui prouvent qu'un classeur est sain comme objet : gel, differences, convergence, circuits, integrite, identites, familles, sensibilite, mutation."
type: "reference"
status: "actif"
---

# Phase 3 — Certifier

La phase 2 s'arrete sur `0 erreur au recalcul` et `chaque ancrage atteint`.
C'est une barre basse. Une golden reelle l'a franchie en portant 8 699
`IFERROR`, 51 plages `SUM` tronquees, dix compteurs de violations cables a
`=0` — et une batterie de controles qui ne surveillait que 24 % du classeur.

Cette phase pose la barre haute, et elle vaut pour **n'importe quel classeur**,
pas seulement pour une golden : le rendu d'un candidat, un modele de production,
une version d'archive se certifient exactement pareil.

> Hors fabrication, le meme protocole est joignable par la skill
> **`/audit-modele`**, qui existe pour ne pas avoir a invoquer « fabriquer un
> pack » quand on audite un classeur qu'on n'a pas fabrique. Ce fichier reste la
> reference detaillee des neuf etapes ; l'autre est un point d'entree.

## Les deux regles qui gouvernent tout le reste

**Un audit sans definition de "parfait" n'est pas verifiable.** La definition
retenue est la **couverture** : chaque cellule doit etre couverte par au moins
une preuve, et le taux de couverture est la note d'audit. Le modele de preuves
est dans [le moteur d'audit](../../../../systeme/scripts/audit-modele/README.md).

**Un controle ne vaut que s'il est independant de ce qu'il controle.** C'est la
regle la moins intuitive et la plus rentable. Un tie `A - B` dont les deux
membres descendent de la meme cellule bouge des deux cotes et ferme toujours :
il ne verifie pas le modele, il verifie une chaine contre elle-meme. Cette
proportion ne se voit pas a la lecture — elle se mesure, a l'etape 9.

**Ce que « couvert » veut dire, cellule par cellule.** Sans cette table, la
couverture n'est qu'un mot :

| Nature de la cellule | Preuve exigee |
|---|---|
| Valeur en dur sur la feuille d'hypotheses | provenance : elle remonte a un ancrage ou a une source |
| Valeur en dur ailleurs | **aucune n'est admise** — defaut par construction |
| Formule | elle appartient a une **famille revue**, et le balayage d'integrite la laisse indemne |
| Cellule dans un circuit | toute reponse discontinue qu'elle porte est figee pendant l'iteration |
| Valeur **notee par la rubric** | en plus : reproduction independante, et stabilite multi-moteur |

Ce qui rend l'exhaustivite atteignable, c'est que les formules se **reduisent** :
une grille repete la meme structure sur des milliers de cellules. Mais l'unite
de revue n'est PAS le squelette : c'est l'**usage**, squelette x feuille x bloc.
Sur une golden reelle, `=X*X*X*(#-X)` servait cinq tetes de remise differentes -
une sur le prix liste, deux sur le gross, deux sur l'invoice - et le squelette est
indifferent a la base. Verifier un usage ne dit rien des quatre autres.

Cette golden porte 84 216 formules pour **169 squelettes mais 389 usages**. C'est
389 qu'il faut lire ; 25 d'entre eux couvrent la moitie du classeur, 50 en couvrent
80 %. Le ratio se mesure au lieu de se supposer - c'est lui qui decide si
l'exhaustivite est un programme ou un slogan.

## La chaine en une commande

```
python outils/auditer_tout.py "<golden>" --sortie audit/
python outils/auditer_tout.py "<golden>" --sortie audit/ --regenere "<regen>" --avec-excel
```

Sans `--avec-excel`, seule la chaine **statique** tourne — une minute, rien
d'autre que Python. Avec, la chaine **dynamique** s'y ajoute : convergence,
sensibilite, commutateurs, mutation, chacune passant par un vrai recalcul. Il
faut compter en dizaines de minutes.

Le pilote ne saute jamais une etape en silence : celles qui n'ont pas tourne
sont inscrites au journal du certificat comme travail non fait, pas comme
resultat favorable. **Lire ce journal avant de conclure.**

## Les dix etapes

L'ordre va du defaut qui invalide tout au defaut qui se corrige a la marge. Les
etapes 3, 8 et 9 passent par le vrai Excel ; les autres ne demandent que Python.

Les neuf premieres demandent si le classeur est juste **avec lui-meme**. **La
dixieme demande s'il est possible** — et c'est la seule qui regarde dehors.

### 0. Savoir ce qu'on audite

Sur un classeur qu'on n'a pas fabrique, la premiere question n'est pas « est-il
juste » mais « qu'est-ce que c'est ». Feuilles, blocs, volumes, densite : de quoi
dimensionner les neuf etapes qui suivent et reperer les intercalaires avant qu'une
etape les compte pour des onglets de calcul.

```
python outils/bilan_classeur.py "<classeur>"
```

Cette etape ne prouve rien et ne rend aucun verdict. Elle evite de lancer une chaine
de quarante minutes sur un classeur dont on aurait vu en dix secondes qu'il n'a pas
la forme attendue.

### 1. Geler la version

Empreinte `sha256`, et le fichier ne bouge plus. Toute reprise repart en
nouvelle version et se re-teste entierement.

Ce n'est pas de la ceremonie : au cours d'un audit reel, le dossier a ete
reorganise et le fichier a change de nom sous l'outil. C'est l'empreinte qui a
permis d'etablir qu'on auditait depuis une heure un fichier qui n'etait pas la
golden.

### 2. Regenerer et differencier

**En phase de fabrication, cette etape est gratuite** : le generateur vient de
tourner. On le relance vers un fichier temporaire et on compare.

```
python systeme/scripts/<pack>/construire.py --sortie "/tmp/regen.xlsx"
python outils/differencier.py "<golden livree>" "/tmp/regen.xlsx" --json audit/d.json
```

Tout ecart est soit une retouche faite a la main apres generation, soit un
generateur non deterministe. Sur une golden reelle, 51 formules differaient —
dont dix ou le fichier livre portait `=0` la ou le generateur ecrivait un vrai
compteur de violations, **note par la rubric**.

Si le classeur n'est pas genere, cette etape n'existe pas : le dire et passer,
plutot que de la marquer verte.

> **Sortie** : le nombre d'ecarts, et pour chacun sa nature.

### 3. Convergence — l'etape qui peut tout invalider

```
python outils/convergence.py "<golden>" --json audit/v.json
```

Rejoue le classeur dans des configurations qui ne devraient rien changer — dont
un depart a froid, cache vide — et compare toutes les valeurs une a une.

> **Sortie** : zero valeur qui bouge. Un ecart, et la phase s'arrete la : les
> valeurs de la rubric n'en sont pas.

### 4. Circuits

```
python outils/circuits.py "<golden>" --json audit/c.json
```

> **Sortie** : les circuits, leur perimetre, et zero marche pouvant basculer
> pendant l'iteration.

### 5. Integrite

```
python outils/integrite.py "<golden>" --detail --json audit/i.json
```

Les vingt controles, leur gravite, et les trois nuances sans lesquelles le
balayage ment : **[le detail des controles d'integrite](controles-integrite.md)**.
La famille `I17 / I19 / I20` est celle qui rapporte le plus — un compteur de
violations annule, saisi ou pose en `=0` produit le meme resultat : un controle
qui ne peut plus se declencher.

> **Sortie** : le nombre de controles passes sur vingt, et les cellules fautives.

### 6. Identites imposees de l'exterieur

Le modele ne se controle que la ou il a pense a se controler. On lui impose
celles qu'il n'a pas declarees.

```
python outils/identites.py "<golden>" --detail --json audit/id.json
```

Module a **jugement**, pas a verdict : imposer des verites generales produit des
exceptions legitimes. Il a trouve un masque oublie sur une ligne de covenant que
ni les vingt controles ni les circuits ni la convergence n'avaient vu.

> **Sortie** : le nombre d'identites **testees**, avant le nombre d'ecarts. Jusqu'au
> 16/09/2026, le module ne reconnaissait qu'un en-tete `FY-2A` : sur une grille datee
> (jours, semaines, mois) il testait zero identite et imprimait « les identites
> tiennent » — Sarrasin, Cobalt et Etain ont ete certifies avec ce faux vert. Il lit
> maintenant une ligne de dates croissantes, et zero teste sort en « etape non faite ».

### 7. Revue des familles

La seule etape qui demande un jugement metier.

```
python outils/familles.py "<golden>" --registre audit/f.json
python outils/familles.py "<golden>" --registre audit/f.json --lister-a-revoir
python outils/familles.py "<golden>" --registre audit/f.json --marquer <id> --statut vue
```

Lire par ordre de cellules couvertes : les dix premieres familles couvrent plus
de la moitie du classeur. Le registre survit d'une passe a l'autre, mais une
famille dont le squelette a bouge **repasse a revoir**.

### 8. Sensibilite et commutateurs

```
python outils/sensibilite.py  "<golden>" --limite 12 --json audit/s.json
python outils/commutateurs.py "<golden>" --json audit/m.json
```

L'adresse du total de la batterie est trouvee toute seule ; `--batterie` la
force si besoin. Jamais exhaustifs : les modules annoncent toujours ce qu'ils
**n'ont pas** essaye — ne pas retirer cette ligne du rapport.

### 9. Mutation — ce que la batterie surveille vraiment

Elle n'evalue pas le modele, elle evalue **ses controles**.

```
python outils/mutation.py "<golden>" --echantillon 45 --json audit/mu.json
```

Ce que la mesure a donne sur une golden reelle — 45 cellules cassees a 1 %, face
aux 66 controles du modele :

```
COUVERTURE REELLE DE LA BATTERIE : 24 %   (11 detectees, 34 invisibles)
intervalle a 95 % : 12 % a 37 %

  Pocket_Price_Waterfall    9 / 14 invisibles   <- le coeur du modele
  Discount_Heads            7 /  9 invisibles
  Checks                    1 /  1 invisible    <- la feuille de controle elle-meme
```

**Trois quarts du classeur pouvaient etre fausses de 1 % sans qu'aucun des 66
controles ne bronche.** La raison vaut mieux que le chiffre : la plupart des ties
sont des identites algebriques, dont les deux membres descendent de la cellule
corrompue, bougent ensemble et ferment toujours.

> **Sortie** : le taux de corruptions detectees, et **ou tombent les angles
> morts**. Une mutation non detectee n'est pas un defaut en soi — une cellule de
> presentation n'a pas a etre surveillee. Ce qui compte est la ou sont les trous.

### 10. Vraisemblance — le classeur dit-il quelque chose de POSSIBLE ?

Les neuf etapes precedentes verifient qu'un classeur est juste **avec lui-meme** :
il boucle, il converge, ses identites ferment, ses controles surveillent quelque
chose. **Aucune ne verifie qu'il dit quelque chose de possible.** Un modele peut
passer les vingt controles d'integrite, tenir sa parite LibreOffice, et afficher une
marge d'EBITDA de 340 %, un multiple negatif ou un TRI de 900 %.

```
python outils/vraisemblance.py "<classeur>" --detail
python outils/vraisemblance.py "<classeur>" --bornes bornes.json
```

**Deux niveaux.** Les **bornes universelles** ne demandent aucune declaration — une
part hors de [-100 %, +100 %], un multiple negatif, un rendement annualise hors de
[-100 %, +300 %]. Elles sont rares et larges a dessein : une fausse alerte est le
meme defaut qu'un faux vert. Les **bornes declarees** viennent d'un fichier que
l'auditeur ecrit ; c'est le pendant, cote grandeurs, des identites imposees de
l'etape 6, et c'est un module a **jugement**, pas a verdict.

**Sans fichier de bornes, l'etape le dit** : elle n'a essaye que l'universel, et
« aucune borne declaree » n'est pas un resultat favorable.

Deux exemptions, apprises en le passant sur une golden reelle :

- **un `%` entre guillemets est un suffixe litteral** — la cellule porte alors 85
  pour 85 %, pas 0,85. Les confondre a rendu quatre fausses alertes ;
- **les lignes de controle sont exemptees** : un tie a −0,001 n'est pas un multiple
  negatif. C'est la troisieme fois que ce correctif s'impose apres I13 et I17 —
  c'est un reflexe, pas un cas.

Ce qu'elle a trouve a son premier vrai passage : quatre cellules d'input sheet
portant une **cible** (85, 62, 48, 45) sous le **format pourcentage herite de leur
ligne**, donc affichees `8500 %`, `6200 %`, `4800 %`, `4500 %` au candidat.
Arithmetiquement inoffensif, et absurde a l'ecran.

> **Sortie** : le nombre d'invraisemblances, et le nombre de bornes declarees. Zero
> borne declaree se lit comme une etape qui n'a rien essaye.

### Puis le certificat

```
python outils/certifier.py "<golden>" --familles audit/f.json --convergence audit/v.json \
    --sensibilite audit/s.json --commutateurs audit/m.json \
    --identites audit/id.json --mutation audit/mu.json --json audit/certificat.json
```

**Une preuve absente n'est pas un defaut prouve — c'est un travail non fait**,
et le certificat garde les deux distincts.

## Auditer un classeur qu'on n'a pas fabrique

La chaine a ete ecrite sur des classeurs generes par les scripts maison. Sur un
classeur etranger elle produit des **fausses alertes**, et chacune coute une
demi-heure. Deux causes restent vivantes ; deux autres ont ete corrigees :

| # | Ce qui se passe | Ce qu'il faut faire |
|---|---|---|
| 3 | **La racine, et elle est toujours la.** Convergence a froid, sensibilite, commutateurs et mutation passent tous par `rejouer.poser()`, qui fait un aller-retour `openpyxl` — `load_workbook` puis `save` — avant chaque recalcul. Sur un gros classeur il est destructeur : 883 Ko -> 447 Ko, 17 366 formules partagees mises a plat, `sharedStrings`, `calcChain` et metadonnees perdus. Le recalcul echoue ensuite, et l'outil impute l'echec au classeur. | `erreurs = -1` **n'est pas un compte d'erreurs**, c'est la sentinelle d'un recalcul rate. Ne jamais la lire comme un defaut du modele. Sur un classeur volumineux, lancer d'abord la chaine statique seule. |
| 4 | I13 signale comme « `SUM` tronquee » une ligne de controle du type `=SUM(D8:D15)-D16`, qui exclut la cellule 16 expres. Le controle n'a pas l'exemption par libelle que I17 porte deja. | Verifier le libelle avant de retenir le defaut. |

**Deux autres causes ont ete corrigees dans le moteur**, et leur correctif porte
la lecon durable : **reconnaitre une cible a ce qu'elle EST, pas a la facon dont
elle s'appelle.** La feuille d'hypotheses se trouve maintenant a l'endroit ou
pointent les plages nommees mono-cellule, et non a son intitule ; un commutateur
se reconnait a ce qu'il vaut — 0 ou 1 — et non a un prefixe `sw_`. Un module neuf
refera la faute : c'est le piege 9 du vert.

**Ce qui sauve l'outil malgre tout** : il ne rend **jamais** de faux vert. Chaque
etape qui n'a rien lu l'ecrit, et le certificat refuse de compter une preuve
absente comme un succes. Le risque, ici, est l'inverse — et une alerte qu'on
finit par ignorer ne protege plus de rien (piege 15).

## Enchainer la chaine dans une livraison

Tous les modules rendent un **code de sortie non nul** quand un defaut est
trouve : ils s'enchainent donc tels quels dans un script de livraison, sans
analyser leur sortie texte. Et `certifier.py` fonctionne meme sans les fichiers
JSON des etapes : il **plafonne** alors la couverture et inscrit les etapes
manquantes au journal, plutot que de faire comme si.

## Lire un resultat vert

Un controle vert ne prouve rien tant qu'on ne lui a pas demande ce qu'il a
compte. Les neuf pieges : **[lire un resultat vert](lire-un-vert.md)**. A lire
avant de conclure, pas apres.

## La forme du rendu

Un audit se rend en **issues log**, jamais en prose : une cle stable, le constat
chiffre, la gravite, la portee, l'effet sur les sorties, le statut. **Separer le
constat de l'effet** — un defaut qui ne deplace aucune valeur reste un defaut.
**Ne rien clore sans re-test.**

## Ce que la phase change pour le reste du pack

Un ecart trouve ici remonte en amont. Un compteur cable a zero, une reference
glissante, un tie tautologique : ce sont des **criteres de rubric qui ne
discriminent pas**, et la phase 4 les notera quand meme. Corriger le generateur
et regenerer coute moins cher que d'expliquer a un lab pourquoi sa golden viole
sa propre gate.

Le point ou la doctrine du metier ne s'applique pas — nos modeles portent des
circularites voulues, la ou un model audit les interdit — est traite dans
**[la methode d'un fonds de PE](methode-pe.md)**.

---
Navigation : [Fabriquer un pack](../SKILL.md) | [Phase 2 - Batir](02-batir.md) | [Phase 4 - Noter](04-noter.md)
