# Atelier de packs

Fabriquer de bout en bout un pack de tache d'evaluation financiere — prompt, input
sheet, golden solution, rubric — puis le noter et le passer au QA.

## Installer

```
/plugin marketplace add <ce depot>
/plugin install pack
```

Puis, dans une session :

```
/pack
```

## Commencer

**[Le mode d'emploi](skills/pack/MODE-EMPLOI.md)** — installation, prerequis, ce que
chaque phase attend de vous. Dix minutes, une seule fois.

**[Les quinze pieges](skills/pack/references/pieges.md)** — les facons dont un pack
passe au vert en etant faux. Le document le plus utile du lot.

## Il vous faut aussi

- **Python** avec `openpyxl`, et **Microsoft Excel** (seul moteur qui recalcule).
- **LibreOffice**, pour le controle de parite. Recommande.
- **Deux gabarits `.docx`** — un prompt et une rubric deja acceptes par votre
  corpus — a deposer dans `skills/pack/gabarits/`. Ils ne sont pas distribues ici :
  ce sont des documents client, demandez-les a qui vous a transmis l'atelier.

## Mettre a jour

Les ameliorations arrivent par `/plugin`. Vos gabarits ne sont jamais touches.

---

*Ce depot est genere depuis la skill source : ne pas l'editer a la main.*
