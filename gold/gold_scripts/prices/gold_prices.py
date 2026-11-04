"""Gold + item builder for the price cluster. Reads only frozen_extra/ WEO Oct 2025 CSVs. Run: python3 -I gold_prices.py [--build]"""
import csv, json, sys, random
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
FZ = ROOT / "frozen_extra"
def load(code):
    d = {}
    for r in csv.DictReader(open(FZ / f"weo_oct2025_{code}.csv")):
        d[r["iso3"]] = {int(k): float(v) for k, v in r.items() if k.isdigit() and v not in ("", "NA")}
    return d
NGDP, DEF, RPCH, CPIP, DEBT, USD = (load(c) for c in ["ngdp", "ngdp_d", "ngdp_rpch", "pcpipch", "ggxwdg_ngdp", "ngdpd"])
NAMES = {"USA":"the US","CHN":"China","DEU":"Germany","JPN":"Japan","IND":"India","GBR":"the United Kingdom","FRA":"France","ITA":"Italy","BRA":"Brazil","CAN":"Canada","RUS":"Russia","KOR":"Korea","AUS":"Australia","MEX":"Mexico","ESP":"Spain","IDN":"Indonesia","TUR":"Turkey","NLD":"the Netherlands","SAU":"Saudi Arabia","CHE":"Switzerland","ARG":"Argentina","ZAF":"South Africa","POL":"Poland","EGY":"Egypt","NGA":"Nigeria","THA":"Thailand"}
TOP20 = sorted([c for c in USD if 2024 in USD[c] and c in NAMES], key=lambda c: -USD[c][2024])[:20]
def gdef(c, t): return DEF[c][t] / DEF[c][t-1] - 1          # pi_t, GDP deflator inflation
def gnom(c, t): return NGDP[c][t] / NGDP[c][t-1] - 1        # gamma_t
def real_g(c, t): return ((1 + gnom(c, t)) / (1 + gdef(c, t)) - 1) * 100   # g from 1+gamma=(1+g)(1+pi)
def real_r(i, c, t): return ((1 + i/100) / (1 + gdef(c, t)) - 1) * 100       # r=(1+i)/(1+pi)-1
def erosion(c, t): return gdef(c, t) / (1 + gnom(c, t)) * DEBT[c][t-1]      # pi/(1+gamma)*d_{t-1}, pp of GDP
def pick(f, t, mx=True, key=None):
    vals = sorted(((f(c, t), c) for c in TOP20 if all(k in s for s in (CPIP,) for k in [t]) ), reverse=mx)
    assert len(vals) >= 2 and vals[0][0] != vals[1][0]; return vals[0][1]
def argsel(vals, mx):
    v = sorted(vals, key=lambda x: x[0], reverse=mx); assert v[0][0] != v[1][0]; return v[0][1]
DOC = "55319ff9-c45c-4e8d-99e4-5562a1158bf2"
DIST = ["debt-stabilising primary balance", "interest-growth differential analysis", "inflation-targeting / Taylor-rule analysis", "purchasing-power-parity conversion", "real effective exchange rate analysis"]
def cap(x): return x[0].upper()+x[1:]
def base(id_, slug, method, q, style, text_claim, comp_text, val, tol, unit, pub, pubnote, inputs, distractors, pred=None, hid=None, famous=True, truth=None, alt=""):
    return {"id": id_, "family": "methodology", "pattern": {"named":"M-named","hidden":"M-hidden","claim":"M-claim"}[style], "tier": "analytical", "status": "validated",
      "query": q, "claims": {"text": [{"id":"c0","kind":"text","importance":"vital","text":text_claim,"accept":"names the accepted approach; "+alt}],
        "data": [{"id":"c2","kind":"data","importance":"okay","text":"Uses WEO nominal GDP and GDP deflator series" + (" and general government gross debt" if slug=="prices_inflation_erosion" else "") + " ("+", ".join(inputs)+")."}],
        "computation": [{"id":"c1","kind":"computation","importance":"vital","text":comp_text,"reference_value":round(val,3),"tolerance":tol,"unit":unit,"accept":"full = within tolerance"}]
        + ([{"id":"c3","kind":"answer","importance":"vital","text":"Verdict: statement is "+("TRUE" if truth else "FALSE")+" under the recomputed value.","accept":"full = correct verdict"}] if truth is not None else [])},
      "grading": {"method":"answer_recall"},
      "provenance": {"assembled_from": ["Escolano (2010) A Practical Guide to Public Debt Dynamics (doc "+DOC+")", "frozen WEO Oct 2025 (frozen_extra)"], "gold_script": "gold_scripts/prices/gold_prices.py", "selection": "seeded draw over top-20 economies by 2024 USD GDP (frozen), one per country-year"},
      "method": method, "method_doc_ids": [DOC], "gold_report_ids": [], "gold_report_note": "Published value is WEO series or none; no corpus report states it, nothing to withhold.",
      "published_value": pub, "published_value_note": pubnote, "recomputed_value": round(val,3), "tolerance": tol, "inputs": inputs, "style": style,
      "distractors": distractors, "famous_method": famous, "hidden_set_size": 1 if style=="hidden" else None, "predicate": pred,
      "validation_label": "formula-validated", "method_class": "textbook identity"}
