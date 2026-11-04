"""Faithfulness check of the formula on each report's OWN published inputs (same table: debt, real growth, deflator inflation, effective interest rate).
Published real-interest contribution should equal (i - pi(1+g))/(1+g+pi+g*pi)*d_{t-1}; real-growth contribution -g/(1+g+pi+g*pi)*d_{t-1}.
Writes frozen_extra/debt_path_tables/own_inputs_check.json and prints a summary. Tolerance 0.15 pp (reports round every input to 0.1)."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
P = json.load(open(ROOT + "/frozen_extra/debt_path_tables/parsed.json"))
def find(t, s):
    for k, v in t['rows'].items():
        if k.startswith(s): return v
res = []
for t in P:
    D = find(t, 'nominal gross public debt') or find(t, 'gross nominal public debt'); g = find(t, 'real gdp growth in percent'); p = find(t, 'inflation gdp deflator'); i = find(t, 'effective interest rate')
    ri = find(t, 'of which real interest rate'); gr = find(t, 'of which real gdp growth'); pdf = find(t, 'primary deficit'); ch = find(t, 'change in gross public sector debt') or find(t, 'change in public sector debt')
    if not all([D, g, p, i, ri, gr]): continue
    for y in t['years']:
        a = str(y); b = str(y-1)
        vals = [D.get(b), g.get(a), p.get(a), i.get(a), ri.get(a), gr.get(a)]
        if any(v is None for v in vals): continue
        d1, G, Pi, I, RI, GR = vals
        G, Pi, I = G/100, Pi/100, I/100
        den = 1 + G + Pi + G*Pi
        cri = (I - Pi*(1+G))/den*d1; cgr = -G/den*d1
        res.append(dict(doc=t['doc'], title=t['title'], year=y, d_prev=d1, pub_ri=RI, calc_ri=round(cri, 3), pub_gr=GR, calc_gr=round(cgr, 3),
                        ok=abs(cri-RI) <= .15 and abs(cgr-GR) <= .15))
json.dump(res, open(ROOT + "/frozen_extra/debt_path_tables/own_inputs_check.json", 'w'))
n = len(res); k = sum(r['ok'] for r in res)
print("own-input checks:", n, "match within 0.15pp:", k, "docs:", len(set(r['doc'] for r in res)), "docs with all years matching:", len({d for d in {r['doc'] for r in res} if all(r['ok'] for r in res if r['doc'] == d)}))
