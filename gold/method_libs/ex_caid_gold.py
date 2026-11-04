"""CAID: current account = national saving minus investment. Gold + items. python3 -I scripts/ex_caid_gold.py"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ex_lib import *
S = load(FX + "weo_oct2025_ngsd_ngdp.csv"); I = load(FX + "weo_oct2025_nid_ngdp.csv"); B = load(FX + "weo_oct2025_bca_ngdpd.csv")
names = names_pool(); allc = sorted(set(S) | set(B))
DOCS = ["8c217509-8bad-4e78-8ed3-6445dbd63e6a", "e5c757ab-1961-49e4-a76b-162d757fc70b"]

def decomp(c, y1, y2):
    ds = S[c][y2] - S[c][y1]; di = I[c][y2] - I[c][y1]
    ca1 = S[c][y1] - I[c][y1]; ca2 = S[c][y2] - I[c][y2]
    contrib_s, contrib_i = ds, -di
    driver = "saving" if abs(contrib_s) > abs(contrib_i) else "investment"
    return dict(dS=round(ds, 2), dI=round(di, 2), dCA=round(ds - di, 2), CA1=round(ca1, 2), CA2=round(ca2, 2), driver=driver,
                gap=round(abs(abs(contrib_s) - abs(contrib_i)), 2))

def cands():
    out = []
    for c in names:
        if c not in S or c not in I or c not in B: continue
        for y1 in range(2008, 2020):
            for y2 in (y1 + 4, y1 + 5):
                if y2 > 2023: continue
                ok = all(y in S[c] and y in I[c] and y in B[c] and abs(S[c][y] - I[c][y] - B[c][y]) < 0.05 for y in (y1, y2))
                if not ok: continue
                d = decomp(c, y1, y2)
                if abs(d["dCA"]) >= 2.5 and d["gap"] >= 1.5 and S[c][y1] > 5 and I[c][y1] > 5:
                    out.append((c, y1, y2, d))
    return out

def validate():
    """Published check: Romania 2019 Article IV box (doc 8c217509 p14): dCA -6.0, dS 1.1, dI 7.1 (2004-07); -3.8, -4.4, -0.6 (2014-18)."""
    r = {}
    for (a, b, pub) in [(2004, 2007, (-6.0, 1.1, 7.1)), (2014, 2018, (-3.8, -4.4, -0.6))]:
        d = decomp("ROU", a, b); got = (d["dCA"], d["dS"], d["dI"])
        r["%d-%d" % (a, b)] = dict(published=pub, recomputed=got, max_abs_diff=round(max(abs(x - y) for x, y in zip(pub, got)), 2),
                                   match=all(abs(x - y) <= 0.25 for x, y in zip(pub, got)))
    return r

def main():
    rng = random.Random(30)
    cs = cands(); rng.shuffle(cs)
    used = {}; picked = []
    # plan: 5 named, 5 hidden, 4 claim (2 true, 2 false), 14 items; balance drivers
    for c, y1, y2, d in cs:
        if used.get(c): continue
        used[c] = 1; picked.append((c, y1, y2, d))
        if len(picked) >= 40: break
    items = []; n = 0
    plan = ["named"] * 5 + ["hidden"] * 5 + ["claim_check"] * 4
    # pass 1: hidden need unique conditions; try candidates in order
    hid = []; rest = []
    for c, y1, y2, d in picked:
        if len(hid) < 5:
            conds, m = find_condition(c, y2, allc, rng)
            if conds: hid.append((c, y1, y2, d, conds)); continue
        rest.append((c, y1, y2, d))
    named = rest[:5]; claims = rest[5:9]
    def mk(style, c, y1, y2, d, query, extra=None):
        return dict(style=style, c=c, y1=y1, y2=y2, d=d, query=query, extra=extra or {})
    out = []
    qn = ["{n}'s current account balance moved from {a}% of GDP in {y1} to {b}% of GDP in {y2}. Looking at the domestic side of the economy rather than the trade accounts, what did most of the work in that shift?",
          "Between {y1} and {y2} the external position of {n} changed by {dca:+.1f} percentage points of GDP. Which domestic macro aggregate was mainly responsible, and how large was each side's contribution?",
          "Why did {n}'s current account balance change so much between {y1} and {y2}? Answer from the economy-wide accounts (income not spent, and what is spent on capital), with numbers."]
    for k, (c, y1, y2, d) in enumerate(named):
        out.append(mk("named", c, y1, y2, d, qn[k % 3].format(n=names[c], a=d["CA1"], b=d["CA2"], y1=y1, y2=y2, dca=d["dCA"])))
    for c, y1, y2, d, conds in hid:
        cond = " and ".join(phrase(*x) for x in conds)
        q = ("Among all economies in the IMF World Economic Outlook database, exactly one had %s in %d. What mainly drove the change in that economy's current account balance between %d and %d, in terms of its domestic accounts, and by how much?" % (cond, y2, y1, y2))
        out.append(mk("hidden", c, y1, y2, d, q, dict(conds=conds, set_size=len(members(conds, y2, allc)))))
    for k, (c, y1, y2, d) in enumerate(claims):
        true = k % 2 == 0
        driver = d["driver"] if true else ("investment" if d["driver"] == "saving" else "saving")
        mov = "improvement" if d["dCA"] > 0 else "deterioration"
        how = {"saving": "a change in national saving", "investment": "a change in domestic investment"}[driver]
        q = ("A staff report states that the %s in %s's current account balance between %d and %d was mainly the result of %s. Is that statement correct?" % (mov, names[c], y1, y2, how))
        out.append(mk("claim_check", c, y1, y2, d, q, dict(statement_true=true, stated_driver=driver)))
    for k, it in enumerate(out, 1):
        c, y1, y2, d = it["c"], it["y1"], it["y2"], it["d"]
        iid = "CAID-%02d" % k
        tgt = "driver is %s: saving moved %+.1f pp and investment %+.1f pp of GDP, so the balance changed %+.1f pp" % (d["driver"], d["dS"], d["dI"], d["dCA"])
        if it["style"] == "claim_check":
            verdict = "The statement is %s (the larger contribution came from %s)." % ("correct" if it["extra"]["statement_true"] else "incorrect", d["driver"])
        else:
            verdict = "Most of the change came from %s." % d["driver"]
        item = dict(
          id=iid, family="methodology", method="caid", style=it["style"], tier="multi_step", status="validated", query=it["query"],
          claims=dict(
            text=[dict(id="c1", kind="text", importance="vital", text="Identifies the national-accounts identity that the current account balance equals national saving minus domestic investment (so the change in the balance equals the change in saving minus the change in investment) as the way to attribute the change.",
                       accept="full = decomposes the change in the balance into the change in gross national saving and the change in investment (% of GDP); partial = discusses saving and investment qualitatively without the numbers; no = decomposes by trade components (exports, imports, income, transfers), by sector (government vs private) only, or by real exchange rate.",
                       supporting_passages=[DOCS[0] + "#romania2019_box1_dCA_eq_dS_minus_dI", DOCS[1] + "#weo2005_ch2_saving_investment"]),
                  dict(id="c4", kind="text", importance="vital", text=verdict, accept="verdict (which side dominated, or correct/incorrect for the statement) must match the recomputed decomposition.")],
            data=[dict(id="c5", kind="data", importance="okay", text="Uses gross national saving and total investment (% of GDP) and the current account balance (WEO Oct 2025: NGSD_NGDP, NID_NGDP, BCA_NGDPD).", accept="full = both saving and investment sourced; partial = one of them or a proxy; no = unrelated series.")],
            computation=[dict(id="c2", kind="computation", importance="vital", text="Change in gross national saving %s to %s: %+.1f pp of GDP." % (y1, y2, d["dS"]), accept="full = within +-0.3 pp; no otherwise.", target=d["dS"], tolerance_abs=0.3),
                         dict(id="c3", kind="computation", importance="vital", text="Change in investment %s to %s: %+.1f pp of GDP." % (y1, y2, d["dI"]), accept="full = within +-0.3 pp; no otherwise.", target=d["dI"], tolerance_abs=0.3),
                         dict(id="c6", kind="computation", importance="okay", text="Change in the current account balance: %+.1f pp of GDP (from %.1f%% to %.1f%%), equal to the change in saving minus the change in investment." % (d["dCA"], d["CA1"], d["CA2"]), accept="full = within +-0.3 pp.", target=d["dCA"], tolerance_abs=0.3)]),
          grading=dict(tolerance_abs_pp=0.3, tolerance_basis=0.2,
                       note="Vital computation tolerance +-0.3 pp of GDP. Gold: change in the current account balance = (S_y2 - I_y2) - (S_y1 - I_y1), S = WEO NGSD_NGDP, I = WEO NID_NGDP; driver = the side with the larger absolute contribution (saving contributes +dS, investment contributes -dI); the gap between the two contributions is at least 1.5 pp for every item. Only country-years where S - I equals the WEO current account balance (BCA_NGDPD) within 0.05 pp in both years are used.",
                       definitions="Saving and investment are gross national saving and total investment as % of GDP (WEO definitions). Current account in % of GDP is S - I by the national-accounts identity. A rising balance counts as an improvement."),
          provenance=dict(source="frozen WEO Oct 2025 (frozen_extra/)", generator="scripts/ex_caid_gold.py",
                          method_text="Romania 2019 Article IV, Box 1 (p14): 'DeltaCA = DeltaS - DeltaI' decomposition table; WEO Sept 2005 ch.2 (p112 ff.) saving-investment perspective",
                          validation="scripts/ex_caid_validation.json"),
          method_doc_ids=DOCS, gold_report_ids=[], published_value=None, recomputed_value=dict(dS=d["dS"], dI=d["dI"], dCA=d["dCA"], driver=d["driver"]),
          inputs=["NGSD_NGDP", "NID_NGDP", "BCA_NGDPD"], validation_label="formula-validated", method_kind="textbook identity", famous_method=True,
          distractors=["decomposing the change by trade components (exports, imports, net income, transfers)", "public versus private sector balances only", "real exchange rate or terms-of-trade explanation", "external debt dynamics"],
          answer_summary="%s (country %s, %d to %d; %s)" % (verdict, names[c], y1, y2, tgt), gold_script="scripts/ex_caid_gold.py",
          validation="Identity check against WEO BCA_NGDPD within 0.05 pp in both years; Romania published decomposition reproduced for 2004-07 (see scripts/ex_caid_validation.json).",
          answer_country=c, years=[y1, y2])
        if it["style"] == "hidden":
            item["hidden_set"] = dict(conditions=[list(x) for x in it["extra"]["conds"]], year=y2, set_size=it["extra"]["set_size"], answer=c)
            assert it["extra"]["set_size"] == 1
        if it["style"] == "claim_check": item["statement_true"] = it["extra"]["statement_true"]
        json.dump(item, open(ROOT + "/items/CAID/%s.json" % iid, "w"), indent=1)
    json.dump(validate(), open(ROOT + "/scripts/ex_caid_validation.json", "w"), indent=1)
    print(len(out), [ (o["style"], o["c"]) for o in out])
main()
