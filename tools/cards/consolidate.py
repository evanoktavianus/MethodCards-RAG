"""Card builder, merge step 2 of 2: consolidation of the same method described in several documents.
Candidate groups = connected components of the cross-document card pairs of pairs.py with (card_text cosine >= 0.85) or (name/alias token
Jaccard >= 0.6); one model call per component (cards listed, the model partitions them into sets of cards for the same method and lists
parameter conflicts); then a programmatic merge. Primary source = triage label 1 first, then centrality, then the number of verified
parameters. The merged card keeps one `sources` entry per document (role `gives_parameter` if the source adds a parameter name, else
`restates`), the union of aliases and questions, and `conflicts` where the same parameter has different values on different cards.
Cards of the same document are never merged. Components of more than 45 cards are split into slices of 45.

  python3 tools/cards/consolidate.py            # dry run: number of components and calls
  python3 tools/cards/consolidate.py --go       # writes work/cards/consolidation.json and work/cards/cards_v3.jsonl
  python3 tools/cards/consolidate.py --skip-calls   # merge again from an existing consolidation.json
Afterwards run embed_cards.py --cards work/cards/cards_v3.jsonl (the text of merged cards has changed)."""
import argparse
import collections
import concurrent.futures as cf
import json
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import llm
from verify_pages import norm

PROMPT = ("Below are method cards from different documents. Partition them into sets of cards that describe the SAME method (same formula or procedure for the same quantity; "
          "cards that are merely related, or the same topic with a different procedure, must stay apart). Cards that match no other card are omitted. For each set also list parameter CONFLICTS "
          "(the same parameter with different values across cards of the set; compare only values shown on the cards). Reply with one JSON object only: "
          "{\"groups\": [{\"card_ids\": [...], \"conflicts\": [{\"parameter\": \"...\", \"values\": [{\"card_id\": \"...\", \"value\": \"...\"}]}]}]}")


def txt(c):
    return "- card_id %s | doc: %s | name: %s | also: %s | formula: %s | params: %s" % (c['card_id'], c['doc_title'][:80], c['name'], '; '.join(c['aliases'][:4]),
        (c['formula'] or c['formula_paraphrase'] or '')[:160], '; '.join('%s = %s' % (p['name'], p['value']) for p in c['parameters'][:8])[:300])


def key_of(c):
    return (0 if c.get('triage_label') == 1 else 1, c.get('central', 2), -len(c['parameters']), c.get('doc_rank', 99))


def components(cards, pairs):
    par = list(range(len(cards)))

    def fd(x):
        while par[x] != x:
            par[x] = par[par[x]]; x = par[x]
        return x
    for i, j, c, nj in pairs:
        if c >= 0.85 or nj >= 0.6:
            par[fd(i)] = fd(j)
    comp = collections.defaultdict(list)
    for i in range(len(cards)):
        comp[fd(i)].append(i)
    comps = [v[k:k + 45] for v in comp.values() if len(v) > 1 for k in range(0, len(v), 45)]
    return [v for v in comps if len(v) > 1]


