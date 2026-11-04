# Ablation results: institutional procedures (hard, 231 questions)

Rows: one run per question and arm. Model, prompt steps, data tool, Python sandbox, turn limit and judge as Ours-cards2. Failed or unfinished answers count as 0. Metric definitions as in scripts/make_ablation.py.

| Arm | answers | failed (=0) | Answer correctness | Method explained | Data correctness | Computation correctness | Fully correct answers | Context recall (method) | Context precision | Faithfulness | Method correctness | mean agent cost / question (USD) | mean judge cost / question (USD) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Cards-fixed | 231 | 0 | 70.2 | 76.2 | 61.7 | 67.4 (n=229) | 33.8 | 55.0 | 56.9 | 51.0 | 70.3 | 0.0029 | 0.0017 |
| Cards-as-text | 231 | 2 | 73.0 | 81.8 | 65.4 | 67.6 (n=229) | 43.7 | 75.2 | 82.8 (n=227) | 58.0 | 81.5 | 0.0035 | 0.0018 |
| Ours-cards2 (control run) | 230 | 2 | 76.9 | 85.9 | 67.3 | 71.2 (n=229) | 48.5 | 75.8 | 80.2 (n=228) | 63.6 (n=229) | 87.9 | 0.0044 | 0.0018 |
| Ours-text2 (main run) | 231 | 1 | 74.9 | 85.1 | 66.9 | 66.8 (n=229) | 45.0 | 57.5 | 39.1 (n=228) | 49.8 | 86.3 | 0.0040 | 0.0017 |
| Ours-cards2 (main run) | 231 | 0 | 77.1 | 86.3 | 69.5 | 70.5 (n=229) | 45.0 | 75.3 | 77.2 | 64.5 | 90.0 | 0.0027 | 0.0017 |

Cost: result-row `cost` (agent calls, including the first attempt when a run was repeated) and `judge2_cost`; the RAGAS-style judge cost is in the `cost` field of the stored judge rows.

## Control minus Cards-fixed (paired cluster bootstrap over methods)

- Answer correctness: control 76.9, Cards-fixed 70.2; difference +6.7 [+0.9, +14.4] (n=231, methods=13)
- Method explained: control 85.9, Cards-fixed 76.2; difference +9.7 [+1.7, +20.0] (n=231, methods=13)
- Data correctness: control 67.3, Cards-fixed 61.7; difference +5.6 [-0.9, +12.9] (n=231, methods=13)
- Computation correctness: control 71.2, Cards-fixed 67.4; difference +3.8 [-2.7, +14.2] (n=229, methods=13)
- Fully correct answers: control 48.5, Cards-fixed 33.8; difference +14.7 [+3.9, +30.2] (n=231, methods=13)
- Context recall (method): control 75.8, Cards-fixed 55.0; difference +20.9 [+3.9, +41.1] (n=231, methods=13)
- Context precision: control 80.2, Cards-fixed 56.9; difference +23.1 [+12.5, +34.7] (n=228, methods=13)
- Faithfulness: control 63.6, Cards-fixed 51.0; difference +12.6 [+6.6, +17.5] (n=229, methods=13)
- Method correctness: control 87.9, Cards-fixed 70.3; difference +17.6 [+6.5, +31.2] (n=231, methods=13)

## Control minus Cards-as-text (paired cluster bootstrap over methods)

- Answer correctness: control 76.9, Cards-as-text 73.0; difference +3.9 [-0.0, +8.6] (n=231, methods=13)
- Method explained: control 85.9, Cards-as-text 81.8; difference +4.1 [-0.5, +10.7] (n=231, methods=13)
- Data correctness: control 67.3, Cards-as-text 65.4; difference +1.9 [-1.7, +6.4] (n=231, methods=13)
- Computation correctness: control 71.2, Cards-as-text 67.6; difference +3.6 [-3.1, +10.0] (n=229, methods=13)
- Fully correct answers: control 48.5, Cards-as-text 43.7; difference +4.8 [-4.1, +14.4] (n=231, methods=13)
- Context recall (method): control 75.8, Cards-as-text 75.2; difference +0.6 [-3.4, +5.2] (n=231, methods=13)
- Context precision: control 80.2, Cards-as-text 82.8; difference -2.8 [-10.2, +4.7] (n=225, methods=13)
- Faithfulness: control 63.6, Cards-as-text 58.0; difference +5.5 [+0.1, +9.3] (n=229, methods=13)
- Method correctness: control 87.9, Cards-as-text 81.5; difference +6.4 [+0.9, +14.7] (n=231, methods=13)

## Control minus Ours-text2 (main run) (paired cluster bootstrap over methods)

- Answer correctness: control 76.9, Ours-text2 (main run) 74.9; difference +2.0 [-3.1, +7.1] (n=231, methods=13)
- Method explained: control 85.9, Ours-text2 (main run) 85.1; difference +0.9 [-1.7, +3.1] (n=231, methods=13)
- Data correctness: control 67.3, Ours-text2 (main run) 66.9; difference +0.4 [-8.3, +7.5] (n=231, methods=13)
- Computation correctness: control 71.2, Ours-text2 (main run) 66.8; difference +4.4 [-5.0, +13.3] (n=229, methods=13)
- Fully correct answers: control 48.5, Ours-text2 (main run) 45.0; difference +3.5 [-5.7, +12.1] (n=231, methods=13)
- Context recall (method): control 75.8, Ours-text2 (main run) 57.5; difference +18.3 [-0.6, +35.1] (n=231, methods=13)
- Context precision: control 80.2, Ours-text2 (main run) 39.1; difference +40.7 [+30.0, +50.9] (n=225, methods=13)
- Faithfulness: control 63.6, Ours-text2 (main run) 49.8; difference +13.7 [+4.0, +23.6] (n=229, methods=13)
- Method correctness: control 87.9, Ours-text2 (main run) 86.3; difference +1.6 [-3.6, +8.0] (n=231, methods=13)

## Control minus Ours-cards2 (main run) (paired cluster bootstrap over methods)

- Answer correctness: control 76.9, Ours-cards2 (main run) 77.1; difference -0.2 [-2.0, +2.0] (n=231, methods=13)
- Method explained: control 85.9, Ours-cards2 (main run) 86.3; difference -0.4 [-3.1, +2.6] (n=231, methods=13)
- Data correctness: control 67.3, Ours-cards2 (main run) 69.5; difference -2.2 [-5.6, +1.3] (n=231, methods=13)
- Computation correctness: control 71.2, Ours-cards2 (main run) 70.5; difference +0.7 [-5.4, +7.1] (n=229, methods=13)
- Fully correct answers: control 48.5, Ours-cards2 (main run) 45.0; difference +3.5 [-4.6, +11.3] (n=231, methods=13)
- Context recall (method): control 75.8, Ours-cards2 (main run) 75.3; difference +0.5 [-3.0, +3.5] (n=231, methods=13)
- Context precision: control 80.2, Ours-cards2 (main run) 77.2; difference +2.4 [-0.9, +6.9] (n=228, methods=13)
- Faithfulness: control 63.6, Ours-cards2 (main run) 64.5; difference -1.0 [-2.8, +0.7] (n=229, methods=13)
- Method correctness: control 87.9, Ours-cards2 (main run) 90.0; difference -2.1 [-5.6, +0.4] (n=231, methods=13)

