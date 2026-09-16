---
title: "Les ateliers avec l'auteur pendant la construction de la golden"
description: "Le protocole qui invite l'auteur du pack a modifier lui-meme la golden a chaque mecanique : copie de travail ouverte dans Excel sur la bonne cellule, essais proposes, relecture cellule par cellule, report ou abandon decide par l'auteur, garde-fous."
type: "reference"
status: "actif"
---

# Les ateliers avec l'auteur

La golden est generee par un script. C'est ce qui la rend reproductible, et c'est aussi ce qui en eloigne l'auteur : il
ne voit le modele qu'une fois fini, et ses intuitions de metier arrivent trop tard pour changer la construction.

Un **atelier** corrige ca. A chaque mecanique ajoutee a la golden, l'auteur ouvre le classeur **sur la cellule qui
compte**, fait ses propres essais, modifie ce qu'il veut, et chaque modification est ensuite **reportee dans le
generateur ou abandonnee, sur sa decision**.

> Protocole demande par Amir le 16/09/2026, en ouvrant la construction de Cobalt v5 : « pendant la construction de la
> GS, tu m'invites a faire des modifications par moi-meme dans le modele, et tu me rends dessus directement ».
>
> **Precise le meme jour, a la revue de la skill : pas besoin d'ouvrir la GS a chaque fois sur la cellule, juste
> proposer au owner de regarder.** L'atelier est desormais le relais de chaque iteration de la golden (voir
> [les portes](portes.md)) : Claude **propose**, et n'ouvre Excel que si le owner le demande.

## Quand

- **A chaque iteration de la golden**, quand sa mini-porte s'ouvre (`porte.py 2 --iteration k`) : une mecanique par
  iteration, batie, recalculee et verifiee. Jamais sur un classeur qui porte encore des erreurs : l'auteur jugerait un
  defaut de construction.
- **Sur la golden complete**, au relais de la porte 2, avant la certification et la livraison.
- A la demande de l'auteur, a tout moment.

## Le deroule

1. **Proposer, sans rien ouvrir**, en trois parties courtes :
   - **ce que la mecanique fait**, en une phrase, et ou elle se lit (onglet, lignes) ;
   - **deux ou trois essais precis** : « passe la semaine du choc de 7 a 8 en `Input_Sheet!E812`, regarde la date de
     terminaison en `Termination!D14` ; coupe l'interrupteur de la boucle en `Controls!D9`, regarde K » ;
   - **ce qu'il peut modifier librement** : les entrees, les formules, la mise en page ; rien n'est interdit, tout sera
     relu.

   S'il valide sans regarder, c'est son droit : le relais s'inscrit `valide`, et l'atelier s'arrete la.

2. **S'il veut modifier**, preparer une copie de travail, jamais le fichier que le generateur ecrit, et ne l'ouvrir
   dans une **nouvelle** instance d'Excel **que s'il le demande** :

   ```
   python outils/atelier.py preparer "<golden recalculee>" --atelier "<build>/ateliers/GS atelier 03 - <Pack>.xlsx"
   python outils/atelier.py ouvrir "<copie>" --cellule "Input_Sheet!E812"          # seulement sur demande
   ```

3. **Attendre « fait »**. L'auteur enregistre et ferme le classeur. Le relais s'inscrit `modifie`.

4. **Relire**, cellule par cellule, contre la golden d'origine, en ecrivant le fichier que la mini-porte lira :

   ```
   python outils/atelier.py relire "<copie>" --reference "<golden recalculee>" --suivre "Termination!D14" --json "<build>/ateliers/it03.json"
   ```

   L'outil refuse de lire un classeur encore ouvert. Il rend le nombre de cellules comparees, puis chaque modification
   avec son libelle de ligne, son en-tete de colonne, l'avant et l'apres, et la valeur des cellules suivies.

5. **Resumer a l'auteur ce qu'il a change**, en langage de metier, et lui demander, **modification par modification** :
   - **la reporter** : une entree devient un parametre du generateur ; une formule devient du code du generateur ; si
     elle change une regle, le modele de reference change aussi, et les ancrages et la table des pieges sont rejoues ;
   - **ou l'abandonner** : c'etait un essai.

   Chaque decision s'inscrit dans le fichier :

   ```
   python outils/atelier.py decider "<build>/ateliers/it03.json" --cellule "Termination!D14" --decision reportee
   ```

6. **Regenerer, recalculer, repasser la mini-porte.** Elle refuse de s'ouvrir tant qu'une modification n'a pas de
   decision, ou qu'une modification `reportee` ne se retrouve pas dans la golden regeneree. Puis montrer l'effet a
   l'auteur, et reprendre le relais.

## Les garde-fous

- **Le generateur reste la source de verite.** Une modification non reportee disparait au prochain build : le dire
  a l'auteur a chaque atelier, en listant ce qui n'a pas ete reporte.
- **Ne jamais ecrire dans un classeur ouvert.** AutoSave ecrase l'une des deux versions sans prevenir. Le generateur
  ecrit ailleurs que la copie d'atelier ; `relire` verifie l'absence du fichier de verrou `~$` avant de lire.
- **Ne jamais fermer ni tuer une instance d'Excel** qu'on n'a pas ouverte : une autre session peut s'en servir.
- **Une copie par atelier**, numerotee, jamais ecrasee : elle garde la trace de ce que l'auteur a essaye.
- **Un report se prouve** : apres regeneration, la cellule reportee porte la modification de l'auteur, et la golden
  retombe sur le modele de reference mis a jour (0 ecart), sinon le report n'est pas fini.
- **Une modification qui touche l'equite** (une regle, un choc, un rang) repasse par la double lecture a l'aveugle
  avant d'entrer dans la golden.

## Ce que l'atelier ne remplace pas

Il ne remplace ni la verification contre le modele de reference, ni la certification de phase 3. Il ajoute la seule
chose que ces controles ne donnent pas : **le jugement de l'auteur sur le modele pendant qu'il se construit.**

---

Navigation : [Retour a la skill](../SKILL.md) | [Les portes](portes.md) | [Phase 2 - Batir](02-batir.md) | [Les outils](../outils/README.md)
