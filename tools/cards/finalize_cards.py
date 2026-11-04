"""Card builder, step after gen_questions.py: puts the generated questions, kind and centrality into the cards, appends the questions to
`card_text` (which is what the embedding and the keyword ranking read), and numbers the cards of each document by centrality.
No model call.  python3 tools/cards/finalize_cards.py [--cards work/cards/cards.jsonl] [--questions work/cards/questions.json]
Writes work/cards/cards_q.jsonl. Run embed_cards.py --cards work/cards/cards_q.jsonl afterwards."""
import argparse
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import llm


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--cards', default=os.path.join(llm.WORK, 'cards.jsonl'))
    ap.add_argument('--questions', default=os.path.join(llm.WORK, 'questions.json'))
    ap.add_argument('--out', default=os.path.join(llm.WORK, 'cards_q.jsonl'))
    a = ap.parse_args()
    Q = json.load(open(a.questions))
    cards = [json.loads(l) for l in open(a.cards, encoding='utf-8') if l.strip()]
    by = collections.defaultdict(list)
    for i, c in enumerate(cards):
        q = Q.get(c['card_id'], {}); c['questions'] = q.get('questions', []); c['central'] = q.get('central', 2); c['kind'] = q.get('kind', 'other'); c['central_flag'] = c['central'] == 1
        c['short_formula'] = ' '.join(c['formula'].split())[:160]
        c['card_text'] = (c['card_text'] + ' Questions: ' + ' '.join(c['questions']))[:3200]
        by[c['doc_id']].append(((c['central'], c['kind'] == 'other'), i))
    for d, L in by.items():
        for r, (_, i) in enumerate(sorted(L), 1):
            cards[i]['doc_rank'] = r
    cards.sort(key=lambda c: (c['doc_id'], c['doc_rank']))
    with open(a.out, 'w', encoding='utf-8') as f:
        for c in cards:
            f.write(json.dumps(c, ensure_ascii=False) + '\n')
    print(len(cards), collections.Counter(c['central'] for c in cards), collections.Counter(c['kind'] for c in cards), sum(1 for c in cards if len(c['questions']) == 3))


if __name__ == '__main__':
    main()
