"""Whole-pipeline tests against a scripted stand-in for OpenRouter (tests/fake_openrouter.py): no key, no network, no real model, no cost.
They check the plumbing: prompt building, the data tool, the code sandbox, the card search, the document index, the judge and the result rows.
They do not check that a model answers well: the scripted model always gives the same two-step answer.
The baseline test needs numpy (the code sandbox preloads it). The Ours test is marked slow and needs the document files (folder MC_DOCS_DIR, default data/documents/; not distributed); without them it is skipped.
The Ours test also reads card source texts only if tools/bank/data/texts.jsonl (env MC_TEXTS) exists; without it the quote check is skipped."""
import json, os, subprocess, sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(ROOT, 'tests'))
pytest.importorskip('numpy')
import fake_openrouter as F  # noqa: E402

MAIN = os.path.join(ROOT, "experiments", "main_run")
needs_cards = pytest.mark.skipif(not os.path.exists(os.path.join(ROOT, "tools", "bank", "cards_final.jsonl")),
                                 reason="cards_final.jsonl (card texts, publishers' terms) is not in this release; the scripted run loads the card file")


def docs_folder():
    return os.environ.get('MC_DOCS_DIR') or os.path.join(ROOT, 'data', 'documents')


def docs_present():
    D = docs_folder()
    return all(os.path.exists(os.path.join(D, n)) for n in ('bm25_global.json', 'istbl.json', 'check.json', 'chunk_vectors.f32')) \
        and (os.path.exists(os.path.join(D, 'chunks_M.jsonl.gz')) or os.path.exists(os.path.join(D, 'chunks_M.jsonl')))


def a_document_id():
    """A document of the methodology index that is not hidden by the default profile (read from the first chunks of the document folder)."""
    import gzip
    hidden = set(json.load(open(os.path.join(ROOT, 'tools', 'retrieval', 'params.json')))['fm_gold_elsewhere'])
    p = os.path.join(docs_folder(), 'chunks_M.jsonl.gz')
    with (gzip.open(p, 'rt', encoding='utf-8') if os.path.exists(p) else open(os.path.join(docs_folder(), 'chunks_M.jsonl'), encoding='utf-8')) as f:
        for line in f:
            d = json.loads(line)['d']
            if d not in hidden:
                return d
    raise RuntimeError('no usable document in the chunk file')


def ids_for_script(with_doc=False):
    card = json.loads(open(os.path.join(ROOT, 'tools', 'bank', 'cards_final.jsonl'), encoding='utf-8').readline())['card_id']
    return card, (a_document_id() if with_doc else 'none')      # a card, and (Ours arms only) a document that is in the methodology index


def run(arms, item, out_abs, extra_env=None):
    card, doc = ids_for_script(with_doc=any(a.startswith('Ours') for a in arms.split(',')))
    srv, base = F.start(card_id=card, doc_id=doc)
    env = {k: v for k, v in os.environ.items() if k != 'OPENROUTER_API_KEY'}
    env.update(OPENROUTER_BASE=base, OPENROUTER_API_KEY='scripted', DATA_TOOL='1', BROAD_DATA='1', ORACLE_SRC='methods')
    env.update(extra_env or {})
    r = subprocess.run([sys.executable, '-I', os.path.join(MAIN, 'run_main.py'), '--go', '--set=hard.json:hard', '--arms=' + arms, '--items=' + item,
                        '--workers=2', '--out=' + os.path.relpath(out_abs, MAIN)], env=env, capture_output=True, text=True, timeout=3000)
    srv.shutdown()
    assert r.returncode == 0, r.stderr[-800:]
    return [json.loads(l) for l in open(out_abs)]


def first_hard_item():
    return json.load(open(os.path.join(ROOT, 'experiments', 'splits', 'hard.json')))['hard'][0]


@needs_cards
def test_baseline_arms_end_to_end(tmp_path):
    rows = run('CoT0,CoT1,PoT,ReAct-v2', first_hard_item(), str(tmp_path / 'r.jsonl'))
    assert {r['arm'] for r in rows} == {'CoT0', 'CoT1', 'PoT', 'ReAct-v2'}
    assert all(r['score_v2'] is not None and not r.get('harness_error') for r in rows)
    react = [r for r in rows if r['arm'] == 'ReAct-v2'][0]
    assert react['tool_calls'] >= 1                      # the model-written code ran in the local sandbox
    assert 'The scripted answer is 4' in react['answer']


def check_ours_rows(rows, arms):
    assert {r['arm'] for r in rows} == set(arms)
    assert all(r['score_v2'] is not None and not r.get('harness_error') for r in rows)
    for r in rows:                                                                   # every tool of the arm was used
        n = r['n']
        assert n['py'] >= 1 and n['src'] >= 1, (r['arm'], n)
        if r['arm'] == 'Ours-text2':
            assert n['search'] >= 1 and n['find'] >= 1, (r['arm'], n)
        else:
            assert n['card_search'] >= 1 and n['get'] >= 1, (r['arm'], n)


@needs_cards
@pytest.mark.slow
@pytest.mark.skipif(not docs_present(), reason="document text is not distributed with the repository (publishers' terms); put the document files in MC_DOCS_DIR (default data/documents/)")
def test_ours_arms_end_to_end(tmp_path):
    rows = run('Ours-cards2,Ours-text2', first_hard_item(), str(tmp_path / 'r.jsonl'))
    check_ours_rows(rows, ('Ours-cards2', 'Ours-text2'))


ORACLE_FILES = ('oracle_methods.json', 'oracle_passages.json', 'oracle_excerpts.json')
oracle_present = all(os.path.exists(os.path.join(ROOT, 'experiments', 'baselines', f)) for f in ORACLE_FILES)


@needs_cards
@pytest.mark.slow
@pytest.mark.skipif(not docs_present(), reason="document text is not distributed with the repository (publishers' terms); put the document files in MC_DOCS_DIR (default data/documents/)")
@pytest.mark.skipif(not oracle_present, reason="Ours-oracle needs experiments/baselines/oracle_methods.json, oracle_passages.json and oracle_excerpts.json, which quote the documents and are not distributed")
def test_ours_oracle_arm_end_to_end(tmp_path):
    rows = run('Ours-oracle', first_hard_item(), str(tmp_path / 'r.jsonl'))
    check_ours_rows(rows, ('Ours-oracle',))
