"""Key-free tests of the ablation, agent-model and extra-analysis tables: no API key, no network, no model call.

They rebuild the three tables from the stored rows and compare them with eval/expected_*.md, check some headline cells, and check
that the released rows hold no trace and no card text."""
import gzip
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import make_metrics as M  # noqa: E402

KNOWN = {'answer', 'error', 'cost', 'truncated', 'tool_calls', 'harness_error', 'item', 'arm', 'rep', 'score_v2', 'parts_v2',
         'vital_all_v2', 'claims_v2', 'judge2_cost', 'judge2_failed', 'judge2_error', 'method', 'style', 'n', 'seen', 'read_ids',
         'cards_seen', 'cards_got', 'n_data_search', 'n_fetch', 'n_series_table', 'n_data_error', 'data_fetched_ids',
         'data_needs', 'data_hit', 'data_needs_fetched', 'data_needs_total', 'cited_card_id', 'cited_none', 'cited_card_known',
         'cited_in_got', 'cited_in_seen', 'any_card_got_true_primary', 'any_card_got_true_any',
         'cited_card_is_true_method_primary', 'cited_card_is_true_method_any', 'cited_card_quotes', 'cited_card_quotes_found',
         'cited_card_quotes_ok', 'method_doc_in_search', 'method_doc_read', 'retrieval', 'final_gate_waived', 'extra_call',
         'fixed_card_ids', 'seen_syn', 'read_ids_syn', 'agent_model', 'turns', 'tool_actions'}


def n_quotes(rows):
    return sum(1 for r in rows if isinstance(r.get('detail'), dict) and isinstance(r['detail'].get('quotes'), dict)
               and any(v for v in r['detail']['quotes'].values()))


TABLES = [('make_ablation.py', 'ablation_results.md', 'expected_ablation.md'),
          ('make_second_model.py', 'second_model_results.md', 'expected_second_model.md'),
          ('make_extra.py', 'extra_analyses.md', 'expected_extra_analyses.md'),
          ('make_controls.py', 'controls_results.md', 'expected_controls.md'),
          ('make_comparisons.py', 'comparisons.md', 'expected_comparisons.md'),
          ('make_band_sensitivity.py', 'band_sensitivity.md', 'expected_band_sensitivity.md'),
          ('make_resources.py', 'resources.md', 'expected_resources.md'),
          ('make_question_review.py', 'question_review.md', 'expected_question_review.md'),
          ('make_retrieval_check.py', 'retrieval_check.md', 'expected_retrieval_check.md')]
HEADLINE = {
    'expected_ablation.md': ['| Cards-fixed | 231 | 0 | 70.2 | 76.2 | 61.7 | 67.4 (n=229) | 33.8 | 55.0 |',
                             '| Cards-as-text | 231 | 2 | 73.0 | 81.8 | 65.4 |',
                             '| Ours-cards2 (control run) | 230 | 2 | 76.9 | 85.9 | 67.3 |'],
    'expected_second_model.md': ['| Answer correctness | 61.4 | 60.2 | 61.5 |', '| Answer correctness | 77.1 | 71.3 | 72.0 |',
                                 '| Ours minus ReAct: Answer correctness | +15.7 [+6.7, +26.2] | +11.1 [+2.3, +20.0] | +10.5 [+1.4, +19.4] |'],
    'expected_controls.md': ['| ReAct-steps | 231 | 1 | 62.8 | 71.2 | 57.7 |', '| Text-410 | 231 | 0 | 76.2 | 87.0 | 69.6 |',
                             '- Answer correctness: Ours-cards2 77.1, ReAct-steps 62.8; difference +14.3 [+5.3, +24.1]'],
    'expected_extra_analyses.md': ['| hard | verified | 142 | 76.4 | 87.0 | 92.7 |', 'p = 0.0024'],
    'expected_comparisons.md': ['| Answer correctness | 77.1 | 61.4 | +15.7 [+6.7, +26.2] (n=231) |', 'rho = -0.59'],
    'expected_band_sensitivity.md': ['| Band hard (METHODS.md) | 141 | 7 | 75.3 | +21.9 [+9.0, +35.3] |'],
    'expected_resources.md': ['| 6. Ours | 9.6 | 19.8 | 0.0027 | 7.5 | 12.8 | 0.0016 |'],
    'expected_question_review.md': ['4 (2.0%, Wilson 95% interval 0.8 to 5.0)', '119 of 120 marks'],
    'expected_retrieval_check.md': ['Agreement 35 of 40 (87.5%, Wilson 95% interval 73.9 to 94.5)', 'pieces 98: correct 98, wrong 0']}


