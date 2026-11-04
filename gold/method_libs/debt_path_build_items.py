"""Builds items/debt_path/DPATH-xx.json from the frozen data (gold), the validation comparison (published values, gold report ids) and the hidden-subject search.
Run:  python3 -I scripts/debt_path_build_items.py   (regenerates all golds and item files)"""
import json, os, sys, math, itertools
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import debt_path_lib as L
OUT = ROOT + "/items/debt_path"; os.makedirs(OUT, exist_ok=True)
idx = {d['id']: d for d in json.load(open(ROOT + "/../../../release/official_benchmark/reference_data/corpus_index.json"))}
NAMES = {}
for d in idx.values():
    c = d['meta'].get('country_code')
    if c and d['meta'].get('country'): NAMES[c] = d['meta']['country']
NAMES.update(dict(SVK='Slovakia', MKD='North Macedonia', BIH='Bosnia and Herzegovina', COM='Comoros', MNE='Montenegro'))
CMP = json.load(open(ROOT + "/frozen_extra/debt_path_tables/comparison.json"))
TOL = 0.3   # percentage points of GDP (abs); published tables round to 0.1 and use an older WEO vintage
METHOD_DOCS = ["55319ff9-c45c-4e8d-99e4-5562a1158bf2", "2dea3fb1-758b-40a4-882b-59f953293e2d", "c010cde9-5069-43d5-a0a6-d162270835fd"]
DIST = ["Debt-stabilising primary balance / required fiscal adjustment (answers a different question: what balance holds the ratio constant)",
        "Fiscal-impulse or change in the cyclically adjusted primary balance (measures policy stance, not debt-ratio attribution)",
        "Naive attribution that divides the change in debt by the deficit (ignores interest-growth interaction and the previous-year debt stock)",
        "Gross financing needs projection (liquidity measure, includes amortisation)",
        "Using the overall deficit as the 'fiscal' term and then also adding interest, which double counts the interest bill"]
def sgn(x): return "%+.1f" % x
def A_vals(d):  # IMF MAC style
    return dict(pd=d['primary_deficit'], ri=d['real_interest_imf'], gr=d['growth_imf'], rest=d['change'] - d['primary_deficit'] - d['auto_imf'])
def B_vals(d):  # Escolano eq 26 style
    return dict(pd=d['primary_deficit'], ni=d['interest_total'], inf=d['inflation'], gr=d['growth'], rest=d['residual'])
LAB = dict(pd="primary deficit (positive = adds to debt)", ri="real-interest-rate effect on last year's debt stock", gr="real GDP growth effect", rest="remainder (change not explained by those three; includes exchange-rate and other flows)",
           ni="nominal interest bill (interest paid divided by last year's GDP-adjusted debt)", inf="GDP-deflator inflation effect")
def published(iso, y):
    m = [o for o in CMP if o['iso'] == iso and o['year'] == y and o['rep_year'] and y <= o['rep_year'] - 1]
    m = [o for o in m if abs(o['pub']['change'] - o['rec']['change']) <= TOL and abs(o['pub']['pd'] - o['rec']['primary_deficit']) <= TOL and abs(o['pub']['ri'] - o['rec']['real_interest_imf']) <= TOL and abs(o['pub']['gr'] - o['rec']['growth_imf']) <= TOL]
    return m
# ---------------- hidden-subject search ----------------
def feats(iso, y):
    d = L.decomp(iso, y)
    if not d: return None
    return dict(d1=d['d_prev'], g=d['g'], pi=d['defl'], pb=-d['primary_deficit'])
