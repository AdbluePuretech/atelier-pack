# Lire un resultat vert

> **COPIE.** L'original vit dans la skill `audit-modele`. `/pack` en
> embarque un double parce qu'il est distribue en plugin et doit
> fonctionner seul. Corriger l'original d'abord, puis recopier.

Les pieges propres a l'audit d'un classeur. Chacun a produit un vert imperite au
moins une fois. Le remede est toujours le meme : **demander au controle ce qu'il
a compte**, et confronter ce nombre a ce qu'on attendait.

## 0. Un cache n'est pas un resultat de calcul

Le piege le plus grave, et le plus invisible : **un classeur genere par un
script porte des valeurs que le script a calculees lui-meme**. Le fichier
s'ouvre, s'affiche, ses chiffres sont plausibles, et Excel ne les a jamais
produits. Sur un classeur circulaire c'est fatal : le point fixe de Python
n'est pas celui d'Excel.

**Ce qui le revele**, sans rien recalculer :

- `xl/calcChain.xml` absent du conteneur - Excel n'a jamais construit de chaine
  de calcul pour ce fichier ;
- `docProps/app.xml` qui annonce `Openpyxl` plutot que `Microsoft Excel` ;
- et la preuve arithmetique, la plus jolie : **un `ROUND(x, 6)` ne peut rendre
  qu'un multiple de 1e-6**. Un cache de `1,08e-89` sur une cellule qui arrondit
  a six decimales prouve que la valeur n'a pas ete produite par la formule qui
  l'accompagne. Aucun recalcul necessaire pour le dire.

Le meme raisonnement se generalise a toute formule dont la sortie est
contrainte : un compteur qui doit etre entier, une part qui doit etre dans
[0, 1], un drapeau qui vaut 0 ou 1. Chercher les caches qui violent la
contrainte de leur propre formule.

## 1. Une reference vers une cellule vide rend zero

Le piege le plus couteux, parce qu'il frappe l'organe de controle lui-meme.
Une batterie qui reprend chaque tie "par reference a la feuille qui le porte"
peut pointer sur des cellules qui n'existent pas : Excel rend 0, la batterie
somme a zero, et elle ne certifie rien.

Cas typique : un tie NON periodique - une reconciliation de volume de base, par
exemple - etire sur dix colonnes de periode. Une seule colonne porte le calcul,
les neuf autres lisent du vide.

**Ce qui le revele** : compter, pour chaque cellule de controle, si toutes ses
references pointent sur une cellule inexistante. Le rapport utile n'est pas
"la batterie ferme a zero" mais "N lignes sur M, et K cases sur L pointent sur
du vide".

## 2. Un seuil de cache a 90 % n'est pas un standard

Une valeur notee se lit dans le cache de calcul. Une cellule sans valeur en
cache est une cellule qu'un correcteur ne peut pas lire sans recalculer - et
recalculer un classeur circulaire sans iteration armee corrompt tout.

Un controle "le cache est plein a plus de 90 %" laisse donc passer des milliers
de cellules muettes. **Pour une reference, la barre est 100 %**, et l'ecart se
liste cellule par cellule.

## 3. Un IF dans un circuit n'est pas forcement une marche

Une marche - IF a seuil, MIN, MAX - placee DANS un circuit fait osciller le
point fixe au lieu de le faire converger. Mais un `IF` dont le test ne lit que
des masques, des constantes ou des cellules situees hors du circuit est **fige
pendant l'iteration** : la fonction reste continue en ses variables de boucle,
et c'est une construction parfaitement legitime.

**Ce qui le revele** : isoler le test de chaque marche - le premier argument
d'un IF, tous les arguments d'un MIN ou d'un MAX - et regarder s'il lit une
cellule du **meme** circuit. Sans cette distinction, un detecteur naif rend des
centaines de faux positifs et fait condamner un classeur sain.

