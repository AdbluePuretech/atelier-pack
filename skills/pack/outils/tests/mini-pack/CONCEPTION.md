# Conception - Essai

## Graine -> pack

| Element | Nature | Passage de la graine |
|---------|--------|----------------------|
| Fee on net proceeds | mecanique | a fee computed on the net proceeds it reduces |
| Interest on net proceeds | mecanique | interest accrues on those net proceeds |
| Net proceeds | sortie | Outputs: net proceeds |

## Noyau dur

La commission se calcule sur le net qu'elle reduit : un point fixe.

## Mecaniques et pieges

| Id | Mecanique | Famille | Piege nomme | Bonne reponse | Erreur plausible | Points qui tombent |
|----|-----------|---------|-------------|---------------|------------------|--------------------|
| M1 | Commission sur le net | auto-reference | commission sur le brut | 1,96 | 2,00 | fee, net |
| M2 | Interets sur le net | chaine | interets sur le brut | 4,90 | 5,00 | interest |

## Boucles

| Boucle | Interrupteur | Convention des pieces | Mecanique | Amplitude estimee |
|--------|--------------|-----------------------|-----------|-------------------|
| Commission sur le net | Brk_Fee | la commission est due sur le net verse | M1 | 0,04 |

## Budget de discrimination

Part du pool en transcription : 15 %

## Niveau

Niveau vise : L1

## Frontieres

Pas de fiscalite.

## Fiche de mise en page

page_de_garde: non
intercalaires: non
noms_onglets: Snake_Case
colonne_libelles: C
premiere_colonne_valeurs: E
colonne_unites: non
volet_fige: non
police: Arial
corps: 9
bandeau: 1F2A36
onglets_colores: non
blocs: libelle gras seul
nombres: deux decimales, negatifs (x)
documents: prompt famille C, rubric famille Ostrom

## Rollout d'enonce

M1 : une passe.

## Tests de declenchement

Commission a 0 % : la boucle disparait.
