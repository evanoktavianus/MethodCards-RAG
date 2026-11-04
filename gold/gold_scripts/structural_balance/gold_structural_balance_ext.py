"""Instance extension for the structural-balance family (SB-15...). python3 -I gold_structural_balance_ext.py [--write]
Same recipe and tolerances as gold_structural_balance.py (HP lambda 100, e_rev=1, e_exp=0; cab tol 0.3, stance tol 0.4).
Does not modify SB-01..14. Selection rule is printed below.

SELECTION RULE (fixed before looking at which cases match, applied mechanically):
 Pool CAB    : country-years 2000-2024, WB-classified economy, WEO published GGSB_NPGDP and all inputs present,
               |cyclical adjustment| = |recomputed CAB - overall balance| >= 0.7 pp. No country excluded (Norway stays in the pool).
 Pool STANCE : same years, |recomputed change in CAB| >= 1.0 pp, previous year also available.
 Eligible    = pool members where recomputed matches published within tolerance. Match-rate = eligible / pool (reported).
 Draw        : seeded shuffle (seed 20261030) of eligible instances; countries of SB-01..14 are skipped, at most one
               instance per country; take the first that fits each slot (named 7, hidden 7, claim 6).
 Hidden      : predicate on two indicators with thresholds on a 0.5 grid just beyond the target value; accepted only if set size == 1 (asserted).
 Claim       : true claim = recomputed value rounded to nearest 0.5; false claim = recomputed +/- 2.0 pp (sign alternating);
               truth decided by |recomputed - claim| <= 0.5 (same as SB-11..14), asserted also against the published value.
"""
import sys, os, csv, json, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sblib import *
TOL = {"cab": 0.3, "stance": 0.4}
D = {k: load(k) for k in ["ngdp_rpch","ggxwdg_ngdp","lur","pcpipch","ggxcnl_ngdp","ggr_ngdp","ggx_ngdp","ngdp_r","ggsb_npgdp"]}
wb = {r["iso3"]: r for r in csv.DictReader(open(REF + "/wb_classifications.csv"))}
econ = [c for c in D["ngdp_r"] if c in wb and wb[c]["income_group"] not in ("Aggregates", "")]
EXISTING = {"DEU","FIN","ROU","ITA","GRC","BRA","PAN","IRL","BWA","GRD","FRA","USA","THA","BEL","NLD","CYP","JPN","SWE","CAN"}
EXISTING_ITEM_COUNTRIES = {"DEU","FIN","ROU","ITA","GRC","BRA","PAN","IRL","BWA","GRD","FRA","USA","THA","BEL"}  # countries of SB-01..14 (items on disk)
hp = {}
def gap(c, y):
    if c not in hp:
        try: hp[c] = hp_gap(D["ngdp_r"][c], 1980, 2030, 100.0)
        except KeyError: hp[c] = None
    return hp[c][y]
def ok(c, y, ks=("ggr_ngdp","ggx_ngdp","ggxcnl_ngdp","ggsb_npgdp","ngdp_r")):
    return all(y in D[k].get(c, {}) for k in ks) and contiguous(D["ngdp_r"].get(c, {}), 1980, 2030)
def cab(c, y): return cab_pot(D["ggr_ngdp"][c][y], D["ggx_ngdp"][c][y], gap(c, y))

pool_cab, pool_st = [], []
for c in sorted(econ):
    for y in range(2000, 2025):
        if not ok(c, y): continue
        r = cab(c, y); ob = D["ggxcnl_ngdp"][c][y]; p = D["ggsb_npgdp"][c][y]
        if abs(r - ob) >= 0.7: pool_cab.append(dict(c=c, y=y, rec=r, pub=p, ob=ob, kind="cab", match=abs(r - p) <= TOL["cab"]))
        if ok(c, y - 1):
            d = r - cab(c, y - 1)
            if abs(d) >= 1.0:
                dp = p - D["ggsb_npgdp"][c][y - 1]
                pool_st.append(dict(c=c, y=y, rec=d, pub=dp, ob=ob, kind="stance", match=abs(d - dp) <= TOL["stance"]))
