---
title: "Le contrat de la rubric"
description: "Les regles d'ecriture contractuelles - criteres autoportants, ponderation et bande du +1, constantes en config, gates, penalites, couverture du formatting - confrontees a ce que le corpus livre reellement."
type: "reference"
status: "actif"
---

# Le contrat de la rubric

Source : les *Rubric Editing & Authoring Guidelines* du client. **Elles font foi.**
Ce qui suit les resume et les confronte a ce que 19 rubrics livrees portent
reellement — l'ecart entre la regle et la pratique est lui-meme une information.

> **Le test d'acceptation dur, celui qui prime sur tout le reste : la Golden
> Solution doit re-noter exactement 100 %** contre la rubric revisee.

## 0. Ce que ce contrat regit

**Il decrit une REVISION, pas une creation.** L'entree n'est pas un sujet : c'est un
**pack complet** — rubric `.docx`, prompt `.docx`, input sheet, golden — plus une
**courte liste de puces de demande de changement**. On applique les puces ; on
n'ecrit pas une rubric depuis zero sauf demande expresse. **Tout ce qu'on ne change
pas explicitement se garde.**

C'est donc le mode d'emploi de la phase de reprise autant que celui de la phase 4.

**Quand une puce et ce contrat se contredisent : on demande avant de continuer.**

### Le livrable

La rubric revisee, le prompt revise — modifie **uniquement** selon les deux
changements permis — et **une note de changement d'une page** : ce qui a change, la
confirmation que le basculement de forme a ete applique, et chaque ligne de format
ajoutee **avec la preuve golden** qu'elle etait deja satisfaite.

**La rubric se livre en `.docx`**, dans une famille livree dont les sections sont en style
de titre — Ostrom, ou la numerotee (voir [la mise en page](mise-en-page.md)). **Jamais de
`.json` livre** : le `.json` n'est qu'un format de travail que les outils savent lire.

### La marche a suivre

1. Lire les puces, et **mapper chacune a une regle** — le repertoire du §12 le fait
   pour les demandes courantes.
2. Lire le prompt, parcourir la golden : savoir ce qu'est le modele et ce que le
   prompt demande **reellement**.
3. Editer selon la spec.
4. **Lancer la verification** : chaque ancrage se rattache a la golden, la golden
   re-note 100 %, la relecture de rendu est propre.
5. Ecrire la note de changement.

## 1. Un critere

**Atomique** — un fait par critere. Pas d'echelons, pas de prorata, pas
d'arithmetique « au cran du dessous ».

**Value-only** — un critere verifie **une valeur de sortie**. On retire toute
mention de « GS » ou « Golden », toute formule ou identite (`= Revenue - COGS`),
toute reference de cellule ou de feuille, tout commentaire de methode.
**Le corps est tronque a la valeur.**

**Autoportant, et c'est le point critique.** Chaque critere est remis au correcteur
**isole de tous les autres**, avec pour seule compagnie la regle de configuration.
Le corps doit donc nommer ce qui **desambigue quelle valeur regarder** :

```
<Entite> — <Poste> — <Periode> — <valeur>

[+2] Consolidated P&L — Gross Profit — FY2018 — 11,233,017
[+3] Corporate Admin segment — Total Revenue — FY2022B — 807,016
[+1] Location A unit P&L — Total Revenue — FY2022B — 491,985
```

**Le prefixe d'entite est obligatoire** : le meme libelle revient d'un bloc a
l'autre — `Gross Profit — FY2018` existe sur le P&L consolide **et** sur chaque
segment, avec des valeurs differentes.

On ajoute le contexte qui **desambigue**, jamais du boilerplate. Et **le signe fait
partie de la valeur** : le test par defaut y est sensible.

## 2. La ponderation

Entiers seulement. **Jamais du +1 partout, jamais une echelle d'origine
(1/2/3/5, 100 points), jamais de fractions.**

| Poids | Ce que c'est | Quantite |
|-------|--------------|----------|
| **+4** keystone | sorties integratives de haut niveau, celles ou le modele se resout | **≈ 3 en tout** |
| **+3** major | tetes de chaine, sorties de premier plan, sorties narratives cles | |
| **+2** supporting | un ancrage isole qui compte ; un ancrage representatif par onglet | |
| **+1** granular | membres de series par periode ou par segment, sous-composants, atomes de format | |

**Un `+5` d'origine se retiere en `+4`.** Et une serie de tetes par periode ne doit
pas frapper vingt keystones : on en garde ≈ 3, le reste passe en `+3`.

### La bande du `+1`

> **Part du `+1` : cible ≈ 33-47 %, plafond strict < 60 %, et ce doit rester la
> plus grosse bande.**

