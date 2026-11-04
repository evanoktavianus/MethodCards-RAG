"""Gold + item generator for growth/labour cluster. python3 -I; reads ONLY frozen_extra/*.csv. Writes items/<slug>/<ID>.json."""
import csv, json, math, random, os
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(H, '..', '..')
def L(f):
    d = {}
    for r in csv.DictReader(open(f'{R}/frozen_extra/weo_oct2025_{f}.csv')):
        d[r['iso3']] = {int(k): float(v) for k, v in r.items() if k.isdigit() and v != ''}
    return d
LE, LP, Y, NID, GAP, LUR = (L(x) for x in ['le', 'lp', 'ngdp_r', 'nid_ngdp', 'ngap_npgdp', 'lur'])
NAMES = {'AUS':'Australia','AUT':'Austria','BEL':'Belgium','CAN':'Canada','CYP':'Cyprus','DEU':'Germany','DNK':'Denmark','ESP':'Spain','EST':'Estonia','FIN':'Finland','FRA':'France','GBR':'the United Kingdom','GRC':'Greece','IRL':'Ireland','ITA':'Italy','JPN':'Japan','KOR':'Korea','LUX':'Luxembourg','MLT':'Malta','NLD':'the Netherlands','NOR':'Norway','NZL':'New Zealand','PRT':'Portugal','SVK':'the Slovak Republic','SVN':'Slovenia','SWE':'Sweden','USA':'the United States','CHE':'Switzerland','ISR':'Israel','ISL':'Iceland','LTU':'Lithuania','LVA':'Latvia','HRV':'Croatia','CZE':'Czechia'}
A, DELTA = 0.33, 0.10   # Mexico 2004 Art IV (270b189d) growth accounting box: capital share 33%, depreciation 10%
OKUN = -0.5             # WEO Oct 2012 Box 4.1 (bc66194c): 1% output gap -> -1/2 pp cyclical unemployment
def okun_cyc(c, y): return OKUN * GAP[c][y]             # u - u* = a*(y-y*), a=-0.5
def okun_nat(c, y): return LUR[c][y] - okun_cyc(c, y)   # u* = u - (u-u*)
def capital(c):
    ys = sorted(k for k in Y[c] if k in NID[c] and k <= 2024)
    inv = {t: NID[c][t] / 100 * Y[c][t] for t in ys}
    t0 = ys[0]; g = (math.log(Y[c][t0 + 9]) - math.log(Y[c][t0])) / 9
    K = {t0: inv[t0] / (DELTA + g)}
    for t in ys[1:]: K[t] = (1 - DELTA) * K[t - 1] + inv[t]
    return K
def ga(c, t0, t1):
    K = capital(c); n = t1 - t0
    gy = (math.log(Y[c][t1]) - math.log(Y[c][t0])) / n * 100
    gk = (math.log(K[t1]) - math.log(K[t0])) / n * 100
    gl = (math.log(LE[c][t1]) - math.log(LE[c][t0])) / n * 100
    return dict(gy=gy, kcon=A * gk, lcon=(1 - A) * gl, tfp=gy - A * gk - (1 - A) * gl)
def pc(c, t0, t1):
    n = t1 - t0; f = lambda a, b: (math.log(a / b))
    pcg = (f(Y[c][t1] / LP[c][t1], 1) - f(Y[c][t0] / LP[c][t0], 1)) / n * 100
    prod = (f(Y[c][t1] / LE[c][t1], 1) - f(Y[c][t0] / LE[c][t0], 1)) / n * 100
    emp = (f(LE[c][t1] / LP[c][t1], 1) - f(LE[c][t0] / LP[c][t0], 1)) / n * 100
    assert abs(pcg - prod - emp) < 1e-9
    return dict(pcg=pcg, prod=prod, emp=emp)
