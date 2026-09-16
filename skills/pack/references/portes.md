---
title: "Les portes : une phase ne se termine que quand sa porte s'ouvre"
description: "Le protocole des portes outillees de la skill pack : le manifeste pack.json, les formats imposes de la conception et des ancrages, porte.py et son journal, le contenu de chaque porte, les relais humains, la golden par iterations, la peremption et les erreurs."
type: "reference"
status: "actif"
---

# Les portes

**Chaque phase se termine par une porte.** `outils/porte.py` lance tous les controles
de la phase, rend une ligne par controle avec son compte, et reste **FERMEE** tant
qu'une ligne n'est pas verte. Puis le owner reprend la main : c'est le **relais**. La
phase suivante ne s'ouvre qu'apres un relais `valide`.

> Decision du 16/09/2026, apres une revue de la skill : « chaque etape doit etre clean »,
> « + de relais entre IA et humain », « iteration GS ». Une sortie de phase ecrite en
> prose se declarait tenue sans avoir ete lue ; une porte ne se declare pas, elle se
> passe.

## Les commandes

```
python outils/porte.py init <dossier du pack>          pack.json, plan de CONCEPTION.md, ancrages.json ; n'ecrase rien
python outils/porte.py 1 pack.json                     la porte d'une phase : 1, 2, 3, 4, 5 ou juicing
python outils/porte.py 2 --iteration 3 pack.json       la mini-porte d'une iteration de la golden
python outils/porte.py relais 2 --iteration 3 --decision valide --note "..." pack.json
python outils/porte.py etat pack.json                  portes ouvertes, relais, peremptions
python -m unittest discover -s outils/tests            les tests des portes, sur un mini-pack synthetique
```

## Le manifeste `pack.json`

A la racine du dossier de travail du pack : **le seul endroit ou les chemins sont
ecrits**, relatifs a ce dossier ou absolus. Un champ devient obligatoire a la porte qui
le lit ; une valeur entre chevrons (`<Nom>`) compte comme non remplie.

| Champ | Des la porte | Contenu |
|-------|--------------|---------|
| `nom`, `niveau` | 1 | le nom ; `L1`, `L2` ou `L3` |
| `graine`, `conception`, `ancrages` | 1 | la graine recue, `CONCEPTION.md`, `ancrages.json` |
| `lot` / `premier_du_lot` | 1 | le dossier des packs deja livres du lot, ou `premier_du_lot: true` |
| `golden`, `input_sheet` | 2 | la golden recalculee, l'input sheet extraite |
| `certificat` | 3 | le `certificat.json` de `auditer_tout.py` |
| `prompt`, `rubric`, `rubric_source` | 4 | le prompt `.docx`, la rubric livree, sa source texte pour `noter.py` |
| `ai_output`, `score_ai_output`, `cible_score`, `paquet` | 5 | le classeur de l'AI Output, sa feuille de score claude.ai, la bande visee (`[0, 45]`), les fichiers livres |
| `juicing` | juicing | `rubric`, `rubric_source`, `score_adverse`, `note_equite` |
| `controles_du_pack` | toutes | `{"2": ["python tester.py"], "2i": [...]}` : les commandes propres au pack |

**Un controle propre au pack** imprime une ou plusieurs lignes
`PORTE <nom> | lu <N> | ecarts <M> | VERT|ROUGE|NON FAIT | <detail>`. Aucune ligne, ou un
`VERT` avec `lu 0`, rend ROUGE.

## Les formats imposes

**`CONCEPTION.md`** porte dix titres, dans cet ordre, que `porte.py init` pose : `Graine
-> pack`, `Noyau dur`, `Mecaniques et pieges`, `Boucles`, `Budget de discrimination`,
`Niveau`, `Frontieres`, `Fiche de mise en page`, `Rollout d'enonce`, `Tests de
declenchement`. Les accents et la casse ne comptent pas.

- `Graine -> pack` : une table `Element | Nature | Passage de la graine`, le passage etant
  une **citation exacte** de la graine ;
- `Mecaniques et pieges` : une table `Id | Mecanique | Famille | Piege nomme | Bonne
  reponse | Erreur plausible | Points qui tombent`, les ids `M1` a `Mn` ;
- `Boucles` : une table `Boucle | Interrupteur | Convention des pieces | Mecanique |
  Amplitude estimee` ;
- `Budget de discrimination` : la ligne `Part du pool en transcription : NN %` ;
- `Niveau` : la ligne `Niveau vise : Lk` ;
- `Fiche de mise en page` : une ligne `cle: valeur` par axe, le bandeau en hexadecimal :

```
page_de_garde: non
intercalaires: oui
noms_onglets: avec espaces
colonne_libelles: B
premiere_colonne_valeurs: E
colonne_unites: non
volet_fige: non
police: Cambria
corps: 9
bandeau: 1F4E5A
onglets_colores: non
blocs: filet sous le libelle, numerotation 1.1
nombres: millions a une decimale, negatifs (x), zero -
documents: prompt famille B, rubric famille numerotee
```

Les onze premiers axes se mesurent ; les options admises sont celles de
[la mise en page](mise-en-page.md) (`noms_onglets` : `Snake_Case`, `avec espaces`, `un
mot` ou `numerote`). Les trois derniers se relisent.

**`ancrages.json`** : une liste d'objets `id`, `mecanique` (`M1`...), `poste`, `periode`,
`cellule` (`Feuille!H42`, facultative en porte 1, obligatoire en porte 2), `valeur`,
`tolerance` (`{"relative": 0.001}` ou `{"absolue": 0.5}`), `nature` (`M`, `S` ou `D`),
`pourquoi`.