UNI = sorted(L.S['ggxwdg_ngdp'])
def hidden_condition(iso, y):
    F = {c: feats(c, y) for c in UNI}; F = {c: f for c, f in F.items() if f}
    t = F[iso]
    lab = dict(d1="general government gross debt at the end of %d, %% of GDP" % (y-1), g="real GDP growth in %d, %%" % y,
               pi="GDP-deflator inflation in %d, %%" % y, pb="general government primary balance in %d, %% of GDP (negative = deficit)" % y)
    W = dict(d1=[15, 10, 6, 4, 2], g=[2, 1, 0.6, 0.3], pi=[3, 1.5, 1, 0.6, 0.3], pb=[3, 1.5, 1, 0.6, 0.3])
    best = None
    for n in (2, 3, 4):
        for ks in itertools.combinations(['d1', 'g', 'pi', 'pb'], n):
            for ws in itertools.product(*[W[k] for k in ks]):
                iv = {}
                for k, w in zip(ks, ws):
                    dec = 0 if k == 'd1' else 1
                    iv[k] = (round(t[k]-w, dec), round(t[k]+w, dec))
                hit = [c for c, f in F.items() if all(iv[k][0] <= f[k] <= iv[k][1] for k in ks)]
                if hit == [iso]:
                    score = sum(w / W[k][0] for k, w in zip(ks, ws))
                    if best is None or score > best[0]: best = (score, ks, iv)
        if best: break
    if not best: return None
    _, ks, iv = best
    return "; ".join("%s between %g and %g" % (lab[k], iv[k][0], iv[k][1]) for k in ks), [iso], {k: iv[k] for k in ks}
# ---------------- item definitions ----------------
NAMED = [("POL", 2019, "A"), ("IDN", 2020, "A"), ("MEX", 2013, "B"), ("SVK", 2018, "A"), ("HUN", 2019, "B"), ("SLV", 2016, "A"), ("MNE", 2012, "A")]
HIDDEN = [("GEO", 2020, "A"), ("PER", 2015, "A"), ("SRB", 2018, "A"), ("CZE", 2012, "B"), ("BIH", 2014, "A"), ("MKD", 2018, "B"), ("SVK", 2013, "A")]
# claim checks: (iso, year, quantity key in A/B dict, set, stated value or None for derived statement)
CLAIMS = [("DEU", 2019, "A", "gr", -0.6), ("ROU", 2015, "A", "ri", 1.4), ("GTM", 2010, "A", "pd", 1.8), ("LTU", 2008, "B", "inf", -0.4), ("COM", 2020, "A", "pd", 2.9), ("SLV", 2018, "A", "ri", 2.3)]
def window(kind):
    return {"A": ("primary deficit, the real-interest-rate cost of servicing the previous year's debt stock, and the drag or boost from real GDP growth",
                  "pd", "ri", "gr"),
            "B": ("primary deficit, the nominal interest bill, the effect of GDP-deflator inflation and the effect of real GDP growth", "pd", "ni", "inf", "gr")}[kind]
def make_claims(kind, vals, iso, y, hidden=False):
    nm = NAMES[iso]
    text = [dict(id="c1", kind="text", importance="vital",
                 text="Identifies that the change in the public debt ratio is attributed to its components by applying the debt-accumulation identity to the previous-year debt stock: primary deficit, an interest-rate term, a growth term (and, in the other published variant, a separate inflation term), as set out in Escolano (2010) 'A Practical Guide to Public Debt Dynamics...' (equations 24-28) and in the IMF (2013) Staff Guidance Note / MAC SRDSF (2021) debt-dynamics annex ('contribution from real interest rate', 'contribution from real GDP growth').",
                 accept="full = names the debt-dynamics decomposition (any of Escolano 2010, IMF 2013 Staff Guidance Note Annex I, MAC SRDSF 2021, or the IMF Public Debt Dynamics Tool) and applies it with the previous-year debt ratio; partial = describes an interest-growth-primary-balance attribution without a source; no = uses a stabilising-balance calculation or a naive deficit/interest split.")]
    comp = []
    keys = {"A": [("pd", True), ("ri", True), ("gr", True), ("rest", False)], "B": [("pd", True), ("ni", True), ("inf", True), ("gr", True), ("rest", False)]}[kind]
    for i, (k, vital) in enumerate(keys, start=2):
        comp.append(dict(id="c%d" % i, kind="computation", importance="vital" if vital else "okay",
                         text="%s: %s percentage points of GDP in %d (%s)." % (NAMES[iso], sgn(vals[k]), y, LAB[k]),
                         accept="full = within %.1f percentage points of %s; partial = correct sign and within 1.0 pp; no = otherwise. Equivalent published variants (IMF real-interest/real-growth vs Escolano nominal split) are accepted only for the pieces the question names." % (TOL, sgn(vals[k])),
                         target=round(vals[k], 3), tolerance_abs=TOL))
    top = max([k for k, _ in keys if k != 'rest'], key=lambda k: abs(vals[k]))
    ans = dict(id="c%d" % (len(comp) + 2), kind="text", importance="vital",
               text="Names the %s as the largest of the named contributions in %d (%s percentage points)." % (LAB[top].split(' (')[0], y, sgn(vals[top])),
               accept="full = identifies it as the dominant named driver with the sign (adds to / reduces debt) stated correctly; partial = right driver without sign or magnitude; no = otherwise.")
    data = [dict(id="c%d" % (len(comp) + 3), kind="data", importance="okay",
                 text="Uses general government gross debt (% of GDP), primary balance, interest paid (primary balance minus overall balance), nominal and real GDP (WEO), i.e. IMF WEO GGXWDG_NGDP, GGXONLB_NGDP, GGXCNL_NGDP, NGDP, NGDP_R.",
                 accept="full = debt, primary balance, interest or overall balance, and nominal/real GDP or growth+deflator all used; partial = most of them; no = other.")]
    return dict(text=text + [ans], data=data, computation=comp), top