el_cab = [x for x in pool_cab if x["match"]]; el_st = [x for x in pool_st if x["match"]]
print("POOL cab: %d country-years, %d countries; matched %d (%.1f%%), %d countries" % (len(pool_cab), len({x['c'] for x in pool_cab}), len(el_cab), 100*len(el_cab)/len(pool_cab), len({x['c'] for x in el_cab})))
print("POOL stance: %d country-years; matched %d (%.1f%%), %d countries" % (len(pool_st), len(el_st), 100*len(el_st)/len(pool_st), len({x['c'] for x in el_st})))
print("NOR in cab pool: %d, matched %d" % (sum(x['c']=='NOR' for x in pool_cab), sum(x['c']=='NOR' and x['match'] for x in pool_cab)))

NAME = {c: r["name"].strip() for c, r in wb.items()}
FIX = {"Egypt, Arab Rep.": "Egypt", "Korea, Rep.": "South Korea", "Turkiye": "Turkey", "Russian Federation": "Russia", "Slovak Republic": "Slovakia",
       "Iran, Islamic Rep.": "Iran", "Venezuela, RB": "Venezuela", "Gambia, The": "The Gambia", "Bahamas, The": "The Bahamas", "Hong Kong SAR, China": "Hong Kong",
       "Kyrgyz Republic": "Kyrgyzstan", "Lao PDR": "Laos", "Yemen, Rep.": "Yemen", "Congo, Dem. Rep.": "the Democratic Republic of the Congo", "Congo, Rep.": "the Republic of Congo"}
def nm(c):
    n = FIX.get(NAME[c], NAME[c])
    return ("the " + n) if n in ("United States", "United Kingdom", "Netherlands", "Philippines", "United Arab Emirates", "Czech Republic") else n

rng = random.Random(20261030)
cand_cab = el_cab[:]; rng.shuffle(cand_cab)
cand_st = el_st[:]; rng.shuffle(cand_st)

IND = {"ngdp_rpch": ("real GDP growth", "%"), "lur": ("unemployment rate", "%"), "pcpipch": ("consumer-price inflation", "%"),
       "ggxwdg_ngdp": ("gross general government debt", "% of GDP"), "ggxcnl_ngdp": ("general government net lending/borrowing", "% of GDP")}
def phrase(a, d, t, y):
    T = ("%g" % abs(t))
    if a == "ngdp_rpch" and t <= 0 and d < 0: return "real GDP fell by more than %s%% in %d" % (T, y)
    if a == "pcpipch" and t <= 0 and d < 0: return "consumer prices fell by more than %s%% in %d" % (T, y)
    v = {"ngdp_rpch": "real GDP grew by %s %s%% in %d", "lur": "the unemployment rate in %d was %s %s%%", "pcpipch": "consumer-price inflation in %d was %s %s%%",
         "ggxwdg_ngdp": "gross public debt in %d was %s %s%% of GDP", "ggxcnl_ngdp": "the general government balance in %d was %s %s%% of GDP"}[a]
    w = "more than" if (d > 0 and a == "ngdp_rpch") else ("less than" if a == "ngdp_rpch" else ("above" if d > 0 else "below"))
    tt = ("%g" % t)
    if a == "ngdp_rpch": return v % (w, tt, y)
    return v % (y, w, tt)
def find_pred(c, y, seed):
    r = random.Random(seed); keys = list(IND); 
    for _ in range(60):
        a, b = r.sample(keys, 2)
        pred = []
        for k in (a, b):
            if y not in D[k].get(c, {}): break
            v = D[k][c][y]; d = r.choice((1, -1))
            t = (math.floor(v * 2) / 2.0 - 0.5) if d > 0 else (math.ceil(v * 2) / 2.0 + 0.5)
            if abs(t) < 1e-9: t = 0.0
            pred.append((k, d, t, phrase(k, d, t, y)))
        else:
            S = [e for e in econ if all(y in D[k].get(e, {}) and d * (D[k][e][y] - t) > 0 for k, d, t, _ in pred)]
            if S == [c]: return pred, len(S)
    return None, None

