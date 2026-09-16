---
title: "Juicer une rubric"
description: "Le protocole impose par Amir quand il demande de juicer une rubric : la golden re-note 100 %, une sortie de modele frontiere tombe entre 20 et 35 % (plafond 40 %), par la structure et sous garde-fous d'equite bloquants ; comment l'appliquer avec les outils de la skill"
type: "reference"
status: "actif"
---

# Juicer une rubric

**Declencheur** : Amir dit « juice », « juicer la rubric », « juice la rubric de <pack> ». On applique
alors le protocole ci-dessous **tel quel** — il prime sur le [contrat de la rubric](contrat-rubric.md)
la ou les deux divergent (voir « Ce qui change par rapport au contrat »). Recu le 14/09/2026, sur
Livorno, AI Output a 82 %.

## Comment l'appliquer avec la skill

1. **L'echantillon adverse** : l'AI Output officiel (Claude for web, conversation neuve, sans la
   rubric). Il n'a jamais vu la rubric, donc il reste un echantillon valide pour **chaque version**
   de la rubric : on le renote a chaque edition sans le rejouer. S'il n'existe pas, le lancer avant
   toute edition (voir la fiche Caliper, chaine de production, point 5).
2. **Les deux feuilles de score** : la golden par `noter.py` (adresses de la golden) ; l'adverse par
   un correcteur ligne a ligne qui lit SES cellules (son classeur n'a pas la mise en page de la
   golden) : une table critere -> cellule du candidat, puis le meme test que la rubric. Chaque
   critere rend passe / echoue avec la valeur lue ; chaque gate, la valeur hors bande ET la
   construction fautive qui la font tomber.
3. **Avant d'editer, lire pourquoi l'adverse perd.** Chaque point perdu se classe : erreur de
   mecanique reelle (levier legitime), ambiguite de l'enonce (a corriger dans le pack, jamais a
   exploiter), affichage ou libelle (a neutraliser par une tolerance de chemin). On juice seulement
   sur la premiere famille.
4. **Un seul echantillon est fragile.** Des gates concentrees sur l'erreur d'un seul run font
   remonter un autre run qui ne la commet pas. Le dire dans le rapport, et recommander un second
   AI Output quand les gates tiennent sur une seule mecanique.
5. **La rubric ne rattrape pas une tache trop facile** : si l'adverse est juste presque partout,
   aucune rubric equitable ne l'amene a 35 %. Le dire, et renvoyer au pack (phase 1).

## Ce qui change par rapport au contrat

| Contrat de la rubric | Mode juicing |
|---|---|
| gates notees `[+N]`, dans le pool | gates a **+0** : elles gardent la mise a zero de section, sans points |
| part du `+1` entre 33 et 47 % | libre : les points de routine se retirent ou se regroupent (levier 1) |
| pool de 200 | pool honnete, declare, sans remplissage |
| `verifier_rubric.py` R1 (poids 1 a 4) | R1 signale les gates a +0 : attendu, a annoter dans le rapport |

Tout le reste du contrat tient : criteres atomiques autoportants, valeur seule, tolerance par defaut
enoncee une fois, penalites a titre court et poignee `[Pn]`, au plus une gate par section.

## Le protocole (texte d'Amir, a appliquer mot pour mot)