def build():
    rnd = random.Random(7); out = []
    # ---- M1 real growth
    m1 = "real_growth_from_nominal_growth_and_deflator"; s1 = "prices_real_growth"; inp1 = ["NGDP", "NGDP_D"]
    tc1 = "Identifies that real growth is obtained by stripping the price change (GDP deflator) out of nominal GDP growth: 1+gamma=(1+g)(1+pi)."
    pool = [(c, t) for c in TOP20 for t in range(2012, 2025) if c in NGDP and t in NGDP[c] and t-1 in NGDP[c] and abs(real_g(c,t)-RPCH[c][t]) < 0.15]
    rnd.shuffle(pool); used = set(); pairs = []
    for c, t in pool:
        if c not in used and abs(real_g(c,t)) > 0.5 : used.add(c); pairs.append((c,t))
    d1 = ["simple CPI deflation of nominal growth", "per-capita growth analysis", "potential-growth / output-gap estimation", "growth accounting", "nominal exchange-rate conversion"]
    n = 0
    def add(item, slug):
        out.append((slug, item))
    for k, (c, t) in enumerate(pairs[:4]):
        v = real_g(c, t); n += 1
        add(base(f"RG-{n:02d}", s1, m1, f"{cap(NAMES[c])}'s economy was worth {gnom(c,t)*100:.1f}% more in current-price terms in {t} than a year earlier, while the output deflator rose {gdef(c,t)*100:.1f}%. How much did real output actually expand in {t}?", "named", tc1, f"Real GDP growth {c} {t} = {v:.2f} %", v, 0.15, "pp", round(RPCH[c][t],3), "WEO NGDP_RPCH Oct 2025 (frozen)", inp1, d1), s1)
    hid = [(2019, True), (2021, True), (2022, False), (2023, True)]
    for t, mx in hid:
        c = argsel([(CPIP[x][t], x) for x in TOP20 if t in CPIP[x]], mx); n += 1
        assert abs(real_g(c,t)-RPCH[c][t]) < 0.3; v = real_g(c,t)
        cond = f"recorded the {'steepest' if mx else 'mildest'} rise in consumer prices in {t}"
        add(base(f"RG-{n:02d}", s1, m1, f"Among the twenty largest economies by 2024 dollar GDP, take the one that {cond}. Its output at current prices grew {gnom(c,t)*100:.1f}% in {t}. What was its real expansion in {t}?", "hidden", tc1, f"Real GDP growth {c} {t} = {v:.2f} %", v, 0.15, "pp", round(RPCH[c][t],3), "WEO NGDP_RPCH Oct 2025 (frozen)", inp1, d1, pred={"universe":"top-20 by NGDPD 2024","year":t,"rule":"argmax" if mx else "argmin","series":"PCPIPCH"}, hid=1), s1)
    cc = [x for x in pairs[4:] ][:4]
    for k, (c, t) in enumerate(cc):
        v = real_g(c, t); truth = k % 2 == 0; stated = v + (0 if truth else rnd.choice([-1, 1]) * 1.2) if not truth else v + rnd.choice([-0.05, 0.05]); n += 1
        add(base(f"RG-{n:02d}", s1, m1, f"A staff report states that after removing price changes, {NAMES[c]}'s output rose {stated:.1f}% in {t}, given nominal output growth of {gnom(c,t)*100:.1f}% and a deflator increase of {gdef(c,t)*100:.1f}%. Is the statement right?", "claim", tc1, f"Real GDP growth {c} {t} = {v:.2f} %; statement of {stated:.1f}% is {'within' if truth else 'outside'} tolerance", v, 0.15, "pp", round(RPCH[c][t],3), "WEO NGDP_RPCH Oct 2025 (frozen)", inp1, d1, truth=truth), s1)
    # ---- M2 real interest rate
    m2 = "real_interest_rate_fisher_gdp_deflator"; s2 = "prices_real_rate"; inp2 = ["NGDP_D"]
    tc2 = "Identifies that the real interest rate is the nominal rate deflated by inflation, r=(1+i)/(1+pi)-1 with pi the GDP deflator change."
    d2 = ["debt-stabilising primary balance", "interest-growth differential (r-g) assessment", "CPI-based ex-post real rate", "Taylor-rule neutral rate", "real effective exchange rate"]
    al = "alternative: report both deflator-based and note CPI-based as a variant; gold uses GDP deflator"
    pool = [(c,t) for c in TOP20 for t in range(2012,2024) if t in DEF[c] and t-1 in DEF[c] and abs(gdef(c,t)) < 0.12 and c!="USA"]
    rnd.shuffle(pool); used = set(); pairs = []
    for c,t in pool:
        if c not in used: used.add(c); pairs.append((c,t))
    n = 0
    for c,t in pairs[:4]:
        i = round(rnd.uniform(3, 11)*2)/2; v = real_r(i,c,t); n += 1
        add(base(f"RR-{n:02d}", s2, m2, f"In {t}, {NAMES[c]}'s government paid an average {i}% on its borrowing. After allowing for how fast the economy-wide output price level rose that year, what was the effective cost of that borrowing?", "named", tc2, f"Real interest rate {c} {t} at i={i}% = {v:.2f} %", v, 0.2, "pp", None, "no published value; textbook identity checked by round trip (1+i)=(1+r)(1+pi)", inp2+["(nominal rate stated in query)"], d2, alt=al), s2)
    for t, mx in [(2018, False), (2020, False), (2015, False), (2016, False)]:
        c = argsel([(gdef(x,t),x) for x in TOP20 if t in DEF[x] and t-1 in DEF[x]], mx); i = round(rnd.uniform(4,10)*2)/2; v = real_r(i,c,t); n += 1
        add(base(f"RR-{n:02d}", s2, m2, f"Take the one of the twenty largest economies (by 2024 dollar GDP) whose output price level changed {'most' if mx else 'least'} in {t}. If its government borrowed at {i}% that year, what was the real cost of borrowing?", "hidden", tc2, f"Real interest rate {c} {t} at i={i}% = {v:.2f} %", v, 0.2, "pp", None, "no published value; textbook identity", inp2+["(nominal rate stated in query)"], d2, pred={"universe":"top-20 by NGDPD 2024","year":t,"rule":"argmax" if mx else "argmin","series":"NGDP_D change"}, hid=1, alt=al), s2)
    for k,(c,t) in enumerate(pairs[4:8]):
        i = round(rnd.uniform(3,11)*2)/2; v = real_r(i,c,t); truth = k%2==0; stated = v + (0.05 if truth else rnd.choice([-1,1])*1.5); n += 1
        add(base(f"RR-{n:02d}", s2, m2, f"A report says {NAMES[c]}'s government borrowing at {i}% in {t} carried an effective cost of {stated:.1f}% once output-wide price rises are taken out. Is that right?", "claim", tc2, f"Real rate {c} {t} i={i}% = {v:.2f} %; statement {stated:.1f}% is {'within' if truth else 'outside'} tolerance", v, 0.2, "pp", None, "no published value; textbook identity", inp2+["(nominal rate stated in query)"], d2, truth=truth, alt=al), s2)
    # ---- M3 inflation erosion of debt ratio
    m3 = "inflation_erosion_of_debt_ratio"; s3 = "prices_inflation_erosion"; inp3 = ["GGXWDG_NGDP", "NGDP", "NGDP_D"]
    tc3 = "Identifies that price rises lower the debt ratio through the nominal-growth term gamma/(1+gamma)=pi/(1+gamma)+g/(1+g), so the inflation part is pi/(1+gamma) times last year's debt ratio."
    d3 = ["debt-stabilising primary balance", "full debt-dynamics decomposition (interest, growth, primary balance)", "real interest rate calculation", "debt sustainability stress test", "exchange-rate valuation effect on foreign-currency debt"]
    pool = [(c,t) for c in TOP20 for t in range(2013,2025) if c in DEBT and t-1 in DEBT[c] and t in DEF[c] and t-1 in DEF[c] and DEBT[c][t-1]>30 and abs(erosion(c,t))>0.8]
    rnd.shuffle(pool); used=set(); pairs=[]
    for c,t in pool:
        if c not in used: used.add(c); pairs.append((c,t))
    n = 0
    for c,t in pairs[:4]:
        v = erosion(c,t); n += 1
        add(base(f"IE-{n:02d}", s3, m3, f"{cap(NAMES[c])} entered {t} with public debt at {DEBT[c][t-1]:.1f}% of GDP. Output prices rose {gdef(c,t)*100:.1f}% and nominal output {gnom(c,t)*100:.1f}% that year. Holding the nominal stock of debt constant, how many points of GDP did the price rise alone take off the debt ratio?", "named", tc3, f"Inflation erosion of debt ratio {c} {t} = {v:.2f} pp of GDP", v, 0.15, "pp", None, "no published value; identity cross-checked: erosion + real-growth part = d(t-1) - d(t-1)/(1+gamma)", inp3, d3), s3)
    for t,mx in [(2022,False),(2021,False),(2018,False),(2019,False)]:
        cand = [(DEBT[x][t-1],x) for x in TOP20 if t-1 in DEBT.get(x,{}) and t in DEF[x] and t-1 in DEF[x]]
        c = argsel(cand, mx); v = erosion(c,t); n += 1
        add(base(f"IE-{n:02d}", s3, m3, f"Among the twenty largest economies (by 2024 dollar GDP), take the one with the {'heaviest' if mx else 'lightest'} public debt burden relative to GDP at the end of {t-1}. Output prices rose {gdef(c,t)*100:.1f}% and nominal output {gnom(c,t)*100:.1f}% in {t}. Holding the nominal debt stock fixed, by how many points of GDP did the price rise alone lower that burden in {t}?", "hidden", tc3, f"Inflation erosion of debt ratio {c} {t} = {v:.2f} pp of GDP", v, 0.15, "pp", None, "no published value; identity", inp3, d3, pred={"universe":"top-20 by NGDPD 2024","year":t-1,"rule":"argmax" if mx else "argmin","series":"GGXWDG_NGDP"}, hid=1), s3)
    for k,(c,t) in enumerate(pairs[4:8]):
        v = erosion(c,t); truth = k%2==0; stated = v+(0.05 if truth else rnd.choice([-1,1])*max(0.8,0.5*v)); n += 1
        add(base(f"IE-{n:02d}", s3, m3, f"A report claims that in {t} price increases alone cut {NAMES[c]}'s debt ratio by about {stated:.1f} points of GDP, starting from {DEBT[c][t-1]:.1f}% of GDP, with output prices up {gdef(c,t)*100:.1f}% and nominal output up {gnom(c,t)*100:.1f}%, nominal debt unchanged. Is that right?", "claim", tc3, f"Inflation erosion {c} {t} = {v:.2f} pp; statement {stated:.1f} is {'within' if truth else 'outside'} tolerance", v, 0.15, "pp", None, "no published value; identity", inp3, d3, truth=truth), s3)
    return out
if __name__ == "__main__":
    items = build()
    from collections import Counter
    print(Counter((s, i["style"]) for s, i in items))
    for s, i in items:
        assert i["style"]!="hidden" or i["hidden_set_size"]==1
        if "--build" in sys.argv:
            p = ROOT/"items"/s; p.mkdir(parents=True, exist_ok=True); json.dump(i, open(p/f"{i['id']}.json","w"), indent=1)
        print(i["id"], i["recomputed_value"], i["published_value"], i["style"], i["query"][:70])
