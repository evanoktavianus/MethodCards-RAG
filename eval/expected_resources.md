# Resources per question

Agent model glm-5.3-flash. Cost in USD per question (agent calls only). Failed or unfinished answers count 0 in every metric.

| Row | Institutional procedures: turns | Tool calls | Cost (USD) | Standard formulas: turns | Tool calls | Cost (USD) |
|---|---|---|---|---|---|---|
| 1. Memory only (CoT) | 1 call | 0 | 0.0006 | 1 call | 0 | 0.0005 |
| 2. Data in prompt | 1 call | 0 | 0.0004 | 1 call | 0 | 0.0001 |
| 3. PoT | 2 calls | 1 program | 0.0006 | 2 calls | 1 program | 0.0002 |
| 4. ReAct | 6.1 | 11.7 | 0.0014 | 4.5 | 6.4 | 0.0006 |
| 5. LongDA-style | 9.6 | 20.2 | 0.0040 | 7.4 | 12.3 | 0.0023 |
| 6. Ours | 9.6 | 19.8 | 0.0027 | 7.5 | 12.8 | 0.0016 |
| Ours, method given (oracle) | 8.9 | 19.3 | 0.0025 | 7.7 | 12.6 | 0.0016 |

Failed or unfinished answers per row, both groups together (440 answers per row): 1. Memory only (CoT) 20; 2. Data in prompt 1; 3. PoT 0; 4. ReAct 2; 5. LongDA-style 1; 6. Ours 1; Ours, method given (oracle) 0.

## Other agent models (institutional procedures, 231 questions)

| Model and setting | Mean cost (USD) | Mean turns | Mean tool calls | Failed |
|---|---|---|---|---|
| Claude Haiku 5.5, ReAct | 0.0079 | 5.2 | 7.5 | 0 |
| Claude Haiku 5.5, Ours | 0.0167 | 8.0 | 15.2 | 0 |
| Claude Haiku 5.5, Ours, method given | 0.0165 | 7.9 | 14.5 | 0 |
| Qwen 3.5 397B, ReAct | 0.0840 | 8.6 | 16.8 | 0 |
| Qwen 3.5 397B, Ours | 0.1434 | 12.4 | 28.0 | 0 |
| Qwen 3.5 397B, Ours, method given | 0.1297 | 12.2 | 25.5 | 0 |

