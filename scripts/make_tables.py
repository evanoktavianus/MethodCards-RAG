#!/usr/bin/env python3
"""Rebuild Tables 1 and 2 from the stored result rows. No key, no model call, standard library only.

    python3 scripts/make_tables.py                      # prints Markdown
    python3 scripts/make_tables.py --json work/tables.json

Score of a row = score_v2 (0-100). A failed or unfinished answer has score_v2 = null and counts as 0, as in the paper.
--check also recomputes every score_v2 from the stored per-part scores (parts_v2) with the claim-kind weights
text 40 / data 20 / computation 25 / answer 15, and reports rows where the two differ.
"""
import argparse, gzip, json, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RES = os.path.join(ROOT, 'experiments', 'main_run')
W = {'text': 40, 'data': 20, 'computation': 25, 'answer': 15}
NAMES = [('CoT0', 'Memory only (CoT)'), ('CoT1', 'Data in prompt (CoT + data table)'), ('PoT', 'PoT (+ data table)'),
         ('ReAct-v2', 'Method left to the model (ReAct)'), ('Ours-text2', 'LongDA-style (ReAct + text search)'),
         ('Ours-cards2', 'Ours (ReAct + method cards)')]


def rows(name):
    for ext in ('.jsonl.gz', '.jsonl'):
        p = os.path.join(RES, name + ext)
        if os.path.exists(p):
            op = gzip.open if ext.endswith('gz') else open
            with op(p, 'rt', encoding='utf-8') as f:
                return [json.loads(l) for l in f if l.strip()]
    sys.exit('missing result file: ' + name)


def mean(xs):
    return sum(xs) / len(xs) if xs else float('nan')


def by_arm(rs):
    d = {}
    for r in rs:
        d.setdefault(r['arm'], []).append(r)
    return d


def score(r):
    return r['score_v2'] if r.get('score_v2') is not None else 0.0


def recomputed(r):
    p = r.get('parts_v2') or {}
    if not p:
        return None
    return round(100 * sum(W[k] * v for k, v in p.items()) / sum(W[k] for k in p), 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json')
    ap.add_argument('--check', action='store_true', help='recompute score_v2 from parts_v2 and list differences')
    a = ap.parse_args()
    hard, easy = by_arm(rows('results_final_hard')), by_arm(rows('results_final_easier'))
    dg, dge = by_arm(rows('results_final_hard_datagiven')), by_arm(rows('results_final_easier_datagiven'))
    out = {'table1': {}, 'table2': {}, 'n': {}, 'unscored': {}}
    for arm, _ in NAMES + [('Ours-oracle', 'Ours + given method')]:
        for grp, d in (('hard', hard), ('easier', easy)):
            rs = d.get(arm, [])
            out['table1'].setdefault(arm, {})[grp] = round(mean([score(r) for r in rs]), 1)
            out['n'].setdefault(arm, {})[grp] = len(rs)
            out['unscored'].setdefault(arm, {})[grp] = sum(1 for r in rs if r.get('score_v2') is None)
    t = out['table1']
    out['table2'] = {}
    for grp, d, g in (('hard', hard, dg), ('easier', easy, dge)):
        out['table2'][grp] = {'method found, data found': t['Ours-cards2'][grp], 'method given, data found': t['Ours-oracle'][grp],
                              'method found, data given': round(mean([score(r) for r in g['Ours-cards2']]), 1),
                              'method given, data given': round(mean([score(r) for r in g['Ours-oracle']]), 1)}
    lines = ['**Table 6: the ladder** (mean score_v2, 0-100; failed or unfinished answers count as 0)', '',
             '| Paper name | Arm | Institutional procedures (231) | Standard formulas (209) |', '|---|---|---|---|']
    for arm, nm in NAMES:
        lines.append('| %s | `%s` | %.1f | %.1f |' % (nm, arm, t[arm]['hard'], t[arm]['easier']))
    for grp, nq, gname in (('hard', 231, 'Institutional procedures'), ('easier', 209, 'Standard formulas')):
        t2 = out['table2'][grp]
        lines += ['', '**Table 7: oracle analysis** (ours only, %s, %d questions)' % (gname, nq), '', '| | method found | method given |', '|---|---|---|',
                  '| data found | %.1f | %.1f |' % (t2['method found, data found'], t2['method given, data found']),
                  '| data given | %.1f | %.1f |' % (t2['method found, data given'], t2['method given, data given'])]
    lines += ['', 'Answers without a score (counted as 0): ' + ', '.join('%s %d/%d' % (k, v['hard'], v['easier']) for k, v in out['unscored'].items()) + ' (institutional procedures / standard formulas).']
    print('\n'.join(lines))
    if a.check:
        bad = []
        for grp, d in (('hard', hard), ('easier', easy), ('hard_datagiven', dg), ('easier_datagiven', dge)):
            for arm, rs in d.items():
                for r in rs:
                    re_ = recomputed(r)
                    if r.get('score_v2') is not None and re_ is not None and abs(re_ - r['score_v2']) > 0.11:
                        bad.append((grp, arm, r['item'], r['score_v2'], re_))
        print('\nscore_v2 recomputed from parts_v2: %d row(s) differ' % len(bad))
        for b in bad:
            print('  ', b)
    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
        json.dump(out, open(a.json, 'w'), indent=1)


if __name__ == '__main__':
    main()
