"""Key-free test of tools/retrieval/build_index.py: two invented documents are chunked, 'embedded' by the scripted stand-in for OpenRouter
(tests/fake_openrouter.py, which answers one fixed vector), written to a temporary folder and loaded by tools/retrieval/local_docs.py.
It checks the plumbing (files, check.json accepted, text search, page reading, texts file), not the quality of the chunker or of real embeddings."""
import json, os, re, subprocess, sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(ROOT, 'tests'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'retrieval'))
pytest.importorskip('numpy')
import fake_openrouter as F  # noqa: E402

BUILD = os.path.join(ROOT, 'tools', 'retrieval', 'build_index.py')
DOC_A = '11111111-aaaa-4bbb-8ccc-000000000001'
DOC_B = '22222222-aaaa-4bbb-8ccc-000000000002'

TEXT_A = """[[page 1]]
The Harbor Levy Handbook describes how a small island authority sets a levy on cargo ships.

The levy rate is fixed each spring by the island council and applied to the registered tonnage of every ship that enters the harbor.

[[page 2]]
The zorblax adjustment lowers the levy for ships that use shore power while they are docked.

The adjustment is applied after the base levy is computed and it never reduces the levy below half of the base amount.
"""

TEXT_B = """[[page 1]]
The Orchard Yield Note explains how a cooperative estimates the apple harvest of its member farms.

Each farm reports the number of mature trees and the average crate count per tree counted in late summer.

[[page 2]]
The quenmark correction removes frost damaged trees from the count before the yield is summed over the farms.

The corrected yield is reported to the cooperative board together with the number of farms that answered.
"""


def build(tmp_path, extra=()):
    docs = tmp_path / 'docs'
    docs.mkdir()
    (docs / (DOC_A + '.txt')).write_text(TEXT_A, encoding='utf-8')
    (docs / (DOC_B + '.txt')).write_text(TEXT_B, encoding='utf-8')
    (docs / 'titles.tsv').write_text('doc_id\ttitle\tpublisher\n%s\tHarbor Levy Handbook\tNone\n' % DOC_A, encoding='utf-8')
    out = tmp_path / 'out'
    texts = tmp_path / 'texts.jsonl'
    srv, base = F.start()
    env = {k: v for k, v in os.environ.items() if k != 'OPENROUTER_API_KEY'}
    env.update(OPENROUTER_BASE=base, OPENROUTER_API_KEY='scripted')
    try:
        r = subprocess.run([sys.executable, BUILD, '--docs-dir', str(docs), '--out', str(out), '--texts-out', str(texts), '--batch', '1', '--go', *extra],
                           env=env, capture_output=True, text=True, timeout=300)
    finally:
        srv.shutdown()
    return r, out, texts


def test_dry_run_writes_nothing(tmp_path):
    docs = tmp_path / 'docs'
    docs.mkdir()
    (docs / (DOC_A + '.txt')).write_text(TEXT_A, encoding='utf-8')
    out = tmp_path / 'out'
    env = {k: v for k, v in os.environ.items() if k != 'OPENROUTER_API_KEY'}
    r = subprocess.run([sys.executable, BUILD, '--docs-dir', str(docs), '--out', str(out), '--texts-out', str(tmp_path / 't.jsonl')],
                       env=env, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr[-800:]
    assert 'DRY RUN' in r.stdout
    assert not out.exists()


def test_build_then_load_and_search(tmp_path):
    r, out, texts = build(tmp_path)
    assert r.returncode == 0, (r.stdout + r.stderr)[-1200:]
    for n in ('chunks_M.jsonl', 'chunk_vectors.f32', 'bm25_global.json', 'istbl.json', 'check.json'):
        assert (out / n).exists(), n
    recs = [json.loads(l) for l in open(out / 'chunks_M.jsonl', encoding='utf-8')]
    assert len(recs) == 4                                   # one chunk per page, two pages per document
    assert {r_['d'] for r_ in recs} == {DOC_A, DOC_B}
    assert all(set(r_) == {'id', 'd', 's', 'p', 'q', 'b', 't'} for r_ in recs)
    a = [r_ for r_ in recs if r_['d'] == DOC_A]
    assert [x['p'] for x in a] == [1, 2] and [x['q'] for x in a] == [0, 1] and a[0]['id'] == DOC_A + '-0'
    assert a[0]['b'] == 'Harbor Levy Handbook' and a[0]['t'].startswith('Harbor Levy Handbook\n\n')
    assert os.path.getsize(out / 'chunk_vectors.f32') == 4 * 1536 * 4

    # texts file: the line format that agent_cards._doctext scans
    lines = open(texts, 'rb').read().splitlines()
    assert len(lines) == 2
    assert all(re.match(rb'\{"id": "([0-9a-f-]{36})"', l) for l in lines)
    assert json.loads(lines[0])['text'] == TEXT_A

    import local_docs
    old = os.environ.get('MC_DOCS_DIR')
    os.environ['MC_DOCS_DIR'] = str(out)
    try:
        L = local_docs.LocalDocs(data_dir=str(out))             # check.json is verified here
        assert L.N == 4
        res = L.search('zorblax adjustment', mode='bm25', k=3)
        assert res['hits'][0]['doc_id'] == DOC_A
        assert L.search('quenmark', mode='bm25', k=3)['hits'][0]['doc_id'] == DOC_B
        rd = L.read(DOC_A, 0, 3)
        assert rd['total_chunks'] == 2 and 'zorblax' in ' '.join(c['text'] for c in rd['chunks'])
        pg = L.pages(DOC_A, 2)
        # pages() returns every chunk that reaches the page (a chunk runs up to where the next one starts)
        assert pg['chunks'][-1]['page'] == 2 and 'zorblax' in ' '.join(c['text'] for c in pg['chunks'])
        # document filter of the Text-410 control: only the listed documents are searched (BM25 and dense)
        allow = tmp_path / 'allow.txt'
        allow.write_text(DOC_B + '\n')
        os.environ['TEXT_ALLOW_FILE'] = str(allow)
        try:
            F2 = local_docs.LocalDocs(data_dir=str(out))
            qv = [1.0] * 1536
            assert [h['doc_id'] for h in F2.search('zorblax adjustment', mode='bm25', k=3)['hits']] in ([], [DOC_B])
            assert {h['doc_id'] for h in F2.search('levy', mode='hybrid', k=5, qvec=qv)['hits']} <= {DOC_B}
            assert F2.search('quenmark', mode='bm25', k=3)['hits'][0]['doc_id'] == DOC_B
        finally:
            os.environ.pop('TEXT_ALLOW_FILE', None)
    finally:
        if old is None:
            os.environ.pop('MC_DOCS_DIR', None)
        else:
            os.environ['MC_DOCS_DIR'] = old