def base(id, style, iso, y, kind, query, claims, extra=None):
    d = L.decomp(iso, y)
    pub = published(iso, y)
    it = dict(id=id, family="methodology", method="debt_path", style=style, tier="analytical", status="validated", query=query, claims=claims,
              grading=dict(computation_tolerance_abs_pp=TOL, note="Contributions are in percentage points of GDP in the target year; published tables round to 0.1 and use older WEO vintages, so 0.3 pp absolute. Gold from frozen WEO Oct 2025."),
              provenance=dict(generator="scripts/debt_path_build_items.py", frozen_data="frozen_extra/weo_oct2025_*.csv (WEO Oct 2025 vintage)", method_text="Escolano 2010 eqs 24-28 (decomposition of changes in the debt ratio); IMF 2013 Staff Guidance Note Fig. 1 footnotes 4-5 and Annex I", subject=dict(iso3=iso, country=NAMES[iso], year=y)),
              method_doc_ids=METHOD_DOCS,
              gold_report_ids=sorted({o['doc'] for o in pub}),
              published_value=[dict(doc=o['doc'], title=o['title'], table_block_sequence=o['seq'], primary_deficit=o['pub']['pd'], real_interest=o['pub']['ri'], real_growth=o['pub']['gr'], change_in_debt=o['pub']['change']) for o in pub],
              recomputed_value={k: round(d[k], 3) for k in ('change', 'primary_deficit', 'real_interest_imf', 'growth_imf', 'interest_total', 'inflation', 'growth', 'residual', 'auto_imf', 'eff_rate', 'defl', 'g', 'd_prev', 'd')},
              inputs=["GGXWDG_NGDP", "GGXONLB_NGDP", "GGXCNL_NGDP", "NGDP", "NGDP_R"], distractors=DIST, famous_method=False,
              gold_script="scripts/debt_path_build_items.py", validation=dict(published_instances_matching=len(pub), tolerance_abs_pp=TOL,
                    note="Every reported report table in gold_report_ids matches the recomputation on change in debt, primary deficit, real-interest and real-growth contributions within tolerance"))
    if extra: it.update(extra)
    return it
items = []; n = 0
def nid(): 
    global n; n += 1; return "DPATH-%02d" % n
def ask(kind, nm, y, who):
    if kind == "A":
        return ("%s: how much of the %d change in the general government gross debt ratio is attributable to each of the primary deficit, the real interest rate paid on last year's debt and real GDP growth? "
                "Give each contribution in percentage points of GDP and say which one mattered most.") % (who, y)
    return ("%s: split the %d change in the general government gross debt ratio into the primary deficit, the nominal interest bill, the effect of GDP-deflator inflation and the effect of real GDP growth, "
            "each in percentage points of GDP, and say which of these four moved the ratio most.") % (who, y)
for iso, y, k in NAMED:
    d = L.decomp(iso, y); vals = A_vals(d) if k == "A" else B_vals(d)
    cl, top = make_claims(k, vals, iso, y)
    q = ask(k, NAMES[iso], y, "For %s" % NAMES[iso])
    items.append(base(nid(), "named", iso, y, k, q, cl, dict(decomposition_variant={"A": "IMF real-interest / real-growth contributions", "B": "Escolano eq. 26 nominal interest / inflation / growth split"}[k], dominant_driver=top)))
