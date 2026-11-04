"""Authors items/EIR/*.json and items/IREV/*.json from the FROZEN data (WEO Oct 2025). python3 -I scripts/fr_items.py regenerates all.
Method kinds: EIR = effective / real / growth-adjusted interest rate on government debt; IREV = interest-to-revenue and debt-to-revenue ratios."""
import json, os, sys, random
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import fr_lib as F
ROOT = os.path.abspath(os.path.join(HERE, ".."))
NAMES = dict(POL="Poland", MEX="Mexico", BRA="Brazil", ZAF="South Africa", IDN="Indonesia", TUR="Turkey", CHL="Chile", COL="Colombia",
  PER="Peru", THA="Thailand", HUN="Hungary", ROU="Romania", CZE="Czechia", PRT="Portugal", ESP="Spain", ITA="Italy", FRA="France",
  DEU="Germany", GBR="the United Kingdom", USA="the United States", JPN="Japan", KOR="Korea", IND="India", PHL="the Philippines",
  EGY="Egypt", MAR="Morocco", KEN="Kenya", GHA="Ghana", NGA="Nigeria", PAK="Pakistan", LKA="Sri Lanka", JOR="Jordan", ARG="Argentina",
  URY="Uruguay", CRI="Costa Rica", HRV="Croatia", BGR="Bulgaria", SRB="Serbia", UKR="Ukraine", KAZ="Kazakhstan", AUS="Australia",
  CAN="Canada", SWE="Sweden", NOR="Norway", ISR="Israel", MYS="Malaysia", VNM="Vietnam", BGD="Bangladesh", TUN="Tunisia", GEO="Georgia")
EIR_DOCS = ["55319ff9-c45c-4e8d-99e4-5562a1158bf2", "2dea3fb1-758b-40a4-882b-59f953293e2d"]
IREV_DOCS = ["2dea3fb1-758b-40a4-882b-59f953293e2d", "afe8e3fb-67da-4099-9ee6-020466614eb8"]
PAGES = json.load(open(os.path.join(HERE, "fr_pages.json")))
def rnd(x, n=1): return round(x, n) + 0.0

# ---------------- eligibility ----------------
def eir_ok(iso, t):
    x = F.rate(iso, t)
    if not x or x["i_curdebt"] is None: return None
    if x["d_prev"] < 15 or not (0.8 <= x["i"] <= 12): return None
    if abs(x["pi"]) > 0.10 or abs(x["gamma"]) > 0.18: return None
    if abs(x["i_avgdebt"] - x["i"]) > 0.5 or abs(x["i_curdebt"] - x["i"]) > 0.5: return None
    if abs(x["i_minus_gamma"] - x["lam"]) > 0.5: return None
    return x
def irev_ok(iso, t):
    x = F.ratios(iso, t)
    if not x: return None
    if x["rev"] < 8 or x["debt"] < 10 or not (1.5 <= x["int_rev"] <= 40): return None
    return x

# ---------------- hidden-subject conditions ----------------
def eir_feats(iso, t):
    try:
        return (F.DEBT[iso][t - 1], F.RG[iso][t], 100 * (F.DEFL[iso][t] / F.DEFL[iso][t - 1] - 1))
    except KeyError: return None
EIR_FDESC = [("general government gross debt at the end of %d", "percent of GDP", -1), ("real GDP growth in %d", "percent", 0), ("GDP-deflator inflation in %d", "percent", 0)]
def irev_feats(iso, t):
    try: return (F.REV[iso][t], F.DEBT[iso][t], F.PB[iso][t])
    except KeyError: return None
IREV_FDESC = [("general government revenue in %d", "percent of GDP", 0), ("general government gross debt at the end of %d", "percent of GDP", 0), ("primary balance in %d", "percent of GDP", 0)]
def find_unique(iso, t, featfn):
    univ = {}
    for k in F.ECON:
        f = featfn(k, t)
        if f: univ[k] = f
    if iso not in univ: return None
    tgt = univ[iso]; n = len(tgt)
    import itertools
    for w in (3, 2, 1.5, 1, 0.75, 0.5):
        for use in list(itertools.combinations(range(n), 2)) + [tuple(range(n))]:
            win = {}
            for u in use:
                lo = int((tgt[u] - w) * 2) / 2.0 if tgt[u] - w >= 0 else -int((-(tgt[u] - w)) * 2 + 0.999) / 2.0
                win[u] = (lo, lo + 2 * w)
            if not all(win[u][0] <= tgt[u] <= win[u][1] for u in use): continue
            m = [k for k, v in univ.items() if all(win[u][0] <= v[u] <= win[u][1] for u in use)]
            if m == [iso]: return use, win, len(univ)
    return None
