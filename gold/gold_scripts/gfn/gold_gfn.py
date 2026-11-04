"""Gross financing needs (GFN). Method doc: 4315e3d9 'A Guide and Tool for Projecting Public Gross Financing Needs'.
GFN_t = overall deficit_t + amortization_t  (guide eq. 1-2; amortization of debt falling due in the year).
Frozen proxy: overall deficit = -GGXCNL_NGDP (WEO Oct 2025, general government);
amortization_t = [short-term debt + long-term debt with payment due within one year] at end t-1, central government
(PSD_2026-10-14: DP.DOD.DSTC.CR.CG + DP.DOD.DLTC.CR.L1.CG, national currency), over NGDP_t (WEO). Loans and securities both covered.
Run: python3 -I gold_scripts/gfn/gold_gfn.py  -> prints validation table against published DSA 'Public gross financing needs' rows."""
import csv, json, re, statistics, os
H = os.path.dirname(os.path.abspath(__file__)) + "/../../"
FX = H + "frozen_extra/"
CORP = H + "../../../corpus_index.json"

def weo(name):
    d = {}
    for r in csv.DictReader(open(FX + name)):
        for k, v in r.items():
            if k.isdigit() and v != "":
                d[(r["iso3"], int(k))] = float(v)
    return d
BAL, NGDP = weo("weo_oct2025_ggxcnl_ngdp.csv"), weo("weo_oct2025_ngdp.csv")

PSD = {}
for line in open(FX + "psd_20261014_maturity_extract.psv").read().splitlines()[1:]:
    _, code, iso, per, val = line.split("|")
    PSD[(code, iso, int(per[:4]))] = float(val)

def amort_gdp(iso, year, sector="CG"):
    st = PSD.get(("DP.DOD.DSTC.CR." + sector, iso, year - 1))
    l1 = PSD.get(("DP.DOD.DLTC.CR.L1." + sector, iso, year - 1))
    g = NGDP.get((iso, year))
    if st is None or l1 is None or not g: return None
    return 100 * (st + l1) / g

def gfn(iso, year, sector="CG"):
    a, b = amort_gdp(iso, year, sector), BAL.get((iso, year))
    if a is None or b is None: return None
    return -b + a

def published():
    T = {x["id"]: x["meta"] for x in json.load(open(CORP))}
    out = []
    for line in open(FX + "corpus_dsa_gfn_tables_20261030.tsv"):
        p = line.rstrip("\n").split("\t")
        if len(p) < 3 or p[0] not in T: continue
        m = T[p[0]]; iso = m.get("country_code"); yr = m.get("year")
        if not iso or not yr: continue
        rows = [[c.strip() for c in r.strip().strip("|").split("|")] for r in p[2].split("~") if r.strip().startswith("|")]
        hdr = next((r for r in rows[:8] if len([c for c in r if re.fullmatch(r"(19|20)\d\d", c)]) >= 4), None)
        g = next((r for r in rows if r and r[0].lower().startswith("public gross financing")), None)
        if not hdr or not g or len(hdr) != len(g): continue
        for h, v in zip(hdr, g):
            if re.fullmatch(r"(19|20)\d\d", h) and re.fullmatch(r"-?\d+\.\d", v) and int(h) <= yr - 1:
                out.append(dict(doc=p[0], title=m["publication_title"][:60], iso=iso, report_year=yr, year=int(h), published=float(v)))
    return out

if __name__ == "__main__":
    rows = []
    seen = set()
    for r in published():
        k = (r["iso"], r["year"], r["doc"])
        if k in seen: continue
        seen.add(k)
        c = gfn(r["iso"], r["year"])
        if c is None: continue
        r["recomputed"] = round(c, 2); r["amort"] = round(amort_gdp(r["iso"], r["year"]), 2); r["diff"] = round(c - r["published"], 2)
        rows.append(r)
    print("matched rows", len(rows), "countries", len({r['iso'] for r in rows}))
    d = [abs(r["diff"]) for r in rows]
    for t in (1, 2, 3): print("within", t, "pp:", sum(x <= t for x in d))
    print("median abs diff", statistics.median(d) if d else None)
    json.dump(rows, open(os.path.dirname(os.path.abspath(__file__)) + "/gfn_validation.json", "w"), indent=1)
    for r in sorted(rows, key=lambda r: abs(r["diff"]))[:25]: print(r["iso"], r["year"], r["report_year"], r["published"], r["recomputed"], r["diff"])