used = set(EXISTING_ITEM_COUNTRIES); chosen = []
def take(pool, n, pred_fn=None):
    got = []
    for x in pool:
        if len(got) == n: break
        if x["c"] in used: continue
        ex = {}
        if pred_fn:
            pr, sz = pred_fn(x)
            if pr is None: continue
            ex = dict(pred=pr, set_size=sz)
        x = dict(x, **ex); got.append(x); used.add(x["c"])
    return got
# slot plan: named 7 (5 cab + 2 stance), hidden 7 (6 cab + 1 stance), claim 6 (cab_claim; 3 true / 3 false)
named = take(cand_cab, 5) + take(cand_st, 2)
hidden = take(cand_cab, 6, lambda x: find_pred(x["c"], x["y"], hash((x["c"], x["y"])) & 0xffff if False else sum(map(ord, x["c"])) * 100 + x["y"])) + \
         take(cand_st, 1, lambda x: find_pred(x["c"], x["y"], sum(map(ord, x["c"])) * 100 + x["y"]))
claims = take(cand_cab, 6)
assert len(named) == 7 and len(hidden) == 7 and len(claims) == 6
for x in named: x["style"] = "named"
for x in hidden: x["style"] = "hidden"
for x in claims: x["style"] = "claim"

def poss(n): return n + ("'" if n.endswith("s") else "'s")
def f1(v): return "%.1f" % abs(v)
def sidebal(ob): return ("general government deficit of %s%% of GDP" % f1(ob)) if ob < 0 else ("general government surplus of %s%% of GDP" % f1(ob))
CAB_NAMED = [
 "{n} recorded a {b} in {y}. Setting aside the effect of where the economy stood relative to its normal capacity that year, what would the balance have been, as a share of capacity-level GDP?",
 "In {y}, {np} public finances showed a {b}. How much of that was down to the economy running away from its full-capacity level, and what balance would remain with activity at that level (percent of GDP at that level)?",
 "Was {np} budget position in {y} stronger or weaker than the headline figure of a {b} suggests once the economy is put back at its normal capacity level? Give the balance you get, in percent of capacity-level GDP.",
 "Looking at {n} in {y} (headline: {b}), what was the fiscal position that policy itself was delivering, i.e. the balance with the economy at full capacity, as a percent of GDP at that level?",
 "{np} {y} accounts show a {b}. Strip out the part due to the economy being above or below its sustainable level of activity: what is the remaining balance in percent of GDP at that sustainable level?",
 ]
CAB_HID = [
 "Consider the economy for which {p}. What was that economy's general government balance in {y} with activity put at its normal capacity level, in percent of GDP at that level?",
 "Which economy is the one for which {p}? For that economy in {y}, how large was the balance that would have applied at full capacity, in percent of capacity-level GDP?",
 "One economy in {y} is singled out by this description: {p}. Adjusting its {y} balance to what it would have been with the economy at its normal capacity level, what do you get (percent of GDP at that level)?",
 "Among all economies, exactly one is such that {p}. What was its {y} fiscal balance once the economy is brought to its normal capacity level, in percent of GDP at that level?",
 ]
ST_NAMED = [
 "{np} general government balance moved from {b0}% to {b1}% of GDP between {y0} and {y}. Once the economic cycle is stripped out, was fiscal policy tighter or looser in {y}, and by how many percentage points of GDP did the underlying balance change?",
 "Did {n} tighten or loosen its fiscal stance in {y}? The headline balance went from {b0}% of GDP in {y0} to {b1}% in {y}; I want the change in the balance net of the cycle, in percentage points of GDP.",
 ]
ST_HID = "Consider the economy for which {p}. Between {y0} and {y}, did its fiscal policy get tighter or looser once the economic cycle is removed, and by how many percentage points of GDP did its underlying balance change?"
def joinp(pr): return " and ".join(p[3] for p in pr) if len(pr) > 1 else pr[0][3]
def sgn(v): return ("%.1f" % v)