hid_report = []
for iso, y, k in HIDDEN:
    d = L.decomp(iso, y); vals = A_vals(d) if k == "A" else B_vals(d)
    hc = hidden_condition(iso, y)
    assert hc and hc[1] == [iso], (iso, y, hc)
    cond, hits, iv = hc
    cl, top = make_claims(k, vals, iso, y, True)
    cl['data'].insert(0, dict(id="c%d" % (len(cl['computation']) + 4), kind="data", importance="vital", text="Identifies the economy as %s (%s) from the stated conditions." % (NAMES[iso], iso), accept="full = names %s; no = any other economy." % NAMES[iso]))
    q = "Using the IMF World Economic Outlook (October 2025 vintage), take the one economy with %s. %s" % (cond, ask(k, "", y, "For that economy").replace("For that economy: ", "For that economy, ").capitalize() if False else ask(k, "", y, "For that economy"))
    items.append(base(nid(), "hidden", iso, y, k, q, cl, dict(hidden_condition=dict(text=cond, intervals=iv, matches=hits, set_size=len(hits)), decomposition_variant={"A": "IMF real-interest / real-growth contributions", "B": "Escolano eq. 26 split"}[k], dominant_driver=top)))
for iso, y, k, key, stated in CLAIMS:
    d = L.decomp(iso, y); vals = A_vals(d) if k == "A" else B_vals(d)
    gold = vals[key]; truth = abs(stated - gold) <= TOL
    nm = NAMES[iso]
    phrase = dict(pd="the primary deficit contributed %s percentage points to the change in the debt ratio" % sgn(stated),
                  ri="the real interest rate paid on the previous year's debt stock contributed %s percentage points to the change in the debt ratio" % sgn(stated),
                  gr="real GDP growth contributed %s percentage points to the change in the debt ratio" % sgn(stated),
                  inf="GDP-deflator inflation contributed %s percentage points to the change in the debt ratio" % sgn(stated))[key]
    q = "A staff report on %s states that in %d, %s (general government gross debt, percent of GDP; contributions measured against the previous year's debt stock). Is this statement accurate? Verify it with the data and give the correct figure." % (nm, y, phrase)
    cl = dict(text=[dict(id="c1", kind="text", importance="vital", text="Identifies the debt-ratio decomposition (primary deficit / interest-rate / growth / inflation terms applied to previous-year debt) as the method for checking the statement, per Escolano (2010) or the IMF (2013) debt-dynamics annex.",
                         accept="full = names the decomposition from an institutional source and uses it; partial = does the calculation without sourcing; no = other method."),
                    dict(id="c3", kind="text", importance="vital", text="Verdict: the statement is %s." % ("TRUE" if truth else "FALSE"),
                         accept="full = verdict matches (%s) and the correct figure is given; partial = verdict only; no = wrong verdict." % ("true" if truth else "false"))],
              data=[dict(id="c4", kind="data", importance="okay", text="Uses WEO general government gross debt, primary balance, interest (primary minus overall balance), nominal and real GDP.", accept="full = all series; partial = most; no = other.")],
              computation=[dict(id="c2", kind="computation", importance="vital", text="Correct value of the stated quantity for %s %d: %s percentage points." % (nm, y, sgn(gold)),
                                accept="full = within %.1f pp of %s; partial = within 1.0 pp; no = otherwise." % (TOL, sgn(gold)), target=round(gold, 3), tolerance_abs=TOL)])
    it = base(nid(), "claim_check", iso, y, k, q, cl, dict(statement=dict(quantity=key, stated=stated, truth=truth, correct_value=round(gold, 3)), decomposition_variant={"A": "IMF", "B": "Escolano eq. 26"}[k]))
    items.append(it)
for it in items:
    json.dump(it, open("%s/%s.json" % (OUT, it['id']), "w"), indent=1, ensure_ascii=False)
print(len(items), "items written")
for it in items:
    print(it['id'], it['style'], it['provenance']['subject']['iso3'], it['provenance']['subject']['year'], 'pub=%d' % it['validation']['published_instances_matching'], it.get('dominant_driver', ''), it.get('statement', ''), (it.get('hidden_condition') or {}).get('text', ''))
