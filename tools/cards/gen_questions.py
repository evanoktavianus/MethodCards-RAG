"""Card builder, question step: for each document, one call from the CARD TEXT ONLY (no document text) that gives, for every card,
three plain-language questions the method answers, a kind and a centrality score (1 = headline method of the document, 2 = supporting
method, 3 = minor item). Card search matches these questions as well as the card text.

  python3 tools/cards/gen_questions.py [--cards work/cards/cards.jsonl]           # dry run: counts only
  python3 tools/cards/gen_questions.py --go --cap 0.5                              # writes work/cards/questions.json (resumable)

Then run finalize_cards.py (puts the questions, kind and centrality into the cards) and embed_cards.py."""
import argparse
import concurrent.futures as cf
import json
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import llm

PROMPT = ("Below are method cards extracted from ONE document (title given). For EACH card output: three plain-language questions that the method answers, "
 "as a practitioner would ask them WITHOUT naming the method or the document (e.g. 'how do I split a change in the current account into saving and investment?'); "
 "\"kind\": one of computational method | indicator definition | statistical standard | administrative rule | other (other = not a quantitative procedure someone would compute); and \"central\": 1 = a headline method of this document (what the document is mainly about), 2 = a supporting method, 3 = a minor item (a definition, a single country's aggregate, a small identity). "
 "Reply with one JSON list only: [{\"card_id\": ..., \"questions\": [q1, q2, q3], \"kind\": ..., \"central\": 1|2|3}, ...] covering every card.")


def txt(c):
    return "- card_id %s | %s | also: %s | when: %s | inputs: %s | formula: %s" % (c['card_id'], c['name'], '; '.join(c['aliases'][:4]), c['applies_when'][:200], '; '.join(c['inputs'][:6])[:200], c['formula'][:200])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--cards', default=os.path.join(llm.WORK, 'cards.jsonl'))
    ap.add_argument('--out', default=os.path.join(llm.WORK, 'questions.json'))
    ap.add_argument('--cap', type=float, default=0.5, help='USD; no new call is started once the cost of this run has reached it')
    ap.add_argument('--workers', type=int, default=16)
    ap.add_argument('--go', action='store_true')
    a = ap.parse_args()
    cards = [json.loads(l) for l in open(a.cards, encoding='utf-8') if l.strip()]
    by = {}
    for c in cards:
        by.setdefault(c['doc_id'], []).append(c)
    Q = json.load(open(a.out)) if os.path.exists(a.out) else {}
    lock = threading.Lock(); spent = [0.0]
    jobs = [(d, cs[i:i + 70]) for d, cs in by.items() for i in range(0, len(cs), 70)]
    jobs = [j for j in jobs if not all(c['card_id'] in Q for c in j[1])]
    print('cards %d | calls to make %d | model %s' % (len(cards), len(jobs), llm.MODEL))
    if not a.go:
        print('DRY RUN: no call made. Add --go to call the model.')
        return

    def one(args):
        d, cs = args
        with lock:
            if spent[0] > a.cap:
                return
        msg = PROMPT + "\n\nDOCUMENT TITLE: %s\n\nCARDS:\n%s" % (cs[0]['doc_title'], '\n'.join(txt(c) for c in cs))
        for att in range(3):
            try:
                c, cost = llm.chat(msg, 16000)
                with lock:
                    spent[0] += cost
                lst = json.loads(c[c.find('['):c.rfind(']') + 1])
                ids = {x['card_id'] for x in cs}
                with lock:
                    for o in lst:
                        if o.get('card_id') in ids:
                            Q[o['card_id']] = {'questions': [str(x) for x in o.get('questions', [])][:3], 'central': int(o.get('central', 2)), 'kind': str(o.get('kind', 'other'))}
                return
            except Exception:
                pass
    with cf.ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(one, jobs))
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(Q, open(a.out, 'w'))
    print('cards with questions', len(Q), 'of', len(cards), 'cost', round(spent[0], 4))


if __name__ == '__main__':
    main()