def merge(cards, res):
    byid = {c['card_id']: c for c in cards}
    used = set(); merged_n = 0; dropped = set()
    for g in res:
        ids = [x for x in g['card_ids'] if x in byid and x not in used]
        ids = list(dict.fromkeys(ids))
        if len(ids) < 2:
            continue
        docs = {byid[x]['doc_id'] for x in ids}
        if len(docs) < 2:
            continue          # same-document sets are not merged
        group = sorted((byid[x] for x in ids), key=key_of); pr = group[0]; used.update(ids)
        names = {norm(p['name']).lower(): p for p in pr['parameters']}
        for o in group[1:]:
            si = len(pr['sources']); s = dict(o['sources'][0])
            newnames = [p for p in o['parameters'] if norm(p['name']).lower() not in names]
            s['role'] = 'gives_parameter' if newnames else 'restates'
            pr['sources'].append(s)
            for p in o['parameters']:
                p2 = dict(p); p2['source'] = si
                if norm(p['name']).lower() not in names:
                    pr['parameters'].append(p2); names[norm(p['name']).lower()] = p2
            pr['aliases'] = list(dict.fromkeys(pr['aliases'] + [o['name']] + o['aliases']))
            pr['questions'] = (pr['questions'] + [q for q in o['questions'] if q not in pr['questions']])[:6]
            dropped.add(o['card_id']); pr.setdefault('merged_card_ids', []).append(o['card_id'])
            if pr['formula'] == '' and o['formula']:
                pr['formula'] = o['formula']; pr['formula_quote'] = dict(o['formula_quote'], source=si); pr['short_formula'] = o['short_formula']
        conf = []
        for cf_ in g.get('conflicts', []):
            vals = []
            for v in cf_.get('values', []):
                c0 = byid.get(v.get('card_id'))
                if c0 and c0['card_id'] in ids:
                    si = next((k for k, s in enumerate(pr['sources']) if s['doc_id'] == c0['doc_id']), 0)
                    vals.append({'value': str(v.get('value')), 'source': si, 'doc_id': c0['doc_id']})
            if len({x['value'] for x in vals}) > 1:
                conf.append({'parameter': str(cf_.get('parameter')), 'values': vals})
        pr['conflicts'] = conf; merged_n += 1
    out = []
    for c in cards:
        if c['card_id'] in dropped:
            continue
        if c.get('merged_card_ids'):
            c['card_text'] = (c['card_text'] + ' Also called: ' + '; '.join(c['aliases']) + ' Questions: ' + ' '.join(c['questions']))[:3600]
            c['pages'] = c['sources'][0]['pages']
        out.append(c)
    return out, merged_n


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--cards', default=os.path.join(llm.WORK, 'cards_v2.jsonl'))
    ap.add_argument('--pairs', default=os.path.join(llm.WORK, 'pairs.json'))
    ap.add_argument('--groups', default=os.path.join(llm.WORK, 'consolidation.json'))
    ap.add_argument('--out', default=os.path.join(llm.WORK, 'cards_v3.jsonl'))
    ap.add_argument('--workers', type=int, default=16)
    ap.add_argument('--go', action='store_true')
    ap.add_argument('--skip-calls', action='store_true')
    a = ap.parse_args()
    cards = [json.loads(l) for l in open(a.cards, encoding='utf-8') if l.strip()]
    comps = components(cards, json.load(open(a.pairs)))
    print('components', len(comps), 'cards', sum(map(len, comps)), '| model', llm.MODEL)
    if not a.skip_calls:
        if not a.go:
            print('DRY RUN: no call made. Add --go to call the model.')
            return
        lock = threading.Lock(); spent = [0.0]; res = []

        def one(idx):
            cs = [cards[i] for i in idx][:45]
            msg = PROMPT + "\n\nCARDS:\n" + '\n'.join(txt(c) for c in cs)
            for att in range(3):
                try:
                    c, cost = llm.chat(msg, 8000)
                    with lock:
                        spent[0] += cost
                    o = json.loads(c[c.find('{'):c.rfind('}') + 1]); ids = {x['card_id'] for x in cs}
                    with lock:
                        res.extend(g for g in o.get('groups', []) if len([x for x in g.get('card_ids', []) if x in ids]) > 1)
                    return
                except Exception:
                    pass
        with cf.ThreadPoolExecutor(a.workers) as ex:
            list(ex.map(one, comps))
        json.dump(res, open(a.groups, 'w')); print('model groups', len(res), 'cost', round(spent[0], 4))
    res = json.load(open(a.groups))
    out, merged_n = merge(cards, res)
    with open(a.out, 'w', encoding='utf-8') as f:
        for c in out:
            f.write(json.dumps(c, ensure_ascii=False) + '\n')
    multi = [c for c in out if len(c['sources']) > 1]
    print('cards before', len(cards), 'after', len(out), 'merged sets', merged_n, 'cards with >1 source', len(multi), 'with conflicts', sum(1 for c in out if c['conflicts']),
          'sources max', max(len(c['sources']) for c in out))


if __name__ == '__main__':
    main()
