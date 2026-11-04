"""Card builder, step 3 of 3: embed the card_text of every card with openai/text-embedding-3-small via OpenRouter
(batched inputs, vectors stored as returned, no extra normalisation, as for the reported bank).

Input : work/cards/cards.jsonl (from parse_cards.py)
Output: work/cards/card_vectors.f32   float32, n_cards x 1536, row i = card on line i of cards.jsonl
        work/cards/card_ids.json      card_id of each row

Safe by default: without --go nothing is called. The key is read only from OPENROUTER_API_KEY and is never printed.

  python3 tools/cards/embed_cards.py              # dry run: cards, calls, token and cost estimate
  python3 tools/cards/embed_cards.py --go
"""
import argparse, concurrent.futures as cf, json, os, sys, urllib.request
from array import array

ROOT = os.environ.get('MC_ROOT') or os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
WORK = os.path.join(ROOT, 'work', 'cards')
BASE = os.environ.get('OPENROUTER_BASE', 'https://openrouter.ai/api/v1')
EMB = 'openai/text-embedding-3-small'
DIM = 1536
PRICE_PER_MTOK = 0.02       # USD per million input tokens (list price of the embedding model)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--cards', default=os.path.join(WORK, 'cards.jsonl'))
    ap.add_argument('--batch', type=int, default=64, help='texts per embedding call')
    ap.add_argument('--maxcalls', type=int, default=4000)
    ap.add_argument('--go', action='store_true', help='make the embedding calls (without it: dry run)')
    ap.add_argument('--dry', action='store_true', help='dry run (the default; wins over --go)')
    a = ap.parse_args()
    if not os.path.exists(a.cards):
        sys.exit('No cards file: %s (run parse_cards.py first).' % a.cards)
    with open(a.cards, encoding='utf-8') as f:
        cards = [json.loads(l) for l in f if l.strip()]
    if not cards:
        sys.exit('The cards file is empty.')
    texts = [c['card_text'] for c in cards]
    batches = [texts[i:i + a.batch] for i in range(0, len(texts), a.batch)]
    toks = sum(len(t) for t in texts) // 4
    print('cards %d | calls planned %d (batch %d, cap %d) | est tokens %d | est cost %.5f USD | model %s | endpoint %s' % (
        len(cards), len(batches), a.batch, a.maxcalls, toks, toks * PRICE_PER_MTOK / 1e6, EMB, BASE))
    if len(batches) > a.maxcalls:
        sys.exit('More calls than --maxcalls: nothing was called.')
    if a.dry or not a.go:
        print('DRY RUN: no call made. Add --go to embed.')
        return
    key = os.environ.get('OPENROUTER_API_KEY')
    if not key:
        sys.exit('OPENROUTER_API_KEY is not set in the environment: nothing was called.')

    def one(b):
        err = None
        for att in range(3):
            try:
                r = urllib.request.Request(BASE.rstrip('/') + '/embeddings', data=json.dumps({'model': EMB, 'input': b}).encode(),
                                           headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
                d = json.load(urllib.request.urlopen(r, timeout=300))['data']
                v = [x['embedding'] for _, x in sorted(enumerate(d), key=lambda p: p[1].get('index', p[0]))]
                if len(v) != len(b):
                    raise ValueError('got %d vectors for %d texts' % (len(v), len(b)))
                return v
            except Exception as e:
                err = e
        raise err

    with cf.ThreadPoolExecutor(8) as ex:
        res = list(ex.map(one, batches))
    arr = array('f')
    for b in res:
        for v in b:
            if len(v) != DIM:
                sys.exit('Unexpected vector size %d (expected %d).' % (len(v), DIM))
            arr.extend(v)
    assert len(arr) == len(cards) * DIM
    with open(os.path.join(WORK, 'card_vectors.f32'), 'wb') as f:
        f.write(arr.tobytes())
    with open(os.path.join(WORK, 'card_ids.json'), 'w', encoding='utf-8') as f:
        json.dump([c['card_id'] for c in cards], f)
    print('embedded %d cards; calls %d; wrote %s and card_ids.json' % (len(cards), len(batches), os.path.join(WORK, 'card_vectors.f32')))


if __name__ == '__main__':
    main()
