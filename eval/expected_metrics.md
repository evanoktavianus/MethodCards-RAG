# RAGAS-style metrics from the stored results

Failed or missing answers count as 0 in every column. Percent.

- Context recall (method): share of the question's method pieces stated in what the agent retrieved (the given passage for the oracle cell).
- Context precision: share of retrieved method items (cards opened, pages read) that state the question's method. Answers that retrieved nothing are left out; failed answers count 0.
- Context recall (data): share of the question's needed series fetched, an equivalent series counting.
- Faithfulness: share of the answer's method claims supported by what the agent retrieved.
- Method correctness (factual correctness): share of the question's method pieces applied correctly in the answer.
- Answer correctness: score_v2, with its parts: Method explained, Data correctness, Computation correctness.

## Full table (RAGAS names)

Institutional procedures (231)

| Row | Context recall (method) | Context precision | Context recall (data) | Faithfulness | Method correctness (factual correctness) | Method explained | Data correctness | Computation correctness | Answer correctness |
|---|---|---|---|---|---|---|---|---|---|
| 1. Memory only (CoT) | n/a | n/a | n/a | n/a | 56.3 | 54.6 | 38.2 | 33.0 | 44.4 |
| 2. Data in prompt | n/a | n/a | given | n/a | 58.3 | 63.2 | 61.7 | 59.9 | 61.8 |
| 3. PoT | n/a | n/a | given | n/a | 59.5 | 65.5 | 61.4 | 58.8 | 62.5 |
| 4. ReAct | n/a | n/a | 59.8 | n/a | 58.7 | 68.5 | 56.3 | 55.6 | 61.4 |
| 5. LongDA-style | 57.5 | 39.1 | 68.0 | 49.8 | 86.3 | 85.1 | 66.9 | 66.8 | 74.9 |
| **6. Ours** | **75.3** | **77.2** | **71.0** | **64.5** | **90.0** | **86.3** | **69.5** | **70.5** | **77.1** |
| Ours + given method (oracle analysis) | 89.1 | 84.5 | 71.3 | 69.9 | 93.0 | 91.1 | 68.8 | 74.6 | 80.4 |

Standard formulas (209)

| Row | Context recall (method) | Context precision | Context recall (data) | Faithfulness | Method correctness (factual correctness) | Method explained | Data correctness | Computation correctness | Answer correctness |
|---|---|---|---|---|---|---|---|---|---|
| 1. Memory only (CoT) | n/a | n/a | n/a | n/a | 78.6 | 76.2 | 42.8 | 40.1 | 57.6 |
| 2. Data in prompt | n/a | n/a | given | n/a | 84.2 | 87.2 | 84.4 | 85.8 | 86.3 |
| 3. PoT | n/a | n/a | given | n/a | 84.3 | 88.7 | 84.7 | 89.2 | 88.0 |
| 4. ReAct | n/a | n/a | 66.3 | n/a | 84.8 | 89.2 | 61.0 | 84.6 | 81.4 |
| 5. LongDA-style | 49.6 | 18.6 | 70.2 | 42.1 | 94.2 | 94.7 | 59.8 | 85.7 | 83.9 |
| **6. Ours** | **73.5** | **80.7** | **69.4** | **62.8** | **89.0** | **91.7** | **59.1** | **83.1** | **81.6** |
| Ours + given method (oracle analysis) | 85.5 | 75.8 | 68.9 | 67.5 | 92.5 | 94.7 | 59.6 | 83.5 | 83.3 |

## Faithfulness and context precision

| Row | Institutional procedures: faithfulness | Institutional procedures: precision | Standard formulas: faithfulness | Standard formulas: precision |
|---|---|---|---|---|
| 5. LongDA-style | 49.8 | 39.1 | 42.1 | 18.6 |
| **6. Ours** | **64.5** | **77.2** | **62.8** | **80.7** |
| Ours + given method (oracle analysis) | 69.9 | 84.5 | 67.5 | 75.8 |

## Table 7: oracle analysis (answer correctness), both groups

|  | Institutional procedures: method found | Institutional procedures: method given | Standard formulas: method found | Standard formulas: method given |
|---|---|---|---|---|
| data found | 77.1 | 80.4 | 81.6 | 83.3 |
| data given | 83.4 | 84.2 | 91.0 | 89.9 |

## Pooled over both groups (440 questions)

| Row (both groups pooled, 440 questions) | Context recall (method) | Context precision | Faithfulness | Method correctness (factual correctness) | Answer correctness |
|---|---|---|---|---|---|
| 5. LongDA-style | 53.8 | 29.4 | 46.1 | 90.1 | 79.2 |
| **6. Ours** | **74.5** | **78.9** | **63.7** | **89.6** | **79.3** |

## Ladder, Institutional procedures (231)