items = []
ci = 0
for x in named + hidden + claims:
    c, y, k, st = x["c"], x["y"], x["kind"], x["style"]
    ob = D["ggxcnl_ngdp"][c][y]
    it = dict(x)
    if st == "named" and k == "cab":
        it["query"] = CAB_NAMED[ci % 5].format(n=nm(c), np=poss(nm(c)), y=y, b=sidebal(ob)); ci += 1
    elif st == "named":
        it["query"] = ST_NAMED[0 if len([i for i in items if i["style"]=="named" and i["kind"]=="stance"]) == 0 else 1].format(n=nm(c), np=poss(nm(c)), y=y, y0=y-1, b0=sgn(D["ggxcnl_ngdp"][c][y-1]), b1=sgn(ob))
    elif st == "hidden" and k == "cab":
        it["query"] = CAB_HID[len([i for i in items if i["style"]=="hidden"]) % 4].format(p=joinp(x["pred"]).replace(" in %d" % y, "") if False else joinp(x["pred"]), y=y)
    elif st == "hidden":
        it["query"] = ST_HID.format(p=joinp(x["pred"]), y=y, y0=y-1)
    else:
        j = len([i for i in items if i["style"] == "claim"])
        truthy = j % 2 == 0   # alternate true/false -> 3/3
        base = round(x["rec"] * 2) / 2.0
        val = base if truthy else base + (2.0 if j % 4 == 1 else -2.0)
        it["claim_value"] = val; it["kind"] = "cab_claim"
        it["truth"] = abs(x["rec"] - val) <= 0.5
        assert it["truth"] == truthy and (abs(x["pub"] - val) <= 0.8) == truthy, (c, y, x["rec"], x["pub"], val)
        def desc(v, fmt="%g"): return ("a deficit of " + fmt + "%% of GDP") % abs(v) if v < 0 else ("a surplus of " + fmt + "%% of GDP") % v
        frame = [
         "A commentary on {n} states: 'In {y} {n} recorded {h}, but with the economy at its normal capacity level the outcome would have been {v}.' Is that statement accurate?",
         "A report on {n} says: 'Against a headline {y} outcome of {h}, the balance with the economy at full capacity was roughly {v}.' Is that claim correct?",
         "An analyst note claims that {np} underlying position in {y}, meaning the balance with the economy at its normal capacity level, was {v} (the headline was {h}). Does that hold up?"][j % 3]
        it["query"] = frame.format(n=nm(c), np=poss(nm(c)), y=y, h=desc(ob, '%.1f'), v=desc(val))
    if st == "hidden": it["hidden_name"] = nm(c)
    items.append(it)

# nearest base item: same style and kind class, closest year (read from the existing item files)
import glob, re
BASES = []
for f in sorted(glob.glob(os.path.join(ROOT, "items", "structural_balance", "SB-*.json"))):
    d = json.load(open(f))
    if d.get("instance_extension"): continue
    m = re.search(r" ([A-Z]{3}) (\d{4})", d["claims"]["computation"][0]["text"])
    BASES.append((d["id"], d["style"], "stance" if "Change in" in d["claims"]["computation"][0]["text"] else ("cyc" if "share" in d["claims"]["computation"][0]["text"] else "cab"), int(m.group(2))))
for n, it in enumerate(items, 15):
    it["id"] = "SB-%02d" % n
    kc = "stance" if it["kind"] == "stance" else "cab"
    cands = [b for b in BASES if b[1] == it["style"] and b[2] == kc] or [b for b in BASES if b[1] == it["style"]]
    it["ext_of"] = min(cands, key=lambda b: (abs(b[3] - it["y"]), b[0]))[0]
    kk = "cab" if it["kind"] in ("cab", "cab_claim") else "stance"
    assert abs(it["rec"] - it["pub"]) <= TOL[kk]
    print(it["id"], it["style"], it["kind"], it["c"], it["y"], "rec %.2f pub %.2f overall %.2f" % (it["rec"], it["pub"], it["ob"]), "truth=%s" % it.get("truth"), "set=%s" % it.get("set_size"))
    print("    ", it["query"])
if "--no-write" in sys.argv or "--write" not in sys.argv: sys.exit()

