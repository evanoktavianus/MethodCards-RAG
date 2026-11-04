# Control results: institutional procedures (231 questions)

Arms: ReAct-steps (ReAct-v2 with the Ours-cards2 prompt steps that need no method tool) and Text-410 (Ours-text2 with the text search restricted to the 410 card documents). One run per question and arm; main-run arms from results_final_hard.jsonl.gz. Failed or unfinished answers count as 0. Metric definitions as in scripts/make_ablation.py; context recall, precision and faithfulness exist only for arms with a method tool (n/a otherwise).

| Arm | answers | failed (=0) | Answer correctness | Method explained | Data correctness | Computation correctness | Fully correct answers | Context recall (method) | Context precision | Faithfulness | Method correctness | mean agent cost / question (USD) | mean judge cost / question (USD) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ReAct-v2 | 231 | 2 | 61.4 | 68.5 | 56.3 | 54.4 (n=229) | 25.1 | n/a | n/a | n/a | 58.7 | 0.0014 | 0.0017 |
| ReAct-steps | 231 | 1 | 62.8 | 71.2 | 57.7 | 52.5 (n=229) | 27.7 | n/a | n/a | n/a | 61.5 | 0.0015 | 0.0029 |
| Ours-text2 | 231 | 1 | 74.9 | 85.1 | 66.9 | 66.8 (n=229) | 45.0 | 57.5 | 39.1 (n=228) | 49.8 | 86.3 | 0.0040 | 0.0017 |
| Text-410 | 231 | 0 | 76.2 | 87.0 | 69.6 | 67.1 (n=229) | 42.0 | 55.3 | 39.0 (n=229) | 47.9 | 87.3 | 0.0040 | 0.0017 |
| Ours-cards2 | 231 | 0 | 77.1 | 86.3 | 69.5 | 70.5 (n=229) | 45.0 | 75.3 | 77.2 | 64.5 | 90.0 | 0.0027 | 0.0017 |

Cost: result-row `cost` (agent calls) and `judge2_cost`.

## Ours-cards2 minus ReAct-steps (paired cluster bootstrap over methods; exact sign-flip test over the 13 methods)

- Answer correctness: Ours-cards2 77.1, ReAct-steps 62.8; difference +14.3 [+5.3, +24.1] (n=231, methods=13); sign-flip p = 0.0049
- Method explained: Ours-cards2 86.3, ReAct-steps 71.2; difference +15.0 [+3.1, +28.9] (n=231, methods=13); sign-flip p = 0.0273
- Data correctness: Ours-cards2 69.5, ReAct-steps 57.7; difference +11.8 [+5.2, +18.7] (n=231, methods=13); sign-flip p = 0.0039
- Computation correctness: Ours-cards2 70.5, ReAct-steps 52.5; difference +18.0 [+4.4, +28.9] (n=229, methods=13); sign-flip p = 0.0264
- Fully correct answers: Ours-cards2 45.0, ReAct-steps 27.7; difference +17.3 [+1.7, +29.2] (n=231, methods=13); sign-flip p = 0.1016
- Context recall (method): Ours-cards2 75.3, ReAct-steps n/a; difference n/a
- Context precision: Ours-cards2 77.2, ReAct-steps n/a; difference n/a
- Faithfulness: Ours-cards2 64.5, ReAct-steps n/a; difference n/a
- Method correctness: Ours-cards2 90.0, ReAct-steps 61.5; difference +28.5 [+8.1, +52.6] (n=231, methods=13); sign-flip p = 0.0039

## ReAct-steps minus ReAct-v2 (paired cluster bootstrap over methods; exact sign-flip test over the 13 methods)