- Trop peu de `+1` → retrograder les membres de serie par periode en `+1`, en
  gardant la premiere periode (ou la periode representative) en `+2`.
- Trop de `+1` → promouvoir en `+2` les ancrages qui ne sont pas des membres de
  serie.

> **Ecart mesure sur le corpus.** Sur 19 rubrics livrees : 1 734 criteres en `+1`
> sur 2 554, soit **68 %** — au-dessus du plafond de 60 %, et loin de la cible
> 33-47 %. Le corpus ne tient pas sa propre bande. A verifier sur chaque pack neuf
> plutot qu'a supposer conforme parce que les voisins le sont.

## 3. Les constantes s'enoncent une fois

Le test de reussite et les unites sont des **constantes** : elles vivent **une
seule fois dans le bloc « Scoring configuration »**, et nulle part ailleurs. Pas de
tolerance repetee par ligne, **pas de note de tolerance par section**.

**Cela vaut meme quand la rubric d'origine portait des bandes absolues variables**
(±50 / ±500 / ±0,2pp) : on les remplace par un seul defaut relatif dans la config,
on ne les reporte pas sur les lignes.

### L'exception qui protege le candidat

Choisir le pourcentage par defaut pour qu'il soit **raisonnable sur le gros des
lignes**. La ou un pourcentage relatif ne l'est pas — typiquement **un taux de
faible magnitude, un TRI de quelques pour cent, ou `≤1 %` relatif s'effondre en une
bande quasi nulle** — cette ligne-la porte une bande absolue en ligne :

```
Project IRR (10-year exit) — 4.2% — pass if within ±0.3pp
```

Le defaut continue de gouverner toutes les autres.

**Une pass text en ligne ne sert qu'aux vraies exceptions** : un zero exact (une
bande relative n'est pas definie a 0), un zero sur toutes les periodes, un evenement
exact, un seuil (`pass if ≥ 2.5x`), un profil (`monotonically non-decreasing`), ou
la bande absolue ci-dessus. **Jamais pour redire le defaut.**

## 4. Les gates

Une gate est **une seule puce, la derniere de sa section**. Elle est **elle-meme un
critere note** — elle porte un `[+N]` et rapporte ces points quand sa condition
tient — **et** elle garde sa section : si le build la rate, **toute la section vaut
0**, ses propres points compris, plancher a 0, **hors plafond de penalites**.

```
[+N] <Nom> gate — <condition>. If not met, every <perimetre nomme> criterion
     in this section scores 0.
```

- **Nommer le perimetre explicitement** — « every Corporate Admin segment criterion
  in this section » — jamais « this segment » ni « the section » tout court.
- **Le perimetre, c'est la section entiere** : on dessine donc **les frontieres de
  section autour de la methode de la gate**. Une gate n'a sa place dans une section
  que si la rater doit invalider **tous** ses atomes.
- **Au plus une gate par section.** S'il en faut deux, on scinde la section.
- Poids selon l'importance de la methode : **+2** (methode secondaire) ou **+3**
  (methode structurelle majeure). Les gates comptent dans le pool positif.

> **Le corpus est partage** : 17 rubrics sur 19 portent des gates de section, dont
> 15 enoncent la mise a zero. Une seule les abolit explicitement — « no criterion
> gates, guards or zeroes any other criterion or any section » — c'est une
> exception, pas la regle.

## 4 bis. Des criteres independants, pas une cascade

**Decision du 16/09/2026 : une faute unique n'emporte pas la rubric.** Une rubric ou une
seule erreur en tete de chaine fait tomber la majorite des points penalise la meme faute
plusieurs fois. C'est un defaut d'equite, meme quand il aide a passer sous 45 %.