def describe(use, win, t, fdesc):
    parts = []
    for u in use:
        lab, unit, off = fdesc[u]
        parts.append("%s was between %g and %g %s" % (lab % (t + off), win[u][0], win[u][1], unit))
    return "Among the economies in the IMF World Economic Outlook database, take the one whose " + ", and whose ".join(parts)

# ---------------- claim builders ----------------
def mk_claims(method, kind, x, gold, tol, style, stated=None, truth=None, hidden_iso=None, hidden_name=None):
    t = x["year"]
    if method == "EIR":
        ident = {"nominal": "Identifies the effective interest rate on government debt (interest paid in the year divided by the debt stock at the end of the previous year; IMF 2013 Staff Guidance Note, DSA table footnote 3; Escolano 2010 Box 1 notation i_t) as the applicable measure.",
                 "real": "Identifies the real effective interest rate r = (1+i)/(1+pi) - 1, with i the interest paid in the year over the end-of-previous-year debt stock and pi GDP-deflator inflation (Escolano 2010, Box 1), as the applicable measure.",
                 "growth": "Identifies the growth-adjusted interest rate lambda = (i - gamma)/(1 + gamma) = (1+r)/(1+g) - 1 (Escolano 2010, eq. 5) with i the effective nominal interest rate (interest paid over previous-year-end debt) and gamma nominal GDP growth, as the applicable measure."}[kind]
        acc = {"nominal": "full = computes interest paid / previous-year-end debt (levels); partial = uses average or current-year debt, or the interest bill as a share of GDP without a debt base; no = uses a sovereign bond yield, a policy rate, or the debt-service ratio.",
               "real": "full = deflates the effective nominal rate by GDP-deflator inflation (or states an equivalent CPI-deflated rate within tolerance); partial = subtracts inflation without dividing by 1+pi (Fisher approximation) within tolerance; no = uses a bond yield or the nominal rate.",
               "growth": "full = (i - gamma)/(1+gamma) or the equivalent (1+r)/(1+g)-1; partial = plain i - gamma within tolerance; no = real rate alone or the stabilising primary balance."}[kind]
        inputs = ["GGXWDG_NGDP", "GGXONLB_NGDP", "GGXCNL_NGDP", "NGDP"] + (["NGDP_D"] if kind == "real" else ["NGDP_D"] if False else [])
        dtext = "Uses gross debt (% GDP) at the end of the previous year, interest paid (primary balance minus overall balance, % GDP) and nominal GDP growth (WEO Oct 2025: GGXWDG_NGDP, GGXONLB_NGDP, GGXCNL_NGDP, NGDP)" + (", plus the GDP deflator (NGDP_D)." if kind == "real" else ".")
        if kind == "real": inputs.append("NGDP_D")
        docs = EIR_DOCS
        unit = "% per year" if kind != "growth" else "percentage points"
    else:
        ident = {"int_rev": "Identifies the interest-to-revenue ratio (interest paid by general government as a share of government revenue, i.e. interest as % of GDP divided by revenue as % of GDP) as the applicable burden measure of repayment capacity (IMF 2013 Staff Guidance Note: debt burden indicators scale debt or debt service by GDP or government revenues).",
                 "debt_rev": "Identifies the debt-to-revenue ratio (gross debt as a share of government revenue, i.e. debt/GDP divided by revenue/GDP) as the applicable debt-burden indicator (IMF 2013 Staff Guidance Note, MAC DSA template: debt-to-revenue ratio)."}[kind]
        acc = {"int_rev": "full = interest/revenue in percent; partial = uses total debt service (interest plus amortisation) or interest/GDP; no = debt-to-revenue or debt-to-GDP.",
               "debt_rev": "full = end-of-year gross debt divided by the same year's revenue, in percent; partial = debt in years of revenue expressed correctly (e.g. 1.5 years = 150%); no = debt-to-GDP or interest-to-revenue."}[kind]
        inputs = ["GGR_NGDP", "GGXWDG_NGDP"] if kind == "debt_rev" else ["GGR_NGDP", "GGXONLB_NGDP", "GGXCNL_NGDP"]
        dtext = "Uses general government revenue and grants (% GDP) and " + ("gross debt (% GDP) (WEO Oct 2025: GGR_NGDP, GGXWDG_NGDP)." if kind == "debt_rev" else "interest paid = primary balance minus overall balance (% GDP) (WEO Oct 2025: GGR_NGDP, GGXONLB_NGDP, GGXCNL_NGDP).")
        docs = IREV_DOCS
        unit = "% of revenue"
    texts = [dict(id="c1", kind="text", importance="vital", text=ident, accept=acc, supporting_passages=["%s#p%s" % (d, PAGES[d]) for d in docs])]
    if style == "hidden":
        texts.append(dict(id="c0", kind="text", importance="vital", text="Identifies the economy meeting the stated conditions as %s." % hidden_name, accept="must name the correct economy (%s) before the computation." % hidden_iso))
    comp_text = "The value for %s in %d is about %s %s." % (hidden_name or "the economy", t, "%g" % gold, unit)
    comps = [dict(id="c2", kind="computation", importance="vital", text=comp_text, accept="full = within +-%g; partial = within +-%g; no = otherwise." % (tol, 2 * tol), target=gold, tolerance_abs=tol)]
    if style == "claim_check":
        texts.append(dict(id="c3", kind="text", importance="vital", text="Judges the statement %s." % ("correct" if truth else "incorrect"), accept="verdict must match."))
    data = [dict(id="c5", kind="data", importance="okay", text=dtext, accept="full = all inputs correctly sourced; partial = some inputs approximated; no = unrelated series.")]
    return dict(text=texts, data=data, computation=comps), inputs, docs

