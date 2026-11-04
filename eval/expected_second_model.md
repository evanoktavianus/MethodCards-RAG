# Agent-model comparison (institutional procedures, 231 questions)

Three agent models, same prompts, tools, data tool, sandbox, turn limits and judges (score_v2 and RAGAS-style judge: deepseek/deepseek-v4.1-flash). One run per question and setting. Failed or missing answers count as 0. Metric definitions as in scripts/make_ablation.py. Differences: paired cluster bootstrap over the 13 methods (4,000 resamples, 95% percentile interval). ReAct has no method tool, so context recall, precision and faithfulness do not apply. A cell with n shows the number of questions that have the metric. Agent costs are at each model's own prices and are not comparable between models.

## (a) Side by side, per setting

### ReAct (ReAct-v2)

| Metric | glm-5.3-flash | Claude Haiku 5.5 | Qwen 3.5 397B |
|---|---|---|---|
| Answer correctness | 61.4 | 60.2 | 61.5 |
| Method explained | 68.5 | 70.7 | 66.3 |
| Data correctness | 56.3 | 49.1 | 49.8 |
| Computation correctness | 54.4 (n=229) | 55.0 (n=229) | 61.9 (n=229) |
| Fully correct answers | 25.1 | 24.7 | 24.7 |
| Context recall (method) | n/a | n/a | n/a |
| Context precision | n/a | n/a | n/a |
| Faithfulness | n/a | n/a | n/a |
| Method correctness | 58.7 | 64.8 | 61.2 |
| Failed answers (counted as 0) | 2 of 231 | 0 of 231 | 0 of 231 |
| Mean agent cost / question (USD) | 0.0014 | 0.0079 | 0.0840 |

### Ours (Ours-cards2)

| Metric | glm-5.3-flash | Claude Haiku 5.5 | Qwen 3.5 397B |
|---|---|---|---|
| Answer correctness | 77.1 | 71.3 | 72.0 |
| Method explained | 86.3 | 79.9 | 82.1 |
| Data correctness | 69.5 | 60.4 | 61.5 |
| Computation correctness | 70.5 (n=229) | 69.2 (n=229) | 66.9 (n=229) |
| Fully correct answers | 45.0 | 43.3 | 39.0 |
| Context recall (method) | 75.3 | 75.7 | 77.7 |
| Context precision | 77.2 | 80.4 (n=230) | 80.4 |
| Faithfulness | 64.5 | 59.7 | 70.3 |
| Method correctness | 90.0 | 81.2 | 81.6 |
| Failed answers (counted as 0) | 0 of 231 | 0 of 231 | 0 of 231 |
| Mean agent cost / question (USD) | 0.0027 | 0.0167 | 0.1434 |

### Ours, method given (Ours-oracle)

| Metric | glm-5.3-flash | Claude Haiku 5.5 | Qwen 3.5 397B |
|---|---|---|---|
| Answer correctness | 80.4 | 72.4 | 71.4 |
| Method explained | 91.1 | 86.7 | 85.9 |
| Data correctness | 68.8 | 58.1 | 59.7 |
| Computation correctness | 74.6 (n=229) | 65.2 (n=229) | 60.0 (n=229) |
| Fully correct answers | 49.8 | 39.8 | 31.6 |
| Context recall (method) | 89.1 | 88.9 | 89.2 |
| Context precision | 84.5 | 81.8 (n=226) | 83.1 (n=228) |
| Faithfulness | 69.9 | 65.6 | 77.8 |
| Method correctness | 93.0 | 88.8 | 84.9 |
| Failed answers (counted as 0) | 0 of 231 | 0 of 231 | 0 of 231 |
| Mean agent cost / question (USD) | 0.0025 | 0.0165 | 0.1297 |

## (b) Differences (percentage points, paired cluster bootstrap, 95% interval)

| Comparison / metric | glm-5.3-flash | Claude Haiku 5.5 | Qwen 3.5 397B |
|---|---|---|---|
| Ours minus ReAct: Answer correctness | +15.7 [+6.7, +26.2] | +11.1 [+2.3, +20.0] | +10.5 [+1.4, +19.4] |
| Ours minus ReAct: Fully correct answers | +19.9 [+5.3, +31.4] | +18.6 [+6.3, +31.6] | +14.3 [-1.0, +27.3] |
| Ours minus ReAct: Method explained | +17.7 [+6.8, +30.6] | +9.1 [+0.2, +18.7] | +15.8 [+2.5, +28.7] |
| Ours minus ReAct: Method correctness | +31.3 [+10.8, +55.4] | +16.4 [-1.1, +35.4] | +20.4 [-0.8, +44.4] |
| Method given minus ReAct: Answer correctness | +19.0 [+9.5, +29.3] | +12.2 [+5.0, +20.9] | +9.9 [+2.1, +17.8] |
| Method given minus ReAct: Method correctness | +34.3 [+14.2, +57.0] | +24.0 [+9.6, +39.7] | +23.7 [+6.1, +42.1] |
| Method given minus ours: Answer correctness | +3.3 [-0.8, +9.3] | +1.1 [-6.3, +10.8] | -0.6 [-7.7, +9.0] |

### Per-method positive counts and exact sign-flip test over the 13 methods (answer correctness, two-sided, all 2^13 sign patterns)

| Comparison | glm-5.3-flash | Claude Haiku 5.5 | Qwen 3.5 397B |
|---|---|---|---|
| Ours minus ReAct | mean +15.7; methods with positive mean: 10 of 13; p = 0.0024 | mean +11.1; methods with positive mean: 8 of 13; p = 0.0381 | mean +10.5; methods with positive mean: 10 of 13; p = 0.0532 |
| Method given minus ReAct | mean +19.0; methods with positive mean: 11 of 13; p = 0.0010 | mean +12.2; methods with positive mean: 9 of 13; p = 0.0103 | mean +9.9; methods with positive mean: 10 of 13; p = 0.0359 |
| Method given minus ours | mean +3.3; methods with positive mean: 8 of 13; p = 0.1963 | mean +1.1; methods with positive mean: 7 of 13; p = 0.6523 | mean -0.6; methods with positive mean: 7 of 13; p = 0.9023 |

