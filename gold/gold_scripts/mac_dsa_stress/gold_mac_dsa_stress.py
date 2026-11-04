"""Standardized DSA stress tests. Method doc: 2dea3fb1 'IMF (2013) Staff Guidance Note for Public DSA in Market-Access Countries', para 29-32 + table of shocks:
 growth: real GDP growth reduced by 1 SD (10-year history) for 2 consecutive years; revenue ratio unchanged, non-interest spending LEVEL kept at baseline => primary balance falls;
         higher deficit => +25bp interest per 1 pp of GDP deterioration; inflation falls 0.25pp per 1pp lower growth.
 interest: nominal rate up by (max real rate over last 10y - average real rate over projection) or 200bp, whichever larger.
 primary balance: shock = max(50% of planned cumulative adjustment, half of 10y SD of baseline primary balance misses -> here half SD of the primary balance, see note).
Baseline from WEO Oct 2025: debt GGXWDG_NGDP, NGDP_RPCH, NGDP_D, GGXONLB_NGDP, GGXCNL_NGDP, GGR_NGDP. Stock-flow residual is added each year so that the baseline equals WEO debt (shocked paths then differ only by the shock). Debt recursion: d_t = d_{t-1}(1+i_t)/((1+g_t)(1+pi_t)) - pb_t, i_t = interest_t/d_{t-1}*(1+g)(1+pi) (effective rate implied by WEO).
Run: python3 -I gold_scripts/mac_dsa_stress/gold_mac_dsa_stress.py [ISO3 ...]   Output: debt 2030 baseline vs growth shock vs interest shock vs both (combined, no double count of growth effect on pb)."""
import csv, os, statistics, sys
H = os.path.dirname(os.path.abspath(__file__)) + "/../../"
FX = H + "frozen_extra/"
def weo(name):
    d = {}
    for r in csv.DictReader(open(FX + name)):
        for k, v in r.items():
            if k.isdigit() and v != "": d[(r["iso3"], int(k))] = float(v)
    return d
DEBT, G, DEF, PB, OB, REV = (weo("weo_oct2025_ggxwdg_ngdp.csv"), weo("weo_oct2025_ngdp_rpch.csv"), weo("weo_oct2025_ngdp_d.csv"),
                              weo("weo_oct2025_ggxonlb_ngdp.csv"), weo("weo_oct2025_ggxcnl_ngdp.csv"), weo("weo_oct2025_ggr_ngdp.csv"))
BASE, END = 2025, 2030
def infl(iso, y): return 100 * (DEF[(iso, y)] / DEF[(iso, y - 1)] - 1)
def eff_rate(iso, y):  # nominal effective interest rate, percent, on previous-year debt
    return (PB[(iso, y)] - OB[(iso, y)]) / DEBT[(iso, y - 1)] * 100

def resid(iso, y):
    # stock-flow residual so that the baseline recursion reproduces the WEO debt path exactly (other identified flows, valuation, privatization)
    g, pi, i, pb = G[(iso, y)], infl(iso, y), eff_rate(iso, y), PB[(iso, y)]
    return DEBT[(iso, y)] - (DEBT[(iso, y - 1)] * (1 + i / 100) / ((1 + g / 100) * (1 + pi / 100)) - pb)

def path(iso, g_shock=0.0, i_shock=0.0, pb_shock=0.0, sd=None, link=True):
    d = DEBT[(iso, BASE)]; out = {}
    cum_extra_def = 0.0
    for y in range(BASE + 1, END + 1):
        g, pi, i, pb = G[(iso, y)], infl(iso, y), eff_rate(iso, y), PB[(iso, y)]
        shock_g = g_shock * sd if (sd is not None and y - BASE <= 2) else 0.0
        # level effect on GDP => spending ratio rises (spending level fixed at baseline): pb falls by (noninterest spending ratio) * (1-(1+g')/(1+g))
        spend = REV[(iso, y)] - pb
        g2 = g - shock_g
        pi2 = pi - 0.25 * shock_g
        pb2 = pb - pb_shock
        if shock_g: pb2 -= spend * ((1 + g / 100) * (1 + pi / 100) / ((1 + g2 / 100) * (1 + pi2 / 100)) - 1)
        worsen = pb - pb2
        i2 = i + i_shock + (0.25 * worsen if link and worsen > 0 else 0.0)
        d = d * (1 + i2 / 100) / ((1 + g2 / 100) * (1 + pi2 / 100)) - pb2 + resid(iso, y)
        out[y] = d
    return out

def sd10(iso):
    v = [G[(iso, y)] for y in range(BASE - 9, BASE + 1) if (iso, y) in G]
    return statistics.pstdev(v) if len(v) >= 8 else None

def interest_shock(iso):
    real = [eff_rate(iso, y) - infl(iso, y) for y in range(BASE - 9, BASE + 1)]
    proj = [eff_rate(iso, y) - infl(iso, y) for y in range(BASE + 1, END + 1)]
    return max(max(real) - statistics.mean(proj), 2.0)

def run(iso):
    sd = sd10(iso)
    b = path(iso)
    gs = path(iso, g_shock=1.0, sd=sd)
    ish = path(iso, i_shock=interest_shock(iso))
    comb = path(iso, g_shock=1.0, i_shock=interest_shock(iso), sd=sd)
    return dict(iso=iso, sd_growth=round(sd, 2), interest_shock_pp=round(interest_shock(iso), 2), baseline_check_2030=round(b[END], 1), weo_2030=DEBT[(iso, END)],
                growth_shock_2030=round(gs[END], 1), interest_shock_2030=round(ish[END], 1), combined_2030=round(comb[END], 1))

if __name__ == "__main__":
    for iso in sys.argv[1:] or "BRA ZAF MEX COL IND TUR POL HUN ROU IDN PER CHL ITA FRA".split():
        try: print(run(iso))
        except Exception as e: print(iso, "ERR", repr(e))