| Ladder row | Method found | Data found | Method used correctly | Accuracy |
|---|---|---|---|---|
| 1. Memory only (CoT) | n/a | n/a | 56.3 | 44.4 |
| 2. Data in prompt | n/a | given | 58.3 | 61.8 |
| 3. PoT | n/a | given | 59.5 | 62.5 |
| 4. ReAct | n/a | 59.8 | 58.7 | 61.4 |
| 5. LongDA-style | 57.5 | 68.0 | 86.3 | 74.9 |
| **6. Ours** | **75.3** | **71.0** | **90.0** | **77.1** |
| Ours + given method (oracle analysis) | 89.1 | 71.3 | 93.0 | 80.4 |

## Ladder, Standard formulas (209)

| Ladder row | Method found | Data found | Method used correctly | Accuracy |
|---|---|---|---|---|
| 1. Memory only (CoT) | n/a | n/a | 78.6 | 57.6 |
| 2. Data in prompt | n/a | given | 84.2 | 86.3 |
| 3. PoT | n/a | given | 84.3 | 88.0 |
| 4. ReAct | n/a | 66.3 | 84.8 | 81.4 |
| 5. LongDA-style | 49.6 | 70.2 | 94.2 | 83.9 |
| **6. Ours** | **73.5** | **69.4** | **89.0** | **81.6** |
| Ours + given method (oracle analysis) | 85.5 | 68.9 | 92.5 | 83.3 |

## Complete table, every metric (metrics as rows)

Columns: 1 CoT0, 2 Data in prompt, 3 PoT, 4 ReAct, 5 LongDA-style, 6 Ours, O = Ours + given method (oracle analysis). Percent; failed answers = 0.
Graph versions are judge-free cross-checks from the method tree. Fully correct answers = every vital claim of the key correct (vital_all_v2).

Institutional procedures (231)

| Metric | 1 | 2 | 3 | 4 | 5 LongDA-style | **6 Ours** | O |
|---|---|---|---|---|---|---|---|
| Context recall (method), judge | n/a | n/a | n/a | n/a | 57.5 | **75.3** | 89.1 |
| Context recall (method), graph strict: opened | n/a | n/a | n/a | n/a | 74.0 | **61.9** | 68.4 |
| Context recall (method), graph loose: seen | n/a | n/a | n/a | n/a | 88.7 | **87.9** | 97.0 |
| Context precision, judge | n/a | n/a | n/a | n/a | 39.1 | **77.2** | 84.5 |
| Context precision, graph rank-weighted | n/a | n/a | n/a | n/a | 37.4 | **54.5** | 64.3 |
| Context recall (data), share of inputs | n/a | given | given | 59.8 | 68.0 | **71.0** | 71.3 |
| Context recall (data), all inputs | n/a | given | given | 23.4 | 28.1 | **32.0** | 36.8 |
| Faithfulness | n/a | n/a | n/a | n/a | 49.8 | **64.5** | 69.9 |
| Method correctness (factual correctness), all pieces | 56.3 | 58.3 | 59.5 | 58.7 | 86.3 | **90.0** | 93.0 |
| Method correctness (factual correctness), vital pieces | 58.5 | 61.4 | 61.8 | 59.4 | 88.0 | **90.0** | 92.9 |
| Method explained | 54.6 | 63.2 | 65.5 | 68.5 | 85.1 | **86.3** | 91.1 |
| Data correctness | 38.2 | 61.7 | 61.4 | 56.3 | 66.9 | **69.5** | 68.8 |
| Computation correctness | 33.0 | 59.9 | 58.8 | 55.6 | 66.8 | **70.5** | 74.6 |
| Answer correctness | 44.4 | 61.8 | 62.5 | 61.4 | 74.9 | **77.1** | 80.4 |
| Fully correct answers | 7.8 | 24.7 | 28.1 | 25.1 | 45.0 | **45.0** | 49.8 |

Standard formulas (209)