BASEDIST = {"EIR": ["sovereign bond yield or marginal borrowing cost (market rate, not interest paid over debt)", "policy interest rate", "interest bill as a share of GDP", "debt-stabilising primary balance or full debt-dynamics decomposition", "debt service (interest plus amortisation) ratios"],
            "IREV": ["debt-to-GDP or interest-to-GDP ratios", "debt-service-to-revenue (includes amortisation)", "gross financing needs", "present-value-of-debt-to-revenue indicators from the low-income-country framework", "primary balance or debt-stabilising balance"]}
CONV = {"EIR": ("Convention for the gold (WEO Oct 2025, general government): interest paid in year t = primary balance minus overall balance (% of GDP_t); effective interest rate i_t = interest_t / gross debt at end of t-1, in levels, i.e. (interest/GDP_t) x (1+gamma_t) / (debt/GDP)_{t-1}, gamma_t = NGDP_t/NGDP_{t-1} - 1; "
                "real rate r_t = (1+i_t)/(1+pi_t) - 1 with pi_t the growth of the GDP deflator NGDP_D; growth-adjusted rate lambda_t = (i_t - gamma_t)/(1 + gamma_t). Items are kept only where the average-debt and current-debt variants of i_t lie within 0.5 pp and (for lambda) plain i - gamma lies within 0.5 pp."),
        "IREV": ("Convention for the gold (WEO Oct 2025, general government): interest paid = primary balance minus overall balance (% of GDP); revenue = general government revenue and grants (GGR_NGDP, % of GDP); "
                 "interest-to-revenue = interest / revenue x 100; debt-to-revenue = end-of-year gross debt (% of GDP) / revenue (% of GDP) x 100, in percent of revenue.")}

def write(method, id_, style, tier, query, claims, inputs, docs, x, gold, tol, kind, extra_gold, answer_summary, rel=None):
    item = dict(id=id_, family="methodology", method=method.lower() if method == "EIR" else "irev", style=style, tier=tier, status="validated", query=query, claims=claims,
        grading=dict(tolerance_abs=tol, note="Verdicts exact. " + CONV[method], definitions=CONV[method]),
        provenance=dict(source="frozen WEO Oct 2025 (frozen_extra/)", generator="scripts/fr_items.py", method_text=("Escolano (2010) Box 1 and eq. 5; IMF 2013 Staff Guidance Note DSA table footnote 3" if method == "EIR" else "IMF 2013 Staff Guidance Note (annex on stress tests: debt-burden indicators; MAC DSA template debt-to-revenue)")),
        validation_label="formula-validated", method_kind="textbook identity", famous_method=True,
        method_doc_ids=docs, gold_report_ids=[], published_value=None, published_value_note="No corpus report states this country-year value for the identity on the frozen vintage; formula printed in the method document (gate a), inputs public (b), gold by script (c).",
        recomputed_value=gold, inputs=inputs, distractors=BASEDIST[method], answer_summary=answer_summary, gold_script="scripts/fr_items.py",
        gold=dict(extra_gold, value=gold, kind=kind))
    d = os.path.join(ROOT, "items", method.lower()); os.makedirs(d, exist_ok=True)
    json.dump(item, open(os.path.join(d, id_ + ".json"), "w"), indent=1, ensure_ascii=False)
    return item

