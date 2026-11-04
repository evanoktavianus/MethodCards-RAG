"""Fiscal stress index. Method doc: b8ca4b08 'Assessing Fiscal Stress' (IMF WP/11/100), Tables 5a/5b + eq. 'Overall index = sum_g w_g sum_i w_ig d_i'.
Thresholds and index weights are printed (strict). Overall weights sum to 100 within AE and within EM. d_i = 1 when the indicator is on the risk side of
its threshold ('<' safe direction => risk if value >= threshold; '>' safe => risk if value < threshold).
Computable from frozen public series: 8 of 12 (AE) / 10 of 12 (EM) indicators. Not computable (no public series): long-term pension and health
projections, weighted average maturity, nonresident share (AE), dependency ratio 20 years ahead. Reduced index = sum(w_i d_i) / sum(w_i available) * 100.
Run: python3 -I gold_scripts/fsi/gold_fsi.py [ISO3 ...]"""
import csv, os, sys
H = os.path.dirname(os.path.abspath(__file__)) + "/../../"
FX = H + "frozen_extra/"
AE = set("AUS AUT BEL CAN HRV CYP CZE DNK EST FIN FRA DEU GRC HKG ISL IRL ISR ITA JPN KOR LVA LTU LUX MAC MLT NLD NZL NOR PRT PRI SMR SGP SVK SVN ESP SWE CHE TWN GBR USA AND".split())

def weo(name):
    d = {}
    for r in csv.DictReader(open(FX + name)):
        for k, v in r.items():
            if k.isdigit() and v != "": d[(r["iso3"], int(k))] = float(v)
    return d
DEBT, OB, PB = weo("weo_oct2025_ggxwdg_ngdp.csv"), weo("weo_oct2025_ggxcnl_ngdp.csv"), weo("weo_oct2025_ggxonlb_ngdp.csv")
SB, DEF, GR, NGDP = weo("weo_oct2025_ggsb_npgdp.csv"), weo("weo_oct2025_ngdp_d.csv"), weo("weo_oct2025_ngdp_rpch.csv"), weo("weo_oct2025_ngdp.csv")
X = {}
for f in ("psd_20261014_maturity_extract.psv", "wdi_20261008_extract.psv"):
    for l in open(FX + f).read().splitlines()[1:]:
        _, code, iso, per, val = l.split("|")
        X[(code, iso, int(per[:4]))] = float(val)

# (name, group, AE weight, AE threshold, EM weight, EM threshold, safe direction)
IND = [
 ("r_minus_g_5y", "basic", 14.9, 3.6, 11.3, 1.1, "<"), ("gross_debt", "basic", 7.3, 72.2, 2.5, 42.8, "<"), ("capb", "basic", 9.4, -4.2, 9.9, -0.5, ">"),
 ("gfn", "alm", 24.6, 17.2, 2.8, 20.6, "<"), ("st_debt_share", "alm", 2.8, 9.1, 9.2, 44.0, "<"), ("fx_debt_share", "alm", None, None, 9.9, 40.3, "<"),
 ("st_ext_debt_to_reserves", "alm", None, None, 19.1, 61.8, "<"), ("fertility_dev", "ltf", 2.4, 0.64, 5.2, 1.3, "<"),
]

def interest(iso, y):
    a, b = PB.get((iso, y)), OB.get((iso, y))
    return None if a is None or b is None else a - b

def rg(iso, y):
    vals = []
    for s in range(y, y + 5):
        i, dprev, p0, p1, g = interest(iso, s), DEBT.get((iso, s - 1)), DEF.get((iso, s - 1)), DEF.get((iso, s)), GR.get((iso, s))
        if None in (i, dprev, p0, p1, g) or dprev <= 0: return None
        pi = p1 / p0 - 1
        vals.append(((i / dprev) - pi) / (1 + pi) * 100 - g)
    return sum(vals) / 5

def st_gg(iso, y, lag=0):
    a, b = X.get(("DP.DOD.DSTC.CR.GG", iso, y - lag)), X.get(("DP.DOD.DLTC.CR.L1.GG", iso, y - lag))
    return None if a is None or b is None else a + b

def value(name, iso, y):
    if name == "r_minus_g_5y": return rg(iso, y)
    if name == "gross_debt": return DEBT.get((iso, y))
    if name == "capb":
        s, i = SB.get((iso, y)), interest(iso, y)
        return None if s is None or i is None else s + i
    if name == "gfn":
        s, ob, g = st_gg(iso, y, 1), OB.get((iso, y)), NGDP.get((iso, y))
        return None if None in (s, ob, g) else -ob + 100 * s / g
    if name == "st_debt_share":
        s, t = st_gg(iso, y), X.get(("DP.DOD.DECT.CR.GG", iso, y))
        return None if s is None or not t else 100 * s / t
    if name == "fx_debt_share":
        f, t = X.get(("DP.DOD.DECF.CR.GG", iso, y)), X.get(("DP.DOD.DECT.CR.GG", iso, y))
        return None if f is None or not t else 100 * f / t
    if name == "st_ext_debt_to_reserves":
        s, r = X.get(("DT.DOD.DSTC.CD", iso, y)), X.get(("FI.RES.TOTL.CD", iso, y))
        return None if s is None or not r else 100 * s / r
    if name == "fertility_dev":
        t = X.get(("SP.DYN.TFRT.IN", iso, y)); return None if t is None else abs(t - 2.1)

def fsi(iso, y):
    ae = iso in AE
    rows, tot_w, hit_w = [], 0.0, 0.0
    for name, grp, wa, ta, we, te, safe in IND:
        w, t = (wa, ta) if ae else (we, te)
        if w is None: continue
        v = value(name, iso, y)
        if v is None: continue
        d = int(v >= t) if safe == "<" else int(v < t)
        rows.append(dict(indicator=name, value=round(v, 2), threshold=t, breach=d, weight=w))
        tot_w += w; hit_w += w * d
    return dict(iso=iso, year=y, group="AE" if ae else "EM", n_indicators=len(rows), available_weight=round(tot_w, 1),
                raw_index=round(hit_w, 1), reduced_index=round(100 * hit_w / tot_w, 1) if tot_w else None, detail=rows)

if __name__ == "__main__":
    isos = sys.argv[1:] or ["BRA", "TUR", "ZAF", "MEX", "ITA", "JPN", "GRC", "USA", "ARG", "COL", "POL", "HUN"]
    for iso in isos:
        for y in (2008, 2015, 2022):
            r = fsi(iso, y)
            print(iso, y, r["group"], "n=%d avail_w=%s raw=%s reduced=%s" % (r["n_indicators"], r["available_weight"], r["raw_index"], r["reduced_index"]),
                  [d["indicator"] for d in r["detail"] if d["breach"]])