Corollaire utile : la presence de la forme lissee `0.5*(a+b+SQRT((a-b)^2+eps))`
quelque part dans le classeur est un bon signe. Elle dit que l'auteur savait
qu'un MAX ne passe pas dans un circuit, et qu'il l'a remplace la ou il fallait.

## 4. Un decompte fait sur un echantillon ment

Une ventilation calculee sur les 400 premiers elements d'une liste de 4 700
donne une repartition fausse, et elle a l'air serieuse. Tronquer l'**echantillon
affiche** est bon ; tronquer la **liste comptee** ne l'est jamais.

## 5. Un litteral dans une formule n'est pas forcement un parametre

Un detecteur de valeurs codees en dur signale les positions d'`INDEX`, les
indices de tranche et les exposants au meme titre qu'un taux enfoui. Le compte
de cellules ne dit rien : **ventiler par valeur distincte**. Douze constantes
distinctes reparties sur 4 000 cellules, c'est douze choses a tracer, pas
4 000.

## 6. Un IFERROR est presque toujours un defaut

Il transforme une erreur visible en valeur plausible. Dans un modele
d'evaluation, c'est exactement ce que l'audit cherche a empecher : le controle
"aucune valeur d'erreur dans le classeur" passe alors pour la mauvaise raison.
Chercher les deux ensemble, jamais l'un sans l'autre.

## 7. Une plage nommee inutilisee peut cacher une hypothese morte

Inoffensif en soi. Mais si une entree porte un nom que personne ne consomme, il
faut verifier qu'elle est bien lue par ailleurs, par reference de cellule. Une
hypothese qui n'entre nulle part dans le calcul est une hypothese morte, et elle
ment sur ce que le modele prend en compte.

## 8. Une convergence constatee n'est pas une convergence prouvee

Le classeur converge sur les entrees livrees. Cela ne dit rien de son
comportement ailleurs. Un point fixe peut etre stable sur un jeu d'hypotheses et
osciller sur le voisin - c'est precisement ce que l'etape de sensibilite
cherche, et pourquoi elle ne se saute pas.

## 9. Un detecteur qui ne trouve rien se lit comme « rien a signaler »

C'est le piege le plus couteux, parce qu'il ne porte sur aucune cellule : il
porte sur l'outil. Une etape qui cherche ses cibles par convention de nommage
n'en trouve aucune sur un classeur qui nomme autrement, et rend alors
`0 configuration KO` - un vert parfait, obtenu sans avoir rien essaye.

Mesure sur une golden reelle, en une seule passe :

| Etape | Ce qu'elle cherchait | Ce que le classeur portait | Rendu |
|-------|----------------------|-----------------------------|-------|
| Sensibilite | plages `i_*` | 101 plages `Inp_*` | 0 hypothese flexee |
| Commutateurs | plages `sw_`, `b_`, `br_` | `Prog_On`, `BreakCirc`, ... | 0 bascule essayee |
| Integrite I1 | feuille `01. Input_Sheet` | feuille `Input_Sheet` | 1 802 hypotheses comptees en defauts |

Les deux premieres se presentaient vertes ; la troisieme noyait sept vrais
defauts sous 5 874 faux. La regle : **avant de lire le verdict d'une etape,
lire son denominateur.** Une etape qui annonce zero cible n'a pas reussi, elle
n'a pas tourne - les modules le disent maintenant eux-memes et sortent en
erreur, mais un module neuf refera la faute.

Le correctif de fond est le meme partout : reconnaitre une cible a ce qu'elle
EST, pas a la facon dont elle s'appelle. Un commutateur, c'est une cellule qui
vaut 0 ou 1 ; une feuille d'hypotheses, c'est celle ou pointent les plages
nommees.

---
Navigation : [Fabriquer un pack](../SKILL.md) | [Phase 3 - Certifier](03-certifier.md) | [Moteur d'audit](../../../../systeme/scripts/audit-modele/README.md)
