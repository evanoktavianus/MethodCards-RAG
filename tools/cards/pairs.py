"""Card builder, merge step 1 of 2 (no model call): candidate pairs of cards from DIFFERENT documents whose card_text vectors have
cosine >= 0.70 or whose name and alias tokens have Jaccard >= 0.5. The vectors are those of embed_cards.py (row i = card i).

  python3 tools/cards/pairs.py [--cards work/cards/cards_v2.jsonl] [--vectors work/cards/card_vectors.f32]
Writes work/cards/pairs.json. Then consolidate.py."""
import argparse
import json
import math
import multiprocessing as mp
import os
import re
import sys
from array import array
from operator import mul

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import llm

STOP = set('the of and a an for in to by on with as at'.split())
D = 1536
cards, V, NT = [], [], []


def nt(c):
    return set(w for w in re.findall(r'[a-z0-9]+', (c['name'] + ' ' + ' '.join(c['aliases'])).lower()) if w not in STOP and len(w) > 2)


def load(cards_path, vec_path):
    global cards, V, NT
    cards = [json.loads(l) for l in open(cards_path, encoding='utf-8') if l.strip()]
    a = array('f'); a.frombytes(open(vec_path, 'rb').read())
    assert len(a) == D * len(cards), 'the number of vectors differs from the number of cards'
    V = []
    for i in range(len(cards)):
        v = a[i * D:(i + 1) * D]; n = math.sqrt(sum(x * x for x in v)) or 1.0; V.append(array('f', [x / n for x in v]))
    NT = [nt(c) for c in cards]


def row(i):
    out = []; vi = V[i]; di = cards[i]['doc_id']
    for j in range(i + 1, len(cards)):
        if cards[j]['doc_id'] == di:
            continue
        cs = sum(map(mul, vi, V[j])); nj = len(NT[i] & NT[j]) / max(1, len(NT[i] | NT[j]))
        if cs >= 0.70 or nj >= 0.5:
            out.append((i, j, round(cs, 4), round(nj, 3)))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--cards', default=os.path.join(llm.WORK, 'cards_v2.jsonl'))
    ap.add_argument('--vectors', default=os.path.join(llm.WORK, 'card_vectors.f32'))
    ap.add_argument('--out', default=os.path.join(llm.WORK, 'pairs.json'))
    a = ap.parse_args()
    load(a.cards, a.vectors)
    with mp.Pool(max(1, mp.cpu_count() - 1)) as p:
        pairs = [x for r in p.imap_unordered(row, range(len(cards)), chunksize=20) for x in r]
    json.dump(pairs, open(a.out, 'w')); print(len(pairs))


if __name__ == '__main__':
    main()