Ce contrat note des valeurs isolees contre la golden (section 1) : il ne peut pas noter
« sur les chiffres du candidat ». L'independance se construit donc dans la tache
([phase 1, section 2](01-concevoir.md#des-difficultes-independantes-pas-une-cascade)), et
la rubric la respecte :

- **une valeur notee = une mecanique**, lue sur des donnees fournies, en deux etapes au
  plus ;
- **les valeurs terminales** (un total, la decision finale) portent un ou deux criteres,
  pas une section ;
- **une gate ne met a zero que son module** : la section qu'elle garde est dessinee
  autour d'une seule mecanique ;
- quand les sorties s'enchainent, l'aval se note sur des grandeurs qui ne dependent pas
  de l'amont (ratios par dollar, effets unitaires).

**Controle** : pour chaque piege nomme, poser l'erreur dans une copie de la golden,
recalculer, renoter avec `noter.py` ; seuls les criteres de son module doivent tomber.

## 5. Les penalites

- **Plafond = `round(0,20 x pool positif)`.** `Final = max(0, positifs − min(penalites, plafond))`.
- **Un jeu equitable en compte 5 a 7.** Moins, on etoffe ; un jeu deja equitable se
  preserve.
- Chacune tire **au plus une fois**, sur une erreur **affirmative** de methode, de
  signe ou de perimetre **qui atterrit quand meme dans la tolerance** — donc qu'aucun
  critere de valeur n'a deja attrapee.
- On garde les poignees `[Pn]` sur les penalites ; on retire toutes les poignees
  `[ID]` des criteres.

### La carve-out, et le piege qui n'est pas celui qu'on croit

Une penalite **qui recouvre une gate** doit le dire **en toutes lettres** :

```
not charged if the <nom de section> gate already scored 0
```

**En mots, jamais par un identifiant.** Le but est de **ne pas facturer deux fois la
meme erreur**.

> **Ou ca derape.** Sur un pack reel, **les sept** penalites portaient cette clause,
> y compris celles dont l'erreur ne fait pas tomber la gate : toutes inertes, et le
> plafond inatteignable par construction. La clause est **prescrite**, mais
> seulement pour une penalite qui **recouvre reellement** sa gate. Le controle reste
> le meme : **pour chaque penalite, exhiber un build qui la declenche.**

## 6. Ne noter que ce que le prompt demande

Avant de noter quoi que ce soit : **le verifier contre le prompt**, et confirmer que
**la golden le produit reellement**. Si une exigence saillante du prompt n'est pas
notee, on l'ajoute ; si un critere note n'est pas dans le prompt, on le retire — ou,
pour du formatting, on l'ajoute au prompt selon les deux leviers.

## 7. Couvrir les onglets constituants, par echantillon

Un modele multi-onglets porte des onglets constituants (P&L par unite, echeanciers)
qui remontent dans les blocs de tete. Prouver que chacun est **bati, par un ancrage
de valeur** — pas par une affirmation de presence, qu'un correcteur ne peut pas
verifier.

**Echantillonner** : un ancrage representatif par onglet — son chiffre d'affaires a
une periode ou il a de l'activite, ou un zero exact la ou le prompt l'impose — prouve
que l'onglet existe *et* qu'il est juste, et rend une gate de roll-up utile. Ces
ancrages vivent dans leur propre section, sous une gate d'unites.

## 7 bis. Noter le resultat de chaque boucle

**Decision d'Amir du 16/09/2026** : les boucles de circularite sont un prerequis du pack, et
**leurs resultats se notent dans la rubric**. Une boucle que la rubric ne mesure pas ne compte
pas comme boucle.

- **Au moins un critere par boucle, sur la valeur qu'elle resout elle-meme** : la cellule qui
  ferme le cycle ou sa sortie immediate (le principal rembourse, la commission, le montant
  grossi). Un total en aval qui absorbe la boucle ne suffit pas.
- **Sa tolerance est plus serree que l'amplitude de la boucle** : coupee, la boucle fait
  echouer ce critere. Quand le defaut relatif l'absorbe, le critere porte sa bande absolue en
  ligne — l'exception de la section 3 —, justifiee par la grandeur : un montant qui se regle
  au cent, un taux resolu.
- **Poids** : `+2` au moins (ancrage significatif), `+3` si la boucle est une tete de chaine.
- **Controle** : `amplitude_boucles.py` coupe chaque interrupteur et renote la golden. Chaque
  boucle doit faire tomber **au moins un critere** ; zero point perdu = boucle decorative = pack
  non conforme au prerequis.

## 8. Le compte

**75 a 200 criteres, en guide.** En dessous de 75, scinder les atomes qui empilent
plusieurs valeurs ou plusieurs periodes. Un modele multi-entites vraiment gros
depasse legitimement 200 : **mieux vaut une couverture autoportante complete que
rester sous le plafond en echantillonnant des sorties exigees.**

> Mesure : de **84 a 221** criteres sur le corpus.

## 9. Le formatting, et les deux leviers

L'objectif est de noter **autant de la presentation qu'il est legitime**. Deux
conditions **non negociables** gouvernent chaque atome :

- **(A)** la convention est **enoncee dans le prompt** ;
- **(B)** la **golden la respecte** — verifie en ouvrant le classeur, sur les vraies
  cellules.

| Dans le prompt ? | La golden la respecte ? | Action |
|---|---|---|
| oui | oui | **ajouter l'atome** — levier 1 |
| oui | non | **ne pas ajouter, signaler** : prompt et golden se contredisent |
| non | oui | **on peut l'ajouter au prompt puis la noter** — levier 2, et seulement si c'est de la presentation |
| non | non | **jamais.** On n'invente pas de convention |

**A sans B casse le test des 100 %** — la golden echouerait sa propre rubric.
**B sans A** note quelque chose qu'on n'a jamais demande a l'agent.

**Levier 1** : la ou le prompt enonce une convention *par section*, ecrire **un
atome par entite ou par bloc** plutot qu'un atome global — chacun autoportant et
citant la phrase du prompt qu'il fait respecter.

**Levier 2** : ajouter une instruction de format au prompt, puis la noter. Procedure
stricte : choisir la candidate, **ouvrir la golden et confirmer qu'elle le fait
deja** (pas de memoire, pas depuis le prompt), sinon **s'arreter** ; **ajouter** une
instruction **specifique et binaire** a la section de sortie xlsx ; verifier qu'elle
**ne change aucun nombre** ; verifier qu'elle n'en contredit aucune autre ; ecrire
les atomes ; consigner la ligne ajoutee et la preuve golden dans la note de
changement.

**Un atome de format** est observable dans la forme reellement livree, **binaire**,
autoportant et citant le prompt, **jamais une valeur deguisee**, et non redondant.
Poids **+1** pour l'essentiel, quelques **+2** pour une structure vraiment
importante.

> Mesure : la section de formatting est presente dans **19 rubrics sur 19**, part
> mediane **5,5 %** du pool.

## 10. Ce que le prompt a le droit de recevoir

**Deux changements, et rien d'autre.** Ni reformatage, ni restructuration, ni
reformulation, ni reordonnancement d'aucune instruction existante.

1. **Le basculement de forme du livrable**, prescrit et applique une fois par pack :
   retirer *« Provide the full answer as text only (not an .xlsx file). »* partout,
   et remplacer l'introduction de sortie xlsx par *« Create a formatted Excel (.xlsx)
   file to the following specifications. »* C'est **la seule edition qui touche du
   texte existant**, et elle ne change que la **forme** du livrable — jamais le
   modele, les entrees ni une valeur.
2. **Des exigences de format ajoutees** (levier 2), strictement additives.

**Ligne dure** : toute amelioration qui demanderait de toucher autre chose est
**hors perimetre** — on ne le fait pas, on le signale.

## 11. La forme du document

Le rendu n'est pas laisse libre — un correcteur automatique lit la rubric par sa
structure (piege 2 : des titres en gras au lieu d'un style de titre lui ont fait
examiner **zero critere**).

- **Un titre H1**, puis un bloc H2 **« Scoring configuration »** de **4 a 6 puces** :
  atomique + value-only + autoportant ; la ponderation 1-4 ; la regle unique de test
  et d'unites ; le pool positif et le re-scoring a 100 % ; le mecanisme de gate — un
  critere note qui met aussi toute sa section a zero, **hors plafond** ; la formule
  du plafond de penalites ; et que chaque item trace vers le prompt.
- **Chaque section** : un H2 `Section X — Nom (N atoms [+ 1 gate], M points)`, les
  criteres de valeur en puces `[+N] <entite — poste — periode — valeur>`, puis la
  gate en **derniere puce**.
- **`Section P — Penalties`** en fin, avec `[−N] [Pn] <corps>`.
- **Des puces partout**, marqueur en tete. **Aucune note de tolerance par section.**

## 12. Le repertoire des demandes courantes

Chaque puce de demande se mappe a une regle. Les huit qui reviennent :

| La demande | Ce qu'on fait |
|---|---|
| « plus de formatting » | les deux leviers : un atome par entite pour une convention deja enoncee, et ajouter au prompt une convention que la golden respecte deja |
| « les criteres manquent de detail / ne se notent pas seuls » | ajouter le prefixe d'entite et le contexte entite-poste-periode-valeur |
| « evitez la repetition » | remonter tolerance et unites en configuration, **une fois** ; retirer les notes par ligne et par section |
| « les gate checks devraient avoir un score » | donner un `[+N]` a chaque gate, garder la mise a zero de section, nommer son perimetre |
| « couvrez les onglets » | un ancrage de valeur echantillonne par onglet requis, dans une section d'unites sous une gate d'unites |
| « ne testez que ce que le prompt demande » | retirer les criteres non demandes ; ajouter les exigences saillantes non notees |
| « trop grossier / une gate deborde » | **scinder la section** pour que la methode de la gate gouverne exactement ses atomes |
| « re-tierer depuis une echelle 1/2/3/5, plate ou sur 100 » | mapper sur 1-4, `+5 → +4`, garder ≈ 3 keystones, ramener la part du `+1` dans sa bande |

## 13. La verification, avant livraison

- **Recalculer sur une copie** de la golden, jamais sur l'original.
- **Modeles circulaires** : un recalcul naif corrompt silencieusement les cellules
  circulaires (tresorerie ↔ interets ↔ sweep, WACC ↔ VE) ou leve des erreurs moteur.
  **Quand le recalcul diverge des valeurs en cache d'origine, ce sont les valeurs en
  cache qui font foi** (`data_only=True`) — et on signale dans la note de changement
  que la notation doit passer par Excel en calcul iteratif, jamais par un recalcul
  naif.
- **Chaque ancrage cite se rattache a la golden**, sur les valeurs en cache. **0 echec.**
- **La golden re-note 100 %** : chaque valeur dans la tolerance, chaque gate tenue,
  chaque atome de format tenu, **aucune penalite ne tire**.
- **Relecture de rendu** : prefixe d'entite sur chaque ligne de valeur ; 0 poids
  fractionnaire ; 0 poignee `[ID]` sur un critere ; `[Pn]` conserves ; 0 artefact
  `(gate-check)`, `GS =` ou reference de cellule ; une pass text en ligne uniquement
  sur une vraie exception ; les points de section somment au pool ; **la part du `+1`
  dans sa bande** ; ≈ 3 keystones.

## 14. Le controle mecanique

Dix des regles ci-dessus se mesurent, et elles sont branchees dans l'orchestrateur
du QA — le contrat ne vit donc plus seulement en prose :

```
python outils/verifier_rubric.py "Rubric - <Pack>.docx"     # ou le .json de travail ; seul le .docx se livre
```

Sortie attendue : `VIOLATIONS DE CONTRAT : 0`, chaque regle avec son compte et son
denominateur. **Calibre sur les 45 rubrics livrees du corpus** — c'est ce balayage
qui a corrige trois de mes propres faux positifs, dont un qui prenait 58 criteres
**structurels** pour des criteres de valeur mal ecrits.

Ce que le balayage a trouve, et qui vaut pour se comparer :

| Regle | Rubrics du corpus en echec |
|---|---|
| part du `+1` au-dessus du plafond de 60 % | **24 / 45** |
| 5 a 7 penalites | 31 / 45 *(a juger)* |
| environ 3 keystones | 13 / 45 *(a juger)* |
| **prefixe d'entite** sur chaque critere de valeur | **13 / 45** |
| poids hors `{1,2,3,4}` | 6 / 45 |
| plus d'une gate par section | 5 / 45 |
| tolerance redite en ligne | 4 / 45 |
| poignee `[ID]` restee sur un critere | 4 / 45 |
| formule ou reference de cellule dans un corps | 2 / 45 |

Le defaut de prefixe est le plus couteux : `Total cash interest — Year 1 — 33.8`
n'a pas d'entite, et le meme libelle vit sur plusieurs blocs. C'est le critere qui
fait echouer un candidat juste.

**Le module ne juge pas les valeurs** — `noter_rubric.py` le fait, en rejouant la
golden. Il juge la forme, celle dont depend la gradabilite.

## 15. L'auto-controle

Treize cases, toutes a cocher avant de livrer :

```
[ ] chaque critere autoportant : entite, poste, periode, valeur sur la ligne
[ ] value-only ; corps tronques a la valeur ; les zeros exacts se declarent
[ ] constantes en configuration une fois ; aucune repetition par ligne ni par section
[ ] gates notees, <= 1 par section, perimetre nomme ; sections dessinees autour
[ ] section de formatting presente ; chaque atome trace vers le prompt ET respecte par la golden
[ ] prompt edite : chaque ligne ajoutee est satisfaite par la golden et consignee
[ ] onglets constituants couverts par ancrage de valeur, pas par presence
[ ] poids dans {1,2,3,4} ; ~3 keystones ; part du +1 entre 33 et 47 %
[ ] penalites 5 a 7, plafond round(0,20 x pool), chacune tire une fois
[ ] ancrages rattaches aux valeurs EN CACHE ; hasard circulaire signale
[ ] chaque boucle notee : >= 1 critere sur sa valeur resolue, qui tombe quand on la coupe
[ ] criteres independants : chaque erreur nommee ne fait tomber que son module
[ ] la golden re-note 100 % ; le docx valide, aucun .json livre
```

---

[Retour a la skill](../SKILL.md) | [Phase 4 - Enoncer et noter](04-noter.md) | [Le contrat du prompt](contrat-prompt.md)