```
RUBRIC JUICING — MAX DISCRIMINATION UNDER STRICT FAIRNESS

OBJECTIVE
Modify the attached rubric so that, when scored against it:
  (a) the GOLDEN SOLUTION re-scores to EXACTLY 100% (positive pool, all gates passed, zero penalties), and
  (b) a frontier-LLM output to the same prompt lands in the 20–35% band (hard ceiling 40%).
Both constraints are binding. A rubric that fails either is rejected. Do not trade one against the other by cheating fairness — juice through structure, not through unfairness.

INDEPENDENT TEST LOOP (run before and after every rubric edit)
1. In a fresh agent/tab, run the ORIGINAL prompt end-to-end with no rubric visible and no hints. Capture the raw model workbook/output as the ADVERSARY sample.
2. Score the adversary sample and the golden solution against the current rubric, criterion by criterion, gate by gate, penalty by penalty. Produce two line-item scoresheets.
3. If golden ≠ 100% OR adversary outside 20–40%, edit and re-score. Iterate until both hold. Report the final two scoresheets with the % and the delta drivers (which criteria/gates/penalties moved the adversary down).

WHERE THE DIFFICULTY MUST COME FROM
Difficulty must come from genuinely interacting mechanics that a strong model gets wrong under ambiguity — circular loops, days-consistent NWC vs reported-balance base, solve-vs-fix on entry EV, MIN() cap logic, blend-vs-single terminal value, un-haircut vs revised drivers, correct anchoring of a reserve/ceiling. Difficulty must NOT come from labeling traps, over-specified prompts, arbitrary rounding, esoteric conventions, or "gotcha" wording. If a criterion only separates the model because the model guessed a label or a display choice, it is not a valid discriminator — cut it.

JUICING LEVERS (apply in this order)
1. Strip or down-weight free points. Any routine per-period criterion (+1) that both golden and adversary nail contributes nothing to spread — reweight to the true routine floor or fold into a block. Keep the positive pool honest; don't pad.
2. Install section GATES on keystone logic. For each section whose headline output depends on a single correct mechanic (e.g., solved entry EV, days-consistent UFCF, MIN-of-caps strategic max, live sensitivity round-trip), add a +0 gate: "If the mechanic is not met (value out of band AND built the wrong way), every criterion in the section scores 0." Gates are where the model bleeds — a wrong mechanic zeroes a whole section it otherwise partially earned.
3. Elevate keystones (+4) on the 2–4 outputs that separate top-tier work from competent work. These carry disproportionate weight so a model that misses the core judgment cannot float on mechanical partial credit.
4. Add penalties [P1..Pn] for method shortcuts that STILL land values in band (e.g., reused single TV method, fixed entry EV, reported-EBITDA valuation base, hardcoded sensitivity). Each fires at most once, is charged only where a workbook value evidences the shortcut, and is not charged where its gate/criterion already scored 0. Cap the penalty pool.
5. Tighten tolerances only where a tighter band is genuinely defensible to a BB/EB banker; leave path-insensitive outputs loose.

FAIRNESS GUARDRAILS (every edit must pass all — bloquant)
- Reflects what strong BB/EB bankers expect: correct IB conventions + sound judgment under ambiguity, not house-specific trivia.
- Does not penalize reasonable omissions or stylistic/display differences when the core analytical logic and IB reasoning are sound.
- Requires no super-niche or borderline-esoteric element that a highly-rated banker could reasonably leave out. If a criterion would fail a top banker who did excellent work, it is unfair — cut or convert to a memo/no-point item.
- Recognizes MULTIPLE valid blue-chip paths: encode explicit path-allowances (accept year-end OR mid-year DCF, either defensible interest rate with a consistent downstream, any internally consistent cap construction). Grade the VALUE and the MECHANIC, not the cell reference or the route.
- Rewards any genuinely top-quality answer: a blue-chip-grade response via a legitimate alternative path must be able to score 100%.

MUST-HAVE TEST
Anything experienced BB/EB bankers would expect in virtually every strong answer is a MUST-HAVE: make it an explicit weighted criterion or a gate. Anything they'd reasonably vary or omit is NOT a must-have: it must not be gated and must not carry keystone weight.

CONVENTIONS (preserve house style)
Atomic criteria: entity/block — line item — period — target value; graded in isolation on value only (no formula/reference match). Default pass ≤1% relative with correct sign unless the criterion states its own tolerance. Direction-labeled lines: grade magnitude, accept either sign. Weight bands 1–4 (+1 routine/per-period; +2 supporting anchor; +3 major structural output; +4 keystone). Gates are +0. State the positive pool total, criterion count, keystone count, gate count, and confirm the reference solution re-scores to 100%.

DELIVERABLE
1. The revised rubric in full, same house format, with every new gate/penalty/path-allowance annotated inline.
2. Golden scoresheet (=100%) and adversary scoresheet (20–40%), line-item, with the delta-driver summary.
3. A short fairness note: for each new gate/keystone/penalty, one line stating why a top BB/EB banker would endorse it.
```

---

Navigation : [la skill pack](../SKILL.md)
