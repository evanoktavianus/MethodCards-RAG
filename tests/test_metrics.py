"""Key-free tests for scripts/make_metrics.py: no API key, no network, no model call.

They rebuild the RAGAS-style metrics from the stored results and check the headline cells and the stored row counts."""
import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import make_metrics as M  # noqa: E402


@pytest.fixture(scope='module')
def ctx():
    return M.Ctx()


@pytest.fixture(scope='module')
def A(ctx):
    return M.build(ctx)


def c(A, g, arm, key):
    v = M.cells(A, g, arm)[key]
    return v if isinstance(v, str) else round(v * 100, 1)


def test_row_counts_per_arm(ctx):
    for g, rows in ctx.results.items():
        arms = {}
        for r in rows:
            arms[r['arm']] = arms.get(r['arm'], 0) + 1
        assert set(arms.values()) == {M.N_EXPECTED[g]}, (g, arms)
        assert len(arms) == (7 if not g.endswith('datagiven') else 2), (g, arms)
        items = [r['item'] for r in rows if r['arm'] == rows[0]['arm']]
        assert len(set(items)) == M.N_EXPECTED[g]


def test_judge_files_complete(ctx):
    for g in ('hard', 'easier'):
        for arm in M.ARMS:
            n = sum(1 for k in ctx.pieces if k[0] == g and k[2] == arm)
            assert n == M.N_EXPECTED[g], (g, arm, n)
        for arm in M.METHOD_ARMS:
            for metric in ('faithfulness', 'precision'):
                n = sum(1 for k in ctx.fp if k[0] == metric and k[1] == g and k[3] == arm)
                assert n == M.N_EXPECTED[g], (metric, g, arm, n)


def test_hard_headlines(A):
    assert c(A, 'hard', 'Ours-cards2', 'answer_correctness') == 77.1
    assert c(A, 'hard', 'Ours-cards2', 'context_recall_method') == 75.3
    assert c(A, 'hard', 'Ours-text2', 'context_recall_method') == 57.5
    assert c(A, 'hard', 'Ours-cards2', 'faithfulness') == 64.5
    assert c(A, 'hard', 'Ours-text2', 'faithfulness') == 49.8
    assert c(A, 'hard', 'Ours-cards2', 'method_correctness_all') == 90.0
    assert c(A, 'hard', 'Ours-text2', 'method_correctness_all') == 86.3
    assert c(A, 'hard', 'Ours-cards2', 'data_recall_share') == 71.0
    assert c(A, 'hard', 'Ours-cards2', 'graph_recall_strict') == 61.9
    assert c(A, 'hard', 'Ours-cards2', 'graph_precision_rank_weighted') == 54.5
    assert c(A, 'hard', 'Ours-cards2', 'fully_correct') == 45.0


def test_context_precision(A):
    assert c(A, 'hard', 'Ours-text2', 'context_precision') == 39.1
    assert c(A, 'hard', 'Ours-cards2', 'context_precision') == 77.2
    assert c(A, 'hard', 'Ours-oracle', 'context_precision') == 84.5
    assert c(A, 'easier', 'Ours-text2', 'context_precision') == 18.6
    assert c(A, 'easier', 'Ours-cards2', 'context_precision') == 80.7
    assert c(A, 'easier', 'Ours-oracle', 'context_precision') == 75.8


def test_only_empty_retrievals_left_out_of_precision(ctx, A):
    skipped = {}
    for (metric, g, item, arm), r in ctx.fp.items():
        if metric == 'precision' and r.get('skipped') == 'no items or pieces':
            skipped[(g, arm)] = skipped.get((g, arm), 0) + 1
    assert skipped == {('hard', 'Ours-text2'): 3, ('easier', 'Ours-text2'): 4}
    # the denominator keeps failed answers (they count 0)
    for g, n_skip in (('hard', 3), ('easier', 4)):
        n = len([v for v in A[g]['Ours-text2'] if v['prec'] is not None])
        assert n == M.N_EXPECTED[g] - n_skip


def test_easier_headlines(A):
    assert c(A, 'easier', 'Ours-cards2', 'answer_correctness') == 81.6
    assert c(A, 'easier', 'Ours-cards2', 'context_recall_method') == 73.5
    assert c(A, 'easier', 'Ours-text2', 'context_recall_method') == 49.6
    assert c(A, 'easier', 'Ours-cards2', 'faithfulness') == 62.8
    assert c(A, 'easier', 'Ours-text2', 'faithfulness') == 42.1
    assert c(A, 'easier', 'Ours-cards2', 'method_correctness_all') == 89.0
    assert c(A, 'easier', 'Ours-text2', 'method_correctness_all') == 94.2
    assert c(A, 'easier', 'Ours-cards2', 'data_recall_share') == 69.4
    assert c(A, 'easier', 'Ours-text2', 'graph_recall_strict') == 33.0


def test_table2(A):
    f = lambda g, arm: round(M.col(A[g][arm], 'answer') * 100, 1)
    assert [f('hard', 'Ours-cards2'), f('hard', 'Ours-oracle'), f('hard_datagiven', 'Ours-cards2'),
            f('hard_datagiven', 'Ours-oracle')] == [77.1, 80.4, 83.4, 84.2]
    assert [f('easier', 'Ours-cards2'), f('easier', 'Ours-oracle'), f('easier_datagiven', 'Ours-cards2'),
            f('easier_datagiven', 'Ours-oracle')] == [81.6, 83.3, 91.0, 89.9]


def test_pooled_440(A):
    _, res = M.pooled(A)
    assert res['Ours-text2']['n'] == res['Ours-cards2']['n'] == 440
    assert round(res['Ours-text2']['context_precision'] * 100, 1) == 29.4
    assert round(res['Ours-cards2']['context_precision'] * 100, 1) == 78.9
    assert round(res['Ours-cards2']['method_correctness'] * 100, 1) == 89.6


def test_failed_answers_count_zero(ctx, A):
    # a failed answer (no score) is 0 in answer correctness and in the judge columns
    failed = [r for r in ctx.results['easier'] if r['arm'] == 'Ours-cards2' and r.get('score_v2') is None]
    assert failed
    r = failed[0]
    v = ctx.answer_values('easier', r)
    assert v['answer'] == 0.0 and v['mc_all'] == 0.0 and v['cr'] == 0.0 and v['faith'] == 0.0 and v['prec'] == 0.0
    assert v['text'] == 0.0 and v['data'] == 0.0 and v['computation'] == 0.0


def test_script_runs_and_prints_tables(capsys):
    sys.argv = ['make_metrics.py']
    M.main()
    out = capsys.readouterr().out
    for s in ('Full table (RAGAS names)', 'Table 7', 'Pooled over both groups (440 questions)',
              'Complete table, every metric', '| **6. Ours** | **75.3** | **77.2** |'):
        assert s in out
