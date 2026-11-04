"""Compare published debt-creating-flows tables (corpus) with the decomposition recomputed from frozen WEO Oct 2025.
Writes frozen_extra/debt_path_tables/comparison.json (one record per table-year with all of: published and recomputed)."""
import json, re, sys, os
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import debt_path_lib as L
idx = {d['id']: d for d in json.load(open(ROOT + "/../../../release/official_benchmark/reference_data/corpus_index.json"))}
P = json.load(open(ROOT + "/frozen_extra/debt_path_tables/parsed.json"))
def pick(rows, pred):
    for k, v in rows.items():
        if pred(k): return v
def rep_year(title):
    m = re.search(r'(20\d\d|19\d\d)', title); return int(m.group(1)) if m else None
out = []
for t in P:
    if t['doc'] not in idx: continue
    meta = idx[t['doc']]['meta']; iso = meta.get('country_code')
    if not iso: continue
    R = t['rows']
    ch = pick(R, lambda k: k in ('change in gross public sector debt', 'change in public sector debt'))
    pdf = pick(R, lambda k: k.startswith('primary deficit'))
    ri = pick(R, lambda k: k.endswith('real interest rate') and 'exchange' not in k)
    gr = pick(R, lambda k: k.endswith('real gdp growth') and 'percent' not in k)
    fx = pick(R, lambda k: 'exchange rate depreciation' in k)
    ad = pick(R, lambda k: k in ('automatic debt dynamics', 'contribution from interest rate growth differential', 'interest rate growth differential'))
    res = pick(R, lambda k: k.startswith('residual'))
    if not (ch and pdf and ri and gr): continue
    ry = meta.get('year') or rep_year(t['title'])
    for y in t['years']:
        ys = str(y)
        if ch.get(ys) is None or pdf.get(ys) is None or ri.get(ys) is None or gr.get(ys) is None: continue
        d = L.decomp(iso, y)
        if not d: continue
        out.append(dict(doc=t['doc'], seq=t['seq'], title=t['title'], iso=iso, rep_year=ry, year=y,
            pub=dict(change=ch[ys], pd=pdf[ys], ri=ri[ys], gr=gr[ys], fx=(fx or {}).get(ys), auto=(ad or {}).get(ys), res=(res or {}).get(ys)),
            rec={k: round(v, 3) for k, v in d.items()}))
json.dump(out, open(ROOT + "/frozen_extra/debt_path_tables/comparison.json", 'w'))
print(len(out), len(set(o['doc'] for o in out)))