| Metric | 1 | 2 | 3 | 4 | 5 LongDA-style | **6 Ours** | O |
|---|---|---|---|---|---|---|---|
| Context recall (method), judge | n/a | n/a | n/a | n/a | 49.6 | **73.5** | 85.5 |
| Context recall (method), graph strict: opened | n/a | n/a | n/a | n/a | 33.0 | **57.2** | 54.5 |
| Context recall (method), graph loose: seen | n/a | n/a | n/a | n/a | 56.0 | **71.2** | 67.0 |
| Context precision, judge | n/a | n/a | n/a | n/a | 18.6 | **80.7** | 75.8 |
| Context precision, graph rank-weighted | n/a | n/a | n/a | n/a | 13.3 | **54.3** | 53.3 |
| Context recall (data), share of inputs | n/a | given | given | 66.3 | 70.2 | **69.4** | 68.9 |
| Context recall (data), all inputs | n/a | given | given | 46.9 | 53.6 | **52.4** | 51.7 |
| Faithfulness | n/a | n/a | n/a | n/a | 42.1 | **62.8** | 67.5 |
| Method correctness (factual correctness), all pieces | 78.6 | 84.2 | 84.3 | 84.8 | 94.2 | **89.0** | 92.5 |
| Method correctness (factual correctness), vital pieces | 78.6 | 84.6 | 84.5 | 84.9 | 94.2 | **88.6** | 92.4 |
| Method explained | 76.2 | 87.2 | 88.7 | 89.2 | 94.7 | **91.7** | 94.7 |
| Data correctness | 42.8 | 84.4 | 84.7 | 61.0 | 59.8 | **59.1** | 59.6 |
| Computation correctness | 40.1 | 85.8 | 89.2 | 84.6 | 85.7 | **83.1** | 83.5 |
| Answer correctness | 57.6 | 86.3 | 88.0 | 81.4 | 83.9 | **81.6** | 83.3 |
| Fully correct answers | 24.4 | 69.9 | 72.7 | 72.2 | 77.5 | **72.2** | 74.2 |

## Count-based metrics (no model calls)

### Institutional procedures (1617 answers)

| Arm | n | Data recall (share of inputs) | Data recall strict (all inputs) | Method recall strict: opened (%) | Method recall loose: seen (%) | Method precision, graph (%) | Method precision rank-weighted (%) | n with retrieved items | Answer correctness | text | data | computation |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CoT0 (memory only) | 231 | n/a | n/a | n/a | n/a | n/a | n/a | - | 44.4 | 54.6 | 38.2 | 33.0 |
| CoT1 (data in prompt) | 231 | given | given | n/a | n/a | n/a | n/a | - | 61.8 | 63.2 | 61.7 | 59.9 |
| PoT | 231 | given | given | n/a | n/a | n/a | n/a | - | 62.5 | 65.5 | 61.4 | 58.8 |
| ReAct | 231 | 59.8 | 23.4 | n/a | n/a | n/a | n/a | - | 61.4 | 68.5 | 56.3 | 55.6 |
| Ours-text2 (LongDA-style) | 231 | 68.0 | 28.1 | 74.0 | 88.7 | 36.8 | 37.4 | 228 | 74.9 | 85.1 | 66.9 | 66.8 |
| Ours-cards2 (ours) | 231 | 71.0 | 32.0 | 61.9 | 87.9 | 41.3 | 54.5 | 231 | 77.1 | 86.3 | 69.5 | 70.5 |
| Ours-oracle (given method) | 231 | 71.3 | 36.8 | 68.4 | 97.0 | 59.6 | 64.3 | 231 | 80.4 | 91.1 | 68.8 | 74.6 |

#### Method found vs not found, mean score (graph version), Institutional procedures

| Arm | version | found: n | found: mean score | not found: n | not found: mean score |
|---|---|---|---|---|---|
| Ours-text2 (LongDA-style) | strict | 171 | 76.7 | 60 | 69.6 |
| Ours-text2 (LongDA-style) | loose | 205 | 77.1 | 26 | 57.7 |
| Ours-cards2 (ours) | strict | 143 | 78.5 | 88 | 74.9 |
| Ours-cards2 (ours) | loose | 203 | 79.5 | 28 | 59.9 |
| Ours-oracle (given method) | strict | 158 | 79.1 | 73 | 83.3 |
| Ours-oracle (given method) | loose | 224 | 80.4 | 7 | 80.1 |

### Standard formulas (1463 answers)

| Arm | n | Data recall (share of inputs) | Data recall strict (all inputs) | Method recall strict: opened (%) | Method recall loose: seen (%) | Method precision, graph (%) | Method precision rank-weighted (%) | n with retrieved items | Answer correctness | text | data | computation |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CoT0 (memory only) | 209 | n/a | n/a | n/a | n/a | n/a | n/a | - | 57.6 | 76.2 | 42.8 | 40.1 |
| CoT1 (data in prompt) | 209 | given | given | n/a | n/a | n/a | n/a | - | 86.3 | 87.2 | 84.4 | 85.8 |
| PoT | 209 | given | given | n/a | n/a | n/a | n/a | - | 88.0 | 88.7 | 84.7 | 89.2 |
| ReAct | 209 | 66.3 | 46.9 | n/a | n/a | n/a | n/a | - | 81.4 | 89.2 | 61.0 | 84.6 |
| Ours-text2 (LongDA-style) | 209 | 70.2 | 53.6 | 33.0 | 56.0 | 12.3 | 13.3 | 205 | 83.9 | 94.7 | 59.8 | 85.7 |
| Ours-cards2 (ours) | 209 | 69.4 | 52.4 | 57.2 | 71.2 | 49.7 | 54.3 | 208 | 81.6 | 91.7 | 59.1 | 83.1 |
| Ours-oracle (given method) | 209 | 68.9 | 51.7 | 54.5 | 67.0 | 52.5 | 53.3 | 209 | 83.3 | 94.7 | 59.6 | 83.5 |

