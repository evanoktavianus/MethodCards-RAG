# Author check of the judge on the retrieval metrics, and of the method pieces

## Context recall (method) (A1)

Agreement 18 of 20 (90.0%, Wilson 95% interval 69.9 to 97.2); Cohen's kappa 0.81 (yes / partly / no; partly counts as a disagreement).

| Agent | Decisions | Agreed | Judge more lenient (judge yes, author no or partly) | Judge stricter (judge no, author yes or partly) | Mean author | Mean judge |
|---|---|---|---|---|---|---|
| Ours-cards2 | 10 | 9 | 0 | 1 | 0.45 | 0.40 |
| Ours-text2 | 10 | 9 | 0 | 1 | 0.70 | 0.60 |

## Context precision (A2)

Agreement 17 of 20 (85.0%, Wilson 95% interval 64.0 to 94.8); Cohen's kappa 0.72 (yes / partly / no; partly counts as a disagreement).

| Agent | Decisions | Agreed | Judge more lenient (judge yes, author no or partly) | Judge stricter (judge no, author yes or partly) | Mean author | Mean judge |
|---|---|---|---|---|---|---|
| Ours-cards2 | 10 | 9 | 1 | 0 | 0.65 | 0.70 |
| Ours-text2 | 10 | 8 | 1 | 1 | 0.45 | 0.40 |

## Context recall and context precision together

Agreement 35 of 40 (87.5%, Wilson 95% interval 73.9 to 94.5); Cohen's kappa 0.77.

## Faithfulness (A3)

Sampled sentences 20; not a method claim (n/a) 3; author marks on the 17 method claims: yes 10, partly 2, no 5.
The judge's own claims were not stored, so only means can be compared (author mark against the judge's answer-level share of supported claims).

| Agent | Method claims | Mean author | Mean judge (answer level) |
|---|---|---|---|
| Ours-cards2 | 7 | 0.79 | 0.54 |
| Ours-text2 | 10 | 0.55 | 0.57 |

## Method pieces

Questions 40; pieces 98: correct 98, wrong 0, unsure 0; correct 100.0% (Wilson 95% interval 96.2 to 100.0).
Questions with a wrong piece: 0 (none). Questions with an important piece missing: 0 (none).
Second mark on the 20 pieces of the context recall rows (piece correct for the method?): correct 19, wrong 0, unsure 1.