- Answer correctness: ReAct-steps 62.8, ReAct-v2 61.4; difference +1.4 [-0.4, +3.2] (n=231, methods=13); sign-flip p = 0.1804
- Method explained: ReAct-steps 71.2, ReAct-v2 68.5; difference +2.7 [+0.9, +4.9] (n=231, methods=13); sign-flip p = 0.0234
- Data correctness: ReAct-steps 57.7, ReAct-v2 56.3; difference +1.4 [-2.5, +4.8] (n=231, methods=13); sign-flip p = 0.5391
- Computation correctness: ReAct-steps 52.5, ReAct-v2 54.4; difference -1.9 [-8.4, +4.1] (n=229, methods=13); sign-flip p = 0.6250
- Fully correct answers: ReAct-steps 27.7, ReAct-v2 25.1; difference +2.6 [-0.8, +7.2] (n=231, methods=13); sign-flip p = 0.3438
- Context recall (method): ReAct-steps n/a, ReAct-v2 n/a; difference n/a
- Context precision: ReAct-steps n/a, ReAct-v2 n/a; difference n/a
- Faithfulness: ReAct-steps n/a, ReAct-v2 n/a; difference n/a
- Method correctness: ReAct-steps 61.5, ReAct-v2 58.7; difference +2.8 [+0.5, +5.7] (n=231, methods=13); sign-flip p = 0.0605

## Ours-cards2 minus Text-410 (paired cluster bootstrap over methods; exact sign-flip test over the 13 methods)

- Answer correctness: Ours-cards2 77.1, Text-410 76.2; difference +0.9 [-4.1, +6.1] (n=231, methods=13); sign-flip p = 0.8247
- Method explained: Ours-cards2 86.3, Text-410 87.0; difference -0.8 [-3.7, +1.5] (n=231, methods=13); sign-flip p = 0.5723
- Data correctness: Ours-cards2 69.5, Text-410 69.6; difference -0.1 [-12.1, +9.0] (n=231, methods=13); sign-flip p = 1.0000
- Computation correctness: Ours-cards2 70.5, Text-410 67.1; difference +3.4 [-6.4, +12.9] (n=229, methods=13); sign-flip p = 0.7275
- Fully correct answers: Ours-cards2 45.0, Text-410 42.0; difference +3.0 [-7.7, +11.4] (n=231, methods=13); sign-flip p = 0.7002
- Context recall (method): Ours-cards2 75.3, Text-410 55.3; difference +20.1 [+2.4, +36.7] (n=231, methods=13); sign-flip p = 0.0571
- Context precision: Ours-cards2 77.2, Text-410 39.0; difference +38.0 [+26.1, +48.1] (n=229, methods=13); sign-flip p = 0.0002
- Faithfulness: Ours-cards2 64.5, Text-410 47.9; difference +16.6 [+5.4, +28.8] (n=231, methods=13); sign-flip p = 0.0068
- Method correctness: Ours-cards2 90.0, Text-410 87.3; difference +2.7 [-0.7, +5.9] (n=231, methods=13); sign-flip p = 0.1763

## Text-410 minus Ours-text2 (paired cluster bootstrap over methods; exact sign-flip test over the 13 methods)

- Answer correctness: Text-410 76.2, Ours-text2 74.9; difference +1.3 [-0.6, +3.2] (n=231, methods=13); sign-flip p = 0.1946
- Method explained: Text-410 87.0, Ours-text2 85.1; difference +2.0 [-0.2, +4.2] (n=231, methods=13); sign-flip p = 0.1875
- Data correctness: Text-410 69.6, Ours-text2 66.9; difference +2.7 [-0.3, +5.2] (n=231, methods=13); sign-flip p = 0.1406
- Computation correctness: Text-410 67.1, Ours-text2 66.8; difference +0.3 [-4.4, +5.4] (n=229, methods=13); sign-flip p = 0.9033
- Fully correct answers: Text-410 42.0, Ours-text2 45.0; difference -3.0 [-7.4, +1.1] (n=231, methods=13); sign-flip p = 0.3281
- Context recall (method): Text-410 55.3, Ours-text2 57.5; difference -2.2 [-7.7, +4.6] (n=231, methods=13); sign-flip p = 0.5615
- Context precision: Text-410 39.0, Ours-text2 39.1; difference -0.4 [-5.0, +4.3] (n=226, methods=13); sign-flip p = 0.8779
- Faithfulness: Text-410 47.9, Ours-text2 49.8; difference -1.9 [-4.7, +1.0] (n=231, methods=13); sign-flip p = 0.3882
- Method correctness: Text-410 87.3, Ours-text2 86.3; difference +1.0 [-3.7, +5.4] (n=231, methods=13); sign-flip p = 0.7554