@pytest.mark.parametrize('script,out,expected', TABLES)
def test_table_matches_expected(script, out, expected):
    r = subprocess.run([sys.executable, '-I', os.path.join(ROOT, 'scripts', script)], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-800:]
    got = open(os.path.join(ROOT, 'work', out), encoding='utf-8').read().split('\n')
    exp = open(os.path.join(ROOT, 'eval', expected), encoding='utf-8').read().split('\n')
    assert [l.rstrip() for l in got if l.strip()] == [l.rstrip() for l in exp if l.strip()]
    text = '\n'.join(exp)
    for cell in HEADLINE[expected]:
        assert cell in text, cell


RESULTS = {'results_ablation_fixed': ('Cards-fixed', None), 'results_ablation_astext': ('Cards-as-text', None),
           'results_ablation_control': ('Ours-cards2', None), 'results_haiku_react': ('ReAct-v2', 'anthropic/claude-haiku-5.5'),
           'results_haiku_cards': ('Ours-cards2', 'anthropic/claude-haiku-5.5'), 'results_haiku_oracle': ('Ours-oracle', 'anthropic/claude-haiku-5.5'),
           'results_qwen_react': ('ReAct-v2', 'qwen/qwen3.5-397b-a17b'), 'results_qwen_cards': ('Ours-cards2', 'qwen/qwen3.5-397b-a17b'),
           'results_qwen_oracle': ('Ours-oracle', 'qwen/qwen3.5-397b-a17b'),
           'results_control_reactsteps': ('ReAct-steps', None), 'results_control_text410': ('Text-410', None)}


@pytest.mark.parametrize('name', sorted(RESULTS))
def test_new_result_rows_have_no_text(name):
    arm, model = RESULTS[name]
    rows = M.read_jsonl(os.path.join(M.MAIN, name + '.jsonl.gz'))
    assert len(rows) == 231 and len({r['item'] for r in rows}) == 231
    if any('trace' in r for r in rows):
        pytest.skip('full rows with traces: the text-free checks are for the released rows')
    assert {r['arm'] for r in rows} == {arm}
    for r in rows:
        assert 'trace' not in r and 'fixed_cards_text' not in r and 'judge2_raw' not in r
        assert isinstance(r.get('retrieval'), dict) or (r.get('harness_error') and not r.get('answer'))   # a run that did not complete has no record
        assert set(r) - KNOWN == set(), set(r) - KNOWN
        if model:
            assert r['agent_model'] == model


def test_fixed_cards_count_as_opened():
    rows = M.read_jsonl(os.path.join(M.MAIN, 'results_ablation_fixed.jsonl.gz'))
    if any('trace' in r for r in rows):
        pytest.skip('full rows with traces')
    for r in rows:
        assert len(r['fixed_card_ids']) == 5 and set(r['fixed_card_ids']) <= set(r['retrieval']['opened'])


@pytest.mark.parametrize('name', ['ragas_judge_results', 'ragas_fp_results', 'ragas_ablation_pieces', 'ragas_ablation_fp', 'ragas_haiku_pieces', 'ragas_haiku_fp', 'ragas_qwen_pieces', 'ragas_qwen_fp', 'ragas_control_pieces', 'ragas_control_fp'])
def test_judge_rows_have_no_quoted_spans(name):
    rows = M.read_jsonl(os.path.join(M.MAIN, 'metrics', name + '.jsonl.gz'))
    assert rows
    if n_quotes(rows):
        pytest.skip('full judge rows with quoted spans')
    assert all(r.get('raw') in (None, '') for r in rows)


def test_text410_document_list():
    ids = [l.strip() for l in open(os.path.join(ROOT, 'experiments', 'main_run', 'CTL_text410_docs.txt')) if l.strip()]
    assert len(ids) == 410 and len(set(ids)) == 410
    assert all(len(i) == 36 and i.count('-') == 4 for i in ids)
