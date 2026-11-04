# The questions and their answer keys

`items/<method>/<ID>.json`: 440 questions in two groups, 231 institutional procedures and 209 standard formulas (lists: `experiments/splits/hard.json` and `easier.json`; per-method points: `experiments/main_run/rule_bands.json`). A written rule on the structure of the method gives one point for each of four criteria: several steps; an institutional procedure rather than a textbook identity; parameters the documents leave open; a method a model is unlikely to do from memory. Three or four points make a method an institutional procedure. Each file is one question with its key.

| Field | Meaning |
|---|---|
| `id`, `method`, `family`, `style` | question id, the calculation method it needs, its family, and its form (`named` country, `hidden` country given by conditions, `claim_check` a statement to verify) |
| `query` | the question as the agent sees it |
| `claims` | the answer key: a list of points by kind (`text`, `data`, `computation`, `answer`); each has an id, an importance, an acceptance rule, and for numbers a target and two tolerances |
| `method_doc_ids` | the methodology documents that state the method (used to measure whether the agent found the right method) |
| `recomputed_value`, `published_value`, `gold_script` | the value recomputed by our reference program on the frozen data, the value printed in an official publication where there is one, and the program (`gold/`) |
| `validation_tier`, `procedure_kind`, `status` | how far the key was validated (see `METHODS.md`) and its status (`validated`) |

How a row is scored (judge v2, `experiments/baselines/run_baselines.py: judge_item_v2`): every point gets 0, 0.5 or 1. Text, data and answer points are judged by a language model against the acceptance rule. Numeric points are scored in code from the value the answer reports: 1 if within the first tolerance of the target, 0.5 if within the second and on the same side of zero, else 0. The score of an answer is the weighted mean of the part scores, with weights text 40, data 20, computation 25, answer 15 (kinds that have no point in the question are left out and the weights rescaled), on a scale of 0 to 100. A failed or unfinished answer counts as 0.

`RUBRIC.md` gives the rules the keys follow. `METHODS.md` lists the methods, their validation tier and their parameter strictness.

Data behind the questions: official statistics frozen at a vintage (IMF World Economic Outlook October 2025; World Bank WDI and Public Sector Debt, extracted October 2026; IMF International Investment Position). They are in `tools/data/store/` (read by the data tool) and `data/frozen_extra/` (read by the prompt builder). See `NOTICE` for their terms.