def popg(c, t0, t1): return (math.log(LP[c][t1]) - math.log(LP[c][t0])) / (t1 - t0) * 100
def uniq_thr(vals, top=True):
    """vals: {c:v}. threshold with exactly one country above (top) or below."""
    s = sorted(vals.items(), key=lambda kv: kv[1], reverse=top)
    (c1, v1), (c2, v2) = s[0], s[1]
    if abs(v1 - v2) < 0.05: return None
    thr = round((v1 + v2) / 2, 1)
    ok = [c for c, v in vals.items() if (v > thr if top else v < thr)]
    return (thr, ok[0]) if ok == [c1] else None
rnd = random.Random(20261030)
def common(i, slug, pat, style, query, text0, acc0, comp, inputs, method, docs, pub, rec, tol, dist, famous, pred=None, hs=None, src=''):
    return {"id": i, "family": "methodology", "pattern": pat, "tier": "analytical", "status": "validated", "query": query,
      "claims": {"text": [{"id": "c0", "kind": "text", "importance": "vital", "text": text0, "accept": acc0}],
        "data": [{"id": "c5", "kind": "data", "importance": "okay", "text": "Uses WEO series: " + ", ".join(inputs) + "."}],
        "computation": comp},
      "grading": {"method": "answer_recall"},
      "provenance": {"assembled_from": [src, "frozen WEO Oct 2025 (frozen_extra)"], "gold_script": "gold_scripts/growth_labour/gold_growth_labour.py", "selection": "seeded draw (20261030), distinct country within style where possible"},
      "method": method, "method_doc_ids": docs, "gold_report_ids": [],
      "gold_report_note": "No corpus report states these values; gold is recomputed from the frozen WEO vintage by formula (formula-validated, no published figure).",
      "published_value": pub, "recomputed_value": rec, "tolerance": tol, "inputs": inputs, "style": style, "distractors": dist,
      "famous_method": famous, "hidden_set_size": 1 if style == 'hidden' else None, "predicate": pred,
      "validation_label": "formula-validated", "method_class": hs}
def claimcheck_values(truth, v, tol):
    return (round(v, 1) if truth else round(v + rnd.choice([-1, 1]) * max(4 * tol, 0.6) , 1))
items = []
# ---------- OKUN ----------
OK_DOC = ["bc66194c-3b20-4007-95c3-b28b252fc286"]
OKD = ["potential-output estimation by HP filter alone", "Phillips-curve / wage-inflation slack measure", "fiscal cyclical adjustment (budget semi-elasticity)", "unemployment-rate forecasting by autoregression"]
okc = sorted(c for c in GAP if c in LUR)
def ok_item(n, style, c, y, kind, **kw):
    cyc = okun_cyc(c, y); nat = okun_nat(c, y)
    name = NAMES[c]
    if kind == 'cyc': tgt, unit, what = cyc, 'pp of labour force', 'cyclical unemployment'
    else: tgt, unit, what = nat, '% of labour force', 'implied natural (structural) unemployment rate'
    return tgt, unit, what, name
