"""Offline test of the card builder tools/cards/ (compile_cards.py -> parse_cards.py -> embed_cards.py) against the scripted stand-in
tests/fake_openrouter.py: no key, no network, no real model, no cost, no publisher text. Two invented documents are written to a temporary
folder; the scripted compiler answers with cards whose quotes are sentences of the request itself, so the verbatim-quote check of
parse_cards.py is really exercised. The cards and vectors are then loaded with the card search of tools/bank/ (bank_server.Bank, the
search code behind bank_client.BankSearch) and a distinctive word of each invented indicator must find its card.
The scripted answers say nothing about the quality of cards a real model would write; this checks the plumbing only."""
import base64, json, os, subprocess, sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(ROOT, 'tests'))
import fake_openrouter as F  # noqa: E402

DIM = 1536
DOCS = {
    'zgap_aaa': ("[[page 1]]\n"
                 "The Zorblax gap indicator measures how far observed revenue departs from its smoothed trend in the invented fiscal framework of Freedonia.\n"
                 "Formula: ZG_t = 100 * (R_t - Rtrend_t) / Rtrend_t\n\n"
                 "[[page 2]]\n"
                 "The trend is a centred moving average over five years, and a gap above two percent triggers the review procedure of the ministry.\n"),
    'qbl_bbb1': ("[[page 1]]\n"
                 "The Quibblet debt ratio compares the stock of guaranteed liabilities with the average primary surplus of the invented republic of Ruritania.\n"
                 "Formula: QD_t = Guarantees_t / Average_surplus_t\n\n"
                 "[[page 2]]\n"
                 "The average surplus is taken over the last four years, and a ratio above three triggers a warning in the annual report.\n"),
}
TITLES = {'zgap_aaa': ('Zorblax gap indicator', 'Ministry of Freedonia'), 'qbl_bbb1': ('Quibblet debt ratio', 'Treasury of Ruritania')}


def run(script, args, env):
    r = subprocess.run([sys.executable, '-I', os.path.join(ROOT, 'tools', 'cards', script)] + args, env=env, cwd=ROOT,
                       capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, (script, r.stdout[-800:], r.stderr[-800:])
    return r.stdout


def test_card_builder_end_to_end_offline(tmp_path):
    docs = tmp_path / 'docs'
    docs.mkdir()
    for d, t in DOCS.items():
        (docs / (d + '.txt')).write_text(t, encoding='utf-8')
    (docs / 'titles.tsv').write_text('doc_id\ttitle\tpublisher\n' + ''.join('%s\t%s\t%s\n' % (d, a, b) for d, (a, b) in TITLES.items()), encoding='utf-8')

    srv, base = F.start()
    try:
        env = {k: v for k, v in os.environ.items() if k not in ('OPENROUTER_API_KEY', 'MC_CARD_MODEL', 'MC_CARD_DOCS', 'MC_ROOT')}
        env.update(OPENROUTER_BASE=base, OPENROUTER_API_KEY='scripted', MC_ROOT=str(tmp_path), NO_PROXY='127.0.0.1', no_proxy='127.0.0.1')

        dry = run('compile_cards.py', ['--docs-dir', str(docs)], env)               # a dry run calls nothing and writes nothing
        assert 'DRY RUN' in dry and not (tmp_path / 'work' / 'cards' / 'compiled').exists()

        run('compile_cards.py', ['--go', '--docs-dir', str(docs), '--cap', '1', '--maxcalls', '10'], env)
        compiled = sorted(os.listdir(tmp_path / 'work' / 'cards' / 'compiled'))
        assert compiled == ['qbl_bbb1_0.json', 'zgap_aaa_0.json'], compiled
        run('parse_cards.py', ['--docs-dir', str(docs)], env)
        run('embed_cards.py', ['--go'], env)
    finally:
        srv.shutdown()

    work = tmp_path / 'work' / 'cards'
    cards = [json.loads(l) for l in open(work / 'cards.jsonl', encoding='utf-8') if l.strip()]
    stats = json.load(open(work / 'cards_stats.json', encoding='utf-8'))
    assert stats['docs_with_cards'] == 2 and stats['cards'] == len(cards)
    assert stats['params_dropped'] == 0 and stats['params_kept_with_quote'] >= 2        # the scripted quotes are verbatim in the documents
    for d in DOCS:
        assert any(c['doc_id'] == d for c in cards), d
    need = ('card_id', 'doc_id', 'doc_title', 'name', 'card_text', 'applies_when', 'pages', 'short_formula', 'kind', 'central', 'conflicts',
            'parameters', 'sources')
    for c in cards:
        for k in need:
            assert k in c, (c['card_id'], k)
        assert c['doc_title'] == TITLES[c['doc_id']][0] and c['card_text'].startswith(c['name'])
        assert c['sources'] and all({'doc_id', 'doc_title', 'pages', 'role'} <= set(s) for s in c['sources'])
        assert c['sources'][0]['doc_id'] == c['doc_id'] and c['sources'][0]['pages']
        assert all(p['quote'] and p['page'] in (1, 2) for p in c['parameters'] if p['value'] is not None)
    assert len({c['card_id'] for c in cards}) == len(cards)

    raw = open(work / 'card_vectors.f32', 'rb').read()
    assert len(raw) == 4 * DIM * len(cards)
    assert json.load(open(work / 'card_ids.json', encoding='utf-8')) == [c['card_id'] for c in cards]

    sys.path.insert(0, os.path.join(ROOT, 'tools', 'bank'))
    from bank_server import Bank
    bank = Bank({'cards': cards, 'vecs_b64': base64.b64encode(raw).decode()})
    for word, doc in (('zorblax', 'zgap_aaa'), ('quibblet', 'qbl_bbb1')):
        hit = bank.search(word, mode='bm25', k=3)['hits'][0]
        assert hit['doc_id'] == doc, (word, hit)
        assert hit['sources'][0]['doc_id'] == doc
    for i in (0, len(cards) - 1):                                                      # dense: a card's own vector finds that card
        import array
        v = array.array('f'); v.frombytes(raw[4 * DIM * i: 4 * DIM * (i + 1)])
        assert bank.search(cards[i]['name'], qvec=list(v), mode='dense', k=1)['hits'][0]['card_id'] == cards[i]['card_id']
