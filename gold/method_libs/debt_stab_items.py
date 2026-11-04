"""Authors items/debt_stab/DSTAB-*.json from the FROZEN data. python3 -I scripts/debt_stab_items.py regenerates all golds,
sensitivities and published-value fields (plain policy questions, definitions in the claims, interest-definition sensitivity)."""
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import debt_stab_lib as L
import debt_stab_sens as SENS
ROOT = os.path.abspath(os.path.join(HERE, ".."))
OUT = os.path.join(ROOT, "items", "debt_stab"); os.makedirs(OUT, exist_ok=True)
NAMES = dict(HUN="Hungary", SRB="Serbia", IND="India", ROU="Romania", DEU="Germany", USA="the United States", ALB="Albania",
  SVN="Slovenia", CHN="China", ARM="Armenia", KAZ="Kazakhstan", CHL="Chile", JAM="Jamaica", EST="Estonia",
  GTM="Guatemala", FJI="Fiji", OMN="Oman", BWA="Botswana", RUS="Russia", THA="Thailand")
CMAP = dict(HUN="Hungary", SRB="Serbia", IND="India", ROU="Romania", DEU="Germany", USA="United States", ALB="Albania", SVN="Slovenia",
  CHN="China", ARM="Armenia", KAZ="Kazakhstan", CHL="Chile", JAM="Jamaica", EST="Estonia", GTM="Guatemala", FJI="Fiji", OMN="Oman",
  BWA="Botswana", RUS="Russia", THA="Thailand")
VAL = json.load(open(os.path.join(HERE, "debt_stab_validation.json")))
REPORTS = {}
for v in VAL:
    if v["status"] != "EXCLUDED": REPORTS.setdefault(v["country"], []).append(v["doc_id"])
# last projection year T of each report's DSA table (the published stabilising balance refers to T), from the parsed tables
PARSED = json.load(open(os.path.join(ROOT, "frozen_extra", "debt_path_tables", "parsed.json")))
T_OF = {}
for q in PARSED: T_OF.setdefault(q["doc"], q["years"][-1])
T_INFERRED = {"fb080958-cf7c-4027-862c-4ebcc331b359": 2023}   # Estonia 2018: table not parsed; its public-DSA figures span 2007-2023
METHOD_DOCS = ["55319ff9-c45c-4e8d-99e4-5562a1158bf2", "2dea3fb1-758b-40a4-882b-59f953293e2d", "c010cde9-5069-43d5-a0a6-d162270835fd"]
CONV = ("Convention for the gold (WEO Oct 2025, general government): effective interest rate r_t = interest paid in year t divided by gross debt at the end of year t-1 "
        "(in levels; interest = primary balance minus overall balance, % of GDP_t, so r_t = interest/GDP_t x (1+g_t) / (debt/GDP)_{t-1}); nominal GDP growth g_t = NGDP_t / NGDP_{t-1} - 1 "
        "from nominal GDP in national currency; primary balance = revenue minus non-interest spending, surplus positive; lambda=(r-g)/(1+g) and p* = lambda x (debt/GDP)_{t-1}.")
DIST = ["overall (headline) balance that holds debt constant, b* = -g/(1+g) d (answers a different question)",
        "cyclically adjusted / structural primary balance", "fiscal-gap or tax-gap indicators (S1/S2) over an infinite horizon",
        "primary balance needed to reach a debt anchor or fiscal-rule ceiling", "debt-change decomposition without a stabilising benchmark"]
BASE_TOL = dict(required=0.15, numeric=0.15, verdict=0.15, gap=0.3, path=1.0, target=0.2)

def r1(x): return round(x, 1) + 0.0
def S(iso, t): return L.stab(L.inputs(iso, t))

