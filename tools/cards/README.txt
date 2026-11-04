Rebuilding method cards from documents you obtain yourself
==========================================================

The release does not contain the source documents. The scripts here build a card bank from a folder of plain-text documents
with the same prompts, the same windowing, the same quote checks and the same embedding model as the reported bank. The reported
cards were extracted, given their questions and merged with z-ai/glm-5.3-flash (temperature 0). A bank rebuilt this way will
DIFFER from the reported one: the model may answer differently from run to run, and three steps of the reported bank are not
included (see "Not included"). Results on a rebuilt bank are therefore not comparable number by number with the reported results.

Pipeline, in order
------------------
 1. compile_cards.py   extract: one call per document (or window) lists every quantitative procedure with its fields
 2. parse_cards.py     verify in the document: a parameter is kept only if its quote occurs verbatim in the document text
 3. triage.py          (optional) one call per document: methodology document (1), periodic or country report (2), neither (3)
 4. gen_questions.py   questions: per document, one call on the card text only gives three plain-language questions per card,
                       a kind and a centrality score
 5. finalize_cards.py  puts the questions, kind and centrality into the cards and the questions into card_text (no model call)
 6. verify_pages.py    verify on the page: a parameter or formula is kept only if its text occurs inside one [[page N]] span;
                       writes the sources (pages, quote, role, hash of the cited pages) (no model call)
 7. embed_cards.py     embeddings of card_text
 8. pairs.py           candidate pairs of cards from different documents (no model call)
 9. consolidate.py     merge: one call per component of candidate pairs partitions the cards into sets of the same method;
                       the sets are merged into one card with several sources and the parameter conflicts
10. embed_cards.py     again on the merged file, because the text of merged cards has changed

Every model call uses the prompt in the script (the prompts are those of the reported run). Nothing is called without --go.

Not included: the pass over country reports, the model judgement that folded country-report cards into library cards, and the
re-extraction of footnotes and boxes for three documents. The reported bank (6,465 cards from 410 documents, see
tools/bank/card_index.jsonl) used them; a bank rebuilt with steps 1 to 10 has none of these cards.

Input format
------------
One folder (DOCS_DIR) with one UTF-8 text file per document, named <doc_id>.txt. A page starts with the marker
[[page N]] (N = 1, 2, ...) at its beginning; the pages in the cards come from these markers.
Optional file DOCS_DIR/titles.tsv, tab separated, one document per line: doc_id <TAB> title <TAB> publisher
(the title goes into the prompt and the card; the publisher is used only when the model gives no institution).

Key and endpoint
----------------
export OPENROUTER_API_KEY=...        (needed only for --go; never printed, never stored)
OPENROUTER_BASE (optional)           default https://openrouter.ai/api/v1
MC_CARD_MODEL (optional)             default z-ai/glm-5.3-flash (the model of the reported cards); when you set another
                                     model, the provider pin of the original run is not sent
Nothing is called without --go. Without --go (or with --dry) each script only prints what it would do.

The commands (from the repository root)
----------------------------------------
Steps 1 to 3 and 7 (the extraction, the document check and the embedding):
1. python3 tools/cards/compile_cards.py --docs-dir DOCS_DIR [--docs=ID,ID] [--cap 1.0] [--maxcalls 50] [--go]
   one model call per document (a long document, above 700,000 tokens, is split into windows), temperature 0.
   Results: work/cards/compiled/<doc_id>_<window>.json. Re-running skips finished windows.
   Failed windows are written as .err files; delete them to retry.
2. python3 tools/cards/parse_cards.py --docs-dir DOCS_DIR
   no model call. Keeps a parameter only if its quote is found verbatim in the document text.
   Results: work/cards/cards.jsonl and work/cards/cards_stats.json (look at param_drop_share_of_quoted).
3. python3 tools/cards/embed_cards.py [--go]
   embeddings of card_text with openai/text-embedding-3-small (1536 numbers per card, one batch of 64 cards per call).
   Results: work/cards/card_vectors.f32 (row i = line i of cards.jsonl) and work/cards/card_ids.json.

Steps 3 to 6 and 8 to 10 (from the repository root; all take --help; defaults read and write work/cards/):
   python3 tools/cards/triage.py --docs-dir DOCS_DIR [--go]
   python3 tools/cards/gen_questions.py [--cap 0.5] [--go]                 -> work/cards/questions.json
   python3 tools/cards/finalize_cards.py                                    -> work/cards/cards_q.jsonl
   python3 tools/cards/verify_pages.py --docs-dir DOCS_DIR                  -> work/cards/cards_v2.jsonl
   python3 tools/cards/embed_cards.py --cards work/cards/cards_v2.jsonl [--go]   (card_vectors.f32 in the same folder)
   python3 tools/cards/pairs.py                                             -> work/cards/pairs.json
   python3 tools/cards/consolidate.py [--go]                                -> work/cards/cards_v3.jsonl
   python3 tools/cards/embed_cards.py --cards work/cards/cards_v3.jsonl [--go]
The scripts are tested for import and for the programmatic parts (page check, finalize, merge) by tests/test_cards_pipeline_steps.py;
the model steps were not run again for this release.

Cost estimates (printed by the dry run; list prices)
-----------------------------------------------------
compile: about 0.0345 USD per million input tokens plus about 6,000 output tokens per window at 0.0823 USD per million
         (chars/4 = tokens): a 100-page document of 300,000 characters costs about 0.003 USD.
embed:   0.02 USD per million tokens; about 1,000 cards cost well under 0.01 USD.
Stops: --cap (USD, default 1.0) and --maxcalls (default 50) for step 1; the dry run prints the numbers first.

Using the rebuilt bank with the system
--------------------------------------
Reading of the code in this repository:
- experiments/agent/agent_cards.py reads the cards from tools/bank/ + env CARDS_FILE (default cards_final.jsonl); the value is
  appended to the path tools/bank/, so give a relative path:
      CARDS_FILE=../../work/cards/cards.jsonl
- tools/bank/bank_client.py (BankSearch) reads the vectors from the fixed path tools/bank/data/card_vectors_final.f32 and its
  card file from the argument cards_file (default cards_final.jsonl). There is no environment variable for the vectors. To
  use the rebuilt vectors, copy work/cards/card_vectors.f32 over tools/bank/data/card_vectors_final.f32 and use the same
  card file for both, in a separate copy of the repository so that the shipped files and the tests stay unchanged.
  The number of vectors must equal the number of cards; card_ids.json lets you check the order.
- tools/bank/bank_search.py (pure python search) reads tools/bank/cards.jsonl and tools/bank/data/card_vectors.f32.
The agent's read_source tool reads document texts from a texts file (env MC_TEXTS, see experiments/agent/agent_cards.py);
that file is not part of this builder.
