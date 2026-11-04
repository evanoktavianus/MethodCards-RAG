"""Offline checks of the card-builder steps after the extraction: page-level source check (verify_pages.py), question step
(gen_questions.py, finalize_cards.py), merge (pairs.py, consolidate.py) and triage.py. No key, no network, no model call: the modules
must import, the model steps must refuse to call without --go, and the programmatic parts (page check, finalize, merge) are run on
invented cards."""
import importlib
import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TOOLS = os.path.join(ROOT, 'tools', 'cards')
sys.path.insert(0, TOOLS)
MODS = ['llm', 'triage', 'gen_questions', 'finalize_cards', 'verify_pages', 'pairs', 'consolidate']


def test_modules_import():
    for m in MODS:
        importlib.import_module(m)


def card(cid, doc, name, formula='', params=(), central=2):
    return {'card_id': cid, 'doc_id': doc, 'doc_title': 'T ' + doc, 'name': name, 'aliases': [], 'applies_when': 'always', 'inputs': ['x'],
            'formula': formula, 'formula_paraphrase': None, 'formula_quote': None, 'short_formula': formula, 'card_text': name + '.',
            'parameters': [{'name': n, 'value': v, 'quote': q, 'page': 1, 'source': 0} for n, v, q in params], 'pages': [1],
            'questions': ['q1'], 'central': central, 'doc_rank': 1, 'triage_label': None}


def test_page_check_and_merge(tmp_path):
    import verify_pages as vp
    import consolidate as co
    docs = tmp_path / 'docs'
    docs.mkdir()
    (docs / 'd1.txt').write_text('[[page 1]]\nThe zorb index uses a weight of 0.4 here.\n[[page 2]]\nElsewhere the weight is 0.9 only.\n')
    (docs / 'd2.txt').write_text('[[page 1]]\nThe zorb index is also defined with a cutoff of 3.0 percent.\n')
    c1 = card('d1-01', 'd1', 'Zorb index', params=[('weight', '0.4', 'a weight of 0.4'), ('bad', '1', 'a weight of 0.4 and 0.9')])
    c2 = card('d2-01', 'd2', 'Zorb index', params=[('cutoff', '3.0', 'a cutoff of 3.0 percent')])
    cards_p = tmp_path / 'cards.jsonl'
    cards_p.write_text('\n'.join(json.dumps(c) for c in (c1, c2)) + '\n')
    out = tmp_path / 'v2.jsonl'
    r = subprocess.run([sys.executable, '-I', os.path.join(TOOLS, 'verify_pages.py'), '--docs-dir', str(docs), '--cards', str(cards_p), '--out', str(out)],
                       capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stderr[-500:]
    v2 = [json.loads(l) for l in open(out)]
    assert [len(c['parameters']) for c in v2] == [1, 1]                 # the quote spanning two pages is dropped
    assert v2[0]['sources'][0]['pages'] == [1] and not v2[0]['source_unverified']
    merged, n = co.merge(v2, [{'card_ids': ['d1-01', 'd2-01'], 'conflicts': []}])
    assert n == 1 and len(merged) == 1 and len(merged[0]['sources']) == 2
    assert {p['name'] for p in merged[0]['parameters']} == {'weight', 'cutoff'}
    assert co.components(v2, [[0, 1, 0.9, 1.0]]) == [[0, 1]]


def test_model_steps_refuse_without_go(tmp_path):
    env = {k: v for k, v in os.environ.items() if k != 'OPENROUTER_API_KEY'}
    cards_p = tmp_path / 'cards.jsonl'
    cards_p.write_text(json.dumps(card('d1-01', 'd1', 'Zorb index')) + '\n')
    r = subprocess.run([sys.executable, '-I', os.path.join(TOOLS, 'gen_questions.py'), '--cards', str(cards_p), '--out', str(tmp_path / 'q.json')],
                       capture_output=True, text=True, env=env, cwd=ROOT)
    assert r.returncode == 0 and 'DRY RUN' in r.stdout
    assert not (tmp_path / 'q.json').exists()