MD = ["afa3529e-c97c-45cb-a668-d1a133131d8c", "9a9aeb9c-3a8b-4e2e-a459-aa8143f05d3f"]
od = os.path.join(ROOT, "items", "structural_balance")
for it in items:
    c, y, k = it["c"], it["y"], it["kind"]; stance = k == "stance"
    inputs = ["GGR_NGDP", "GGX_NGDP", "NGDP_R", "GGXCNL_NGDP"]
    t = ("Change in underlying balance %s %d-%d = %.2f pp of GDP" % (c, y-1, y, it["rec"])) if stance else ("Underlying (capacity-level) balance %s %d = %.2f %% of potential GDP" % (c, y, it["rec"]))
    comp = [{"id": "c1", "kind": "computation", "importance": "vital", "text": t, "reference_value": round(it["rec"], 3), "tolerance": TOL["stance" if stance else "cab"], "unit": "pp",
             "accept": "full = within tolerance; the output gap is the HP-filter (lambda=100) cycle of log real GDP, revenue elasticity 1, expenditure elasticity 0"}]
    verdict = []
    if "truth" in it:
        verdict = [{"id": "c4", "kind": "text", "importance": "vital", "text": "Judges the statement %s." % ("ACCURATE" if it["truth"] else "NOT accurate"), "accept": "verdict must match; reasoning must cite the recomputed value"}]
    if stance:
        verdict = [{"id": "c4", "kind": "text", "importance": "vital", "text": "States whether the underlying fiscal stance %s." % ("tightened" if it["rec"] > 0 else "loosened"), "accept": "direction must match the sign of the change in the underlying balance"}]
    if it["style"] == "hidden":
        verdict.append({"id": "c6", "kind": "text", "importance": "okay", "text": "Identifies the economy as %s." % it["hidden_name"], "accept": "names the country satisfying the stated conditions"})
    item = {"id": it["id"], "family": "methodology", "pattern": "M-" + it["style"], "tier": "analytical", "status": "validated", "query": it["query"],
            "instance_extension": True, "extension_of": it["ext_of"],
            "claims": {"text": [{"id": "c0", "kind": "text", "importance": "vital",
                        "text": "Identifies that the answer requires cyclically adjusting the budget balance (potential-output gap from a statistical trend, then removing the cyclical budget component).",
                        "accept": "full = names cyclically adjusted / structural balance approach with an output-gap estimate; acceptable alternatives: OECD or EC semi-elasticity approach, production-function output gap; no = raw balance only"}] + verdict,
                       "data": [{"id": "c5", "kind": "data", "importance": "okay", "text": "Uses general government revenue, expenditure and real GDP series from the WEO (%s)." % ", ".join(inputs)}],
                       "computation": comp},
            "grading": {"method": "answer_recall"},
            "provenance": {"assembled_from": ["Fiscal Monitor Oct 2012 / Oct 2013 data-conventions note (CAB: HP potential output, revenue elasticity 1, expenditure elasticity 0)", "frozen WEO Oct 2025 (+frozen_extra)"],
                           "gold_script": "gold_scripts/structural_balance/gold_structural_balance_ext.py",
                           "selection": "instance extension; drawn from the eligible pool (|cyclical adjustment|>=0.7pp or |stance change|>=1.0pp, recompute within tolerance of WEO), seeded draw, one per country"},
            "method": "cyclically_adjusted_balance_hp_filter", "method_doc_ids": MD,
            "method_doc_alternatives": ["5bc9162b-f850-4bd4-a964-d3632f04cb9b (multivariate filter, alternative output-gap method)"],
            "gold_report_ids": [], "gold_report_note": "No corpus country report states these values; published value is the IMF WEO Oct 2025 GGSB_NPGDP series (frozen), not a corpus document, so nothing needs withholding.",
            "published_value": round(it["pub"], 3), "recomputed_value": round(it["rec"], 3), "tolerance": TOL["stance" if stance else "cab"],
            "inputs": inputs, "style": it["style"],
            "distractors": ["debt-stabilising primary balance", "fiscal multiplier / fiscal impulse from multipliers", "revenue buoyancy", "fiscal rule calibration"],
            "famous_method": True, "hidden_set_size": it.get("set_size"), "predicate": [p[3] for p in it["pred"]] if "pred" in it else None}
    p = os.path.join(od, it["id"] + ".json")
    assert not os.path.exists(p), p
    json.dump(item, open(p, "w"), indent=1)
print("wrote", len(items))