def find_unique(iso, t):
    """conditions on previous-year-end debt, primary balance, nominal growth that single out iso in year t (over all frozen economies)"""
    univ = {}
    for k in L.DEBT:
        if len(k) != 3: continue
        x = L.inputs(k, t)
        if x: univ[k] = (x["d_prev"], x["pb"], 100 * x["gamma"], x["d_t"])
    tgt = univ[iso]
    import itertools
    for w in (3, 2, 1.5, 1, 0.75, 0.5):
        for use in ((0, 1), (0, 2), (1, 2), (0, 1, 2)):
            win = {}
            for u in use:
                lo = int((tgt[u] - w) * 2) / 2.0 if tgt[u] - w >= 0 else -int((-(tgt[u] - w)) * 2 + 0.999) / 2.0
                hi = lo + 2 * w
                win[u] = (lo, hi)
            if not all(win[u][0] <= tgt[u] <= win[u][1] for u in use): continue
            m = [k for k, v in univ.items() if all(win[u][0] <= v[u] <= win[u][1] for u in use)]
            if m == [iso]: return use, win, len(univ)
    return None

def describe(use, win, t):
    lab = {0: "general government gross debt at the end of %d was between %s and %s percent of GDP" % (t - 1, "%g", "%g"),
           1: "primary balance in %d was between %s and %s percent of GDP" % (t, "%g", "%g"),
           2: "nominal GDP growth in %d was between %s and %s percent" % (t, "%g", "%g")}
    parts = [lab[u] % win[u] for u in use]
    return "Among the economies in the IMF World Economic Outlook database, take the one whose " + ", and whose ".join(parts) + ". "


def widen(base, maxdev):
    """smallest multiple of 0.05 that covers the largest deviation of the alternative definitions from the canonical value (+0.01 margin)"""
    if maxdev <= base: return base
    return round(math.ceil((maxdev + 0.01) / 0.05) * 0.05, 2)

def published_for(iso, t):
    """published debt-stabilising primary balance from a DSA baseline table of the same country, matched on the table's last projection year T"""
    rows = [v for v in VAL if v["country"] == CMAP[iso] and v["status"] != "EXCLUDED"]
    cands = []
    for v in rows:
        T = T_OF.get(v["doc_id"]) or T_INFERRED.get(v["doc_id"])
        cands.append(dict(report_id=v["doc_id"], report_title=v["title"], report_year=v["year"], table_last_projection_year=T,
                          table_year_inferred=v["doc_id"] in T_INFERRED, published_value=v["published"], status=v["status"],
                          recomputed_pure_formula_report_vintage=v.get("pure"), other_identified_flows_included=(v["status"] == "MATCH_WITH_OTHER_FLOWS")))
    near = [c for c in cands if c["table_last_projection_year"] is not None and abs(c["table_last_projection_year"] - t) <= 1]
    others = [c for c in cands if c not in near]
    return near, others

SPEC = [
 ("DSTAB-01","named","HUN",2019,"required",{}),("DSTAB-02","named","SRB",2018,"required",{}),
 ("DSTAB-03","named","IND",2022,"gap",{}),("DSTAB-04","named","ROU",2023,"gap",{}),
 ("DSTAB-05","named","DEU",2024,"path",{"n":5}),("DSTAB-06","named","USA",2023,"path",{"n":5}),
 ("DSTAB-07","named","ALB",2018,"target",{"n":5,"target":60.0}),
 ("DSTAB-08","hidden","SVN",2023,"required",{}),("DSTAB-09","hidden","CHN",2022,"gap",{}),
 ("DSTAB-10","hidden","ARM",2018,"gap",{}),("DSTAB-11","hidden","KAZ",2018,"required",{}),
 ("DSTAB-12","hidden","CHL",2017,"path",{"n":5}),("DSTAB-13","hidden","JAM",2024,"path",{"n":5}),
 ("DSTAB-14","hidden","EST",2022,"required",{}),
 ("DSTAB-15","claim_check","GTM",2023,"verdict",{"true":True}),("DSTAB-16","claim_check","FJI",2019,"verdict",{"true":False}),
 ("DSTAB-17","claim_check","OMN",2019,"numeric",{"true":True}),("DSTAB-18","claim_check","BWA",2019,"numeric",{"true":False}),
 ("DSTAB-19","claim_check","RUS",2018,"verdict",{"true":False}),("DSTAB-20","claim_check","THA",2016,"numeric",{"true":True}),
]
IDENT = {"id": "c1", "kind": "text", "importance": "vital",
 "text": "Identifies the debt-dynamics identity d_t=(1+lambda)d_{t-1}-p_t with lambda=(r-g)/(1+g) (the debt-stabilising primary balance p*=lambda*d_{t-1}) as the applicable method.",
 "accept": "full = names the debt-dynamics / debt-stabilising primary balance approach (Escolano 2010; IMF 2013 Staff Guidance Note for public DSA; MAC SRDSF) or applies the equivalent formula; partial = uses only a rule of thumb (r-g)*d without the 1+g denominator; no = uses an overall-balance, structural-balance or S1/S2 method.",
 "supporting_passages": ["55319ff9-c45c-4e8d-99e4-5562a1158bf2#escolano_eq5_7_20"]}