used = set(); k = 0
def mk_okun():
    global k
    n = 0
    def nid(): 
        nonlocal n; n += 1; return f"OK-{n:02d}"
    cands = [(c, y) for c in okc for y in (2009, 2010, 2012, 2013, 2015, 2020, 2021) if y in GAP[c] and y in LUR[c] and abs(GAP[c][y]) >= 1.5]
    rnd.shuffle(cands); pick = []; seenc = set()
    for c, y in cands:
        if c not in seenc: pick.append((c, y)); seenc.add(c)
    # named
    for j, (c, y) in enumerate(pick[:5]):
        kind = 'cyc' if j % 2 == 0 else 'nat'
        tgt, unit, what, name = ok_item(0, 'named', c, y, kind)
        if kind == 'cyc': q = f"In {y}, how many percentage points of {name}'s unemployment rate were due to weak (or overheated) demand rather than structural causes? Give a signed number, positive if unemployment was above its sustainable level."
        else: q = f"What unemployment rate would {name} have had in {y} if the economy had been running at its normal capacity?"
        items.append(common(nid(), 'okun', 'M-named', 'named', q,
          "Identifies the relationship between the output gap and the deviation of unemployment from its natural rate (Okun's law, coefficient about -1/2).",
          "full = names Okun's law / output-gap-to-unemployment-gap link with coefficient near 0.5 (0.4-0.6 acceptable); no = simple regression of unemployment on growth without the gap",
          [{"id": "c1", "kind": "computation", "importance": "vital", "text": f"{what} {c} {y} = {tgt:.2f} {unit}", "reference_value": round(tgt, 3), "tolerance": 0.15, "unit": "pp", "accept": "full = within tolerance; output gap from WEO NGAP_NPGDP, coefficient -0.5 on (y - y*), natural rate = actual unemployment minus cyclical part"}],
          ["NGAP_NPGDP", "LUR"], 'okun_gap_cyclical_unemployment', OK_DOC, None, round(tgt, 3), 0.15, OKD, False,
          hs='institutional procedure', src="WEO Oct 2012 Box 4.1 (bc66194c, blocks 1880 and 1882-1884)"))
    # hidden
    hid = 0
    for y in (2009, 2010, 2012, 2013, 2020, 2021, 2015, 2011, 2014):
        if hid >= 5: break
        vals = {c: LUR[c][y] for c in okc if y in LUR[c] and y in GAP[c]}
        r = uniq_thr(vals, top=True)
        if not r: continue
        thr, c = r
        if abs(GAP[c][y]) < 0.5: continue
        ncountries = len(vals)
        tgt = okun_cyc(c, y)
        pred = f"among the {ncountries} economies with a published WEO output gap, unemployment rate (LUR) > {thr} in {y}"
        q = f"In {y}, among advanced economies, exactly one had an unemployment rate above {thr}% (among the group with an official output-gap estimate). How much of that economy's unemployment rate was cyclical, in percentage points, signed (positive if above the sustainable level)?"
        items.append(common(nid(), 'okun', 'M-hidden', 'hidden', q,
          "Identifies the relationship between the output gap and the deviation of unemployment from its natural rate (Okun's law, coefficient about -1/2).",
          "full = names Okun's law / output-gap-to-unemployment-gap link with coefficient near 0.5; no = simple regression only",
          [{"id": "c1", "kind": "computation", "importance": "vital", "text": f"Cyclical unemployment of the identified economy ({c}) in {y} = {tgt:.2f} pp", "reference_value": round(tgt, 3), "tolerance": 0.15, "unit": "pp", "accept": "full = within tolerance; correct country identification required (hidden)"}],
          ["LUR", "NGAP_NPGDP"], 'okun_gap_cyclical_unemployment', OK_DOC, None, round(tgt, 3), 0.15, OKD, False, pred=pred,
          hs='institutional procedure', src="WEO Oct 2012 Box 4.1 (bc66194c)"))
        items[-1]['hidden_answer_country'] = c; hid += 1
    # claim check
    cc = [p for p in pick[5:] if p][:4]
    for j, (c, y) in enumerate(cc):
        truth = j % 2 == 0; v = okun_cyc(c, y); shown = claimcheck_values(truth, v, 0.15)
        q = f"A staff note says that in {y}, about {shown:+.1f} percentage points of {NAMES[c]}'s unemployment rate was cyclical (positive meaning above the sustainable rate). Is that statement accurate?"
        items.append(common(nid(), 'okun', 'M-claim', 'claim_check', q,
          "Identifies the relationship between the output gap and the deviation of unemployment from its natural rate (Okun's law, coefficient about -1/2) and uses it to judge the statement.",
          "full = Okun-gap approach with output gap and coefficient near 0.5",
          [{"id": "c1", "kind": "computation", "importance": "vital", "text": f"Recomputed cyclical unemployment {c} {y} = {v:.2f} pp", "reference_value": round(v, 3), "tolerance": 0.15, "unit": "pp", "accept": "full = within tolerance"},
           {"id": "c2", "kind": "text", "importance": "vital", "text": f"Verdict: statement is {'TRUE' if truth else 'FALSE'} (stated {shown:+.1f} vs recomputed {v:+.2f}; threshold 0.5 pp)", "accept": "full = correct verdict"}],
          ["NGAP_NPGDP", "LUR"], 'okun_gap_cyclical_unemployment', OK_DOC, shown, round(v, 3), 0.15, OKD, False,
          hs='institutional procedure', src="WEO Oct 2012 Box 4.1 (bc66194c)"))
        items[-1]['claim_truth'] = truth
        assert (abs(shown - v) <= 0.5) == truth