**La feuille de score** importee de claude.ai : `pourcentage`, `points`, `pool`, `source`,
`date` et `rubric_sha256`, l'empreinte de la rubric notee. Un score rendu sur une autre
version de la rubric ne compte pas.

## Ce que verifie chaque porte

| Porte | Lignes |
|-------|--------|
| **1** | `P1.plan` dix titres · `P1.niveau` conception = manifeste · `P1.graine` chaque passage trouve dans la graine · `P1.pieges` un par mecanique · `P1.boucles` au moins le plancher (L1 : 1, L2 : 4, L3 : 6), convention et mecanique renseignees · `P1.ancrages` au moins un par mecanique, complets · `P1.budget` ≤ 20 % · `P1.fiche` chaque axe dans les options admises · `P1.distance` 3 axes de structure et 2 d'habillage, dont la teinte, d'ecart avec chaque pack du lot |
| **2, iteration k** | `P2i.cache` · `P2i.iteration` · `P2i.ancrages` des mecaniques M1 a Mk · `P2i.boucles` declarees pour M1 a Mk · `P2i.atelier` si le dernier relais a ete `modifie` |
| **2** | `P2.cache` 0 erreur et 0 formule sans cache, lu dans le XML · `P2.iteration` calcPr arme · `P2.ancrages` tous atteints · `P2.boucles` ≥ plancher et ≥ declarees · `P2.inputs_morts` 0 morte et plus de 0 consommee · `P2.formules_sures` · `P2.niveau` tenu ≥ vise · `P2.mise_en_page` 0 ecart IB, 0 trop proche · `P2.input_sheet` 0 formule vers le modele, 0 lien externe, 0 groupement · `P2.iterations` 0 a n validees |
| **3** | `P3.certificat` empreinte de la golden actuelle, couverture ≥ 95 %, aucune etape non faite (cle en `0`), aucun defaut critique |
| **4** | `P4.prompt` `verifier_prompt.py` · `P4.rubric` `verifier_rubric.py` · `P4.golden_100` · `P4.amplitude` chaque boucle coupee fait tomber un critere (Excel) · `P4.tracabilite` 0 orpheline dans les deux sens |
| **5** | formules sures, hypotheses mortes, tracabilite, mise en page sur le paquet · `P5.parite` LibreOffice · `P5.audit_golden` · `P5.traces_ia` · `P5.equite` sur l'AI Output · `P5.score` dans la cible, sur la rubric actuelle · `P5.paquet` · `P5.metadonnees` · `P5.calcpr` |
| **juicing** | `PJ.golden_100` sur la rubric juicee · `PJ.score_adverse` entre 20 et 40 % · `PJ.note_equite` une entree par gate et par keystone |

**Trois verdicts.** `VERT` : quelque chose a ete lu et il n'y a aucun ecart. `ROUGE` : un
ecart, un outil qui plante, une sortie illisible, ou **rien lu**. `NON FAIT` : un livrable
absent, un champ vide, Excel ou LibreOffice absent. Seul le vert ouvre.

## Le relais

**A chaque porte ouverte, Claude s'arrete et presente toujours la meme chose :**

1. ce qui a ete fait, en quelques lignes ;
2. le tableau de la porte ;
3. **ce qui vaut un coup d'oeil** : le fichier et les cellules ou passages, **proposes,
   jamais ouverts**. La golden ne s'ouvre (`atelier.py ouvrir`) que si le owner le
   demande ;
4. la decision : `valide`, `modifie` ou `refuse`.

| Decision | Suite |
|----------|-------|
| `valide` | `porte.py relais k --decision valide` ; la suite s'ouvre |
| `modifie` | le owner retouche ; Claude relit chaque modification (`atelier.py relire --json build/ateliers/itNN.json` pour la golden, paragraphe par paragraphe pour un document), la reporte ou l'abandonne **sur la decision du owner** (`atelier.py decider`), puis repasse la porte |
| `refuse` | retour dans la phase, avec la note |

## La golden par iterations

- **Iteration 0, le squelette** : input sheet, carte des onglets, mise en page de la fiche.
- **Iterations 1 a n** : une mecanique par iteration, dans l'ordre `M1`, `M2`...
- **Finale** : la golden complete, qui passe la porte 2.

A chaque mini-porte ouverte, la golden est copiee dans
`build/iterations/GS itNN - <nom>.xlsx`. Au relais, `atelier.py relire` de cette copie
contre la precedente montre exactement ce que la mecanique a ajoute. **Pas d'iteration
k+1 sans relais k valide.**

## Le journal et la peremption

`portes.json`, a cote du manifeste, ne s'ecrit qu'en ajout : chaque passage de porte avec
ses lignes et l'empreinte de chaque fichier lu, chaque relais. **Une porte dont un
fichier a change est perimee, et toutes les suivantes avec elle** ; une porte perimee
bloque la suivante et refuse son relais. Deux exceptions, sans lesquelles la chaine se
bloquerait d'elle-meme :

- **une iteration suit sa copie figee, pas la golden vivante** : l'iteration suivante
  regenere la golden, c'est son travail ;
- **la porte 1 et les iterations suivent les ancrages sans leurs cellules** : les remplir
  est le travail de la phase 2. Changer une valeur ou une tolerance, en revanche, perime.

## Ce que les portes ne font pas

- La **phase 3 utilisee seule**, pour auditer un classeur quelconque, reste
  `auditer_tout.py` sans manifeste.
- Les packs **anterieurs au 16/09/2026** ne sont pas migres ; `init` les equipe s'ils
  adoptent les portes.
- La **notation** reste sur claude.ai : la porte n'en importe que la feuille de score.

---

Navigation : [Retour a la skill](../SKILL.md) | [Les ateliers](ateliers.md) | [Phase 2 - Batir](02-batir.md) | [La mise en page](mise-en-page.md)
