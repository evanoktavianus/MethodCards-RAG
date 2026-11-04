"""IMF reserve-adequacy metric for emerging markets. Method doc: e7c9a1d0 'IMF (2011) Assessing Reserve Adequacy' (weights printed in para 39):
 Fixed:    30% STD + 15% OPL + 10% M2 + 10% X
 Floating: 30% STD + 10% OPL +  5% M2 +  5% X       (STD short-term external debt, OPL other portfolio liabilities, M2 broad money, X exports of goods and services)
Frozen inputs (USD): STD = WDI DT.DOD.DSTC.CD (original maturity, public+private; doc asks remaining maturity -> approximation);
OPL = IMF IIP liabilities, portfolio investment (P_MV, API IMF.STA/IIP, pulled 2026-10-29); M2 = WDI FM.LBL.BMNY.CN / WDI PA.NUS.FCRF; X = WDI BX.GSR.GNFS.CD;
reserves = WDI FI.RES.TOTL.CD (gross, includes gold? FI.RES.TOTL.CD is total reserves incl. gold).  Ratio = reserves / metric * 100. Doc range 100-150 percent.
Exchange-rate regime (fixed vs floating) is an analyst choice (AREAER, not a public series): both are reported.
Run: python3 -I gold_scripts/ara_em/gold_ara_em.py"""
import csv, os, re, json, statistics
H = os.path.dirname(os.path.abspath(__file__)) + "/../../"
FX = H + "frozen_extra/"
CORP = H + "../../../corpus_index.json"
W = {"fixed": (.30, .15, .10, .10), "floating": (.30, .10, .05, .05)}
D = {}
for l in open(FX + "wdi_20261008_extract.psv").read().splitlines()[1:]:
    _, code, iso, per, val = l.split("|"); D[(code, iso, int(per[:4]))] = float(val)
for l in open(FX + "imf_iip_20261029_portfolio_other_liab.psv").read().splitlines()[1:]:
    _, code, iso, per, val = l.split("|"); D[("IIP." + code, iso, int(per[:4]))] = float(val)
for r in csv.DictReader(open(FX + "wdi_20261008_pa_nus_fcrf.csv")):
    for k, v in r.items():
        if k.isdigit() and v != "": D[("PA.NUS.FCRF", r["iso3"], int(k))] = float(v)
for l in open(FX + "wdi_20261008_ara_ig_extract.psv").read().splitlines():
    c, iso, ps, vs = l.split("|")
    if c == "DT.DOD.DSTC.CD":
        for p, v in zip(ps.strip("{}").split(","), vs.strip("{}").split(",")): D[(c, iso, int(p))] = float(v)

def metric(iso, y, regime):
    std, opl, m2lcu, fx, x = (D.get(("DT.DOD.DSTC.CD", iso, y)), D.get(("IIP.P_MV", iso, y)), D.get(("FM.LBL.BMNY.CN", iso, y)),
                             D.get(("PA.NUS.FCRF", iso, y)), D.get(("BX.GSR.GNFS.CD", iso, y)))
    if None in (std, opl, m2lcu, fx, x) or fx == 0: return None
    a, b, c, d = W[regime]
    return a * std + b * opl + c * m2lcu / fx + d * x

def ratio(iso, y, regime):
    m, r = metric(iso, y, regime), D.get(("FI.RES.TOTL.CD", iso, y))
    return None if not m or r is None else 100 * r / m

def published():
    T = {x["id"]: x["meta"] for x in json.load(open(CORP))}
    out = []
    for l in open(FX + "corpus_ara_text_blocks_20261030.tsv"):
        did, seq, t = l.rstrip("\n").split("\t")
        m = T.get(did); 
        if not m or not m.get("country_code") or not m.get("year"): continue
        for mm in re.finditer(r"(\d{2,3}) percent of (?:the )?(?:IMF'?s? |staff'?s? |Fund'?s? )?ARA", t):
            seg = t[max(0, mm.start() - 260): mm.end()]
            ys = [int(y) for y in re.findall(r"(?:end-|in |of )(20\d\d)", seg) if m["year"] - 2 <= int(y) <= m["year"]]
            out.append(dict(doc=did, iso=m["country_code"], report_year=m["year"], year=(ys[-1] if ys else None), published=int(mm.group(1)), text=seg[-200:]))
    return out

if __name__ == "__main__":
    rows = []
    for p in published():
        if p["year"] is None: continue
        for reg in W:
            v = ratio(p["iso"], p["year"], reg)
            if v is not None: p[reg] = round(v, 1)
        if "fixed" in p or "floating" in p: rows.append(p)
    print("published mentions with year and inputs:", len(rows))
    for reg in W:
        d = [abs(r[reg] / r["published"] - 1) for r in rows if reg in r]
        print(reg, "n", len(d), "within 10%:", sum(x <= .10 for x in d), "within 20%:", sum(x <= .20 for x in d), "median rel err", round(statistics.median(d), 3))
    best = [min((abs(r[g] / r["published"] - 1) for g in W if g in r)) for r in rows]
    print("best-of-two within 10%:", sum(x <= .1 for x in best), "of", len(rows), "(optimistic: regime unknown)")
    for r in rows[:40]: print(r["iso"], r["year"], r["published"], r.get("fixed"), r.get("floating"))