# ---------- GROWTH ACCOUNTING / DECOMP ----------
GA_DOC = ["270b189d-9e67-4642-8c7d-bd1d160c5e14", "3ed94aa0-95d3-4293-bbff-32bf7d10acd8"]
GAD = ["labour-productivity or per-capita income decomposition (employment rate)", "potential-output estimation by filter", "convergence (beta) regression", "investment-rate / saving-gap analysis"]
PC_DOC = ["a507cd39-1045-434b-96b9-38bb047b94a9"]
PCD = ["Cobb-Douglas growth accounting with capital and TFP", "dependency-ratio / demographic dividend", "fiscal sustainability", "unemployment gap analysis"]
WINS = [(2000, 2008), (2005, 2019), (2010, 2019), (2012, 2019), (2015, 2024), (2010, 2024), (2005, 2015), (2012, 2023)]
lec = sorted(c for c in LE if c in Y and c in NID and c in LP and 2000 in LE[c] and 2024 in LE[c] and 1980 in NID[c] and 2024 in Y[c] and c in NAMES)
def mk_gen(slug, pre, fn, docs, dist, famous, hs, method, qgen, text0, acc0, tgtkey, tol, inputs, unit, src, valid):
    n = 0
    def nid():
        nonlocal n; n += 1; return f"{pre}-{n:02d}"
    pool = [(c, w) for c in lec for w in WINS if all(t in LE[c] and t in Y[c] and t in LP[c] for t in w)]
    rnd.shuffle(pool); seen = set(); pick = []
    for c, w in pool:
        if c not in seen: pick.append((c, w)); seen.add(c)
    for c, w in pick[:5]:
        v = fn(c, *w)[tgtkey]
        items.append(common(nid(), slug, 'M-named', 'named', qgen(NAMES[c], w), text0, acc0,
          [{"id": "c1", "kind": "computation", "importance": "vital", "text": f"{c} {w[0]}-{w[1]}: {tgtkey} = {v:.2f} pp per year", "reference_value": round(v, 3), "tolerance": tol, "unit": unit, "accept": valid}],
          inputs, method, docs, None, round(v, 3), tol, dist, famous, hs=hs, src=src))
    hid = 0
    for w in WINS:
        if hid >= 5: break
        vals = {c: popg(c, *w) for c in lec if all(t in LE[c] and t in Y[c] and t in LP[c] for t in w)}
        if slug == 'growth_accounting':
            vals = {c: (math.log(Y[c][w[1]]) - math.log(Y[c][w[0]])) / (w[1] - w[0]) * 100 for c in vals}
            pname = 'average real GDP growth (NGDP_R)'
        else: pname = 'average population growth (LP)'
        r = uniq_thr(vals, top=True)
        if not r: continue
        thr, c = r
        v = fn(c, *w)[tgtkey]
        pred = f"among the {len(vals)} economies with WEO employment data, {pname} > {thr}% per year over {w[0]}-{w[1]}"
        what = 'real output growth' if slug == 'growth_accounting' else 'population growth'
        q = f"Over {w[0]}-{w[1]}, exactly one economy in the group of advanced economies reporting employment data had {what} above {thr}% a year. {qgen('that economy', w, hidden=True)}"
        items.append(common(nid(), slug, 'M-hidden', 'hidden', q, text0, acc0,
          [{"id": "c1", "kind": "computation", "importance": "vital", "text": f"{c} {w[0]}-{w[1]}: {tgtkey} = {v:.2f} pp per year", "reference_value": round(v, 3), "tolerance": tol, "unit": unit, "accept": valid + "; correct country identification required (hidden)"}],
          inputs, method, docs, None, round(v, 3), tol, dist, famous, pred=pred, hs=hs, src=src))
        items[-1]['hidden_answer_country'] = c; hid += 1
    for j, (c, w) in enumerate(pick[5:9]):
        truth = j % 2 == 0; v = fn(c, *w)[tgtkey]; shown = claimcheck_values(truth, v, tol)
        q = f"A country note says that over {w[0]}-{w[1]}, {qgen(NAMES[c], w, claim=shown)} Is that accurate?"
        items.append(common(nid(), slug, 'M-claim', 'claim_check', q, text0, acc0,
          [{"id": "c1", "kind": "computation", "importance": "vital", "text": f"Recomputed {c} {w[0]}-{w[1]}: {tgtkey} = {v:.2f} pp per year", "reference_value": round(v, 3), "tolerance": tol, "unit": unit, "accept": valid},
           {"id": "c2", "kind": "text", "importance": "vital", "text": f"Verdict: statement is {'TRUE' if truth else 'FALSE'} (stated {shown:+.1f} vs recomputed {v:+.2f}; threshold 0.5 pp)", "accept": "full = correct verdict"}],
          inputs, method, docs, shown, round(v, 3), tol, dist, famous, hs=hs, src=src))
        items[-1]['claim_truth'] = truth
        assert (abs(shown - v) <= 0.5) == truth
