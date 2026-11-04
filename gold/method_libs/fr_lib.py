"""Fiscal-ratio cluster. Frozen inputs only (WEO Oct 2025). Run with python3 -I.
EIR  : effective interest rate, real interest rate, growth-adjusted interest rate (Escolano 2010 Box 1 + eq 5; IMF 2013 Staff Guidance Note, DSA table footnote 3).
IREV : interest-to-revenue and debt-to-revenue ratios (IMF 2013 Staff Guidance Note, Annex on stress tests: 'debt-to-revenue ratio' burden indicator).
Conventions (percent):
  d_prev   gross debt/GDP at end of t-1 (GGXWDG_NGDP)           interest_t = GGXONLB_NGDP - GGXCNL_NGDP  (% GDP_t)
  gamma    nominal GDP growth = NGDP_t/NGDP_{t-1}-1              pi = GDP-deflator growth = NGDP_D_t/NGDP_D_{t-1}-1
  i_t      = interest_t/d_prev*(1+gamma)    (interest paid in t divided by debt stock at end of t-1, in levels)
  r_t      = (1+i_t)/(1+pi)-1               (Escolano Box 1: real interest rate)
  lam_t    = (i_t-gamma)/(1+gamma) = (1+r)/(1+g)-1          (Escolano eq 5; g = real growth)
  rev      = GGR_NGDP (general government revenue and grants, % GDP)
  IREV_int = interest_t/rev_t*100 ; IREV_debt = debt_t/rev_t*100 (end-year debt over same-year revenue, % of revenue)
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
DEBT = load("ggxwdg_ngdp"); PB = load("ggxonlb_ngdp"); OB = load("ggxcnl_ngdp"); NG = load("ngdp"); DEFL = load("ngdp_d")
REV = load("ggr_ngdp"); RG = load("ngdp_rpch")
ECON = sorted(k for k in DEBT if len(k) == 3)
def rate(iso, t):
    """dict with nominal effective rate i, real rate r, growth-adjusted lam (all in %), plus inputs; None if missing"""
    try:
        d0 = DEBT[iso][t - 1]; pb = PB[iso][t]; ob = OB[iso][t]; n1 = NG[iso][t]; n0 = NG[iso][t - 1]
        p1 = DEFL[iso][t]; p0 = DEFL[iso][t - 1]; g_real = RG[iso][t]; d1 = DEBT[iso][t]
    except KeyError:
        return None
    if d0 <= 0: return None
    gamma = n1 / n0 - 1.0; pi = p1 / p0 - 1.0; interest = pb - ob
    i = interest / d0 * (1 + gamma)
    r = (1 + i) / (1 + pi) - 1
    lam = (i - gamma) / (1 + gamma)
    # sensitivities of the nominal rate to the debt base
    i_avg = interest / (0.5 * (d0 / (1 + gamma) + d1))
    i_cur = interest / d1 if d1 > 0 else None
    return dict(iso=iso, year=t, d_prev=d0, d_t=d1, interest=interest, gamma=gamma, pi=pi, g_real=g_real,
                i=100 * i, r=100 * r, lam=100 * lam, i_minus_gamma=100 * (i - gamma),
                i_avgdebt=100 * i_avg, i_curdebt=None if i_cur is None else 100 * i_cur)
def ratios(iso, t):
    try:
        rev = REV[iso][t]; d1 = DEBT[iso][t]; pb = PB[iso][t]; ob = OB[iso][t]
    except KeyError:
        return None
    if rev <= 0: return None
    interest = pb - ob
    return dict(iso=iso, year=t, rev=rev, debt=d1, interest=interest, int_rev=100 * interest / rev, debt_rev=100 * d1 / rev)
