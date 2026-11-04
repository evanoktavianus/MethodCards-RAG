"""Debt-stabilising primary balance (Escolano 2010, eqs 7-8, 20, 22; IMF 2013 Staff Guidance Note, DSA table footnote 9).
Frozen inputs only (WEO Oct 2025 vintage, frozen_extra/). Run with python3 -I; import via sys.path.insert(0, scripts dir).
Conventions (percent of GDP unless noted):
  d_prev  gross debt ratio at end of previous year (GGXWDG_NGDP)
  gamma   nominal GDP growth in year t = NGDP_t / NGDP_{t-1} - 1 (national currency)
  i_t     interest paid, % of GDP_t = primary balance - overall balance = GGXONLB_NGDP - GGXCNL_NGDP
  r_t     effective nominal interest rate = interest_t / debt_{t-1} (levels) = i_t/d_prev*(1+gamma)
  lam     (r-g)/(1+g) = (r-gamma)/(1+gamma) = i_t/d_prev - gamma/(1+gamma)   (Escolano eq 5)
  p*      = lam * d_prev   debt-stabilising primary balance (surplus positive)
"""
import csv, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
EXTRA = os.path.join(ROOT, "frozen_extra")

def load(code):
    out = {}
    with open(os.path.join(EXTRA, "weo_oct2025_%s.csv" % code.lower())) as f:
        rd = csv.reader(f); hdr = next(rd); yrs = [int(y) for y in hdr[2:]]
        for row in rd:
            d = {}
            for y, v in zip(yrs, row[2:]):
                if v not in ("", "n/a"):
                    try: d[y] = float(v)
                    except ValueError: pass
            out[row[0]] = d
    return out

DEBT = load("ggxwdg_ngdp"); PB = load("ggxonlb_ngdp"); OB = load("ggxcnl_ngdp"); NG = load("ngdp")
RG = load("ngdp_rpch"); INFL = load("pcpipch")

def inputs(iso, t):
    """returns dict or None if any needed value missing"""
    try:
        d_prev = DEBT[iso][t - 1]; d_t = DEBT[iso][t]
        pb = PB[iso][t]; ob = OB[iso][t]; n1 = NG[iso][t]; n0 = NG[iso][t - 1]
    except KeyError:
        return None
    gamma = n1 / n0 - 1.0
    i = pb - ob
    return dict(iso=iso, year=t, d_prev=d_prev, d_t=d_t, pb=pb, ob=ob, interest=i, gamma=gamma)

def stab(x):
    """x from inputs(); returns dict with r, lam, p_star, gap, ..."""
    g = x["gamma"]; d0 = x["d_prev"]
    r = x["interest"] / d0 * (1 + g)           # effective nominal rate (fraction)
    lam = (r - g) / (1 + g)
    p_star = lam * d0                           # % of GDP
    gap = x["pb"] - p_star                      # actual minus stabilising
    return dict(x, r=r, lam=lam, p_star=p_star, gap=gap, d_change_implied=-gap, d_change_actual=x["d_t"] - x["d_prev"])

def stab_general(d_prev, r_pct, g_pct, other=0.0):
    """report-style: inputs in percent. p* = d_prev*(r-g)/(1+g) (+ other identified flows)."""
    g = g_pct / 100.0; r = r_pct / 100.0
    return d_prev * (r - g) / (1 + g) + other

def project(d0, p, lam, n):
    """Escolano eq 7 with constant lam and constant primary balance p: path [d_0..d_n]"""
    path = [d0]
    for _ in range(n): path.append((1 + lam) * path[-1] - p)
    return path

def balance_for_target(d0, dN, lam, n):
    """Escolano eq 22: constant primary balance reaching dN after n periods"""
    return lam / ((1 + lam) ** (-n) - 1) * ((1 + lam) ** (-n) * dN - d0)
