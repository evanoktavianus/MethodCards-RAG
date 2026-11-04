# MethodCards-RAG

Method cards for agentic retrieval-augmented generation on public-finance statistics: an agent that finds the published calculation method a question needs, among cards built from institutional methodology documents, and applies it to official statistics. Every question has an answer key computed from frozen public data.

Article: submitted to Electronics. Authors: Evan Oktavianus, Dana Indra Sensuse, Imairi Eitiveni (Faculty of Computer Science, Universitas Indonesia).

## Where things are

| Folder | What it holds |
|---|---|
| `tools/bank/card_index.jsonl` | the 6,465 method cards built from 410 methodology documents as an index without text: card id, document, pages, name, and a flag for cards whose source sentence was not verified in the document; the cards themselves are not distributed (see Documents); the check that the 284 stored source sentences of the 92 cards cited in our answers occur on their cited pages needs the documents, so it cannot be rerun from this repository |
| `tools/bank/` | card search used by the Ours arms (BM25 and dense cosine, merged by reciprocal rank fusion): `bank_search.py`, `bank_server.py`, `bank_client.py`; it reads `cards_final.jsonl` and `data/card_vectors_final.f32` in this folder; `bank_pg_client.py` is the same search in PostgreSQL, as used for the reported runs |
| `tools/cards/` | the card builder, step by step: extraction (`compile_cards.py`, `parse_cards.py`), document triage, question generation (`gen_questions.py`, `finalize_cards.py`), page-level source check (`verify_pages.py`), embedding (`embed_cards.py`) and merging of cards across documents (`pairs.py`, `consolidate.py`); `README.txt` gives the order, the input format, the commands and the cost |
| `tools/retrieval/` | `local_docs.py` (document search and page reading from files), `build_index.py` (makes those files from your own text documents), the export scripts that made them for the reported runs, query embedding and search parameters |
| `tools/data/` | the data tool the agents use (`datatool.py`) and its frozen store of macro-fiscal series (sources and vintages in `NOTICE`) |
| `data/documents/` | not in the repository: where the document files go (see Documents) |
| `dataset/items/` | 440 questions with answer keys (231 institutional procedures, 209 standard formulas); `DATA.md` describes the fields; `RUBRIC.md`, `METHODS.md` give the rules and the methods |
| `gold/` | the reference programs that recompute each key's value on the frozen data; the programs of a few methods also read tables copied from documents, which are not distributed |
| `data/` (other) | frozen extracts read by the prompt builder (`frozen_extra/`), the document index and the country income classification |
| `experiments/splits/` | the two question lists: `hard.json` (institutional procedures) and `easier.json` (standard formulas) |
| `experiments/main_run/` | `run_main.py` (all arms) and the stored result rows `results_final_hard`, `results_final_easier`, `results_final_hard_datagiven`, `results_final_easier_datagiven` (gzipped JSON lines, one row per question and arm, with answer, cost, judge verdicts and a `retrieval` record of ids; the agents' step-by-step texts are not distributed); the 231 institutional procedures again in the two ablation arms and the control run of ours (`results_ablation_fixed`, `results_ablation_astext`, `results_ablation_control`), the two control arms (`results_control_reactsteps`, `results_control_text410`; the 410 document ids of Text-410 are in `CTL_text410_docs.txt`) and with two further agent models (`results_haiku_react`, `results_haiku_cards`, `results_haiku_oracle`; `results_qwen_react`, `results_qwen_cards`, `results_qwen_oracle`) |
| `experiments/main_run/metrics/` | the stored judge outputs behind the retrieval and generation metrics (`ragas_judge_results`, `ragas_fp_results`; for the ablation `ragas_ablation_pieces`, `ragas_ablation_fp`; for the two further models `ragas_haiku_pieces`, `ragas_haiku_fp`, `ragas_qwen_pieces`, `ragas_qwen_fp`; for the control arms `ragas_control_pieces`, `ragas_control_fp`; gzipped JSON lines, one row per question and arm) |
| `experiments/main_run/judge/` | `ragas_judge.py`, the RAGAS-style judge (prompts and settings) that produced the stored judge outputs in `experiments/main_run/metrics/`, with its helpers `mm_common.py`, and `cut_share.py`, which counts how many retrieved cards and pages are longer than the 1,500 characters the context-precision judge sees; a rerun needs the full answer rows with tool traces, which are not distributed |
| `experiments/baselines/`, `agent/`, `data_blocks/`, `prompts_data/`, `prompts/` | arm code, the judge, the prompt builder and the data blocks it shows |
| `dataset/references/` | the references the metrics use: method pieces per question, equivalent series per needed series, the method tree and the map from the 28 methods to its nodes |
| `eval/human_check/` | 40 blind answers with the author's scores, and the table of the author's and the judge's scores per point |
| `eval/human_check_retrieval/` | the author's blind check of 60 judge decisions on context recall, context precision and faithfulness, and of the method pieces of 40 questions (ids and marks only; the grading sheet quotes documents and is not distributed) |
| `eval/question_review/` | the marks of the review of 200 questions by language-model agents and of the author's check of 40 of them (no question text), and the four questions with a wrong reference |
| `eval/card_audit/` | the counts of the author's audit of 30 method cards against their sources (the audit sheet holds document text and is not distributed) |
| `eval/expected_metrics.md` | the output of `scripts/make_metrics.py`, to diff your rebuild against |
| `eval/expected_ablation.md`, `expected_second_model.md` (the three-model table), `expected_controls.md`, `expected_extra_analyses.md`, `expected_comparisons.md`, `expected_band_sensitivity.md`, `expected_resources.md`, `expected_question_review.md` | the output of `scripts/make_ablation.py`, `make_second_model.py`, `make_controls.py`, `make_extra.py`, `make_comparisons.py`, `make_band_sensitivity.py`, `make_resources.py` and `make_question_review.py`, to diff your rebuild against |
| `scripts/` | key-free scripts: the tables, the metrics, the ablation, agent-model, comparison, grouping, resource and extra-analysis tables, the judge-agreement and question-review numbers |
| `tests/` | the test suite, with a scripted stand-in for OpenRouter (`fake_openrouter.py`) |

## Arm ids and the paper

Arm ids in the code and in the result files, and the row of the paper they stand for.

| Arm id (code, result files) | In the paper |
|---|---|
| `CoT0` | Ladder row 1, Memory only (CoT) |
| `CoT1` | Ladder row 2, Data in prompt (CoT + data table) |
| `PoT` | Ladder row 3, PoT |
| `ReAct-v2` | Ladder row 4, ReAct |
| `Ours-text2` | Ladder row 5, LongDA-style (search over the raw text of the documents) |
| `Ours-cards2` | Ladder row 6, Ours (method-card search); also the data-found, method-found cell of the oracle analysis |
| `Ours-oracle` | Oracle analysis, method given; the data-given cells are the same arms in `results_final_*_datagiven` (run without `DATA_TOOL=1`) |
| `Cards-as-text` | Ablation: cards searched and read through the raw-text tools |
| `Cards-fixed` | Ablation: the five cards of one search in the first message, no method tools |
| `ReAct-steps` | Control for RQ1: ReAct with the prompt steps of ours (Section 4.4) |
| `Text-410` | Control for RQ3: LongDA-style restricted to the 410 documents of the cards (Section 4.4) |
| `Ours-cards2` in `results_ablation_control` | Control run of ours with the code used for both ablations |
| `ReAct-v2`, `Ours-cards2`, `Ours-oracle` in `results_haiku_*`, `results_qwen_*` | The three settings with claude-haiku-5.5 and qwen3.5-397b-a17b (Table 11) |

Question groups: `hard.json` is the institutional procedures (231 questions), `easier.json` the standard formulas (209).

## Setup

Python 3.10 or later. The release tests were run on Python 3.14; the reported runs used Python 3.13.5 with numpy 2.2.4, pandas 2.2.3, scipy 1.15.3 and statsmodels 0.14.4 (paper, Section 4.9). Run everything from the repository root.

```
python3 -m venv .venv && source .venv/bin/activate
pip install -e '.[test]'          # all that the key-free tier needs
pip install -e '.[run]'           # model runs: numpy, pandas, scipy, statsmodels (code sandbox, document index)

python3 -m pytest -q              # key-free tests, about 30 seconds
```

## Results, commands and result files

No row needs a model call or a key. Output of the commands goes to the screen or to `work/`.

| Paper | Command | Stored result |
|---|---|---|
| Table 6 (the ladder), Table 7 (oracle analysis, both groups); also checks that every score is the weighted mean of its parts | `python3 scripts/make_tables.py --check` | `experiments/main_run/results_final_*.jsonl.gz` |
| Retrieval and generation metrics for every arm: context recall (method and data), context precision, faithfulness, method correctness, method explained, data and computation correctness, answer correctness, fully correct answers; pooled over the 440 questions | `python3 scripts/make_metrics.py` | `experiments/main_run/metrics/`, `dataset/references/`, `eval/expected_metrics.md` |
| Human check of the judge: agreement and Cohen's kappa | `python3 scripts/judge_agreement.py` | `eval/human_check/` |
| Human check of the judge on the retrieval metrics, and of the method pieces | `python3 scripts/make_retrieval_check.py` | `eval/human_check_retrieval/`, `eval/expected_retrieval_check.md` |
| Ablation of the card search (institutional procedures): the five cards of one search put in the first message (`Cards-fixed`), cards searched and read through the text tools (`Cards-as-text`), and a control run of ours; all metrics, with paired bootstrap differences over methods | `python3 scripts/make_ablation.py` | `experiments/main_run/results_ablation_*.jsonl.gz`, `metrics/ragas_ablation_*`, `eval/expected_ablation.md` |
| Three agent models (glm-5.3-flash, claude-haiku-5.5, qwen3.5-397b-a17b) in three settings (ReAct, ours, ours with the method given) on the institutional procedures, side by side on every metric | `python3 scripts/make_second_model.py` | `experiments/main_run/results_haiku_*.jsonl.gz`, `results_qwen_*.jsonl.gz`, `metrics/ragas_haiku_*`, `metrics/ragas_qwen_*`, `eval/expected_second_model.md` |
| Control runs (institutional procedures): ReAct with the prompt steps of ours (`ReAct-steps`) and the LongDA-style baseline restricted to the 410 documents of the cards (`Text-410`), next to ReAct, LongDA-style and ours of the main run; all metrics, with paired bootstrap differences over methods | `python3 scripts/make_controls.py` | `experiments/main_run/results_control_*.jsonl.gz`, `metrics/ragas_control_*`, `eval/expected_controls.md` |
| Paired comparisons of the main run: our agent minus ReAct and minus the LongDA-style baseline on every metric of Tables 6 and 8 in both groups, the oracle analysis (Table 7), robustness (Table 10: subsets, leave one method out, tolerances halved and doubled) and the analysis over all 28 methods (Spearman correlation, pooled gain, sign-flip test); 95% cluster bootstrap over methods | `python3 scripts/make_comparisons.py` | `experiments/main_run/results_final_*.jsonl.gz`, `metrics/`, `eval/expected_comparisons.md` |
| Sensitivity to the grouping: the gain of our agent on the questions of each `Band` of `dataset/METHODS.md` and of the groups of the paper | `python3 scripts/make_band_sensitivity.py` | `eval/expected_band_sensitivity.md` |
| Resources per question (Table D1): model turns, tool actions, cost and failed answers per row, and the cost of the two further agent models | `python3 scripts/make_resources.py` | `experiments/main_run/results_*.jsonl.gz`, `eval/expected_resources.md` |
| Review of the question set: wrong references among 200 questions (with Wilson interval) and the agreement of the author's check of 40 of them with the review (marks and Cohen's kappa) | `python3 scripts/make_question_review.py` | `eval/question_review/`, `eval/expected_question_review.md` |
| Extra analyses: answers by verified or unverified cited card, method found per 1,000 tokens of context, per-method gains with exact sign-flip tests, the card named in our answers (from a document of the method; the method's own card), the method source named on the composite-indicator questions | `python3 scripts/make_extra.py` | `eval/expected_extra_analyses.md` |
| Data tool against the values the prompt builder shows, for all 440 questions | `python3 tools/data/check_values.py` | `tools/data/check_values_report.json` |
| The question set, the splits, one row per question and arm, the numeric scoring rule, no keys or private paths in the repository | `python3 -m pytest -q` | `tests/test_keyfree.py` |
| Card search finds a card by its own vector | `python3 -m pytest -q tests/test_cards.py` | `tools/bank/data/` |
| The whole pipeline of every arm against a scripted stand-in for the model (the Ours arms need the document files, see Documents) | `python3 -m pytest -q -m "slow or not slow" tests/test_scripted_run.py` (several minutes) | none |

Expected output of the first rows: ours 77.1 (institutional procedures) and 81.6 (standard formulas), the memory-only baseline 44.4 and 57.6, the oracle table (institutional procedures) 77.1, 80.4, 83.4, 84.2 and (standard formulas) 81.6, 83.3, 91.0, 89.9; context recall (method) of ours 75.3 and 73.5, of the text-search baseline 57.5 and 49.6. Failed or unfinished answers count as 0 in every column; context precision leaves out answers that retrieved no method item, which only the text-search arm has (3 institutional procedures, 4 standard formulas); judge agreement 170 of 178 scored rows (95.5%), kappa 0.92. The answer-to-system key of the human check is withheld on purpose; the marks are in `eval/human_check/human_check_40.md`.

Expected output of the ablation (answer correctness, institutional procedures): ours, control run 76.9, `Cards-as-text` 73.0, `Cards-fixed` 70.2 (main run: ours 77.1, text-search baseline 74.9); context recall (method) 75.8, 75.2, 55.0. Controls, answer correctness: `ReAct-steps` 62.8 (ReAct 61.4, ours 77.1), `Text-410` 76.2 (text-search baseline 74.9). Agent models, answer correctness (ReAct, ours, ours with the method given): glm-5.3-flash 61.4, 77.1, 80.4; claude-haiku-5.5 60.2, 71.3, 72.4; qwen3.5-397b-a17b 61.5, 72.0, 71.4. The scripts write to `work/` and print the same text as the files in `eval/`; `python3 -m pytest -q tests/test_new_tables.py` compares them.

## Runs with a model

These need `OPENROUTER_API_KEY` in the environment. Answer model `z-ai/glm-5.3-flash`, temperature 0; judge `deepseek/deepseek-v4.1-flash`; query, card and series embeddings `openai/text-embedding-3-small`; all through OpenRouter. The cost of the glm-5.3-flash runs (answers plus judge) was USD 0.2 to 1.1 per arm and question group; each stored row carries its `cost` and `judge2_cost` (agent costs of the other models are at their own prices).

```
export OPENROUTER_API_KEY=...
mkdir -p work

# count the calls first: no model call, no key
python3 -I experiments/main_run/run_main.py --dry --set=hard.json:hard --arms=CoT0,CoT1,PoT,ReAct-v2,Ours-text2,Ours-cards2,Ours-oracle

# the four baseline arms on five questions (settings of the reported runs)
DATA_TOOL=1 BROAD_DATA=1 ORACLE_SRC=methods \
  python3 -I experiments/main_run/run_main.py --go --set=hard.json:hard --arms=CoT0,CoT1,PoT,ReAct-v2 --limit=5 --out=../../work/baselines_hard.jsonl

# the Ours arms (need the document files, see Documents; Ours-oracle also needs the three oracle files named there, so leave it out of --arms without them; the index takes about two minutes to load)
DATA_TOOL=1 ORACLE_SRC=methods \
  python3 -I experiments/main_run/run_main.py --go --set=hard.json:hard --arms=Ours-text2,Ours-cards2,Ours-oracle --limit=5 --out=../../work/ours_hard.jsonl
```

The ablation arms are `Cards-fixed` (the five cards of one search with the question as query are in the first message, no method tools; the prompt differs from ours only in the sentences about the method tools) and `Cards-as-text` (the text-search prompt and tools of `Ours-text2`, over the text of the cards instead of documents, ranked by the card search); their configurations are `fixed` and `astext` in `experiments/agent/agent_cards.py`. The other agent models are selected with `AGENT_MODEL=anthropic/claude-haiku-5.5` or `AGENT_MODEL=qwen/qwen3.5-397b-a17b` (the provider pin of the default model is sent only for the default model; each row then carries `agent_model`, and the run prints its token tally); `--max-cost=USD` stops starting new jobs once the agent and judge cost of this launch has reached the cap.

```
# the ablation arms and another agent model on five questions
DATA_TOOL=1 ORACLE_SRC=methods \
  python3 -I experiments/main_run/run_main.py --go --set=hard.json:hard --arms=Cards-fixed,Cards-as-text --limit=5 --out=../../work/ablation_hard.jsonl
AGENT_MODEL=anthropic/claude-haiku-5.5 DATA_TOOL=1 BROAD_DATA=1 ORACLE_SRC=methods \
  python3 -I experiments/main_run/run_main.py --go --set=hard.json:hard --arms=ReAct-v2 --limit=5 --max-cost=1 --out=../../work/haiku_hard.jsonl
```

The control arms: `ReAct-steps` is `ReAct-v2` with the prompt steps of `Ours-cards2` that need no method tool (`STEPS_LINE` in `run_baselines.py`); it needs no document files:

```
DATA_TOOL=1 BROAD_DATA=1 ORACLE_SRC=methods \
  python3 -I experiments/main_run/run_main.py --go --set=hard.json:hard --arms=ReAct-steps --limit=5 --out=../../work/reactsteps_hard.jsonl
```

`Text-410` is `Ours-text2` with the text search restricted to the document ids in a file; it runs alone and with that file set:

```
TEXT_ALLOW_FILE=experiments/main_run/CTL_text410_docs.txt DATA_TOOL=1 ORACLE_SRC=methods \
  python3 -I experiments/main_run/run_main.py --go --set=hard.json:hard --arms=Text-410 --limit=5 --out=../../work/text410_hard.jsonl
```

`--set=hard.json:hard` or `easier.json:easier` selects the group, `--items=ID,ID` selects questions, `--workers=N` sets concurrency; the run is resumable and writes one judged row per question and arm. The data-given cells of Table 7 are the same run without `DATA_TOOL=1`. The Ours arms keep the document index in memory (about 2 GB of memory).

Model-written code runs in a child process of your machine (`python -I`, cpu and file limits, a guard that blocks file access and system modules). That is not user isolation: if you do not trust the model, run the repository in a container or on a throw-away machine. `MC_SANDBOX=ssh` with `MC_SANDBOX_HOST=<host>` sends the code to another machine instead, as the reported runs did.

Runs with a model will not reproduce the stored rows exactly: model outputs vary across providers and over time.

### Documents

The document text is not part of this repository. The Ours-text2 arm (text search), the page reading of the card arms and the quote check need it; the baseline arms, the card search, the tables, the metrics and the tests of the stored results do not. `tools/retrieval/local_docs.py` serves the document files from the folder `data/documents/` (or the folder in `MC_DOCS_DIR`) with BM25 and dense search merged by reciprocal rank fusion; it expects `chunks_M.jsonl.gz` (or `.jsonl`), `chunk_vectors.f32`, `bm25_global.json`, `istbl.json` and `check.json`. To make them from your own documents, put one `<doc_id>.txt` per document in a folder (a `[[page N]]` marker at the start of each page, an optional `titles.tsv`; see `tools/cards/README.txt`) and run `python3 tools/retrieval/build_index.py --docs-dir <folder>` (a dry run by default; `--go` embeds the chunks; three short documents of about 54,000 characters cost USD 0.0003). It writes the files above and the full-text file below. `tools/retrieval/export_corpus_from_postgres.py` wrote the files from the database of the reported runs. The full texts read by the card arms are expected in `tools/bank/data/texts.jsonl` (or the file in `MC_TEXTS`). Without these files the Ours arms stop with a message that says so. `Ours-oracle` also needs `experiments/baselines/oracle_methods.json`, `oracle_passages.json` and `oracle_excerpts.json`, the method passages that the arm puts in the first message; they quote the documents and are not distributed, and without them the arm stops with a message that names the files (the scripted test of `Ours-oracle` is skipped with the same reason). The method cards are not distributed either: build them from your own documents with `tools/cards/` (`README.txt` there gives the input format, the three commands and the cost) and point the system at them with `CARDS_FILE` and `tools/bank/data/card_vectors_final.f32`; a rebuilt bank will differ from the one behind the reported results, which stay in `experiments/main_run/`. The stored result rows hold answers, scores, judge verdicts and a record of ids (cards opened, pages read, series fetched); the agents' step-by-step texts are not distributed. Each row of an agent arm also holds two counts taken from the step-by-step texts: `turns` (model calls) and `tool_actions` (tool actions executed); the older field `tool_calls` of the ReAct rows counts only the Python runs. The card search runs in memory over the card vectors in `tools/bank/data/`; `bank_pg_client.py` documents the PostgreSQL version of the same algorithm, as used for the reported runs.

## Notes on the stored results

Text copied from documents is not distributed. In all result and judge files the `trace` (the agents' step-by-step texts) is replaced by the compact `retrieval` record (card ids opened or seen, [document, page] pairs read or returned, series ids; no text), the five card texts of `Cards-fixed` are replaced by their ids in `fixed_card_ids`, and the short spans that the context-recall judge copied from the context (`detail.quotes`) are empty; no script reads them. Each run is stored as one row per question and arm.

## Tests

```
python3 -m pytest -q                         # key-free, no network, about 30 seconds
python3 -m pytest -q -m "slow or not slow"   # adds the scripted end-to-end runs of the arms (the Ours arms only with the document files; about 4 minutes)
```

## Licence

Software (`scripts/`, `tools/` code, `experiments/` code, `gold/`, `tests/`): Apache License 2.0 (`LICENSE`). Questions, keys, the card index, stored results and the human check (`dataset/`, `eval/`, `tools/bank/card_index.jsonl`, `experiments/main_run/results_*`, `experiments/main_run/metrics/`): Creative Commons Attribution 4.0 International (`LICENSE-DATA.txt`); credit the authors (`NOTICE`). The official statistics and the text and tables taken from published documents keep the terms of their publishers; see `NOTICE`. The repository does not redistribute the documents.