mk_okun()
def qga(name, w, hidden=False, claim=None):
    if claim is not None: return f"output growth that is not accounted for by more capital or more workers contributed about {claim:+.1f} percentage points a year in {name}."
    return f"On average per year, how many percentage points of {name}'s growth came from improvements in efficiency, once the contributions of the capital stock and of employment are set aside?" if not hidden else "On average per year, how many percentage points of that economy's growth came from improvements in efficiency, once the contributions of the capital stock and of employment are set aside?"
mk_gen('growth_accounting', 'GA', ga, GA_DOC, GAD, False, 'institutional procedure', 'growth_accounting_tfp_residual', qga,
  "Identifies growth accounting with a Cobb-Douglas production function (capital stock from investment by perpetual inventory, employment, TFP as residual).",
  "full = Cobb-Douglas growth accounting with TFP residual; capital share 0.33 and depreciation 10% (Mexico 2004 Art. IV convention) or close alternative acceptable (capital share 0.3-0.4)",
  'tfp', 0.4, ["NGDP_R", "NID_NGDP", "LE"], 'pp',
  "Mexico 2004 Art IV growth-accounting box (270b189d, block 125) and WEO Apr 2015 Ch.3 (3ed94aa0, blocks 1055-1059)",
  "full = within tolerance; capital stock by perpetual inventory (delta 10%, K_1980=I_1980/(delta+g)), capital share 0.33, TFP = gY - a*gK - (1-a)*gL")
def qpc(name, w, hidden=False, claim=None):
    if claim is not None: return f"rising (or falling) employment relative to population added about {claim:+.1f} percentage points a year to growth in income per person in {name}."
    return f"On average per year, how many percentage points of {name}'s growth in real income per person came from changes in the share of the population in work, as opposed to output per worker?" if not hidden else "On average per year, how many percentage points of that economy's growth in real income per person came from changes in the share of the population in work, as opposed to output per worker?"
mk_gen('pc_decomp', 'PC', pc, PC_DOC, PCD, True, 'textbook identity', 'gdp_per_capita_growth_decomposition', qpc,
  "Identifies the decomposition of GDP-per-capita growth into labour productivity (GDP per worker) and the employment rate (employment per capita).",
  "full = log-difference decomposition into productivity and employment-to-population (working-age share lumped in employment rate acceptable)",
  'emp', 0.15, ["NGDP_R", "LE", "LP"], 'pp',
  "San Marino 2023 Art IV (a507cd39, blocks 568-570), after Jaumotte et al. 2016",
  "full = within tolerance; employment-rate contribution = annualised dln(LE/LP)")
for it in items:
    slug = {'OK': 'okun', 'GA': 'growth_accounting', 'PC': 'pc_decomp'}[it['id'][:2]]
    json.dump(it, open(f"{R}/items/{slug}/{it['id']}.json", 'w'), indent=1)
from collections import Counter
print(Counter((i['id'][:2], i['style']) for i in items))
