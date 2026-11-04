"""Test of the local card search; it needs numpy and the card files of this repository only (no document text, no key, no network)."""
import json, os, sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
np = pytest.importorskip("numpy")
CARDS = os.path.join(ROOT, "tools", "bank", "cards_final.jsonl")


@pytest.mark.skipif(not os.path.exists(CARDS), reason="cards_final.jsonl (card texts, publishers' terms) is not in this release; only tools/bank/card_index.jsonl is")
def test_card_search_finds_a_card_by_its_own_vector():
    sys.path.insert(0, os.path.join(ROOT, 'tools', 'bank'))
    from bank_client import BankSearch
    cards = [json.loads(l) for l in open(os.path.join(ROOT, 'tools', 'bank', 'cards_final.jsonl'), encoding='utf-8')]
    vecs = np.fromfile(os.path.join(ROOT, 'tools', 'bank', 'data', 'card_vectors_final.f32'), dtype=np.float32).reshape(len(cards), 1536)
    b = BankSearch()
    try:
        for i in (0, 1234, 6464):
            r = b.search(cards[i]['name'], k=5, mode='dense', qvec=vecs[i].tolist())
            assert r['hits'][0]['card_id'] == cards[i]['card_id']
        r = b.search('debt stabilising primary balance', k=5, mode='bm25')
        assert r['hits'] and r['hits'][0]['card_id']
    finally:
        b.close()