def build():
    out = []
    # ----- EIR -----
    def pick_year(ok, iso, t0):
        for dt in (0, -1, 1, -2, 2, -3, 3, -4, 4):
            if 2011 <= t0 + dt <= 2024 and ok(iso, t0 + dt): return t0 + dt
        return None
    QN = {"nominal": "What average interest rate did the government of %s pay on its debt in %d?",
          "real": "What was the average inflation-adjusted interest rate that %s's government paid on its debt in %d?",
          "growth": "How much higher or lower was the interest rate the government of %s paid on its debt in %d than the nominal growth rate of its economy?"}
    VQ = {"nominal": " What average interest rate did its government pay on its debt in %d?", "real": " What was the average inflation-adjusted interest rate its government paid on its debt in %d?",
          "growth": " How much higher or lower was the interest rate its government paid on its debt in %d than the nominal growth rate of its economy?"}
    VAL = {"nominal": lambda x: x["i"], "real": lambda x: x["r"], "growth": lambda x: x["lam"]}
    n = 0
    named = [("nominal", "POL", 2019), ("nominal", "MEX", 2016), ("growth", "PHL", 2017), ("nominal", "IDN", 2018), ("growth", "BRA", 2018), ("growth", "PER", 2016)]
    for kind, iso, t0 in named:
        t = pick_year(eir_ok, iso, t0)
        if t is None: print("EIR named skip", iso); continue
        x = eir_ok(iso, t); g = rnd(VAL[kind](x), 2); n += 1
        cl, inp, docs = mk_claims("EIR", kind, x, g, 0.5, "named", hidden_name=NAMES[iso])
        out.append(write("EIR", "EIR-%02d" % n, "named", "single_step", QN[kind] % (NAMES[iso], t), cl, inp, docs, x, g, 0.5, kind, dict(iso3=iso, year=t, unit="%" if kind != "growth" else "pp"),
              "%s %d: interest %.2f%% GDP, previous debt %.1f, nominal growth %.2f%%, i=%.2f%%, r=%.2f%%, lambda=%.2f. Gold %.2f" % (iso, t, x["interest"], x["d_prev"], 100 * x["gamma"], x["i"], x["r"], x["lam"], g)))
    hidden = [("nominal", "COL", 2018), ("nominal", "THA", 2015), ("growth", "CZE", 2017), ("nominal", "ROU", 2016), ("growth", "KEN", 2014), ("growth", "PRT", 2017), ("nominal", "ISR", 2013), ("nominal", "EGY", 2019)]
    nh = 0
    for kind, iso, t0 in hidden:
        if nh >= 6: break
        for t in [t0] + [t0 + k for k in (-1, 1, -2, 2)]:
            if not eir_ok(iso, t): continue
            u = find_unique(iso, t, eir_feats)
            if u: break
        else: print("EIR hidden skip", iso); continue
        use, win, nu = u; x = eir_ok(iso, t); g = rnd(VAL[kind](x), 2); n += 1; nh += 1
        q = describe(use, win, t, EIR_FDESC) + "." + VQ[kind] % t
        cl, inp, docs = mk_claims("EIR", kind, x, g, 0.5, "hidden", hidden_iso=iso, hidden_name=NAMES[iso])
        out.append(write("EIR", "EIR-%02d" % n, "hidden", "multi_step", q, cl, inp, docs, x, g, 0.5, kind,
              dict(iso3=iso, year=t, unit="%" if kind != "growth" else "pp", hidden_condition=dict(fields=["d_prev", "real_growth", "deflator_inflation"], used=list(use), windows={str(k): list(v) for k, v in win.items()}, universe=nu, answer_set_size=1)),
              "%s %d hidden: i=%.2f%%, r=%.2f%%, lambda=%.2f. Gold %.2f" % (iso, t, x["i"], x["r"], x["lam"], g)))
    claims_spec = [("nominal", "CHL", 2016, True), ("nominal", "SRB", 2016, False), ("growth", "MAR", 2016, False), ("growth", "ESP", 2016, True)]
    for kind, iso, t0, truth in claims_spec:
        t = pick_year(eir_ok, iso, t0)
        if t is None: print("EIR claim skip", iso); continue
        x = eir_ok(iso, t); v = VAL[kind](x); n += 1
        if kind == "growth":
            # verdict on sign relative to growth
            above = v > 0
            if abs(v) < 0.5: print("EIR growth claim too close", iso); continue
            stated_above = above if truth else (not above)
            q = "A review of %s says: 'In %d the government's debt carried an interest rate that was %s the growth of the nominal economy.' Is this statement correct?" % (NAMES[iso], t, "above" if stated_above else "below")
            g = rnd(v, 2)
            cl, inp, docs = mk_claims("EIR", kind, x, g, 0.5, "claim_check", truth=truth, hidden_name=NAMES[iso])
            gold_extra = dict(iso3=iso, year=t, kind="verdict", truth=truth, unit="pp", answer="TRUE" if truth else "FALSE")
            out.append(write("EIR", "EIR-%02d" % n, "claim_check", "single_step", q, cl, inp, docs, x, g, 0.5, "verdict", gold_extra, "%s %d lambda %.2f (%s); statement %s" % (iso, t, v, "above" if above else "below", truth)))
        else:
            gv = rnd(v, 1)
            stated = gv + (0.1 if truth else (1.6 if gv < 6 else -1.6))
            stated = rnd(stated, 1)
            what = "an average interest rate of about %.1f%% on its debt" if kind == "nominal" else "an average inflation-adjusted interest rate of about %.1f%% on its debt"
            q = "A review of %s says: 'In %d the government paid %s.' Is this correct to within 0.5 percentage points?" % (NAMES[iso], t, what % stated)
            cl, inp, docs = mk_claims("EIR", kind, x, rnd(v, 2), 0.5, "claim_check", truth=truth, hidden_name=NAMES[iso])
            gold_extra = dict(iso3=iso, year=t, kind="numeric", truth=truth, stated=stated, unit="%", answer="TRUE" if truth else "FALSE")
            out.append(write("EIR", "EIR-%02d" % n, "claim_check", "single_step", q, cl, inp, docs, x, rnd(v, 2), 0.5, "numeric", gold_extra, "%s %d value %.2f stated %.1f -> %s" % (iso, t, v, stated, truth)))
    # ----- IREV -----
    n = 0
    QI = {"int_rev": "What share of the revenue of the government of %s went to paying interest on its debt in %d?",
          "debt_rev": "How large was the debt of the government of %s relative to its annual revenue at the end of %d?"}
    VI = {"int_rev": " What share of its government revenue went to paying interest on its debt in %d?", "debt_rev": " How large was its government debt relative to its annual government revenue at the end of %d?"}
    TOL = {"int_rev": 0.5}
    def tolfor(kind, v): return 0.5 if kind == "int_rev" else max(5.0, round(0.03 * v, 0))
    named = [("int_rev", "HUN", 2012), ("int_rev", "PER", 2019), ("int_rev", "TUR", 2021), ("debt_rev", "JPN", 2016), ("debt_rev", "DEU", 2015), ("debt_rev", "MYS", 2018)]
    for kind, iso, t0 in named:
        t = pick_year(irev_ok, iso, t0)
        if t is None: print("IREV named skip", iso); continue
        x = irev_ok(iso, t); g = rnd(x[kind], 1); tol = tolfor(kind, g); n += 1
        cl, inp, docs = mk_claims("IREV", kind, x, g, tol, "named", hidden_name=NAMES[iso])
        out.append(write("IREV", "IREV-%02d" % n, "named", "single_step", QI[kind] % (NAMES[iso], t), cl, inp, docs, x, g, tol, kind, dict(iso3=iso, year=t, unit="% of revenue"),
              "%s %d: interest %.2f%% GDP, revenue %.2f%% GDP, debt %.1f%% GDP -> int/rev %.1f%%, debt/rev %.1f%%. Gold %.1f" % (iso, t, x["interest"], x["rev"], x["debt"], x["int_rev"], x["debt_rev"], g)))
    hidden = [("int_rev", "COL", 2019), ("debt_rev", "FRA", 2017), ("int_rev", "ITA", 2014), ("debt_rev", "ZAF", 2016), ("int_rev", "PAK", 2015), ("debt_rev", "CAN", 2013), ("int_rev", "BGD", 2022), ("debt_rev", "PHL", 2020)]
    nh = 0
    for kind, iso, t0 in hidden:
        if nh >= 6: break
        for t in [t0] + [t0 + k for k in (-1, 1, -2, 2)]:
            if not irev_ok(iso, t): continue
            u = find_unique(iso, t, irev_feats)
            if u: break
        else: print("IREV hidden skip", iso); continue
        use, win, nu = u; x = irev_ok(iso, t); g = rnd(x[kind], 1); tol = tolfor(kind, g); n += 1; nh += 1
        q = describe(use, win, t, IREV_FDESC) + "." + VI[kind] % t
        cl, inp, docs = mk_claims("IREV", kind, x, g, tol, "hidden", hidden_iso=iso, hidden_name=NAMES[iso])
        out.append(write("IREV", "IREV-%02d" % n, "hidden", "multi_step", q, cl, inp, docs, x, g, tol, kind,
              dict(iso3=iso, year=t, unit="% of revenue", hidden_condition=dict(fields=["revenue", "debt", "primary_balance"], used=list(use), windows={str(k): list(v) for k, v in win.items()}, universe=nu, answer_set_size=1)),
              "%s %d hidden: int/rev %.1f%%, debt/rev %.1f%%. Gold %.1f" % (iso, t, x["int_rev"], x["debt_rev"], g)))
    claims_spec = [("int_rev", "MEX", 2017, True), ("debt_rev", "ESP", 2014, False), ("int_rev", "EGY", 2016, False), ("debt_rev", "AUS", 2019, True)]
    for kind, iso, t0, truth in claims_spec:
        t = pick_year(irev_ok, iso, t0)
        if t is None: print("IREV claim skip", iso); continue
        x = irev_ok(iso, t); v = x[kind]; gv = rnd(v, 1); tol = tolfor(kind, gv); n += 1
        step = 0.1 if kind == "int_rev" else 1.0
        off = (step if truth else (v * 0.35 if kind == "debt_rev" else 5.0))
        stated = rnd(gv + (off if (truth or True) else 0), 0 if kind == "debt_rev" else 1)
        if kind == "debt_rev" and truth: stated = rnd(gv, 0)
        if kind == "int_rev" and truth: stated = rnd(gv + 0.1, 1)
        tolq = "within half a percentage point" if kind == "int_rev" else "within 5 percentage points"
        if kind == "int_rev":
            q = "A review of %s says: 'In %d interest payments absorbed about %.1f%% of government revenue.' Is this correct to within half a percentage point?" % (NAMES[iso], t, stated)
        else:
            q = "A review of %s says: 'At the end of %d government debt stood at about %d%% of annual government revenue.' Is this correct to within 5 percentage points?" % (NAMES[iso], t, stated)
        ok = abs(stated - v) <= (0.5 if kind == "int_rev" else 5.0)
        if ok != truth: print("IREV claim truth mismatch", iso, v, stated, truth); n -= 1; continue
        cl, inp, docs = mk_claims("IREV", kind, x, gv, 0.5 if kind == "int_rev" else 5.0, "claim_check", truth=truth, hidden_name=NAMES[iso])
        out.append(write("IREV", "IREV-%02d" % n, "claim_check", "single_step", q, cl, inp, docs, x, gv, 0.5 if kind == "int_rev" else 5.0, "numeric",
              dict(iso3=iso, year=t, truth=truth, stated=stated, unit="% of revenue", answer="TRUE" if truth else "FALSE"), "%s %d value %.2f stated %s -> %s" % (iso, t, v, stated, truth)))
    return out

if __name__ == "__main__":
    items = build()
    from collections import Counter
    for m in ("eir", "irev"):
        its = [i for i in items if i["method"] == m]
        print(m, len(its), Counter(i["style"] for i in its), Counter(i["gold"]["iso3"] for i in its).most_common(3))
