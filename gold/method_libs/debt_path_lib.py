"""Debt-dynamics decomposition (Escolano 2010 eqs 24-28; IMF 2013 MAC DSA Annex I / Figure 1 footnotes 4-5), computed from frozen WEO Oct 2025.
All contributions are in percentage points of GDP in year t and use previous-year debt d_{t-1}:
  denominator  D = 1 + g + pi + g*pi = (1+g)(1+pi) = 1 + nominal growth
  interest effect (total)          = i/(1+gamma)*d_{t-1}   (Escolano eq. 26 first term) ;  i = interest_t / debt_{t-1} in levels
  inflation effect                 = -pi/(1+gamma)*d_{t-1}
  real growth effect               = -g/(1+g)*d_{t-1}      (Escolano eq. 26)  [IMF MAC footnote 5 uses -g/(1+g+pi+g*pi); both reported]
  real interest rate effect        = (i - pi)/(1+gamma)*d_{t-1} = r/(1+g)*d_{t-1} (Escolano eq 27/28);  IMF MAC footnote 5: (i - pi(1+g))/(1+gamma)*d_{t-1}
  primary deficit contribution     = -primary balance_t
  residual (no FX/other flows in the frozen data) = change in debt - primary deficit - automatic debt dynamics
"""
import csv, os
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
FX = ROOT + "/frozen_extra/"
def load(code):
    d = {}
    with open(FX + "weo_oct2025_%s.csv" % code) as f:
        for r in csv.DictReader(f):
            d[r['iso3']] = {int(k): float(v) for k, v in r.items() if k.isdigit() and v not in ('', None)}
    return d
S = {k: load(k) for k in ['ggxwdg_ngdp', 'ggxonlb_ngdp', 'ggxcnl_ngdp', 'ngdp', 'ngdp_r']}
def decomp(iso, t):
    try:
        D1 = S['ggxwdg_ngdp'][iso][t-1]; D0 = S['ggxwdg_ngdp'][iso][t]
        pb = S['ggxonlb_ngdp'][iso][t]; ob = S['ggxcnl_ngdp'][iso][t]
        Y0 = S['ngdp'][iso][t]; Y1 = S['ngdp'][iso][t-1]
        R0 = S['ngdp_r'][iso][t]; R1 = S['ngdp_r'][iso][t-1]
    except KeyError:
        return None
    gam = Y0/Y1 - 1; g = R0/R1 - 1; pi = (1+gam)/(1+g) - 1
    intr_gdp = pb - ob                       # interest paid, % of GDP_t
    i = (intr_gdp/100*Y0) / (D1/100*Y1)      # effective nominal interest rate on previous-year debt
    f = D1/(1+gam)
    out = dict(change=D0-D1, primary_deficit=-pb, interest_total=i*f, inflation=-pi*f,
               growth=-g/(1+g)*D1, real_interest=(i-pi)*f, real_interest_imf=(i-pi*(1+g))*f,
               growth_imf=-g*D1/(1+gam), eff_rate=i*100, defl=pi*100, g=g*100, gamma=gam*100, d_prev=D1, d=D0)
    out['auto'] = out['interest_total'] + out['inflation'] + out['growth']
    out['auto_imf'] = out['real_interest_imf'] + out['growth_imf']
    out['residual'] = out['change'] - out['primary_deficit'] - out['auto']
    return out
