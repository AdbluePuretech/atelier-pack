---
title: "Les gabarits de document"
description: "Ou deposer le prompt et la rubric d'exemple du corpus, sans lesquels le format ne peut pas etre repris."
type: "reference"
status: "actif"
---

# Les gabarits

Deposer ici **un prompt et une rubric deja acceptes par le corpus**, au format
`.docx` — ou, mieux, pointer `PACK_GABARITS` sur le dossier ou ils vivent deja et
ne rien copier du tout.

**Les noms sont imposes par l'outil :**

| Fichier attendu | Profil | Ce que le profil rend |
|---|---|---|
| `Rubric - Ostrom.docx` | `ostrom` | un `Title`, un `Heading1` par section |
| `Prompt - Project_Madrid.docx` | `madrid` | titre gras 16, paragraphe d'attaque |

`ostrom` et `madrid` sont des **profils de rendu**, pas des packs au choix : chacun
lit la structure de styles de son document. Le nom vient du pack qui a servi de
modele quand l'outil a ete ecrit — c'est un accident historique, pas une
convention.

`txt_vers_docx.py` part de ces fichiers, copie toutes les parties de leur paquet —
styles, numerotation, theme, reglages, table de polices — et ne regenere que le
contenu. C'est ce qui produit un vrai document au bon format plutot qu'une
imitation.

**Sans eux, l'outil ne peut pas travailler.** Et un format reconstitue de memoire se
voit immediatement : les puces ne sont plus des puces, les titres ne sont plus des
styles de titre, et les outils qui lisent le document par ses styles deviennent
aveugles.

## Nommage

L'outil connait ses gabarits par un nom court, declare en tete de
`../outils/txt_vers_docx.py`. Ajouter un gabarit, c'est deposer le `.docx` ici et
ajouter son nom a cette table.

Le dossier peut aussi etre designe ailleurs par la variable d'environnement
`PACK_GABARITS`.

## Pourquoi ils ne sont pas versionnes

Ce sont des documents du corpus client. Ils se recuperent aupres de celui qui
fournit le corpus, ils ne se redistribuent pas avec la skill.

---

[Retour a la skill](../SKILL.md) | [Les contrats de format](../references/contrats-format.md)