#### Method found vs not found, mean score (graph version), Standard formulas

| Arm | version | found: n | found: mean score | not found: n | not found: mean score |
|---|---|---|---|---|---|
| Ours-text2 (LongDA-style) | strict | 69 | 83.4 | 140 | 84.1 |
| Ours-text2 (LongDA-style) | loose | 117 | 83.5 | 92 | 84.4 |
| Ours-cards2 (ours) | strict | 119 | 82.1 | 89 | 81.9 |
| Ours-cards2 (ours) | loose | 148 | 80.3 | 60 | 86.3 |
| Ours-oracle (given method) | strict | 114 | 80.5 | 95 | 86.7 |
| Ours-oracle (given method) | loose | 140 | 81.5 | 69 | 86.8 |

### Institutional procedures, data given (462 answers)

| Arm | n | Data recall (share of inputs) | Data recall strict (all inputs) | Method recall strict: opened (%) | Method recall loose: seen (%) | Method precision, graph (%) | Method precision rank-weighted (%) | n with retrieved items | Answer correctness | text | data | computation |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Ours-cards2 (ours) | 231 | given | given | 60.2 | 84.4 | 38.0 | 52.4 | 231 | 83.4 | 89.7 | 81.8 | 75.6 |
| Ours-oracle (given method) | 231 | given | given | 59.3 | 94.8 | 50.9 | 55.1 | 231 | 84.2 | 92.1 | 81.2 | 75.5 |

#### Method found vs not found, mean score (graph version), Institutional procedures, data given

| Arm | version | found: n | found: mean score | not found: n | not found: mean score |
|---|---|---|---|---|---|
| Ours-text2 (LongDA-style) | strict | n/a | n/a | n/a | n/a |
| Ours-text2 (LongDA-style) | loose | n/a | n/a | n/a | n/a |
| Ours-cards2 (ours) | strict | 139 | 85.9 | 92 | 79.8 |
| Ours-cards2 (ours) | loose | 195 | 85.1 | 36 | 74.3 |
| Ours-oracle (given method) | strict | 137 | 80.8 | 94 | 89.1 |
| Ours-oracle (given method) | loose | 219 | 84.1 | 12 | 85.3 |

### Standard formulas, data given (418 answers)

| Arm | n | Data recall (share of inputs) | Data recall strict (all inputs) | Method recall strict: opened (%) | Method recall loose: seen (%) | Method precision, graph (%) | Method precision rank-weighted (%) | n with retrieved items | Answer correctness | text | data | computation |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Ours-cards2 (ours) | 209 | given | given | 50.2 | 68.4 | 44.9 | 48.9 | 205 | 91.0 | 95.0 | 84.4 | 90.0 |
| Ours-oracle (given method) | 209 | given | given | 52.2 | 64.6 | 49.8 | 50.6 | 208 | 89.9 | 95.6 | 78.9 | 89.5 |

#### Method found vs not found, mean score (graph version), Standard formulas, data given

| Arm | version | found: n | found: mean score | not found: n | not found: mean score |
|---|---|---|---|---|---|
| Ours-text2 (LongDA-style) | strict | n/a | n/a | n/a | n/a |
| Ours-text2 (LongDA-style) | loose | n/a | n/a | n/a | n/a |
| Ours-cards2 (ours) | strict | 105 | 91.6 | 104 | 90.4 |
| Ours-cards2 (ours) | loose | 143 | 88.9 | 66 | 95.7 |
| Ours-oracle (given method) | strict | 109 | 88.7 | 100 | 91.1 |
| Ours-oracle (given method) | loose | 135 | 89.3 | 74 | 90.9 |

Answer correctness = mean score_v2 (failed or missing = 0); parts (percent) = mean parts_v2 over answers whose item has that claim kind; failed or missing answers = 0.
Data recall: needed series fetched directly or via an equivalent; "given" = data supplied in the prompt.
Method recall strict (opened): ours/oracle = a card under the question's node(s)/variants opened with get_card (or cited); LongDA-style = a page read with read_source or returned by find_in_document that a node card cites. Loose (seen): also a card shown in a search result; LongDA-style = also a search_methodology hit that a node card cites.
Graph precision: share of retrieved items under the node (ours: cards opened; LongDA-style: distinct pages read), and rank-weighted average precision over the retrieval order; over answers with at least one item.
