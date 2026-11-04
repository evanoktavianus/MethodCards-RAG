"""Key-free tests: no API key, no network, no model call, no remote host. Run from the repository root:  python3 -m pytest -q

They check that the released files are complete and consistent, that the tables of the paper are rebuilt from the stored rows,
that the judge-agreement numbers are rebuilt from the human check, and that the repository carries no keys or private paths.
"""
import glob, gzip, json, os, re, subprocess, sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path[:0] = [os.path.join(ROOT, 'scripts'), os.path.join(ROOT, 'tools', 'data')]
import make_tables as mt          # noqa: E402
import judge_agreement as ja      # noqa: E402

ARMS7 = {'CoT0', 'CoT1', 'PoT', 'ReAct-v2', 'Ours-text2', 'Ours-cards2', 'Ours-oracle'}


def items():
    out = {}
    for p in glob.glob(os.path.join(ROOT, 'dataset', 'items', '*', '*.json')):
        d = json.load(open(p, encoding='utf-8'))
        out[os.path.basename(p)[:-5]] = d
    return out


def test_question_set():
    it = items()
    hard = json.load(open(os.path.join(ROOT, 'experiments', 'splits', 'hard.json')))['hard']
    easy = json.load(open(os.path.join(ROOT, 'experiments', 'splits', 'easier.json')))['easier']
    assert len(it) == 440 and len(hard) == 231 and len(easy) == 209
    assert not set(hard) & set(easy) and set(hard) | set(easy) == set(it)


@pytest.mark.parametrize('name,n_items', [('results_final_hard', 231), ('results_final_easier', 209)])
def test_one_row_per_item_and_arm(name, n_items):
    rs = mt.rows(name)
    assert len(rs) == 7 * n_items
    assert {r['arm'] for r in rs} == ARMS7
    assert len({(r['item'], r['arm']) for r in rs}) == len(rs)


def test_datagiven_rows():
    rs = mt.rows('results_final_hard_datagiven')
    assert len(rs) == 2 * 231 and {r['arm'] for r in rs} == {'Ours-cards2', 'Ours-oracle'}


def test_table1_and_table2_rebuild(capsys):
    sys.argv = ['make_tables.py']
    mt.main()
    out = capsys.readouterr().out
    expect = {'CoT0': (44.4, 57.6), 'CoT1': (61.8, 86.3), 'PoT': (62.5, 88.0), 'ReAct-v2': (61.4, 81.4),
              'Ours-text2': (74.9, 83.9), 'Ours-cards2': (77.1, 81.6)}
    for arm, (h, e) in expect.items():
        assert re.search(r'`%s` \| %.1f \| %.1f \|' % (arm, h, e), out), arm
    assert '| data found | 77.1 | 80.4 |' in out and '| data given | 83.4 | 84.2 |' in out


def test_score_is_weighted_mean_of_parts():
    bad = 0
    for name in ('results_final_hard', 'results_final_easier', 'results_final_hard_datagiven'):
        for r in mt.rows(name):
            re_ = mt.recomputed(r)
            if r.get('score_v2') is not None and re_ is not None and abs(re_ - r['score_v2']) > 0.11:
                bad += 1
    assert bad == 0


def test_judge_agreement():
    import csv
    p = os.path.join(ROOT, 'eval', 'human_check', 'human_check_scores.csv')
    pairs = [(float(r['judge_score']), float(r['author_score'])) for r in csv.DictReader(open(p)) if r['judge_score'] != '']
    assert len(pairs) == 178
    assert sum(1 for j, h in pairs if j == h) == 170
    assert abs(ja.kappa(pairs) - 0.924) < 0.002


def test_numeric_band_rule():
    sys.path[:0] = [os.path.join(ROOT, 'experiments', d) for d in ('baselines', 'prompts', 'prompts_data', 'data_blocks')]
    import run_baselines as rb
    spec = (1.069, 1.0, 2.0)
    assert rb.band_score(spec, 1.5) == 1.0        # within the full band
    assert rb.band_score(spec, 2.8) == 0.5        # within the partial band, same sign
    assert rb.band_score(spec, -0.15) == 0.0      # inside the partial distance but the opposite sign: no credit
    assert rb.band_score(spec, None) == 0.0


def test_data_tool_without_key(monkeypatch):
    monkeypatch.delenv('OPENROUTER_API_KEY', raising=False)
    import datatool as dt
    t = dt.fetch_series('imf_weo:GGXWDG_NGDP', 'IND', 2021, 2022)
    assert '83.473' in t and '82.166' in t
    s = dt.search_series('general government gross debt percent of GDP', limit=3, mode='bm25')
    assert 'imf_weo:GGXWDG_NGDP' in s


def test_method_cards_present():
    bank = os.path.join(ROOT, "tools", "bank")
    p = os.path.join(bank, "cards_final.jsonl")
    if not os.path.exists(p):               # release without card texts: the text-free index has one line per card
        p = os.path.join(bank, "card_index.jsonl")
    n = sum(1 for _ in open(p, encoding="utf-8"))
    assert n == 6465


def test_all_python_compiles():
    for p in glob.glob(os.path.join(ROOT, '**', '*.py'), recursive=True):
        compile(open(p, encoding='utf-8').read(), p, 'exec')


def test_dry_run_needs_neither_key_nor_vm():
    env = {k: v for k, v in os.environ.items() if k not in ('OPENROUTER_API_KEY', 'MC_SANDBOX_HOST', 'MC_BANK_HOST')}
    r = subprocess.run([sys.executable, '-I', os.path.join(ROOT, 'experiments', 'main_run', 'run_main.py'), '--dry',
                        '--set=hard.json:hard', '--arms=CoT0,CoT1,PoT,ReAct-v2'], capture_output=True, text=True, env=env, timeout=300)
    assert r.returncode == 0 and 'jobs to run 924' in r.stdout, r.stderr[-500:]


TEXT_EXT = ('.py', '.md', '.json', '.jsonl', '.csv', '.tsv', '.psv', '.txt', '.sh', '.toml', '.yml', '.yaml', '.cff', '.sql')


def _text_files():
    for p in glob.glob(os.path.join(ROOT, '**', '*'), recursive=True):
        if os.path.isfile(p) and p.endswith(TEXT_EXT) and os.sep + '.git' + os.sep not in p and os.sep + '.venv' + os.sep not in p \
                and os.path.basename(p) != 'test_keyfree.py' and os.sep + 'documents' + os.sep not in p \
                and not p.endswith(os.path.join('tools', 'bank', 'data', 'texts.jsonl')):
            yield p


def test_no_keys_or_private_paths():
    pat = re.compile(r'sk-or-[A-Za-z0-9]{8,}|sk-ant-[A-Za-z0-9]{8,}|/Users/[a-z]+|ringkas[a]nnet|ash[_-]dms|econ_run|ghp_[A-Za-z0-9]{20,}')
    hits = []
    for p in _text_files():
        with open(p, encoding='utf-8', errors='ignore') as f:
            for n, line in enumerate(f, 1):
                if pat.search(line):
                    hits.append('%s:%d' % (os.path.relpath(p, ROOT), n))
                    break
    for p in glob.glob(os.path.join(ROOT, '**', '*.gz'), recursive=True):
        if os.sep + 'documents' + os.sep in p:      # public document text, scanned once at export time
            continue
        with gzip.open(p, 'rt', encoding='utf-8', errors='ignore') as f:
            for n, line in enumerate(f, 1):
                if pat.search(line):
                    hits.append('%s:%d' % (os.path.relpath(p, ROOT), n))
                    break
    assert not hits, hits