DATA = {"id": "c5", "kind": "data", "importance": "okay",
 "text": "Uses general government gross debt (% GDP), primary balance and overall balance (interest = primary minus overall balance, % GDP), and nominal GDP (WEO Oct 2025: GGXWDG_NGDP, GGXONLB_NGDP, GGXCNL_NGDP, NGDP).",
 "accept": "full = all inputs correctly sourced; partial = some inputs approximated (e.g. real growth plus deflator); no = unrelated series."}
INPUTS = ["GGXWDG_NGDP", "GGXONLB_NGDP", "GGXCNL_NGDP", "NGDP"]
golds = []; sens_rows = []
for (iid, style, iso, t, kind, ex) in SPEC:
    s = S(iso, t); nm = NAMES[iso]; cap = nm[0].upper() + nm[1:]
    pstar = s["p_star"]; gap = s["gap"]
    # numeric claim-check statement shown
    shown = None
    if kind == "numeric": shown = pstar if ex["true"] else pstar + (2.0 if pstar < 0 else -2.0)
    sens = SENS.sensitivity(iso, t, kind, ex, shown)
    base = BASE_TOL[kind]; tol = widen(base, sens["max_abs_dev_from_canonical"])
    if kind in ("verdict", "numeric", "required"): tol_req = tol
    claims = [dict(IDENT)]; q = ""; gold = {}
    if style == "hidden":
        u = find_unique(iso, t)
        if not u: raise SystemExit("no unique condition for %s %d" % (iso, t))
        use, win, nuniv = u; pre = describe(use, win, t); who = "that economy"
        gold["hidden_condition"] = dict(fields=["d_prev", "pb", "nominal_growth"], used=list(use), windows={str(k): v for k, v in win.items()}, universe=nuniv, answer_set_size=1)
    else: pre = ""; who = nm
    poss = who + "'s" if style == "named" else "that economy's"
    sens_txt = " The gold uses the convention stated in the grading note; interest-definition alternatives (average debt, current-year debt, real-rate form) move the value by at most %.2f pp, covered by the tolerance." % sens["max_abs_dev_from_canonical"]
    if kind == "required":
        q = pre + ("What primary balance would %s have needed in %d to stop its debt-to-GDP ratio from rising?" % (who, t))
        gold.update(value=r1(pstar), unit="% of GDP")
        claims.append(dict(id="c2", kind="computation", importance="vital", text="Primary balance needed in %d is about %.1f%% of GDP (%s), computed as p* = lambda x previous-year debt with the effective interest rate = interest paid in %d / debt at end of %d and nominal growth = NGDP_%d/NGDP_%d - 1; surplus positive." % (t, r1(pstar), "surplus" if pstar > 0 else "a deficit of this size keeps the ratio constant", t, t - 1, t, t - 1), accept="full = within +-%.2f pp (sign convention: surplus positive; a deficit stated as a positive 'deficit of x' with explicit wording is accepted); partial = right sign within +-0.5 pp; no = otherwise.%s" % (tol, sens_txt), target=r1(pstar), tolerance_abs=tol))
        claims.append(dict(id="c3", kind="text", importance="vital", text="States that the actual primary balance of %.1f%% was %s the required balance, so the debt ratio %s (implied change %+.1f pp before other flows)." % (r1(s["pb"]), "above" if gap > 0 else "below", "falls" if gap > 0 else "rises", -gap), accept="verdict direction must match."))
        gold["answer"] = "%.1f" % r1(pstar)
    elif kind == "gap":
        q = pre + ("By how many percentage points of GDP did %s primary balance in %d exceed, or fall short of, the level needed to stop its debt-to-GDP ratio from rising?" % (poss, t))
        gold.update(value=r1(gap), unit="pp of GDP")
        claims.append(dict(id="c2", kind="computation", importance="vital", text="Gap (actual minus required primary balance, positive = actual above required) is about %+.1f pp of GDP (actual %.1f, required %.1f); required balance p* = lambda x previous-year debt with effective interest rate = interest paid in %d / debt at end of %d and nominal growth = NGDP_%d/NGDP_%d - 1." % (r1(gap), r1(s["pb"]), r1(pstar), t, t - 1, t, t - 1), accept="full = within +-%.2f pp (sign: positive = actual above required; the reverse convention is accepted if stated explicitly and the direction of the verdict agrees).%s" % (tol, sens_txt), target=r1(gap), tolerance_abs=tol))
        claims.append(dict(id="c3", kind="text", importance="vital", text="Concludes the actual balance was %s the debt-stabilising level, i.e. the debt ratio was %s." % ("above" if gap > 0 else "below", "set to fall" if gap > 0 else "set to rise"), accept="direction must match."))
        gold["answer"] = "%+.1f" % gap
    elif kind == "path":
        n = ex["n"]; path = L.project(s["d_t"], s["pb"], s["lam"], n)
        end = path[-1]; rising = end > s["d_t"]
        q = pre + ("Suppose %s kept the primary balance, interest rate and nominal growth it recorded in %d for the next %d years. Would its debt-to-GDP ratio be higher or lower than at the end of %d after that period, and at about what level?" % (who, t, n, t))
        gold.update(value=r1(end), unit="% of GDP", start=r1(s["d_t"]), path=[r1(x) for x in path], direction="rising" if rising else "falling")
        claims.append(dict(id="c2", kind="computation", importance="vital", text="Debt ratio after %d years is about %.1f%% of GDP (start %.1f at end-%d), iterating d_t=(1+lambda)d_{t-1}-p with constant lambda=(r-g)/(1+g)=%.4f and constant primary balance p=%.1f%% of GDP; r = interest paid in %d / debt at end of %d, g = NGDP_%d/NGDP_%d - 1." % (n, r1(end), r1(s["d_t"]), t, s["lam"], r1(s["pb"]), t, t - 1, t, t - 1), accept="full = within +-%.2f pp of GDP.%s" % (tol, sens_txt), target=r1(end), tolerance_abs=tol))
        claims.append(dict(id="c3", kind="text", importance="vital", text="Debt ratio is on a %s path (%s the starting level)." % ("rising" if rising else "falling", "above" if rising else "below"), accept="direction must match."))
        gold["answer"] = "%.1f (%s)" % (end, "rising" if rising else "falling")
    elif kind == "target":
        n = ex["n"]; tg = ex["target"]; pn = L.balance_for_target(s["d_t"], tg, s["lam"], n)
        ref = s["lam"] * s["d_t"]   # constant-ratio balance for the END-year debt (not the previous-year debt)
        q = ("%s's government debt stood at %.1f%% of GDP at the end of %d. If the interest and growth conditions of %d persisted, what constant primary balance would bring the debt ratio to %.0f%% of GDP within %d years?" % (cap, r1(s["d_t"]), t, t, tg, n))
        chk = L.project(s["d_t"], pn, s["lam"], n)[-1]; assert abs(chk - tg) < 1e-6
        gold.update(value=r1(pn), unit="% of GDP", target_debt=tg, years=n, stabilising_reference=round(ref, 2))
        claims.append(dict(id="c2", kind="computation", importance="vital", text="Constant primary balance needed is about %.1f%% of GDP (Escolano eq. 22 with lambda=%.4f, N=%d), where lambda=(r-g)/(1+g), r = interest paid in %d / debt at end of %d and g = NGDP_%d/NGDP_%d - 1 (surplus positive)." % (r1(pn), s["lam"], n, t, t - 1, t, t - 1), accept="full = within +-%.2f pp.%s" % (tol, sens_txt), target=r1(pn), tolerance_abs=tol))
        claims.append(dict(id="c3", kind="text", importance="vital", text="Notes that this is %s than the about %.2f%% of GDP (lambda x %.1f) that would merely hold the %.1f%% ratio constant." % ("higher" if pn > ref else "lower", ref, r1(s["d_t"]), r1(s["d_t"])), accept="direction must match."))
        gold["answer"] = "%.1f" % pn
    elif kind == "verdict":
        ok = gap > 0; stm_dir = ok if ex["true"] else (not ok)
        stm = "primary balance of %.1f%% of GDP in %d was %sto stop the debt ratio rising" % (r1(s["pb"]), t, "more than enough " if stm_dir else "not enough ")
        q = "A review of %s says: 'The %s'. Is this statement correct?" % (nm, stm)
        truth = (stm_dir == ok)
        assert not sens.get("verdict_flips")
        gold.update(truth=truth, required=r1(pstar), actual=r1(s["pb"]), unit="% of GDP"); gold["answer"] = "TRUE" if truth else "FALSE"
        claims.append(dict(id="c2", kind="computation", importance="vital", text="Required balance is about %.1f%% of GDP versus an actual %.1f%%; required p* = lambda x previous-year debt, r = interest paid in %d / debt at end of %d, g = NGDP_%d/NGDP_%d - 1 (surplus positive)." % (r1(pstar), r1(s["pb"]), t, t - 1, t, t - 1), accept="within +-%.2f pp.%s" % (tol, sens_txt), target=r1(pstar), tolerance_abs=tol))
        claims.append(dict(id="c3", kind="text", importance="vital", text="Judges the statement %s." % ("correct" if truth else "incorrect"), accept="verdict must match."))
    elif kind == "numeric":
        q = "A review of %s says: 'Holding the debt ratio constant in %d would have required a primary balance of about %.1f%% of GDP.' Is this correct to within a quarter of a percentage point?" % (nm, t, shown)
        truth = abs(shown - pstar) <= 0.25
        assert all(v == truth for v in sens["stated_within_0.25"].values())
        gold.update(truth=truth, required=r1(pstar), stated=r1(shown), unit="% of GDP"); gold["answer"] = "TRUE" if truth else "FALSE"
        claims.append(dict(id="c2", kind="computation", importance="vital", text="Required balance is about %.1f%% of GDP (stated %.1f); required p* = lambda x previous-year debt, r = interest paid in %d / debt at end of %d, g = NGDP_%d/NGDP_%d - 1 (surplus positive)." % (r1(pstar), r1(shown), t, t - 1, t, t - 1), accept="within +-%.2f pp.%s" % (tol, sens_txt), target=r1(pstar), tolerance_abs=tol))
        claims.append(dict(id="c3", kind="text", importance="vital", text="Judges the statement %s." % ("correct" if truth else "incorrect"), accept="verdict must match."))
    claims.append(dict(DATA))
    sens["flag_spread_gt_0.15"] = sens["spread"] > 0.15
    sens["tolerance_before"] = base; sens["tolerance_used"] = tol
    sens["within_tolerance_before"] = sens["max_abs_dev_from_canonical"] <= base
    sens["action"] = ("replaced item (see replaces)" if iid in REPLACED else ("tolerance widened %.2f -> %.2f to cover all four definitions" % (base, tol) if tol > base else "none: all definitions within tolerance"))
    sens["canonical"] = "a"
    # published value
    near, others = published_for(iso, t)
    pub = dict(published_value=None, published_report_id=None)
    if near:
        c = min(near, key=lambda c: abs(c["table_last_projection_year"] - t))
        pub = dict(published_value=c["published_value"], published_report_id=c["report_id"], published_report_title=c["report_title"], published_year=c["table_last_projection_year"],
                   published_year_gap=c["table_last_projection_year"] - t, published_quantity="debt-stabilising primary balance of the DSA baseline table, % of GDP (last projection year)",
                   published_vintage_note="Stated in a %d report for its last projection year %d%s, i.e. a forecast-vintage figure; the item gold uses %d outturn from WEO Oct 2025. Differs from the gold by %.1f pp mainly through vintage, so it is NOT a check of the gold; it only shows that the same method is published for this country%s." % (c["report_year"], c["table_last_projection_year"], " (inferred, table not parsed)" if c["table_year_inferred"] else "", t, abs(c["published_value"] - pstar), "; the report adds other identified debt-creating flows to its figure" if c["other_identified_flows_included"] else ""))
    else:
        why = "No DSA baseline table in the corpus states a debt-stabilising primary balance for %s for %d or an adjacent year: the published figure always refers to the last projection year of the table (report year + 4 or 5), and the validated reports for this country give " % (nm, t)
        if others: why += "; ".join("%s (report %d, last projection year %s): %s" % (o["report_id"][:8], o["report_year"], o["table_last_projection_year"] if o["table_last_projection_year"] else "not parsed", o["published_value"]) for o in others) + "."
        else: why += "none (no validated report for this country)."
        pub["published_value_note"] = why
    if near and len(near) > 1: pub["published_also_near"] = [c for c in near if c["report_id"] != pub["published_report_id"]]
    if others: pub["published_other_years"] = others
    item = dict(id=iid, family="methodology", method="debt_stab", style=style, tier="single_step" if style != "hidden" else "multi_step", status="validated", query=q,
      claims={"text": [c for c in claims if c["kind"] == "text"], "data": [c for c in claims if c["kind"] == "data"], "computation": [c for c in claims if c["kind"] == "computation"]},
      grading=dict(tolerance_abs_pp=tol, tolerance_basis=BASE_TOL[kind], note="Vital computation tolerance +-%.2f (path endpoint pp of GDP; gap/required/horizon-target pp). Verdicts and directions exact. %s Sensitivity: the four interest-definition variants are recorded in the sensitivity object; the tolerance covers them." % (tol, CONV), definitions=CONV),
      provenance=dict(source="frozen WEO Oct 2025 (frozen_extra/)", generator="scripts/debt_stab_items.py", method_text="Escolano (2010) eqs 5,7,20,22; IMF 2013 Staff Guidance Note (DSA table footnote on debt-stabilising primary balance)", validation="scripts/debt_stab_validation.json (28 of 29 published instances reproduced)"),
      method_doc_ids=METHOD_DOCS, gold_report_ids=REPORTS.get(CMAP[iso], []),
      recomputed_value=gold.get("value", gold.get("answer")),
      inputs=INPUTS, distractors=DIST, famous_method=True,
      answer_summary="%s %d: debt prev %.1f, effective rate %.2f%%, nominal growth %.2f%%, lambda %.4f, required primary balance %.2f, actual %.2f, gap %+.2f. Gold: %s" % (iso, t, s["d_prev"], 100 * s["r"], 100 * s["gamma"], s["lam"], pstar, s["pb"], gap, gold["answer"]),
      gold_script="scripts/debt_stab_items.py", validation_note="The formula is validated on 29 published country-years; item gold is on frozen WEO Oct 2025 data for a historic year, so it is not itself a published number (see published_value_note / published_vintage_note).",
      sensitivity=sens,
      gold=dict(iso3=iso, year=t, kind=kind, **gold))
    item.update(pub)
    json.dump(item, open(os.path.join(OUT, iid + ".json"), "w"), indent=1)
    golds.append(dict(id=iid, iso=iso, year=t, kind=kind, style=style, answer=gold["answer"], sensitivity_spread=sens["spread"], published_value=item["published_value"]))
    sens_rows.append((iid, iso, t, kind, sens, item))
json.dump(golds, open(os.path.join(HERE, "debt_stab_golds.json"), "w"), indent=1)
json.dump({r[0]: r[4] for r in sens_rows}, open(os.path.join(HERE, "debt_stab_sensitivity.json"), "w"), indent=1)
for g in golds: print(g)
