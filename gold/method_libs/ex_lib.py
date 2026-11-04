"""Shared helpers for the external cluster (CAID, REER). python3 -I; reads only frozen files."""
import csv, os, random, math
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FX = ROOT + "/frozen_extra/"
REF = os.path.abspath(ROOT + "/../../../release/official_benchmark/reference_data/")

def load(path):
    d = {}
    for r in csv.DictReader(open(path)):
        v = {}
        for k, x in r.items():
            if k.isdigit() and x not in ("", "n/a", "null"):
                try: v[int(k)] = float(x)
                except ValueError: pass
        d[r["iso3"]] = v
    return d

def names_pool():
    n = {}
    for r in csv.DictReader(open(REF + "/wb_classifications.csv")):
        if r["income_group"].strip() not in ("Aggregates", ""):
            n[r["iso3"]] = r["name"]
    return n

IND = {  # indicator -> (file, phrase builder)
 "BCA_NGDPD": FX + "weo_oct2025_bca_ngdpd.csv",
 "NGDP_RPCH": FX + "weo_oct2025_ngdp_rpch.csv",
 "PCPIPCH": FX + "weo_oct2025_pcpipch.csv",
 "GGXWDG_NGDP": FX + "weo_oct2025_ggxwdg_ngdp.csv",
 "NGDPDPC": FX + "weo_oct2025_ngdpdpc.csv",
 "LUR": FX + "weo_oct2025_lur.csv",
}
_cache = {}
def ind(code):
    if code not in _cache: _cache[code] = load(IND[code])
    return _cache[code]

PHR = {
 "BCA_NGDPD": ("a current account {cmp} {thr}% of GDP", "balance"),
 "NGDP_RPCH": ("real GDP growth {cmp} {thr}%", ""),
 "PCPIPCH": ("average consumer price inflation {cmp} {thr}%", ""),
 "GGXWDG_NGDP": ("general government gross debt {cmp} {thr}% of GDP", ""),
 "NGDPDPC": ("GDP per capita {cmp} US$ {thr}", ""),
 "LUR": ("an unemployment rate {cmp} {thr}%", ""),
}
def phrase(code, op, thr):
    t = PHR[code][0]
    if code == "BCA_NGDPD":
        return ("a current account surplus above %g%% of GDP" % thr) if op == ">" else ("a current account balance below %g%% of GDP" % thr)
    cmp = "above" if op == ">" else "below"
    return t.format(cmp=cmp, thr=("{:,}".format(int(thr)) if code == "NGDPDPC" else thr))

def members(conds, year, pool):
    out = []
    for c in pool:
        ok = True
        for code, op, thr in conds:
            v = ind(code).get(c, {}).get(year)
            if v is None or not ((v > thr) if op == ">" else (v < thr)): ok = False; break
        if ok: out.append(c)
    return out

def find_condition(country, year, pool, rng, codes=("BCA_NGDPD","NGDP_RPCH","PCPIPCH","GGXWDG_NGDP","NGDPDPC","LUR")):
    """Greedy: add threshold conditions (rounded) the country satisfies until the set has size exactly 1 (max 3)."""
    for _ in range(200):
        cs = rng.sample(list(codes), 3)
        conds = []
        for code in cs:
            v = ind(code).get(country, {}).get(year)
            if v is None: break
            if code == "NGDPDPC": step = 1000
            elif code == "GGXWDG_NGDP": step = 5
            else: step = 1
            if rng.random() < .5:
                thr = math.floor(v / step) * step; op = ">"
            else:
                thr = math.ceil(v / step) * step; op = "<"
            if (v > thr) if op == ">" else (v < thr):
                conds.append((code, op, thr))
            else: break
            m = members(conds, year, pool)
            if m == [country]: return conds, m
        # fallthrough: try again
    return None, None
