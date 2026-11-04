"""Stress-test paths following the Staff Guidance Note, same inputs and baseline as gold_mac_dsa_stress.py (imported).
Rules taken from the Staff Guidance Note 2dea3fb1 (Table 3 block 138, example tables blocks 153-154, para 32 block 157):
 1. Growth shock: the spending-ratio effect is the CUMULATIVE level effect inside the two shock years (spending level fixed at baseline, GDP level lower by the
    accumulated growth and inflation shortfall), and it is ZERO after the shock years (the example table returns the primary balance to baseline in year 3).
    gold_mac_dsa_stress.py applies only the single-year differential (the base paths and shock sizes; its numbers are printed under the key 'v1').
 2. Combined shock: 'the largest effect of individual shocks on all relevant variables' (para 32): per variable the larger effect, not the sum. Growth, inflation,
    primary balance come from the growth leg; the interest effect is max(interest-shock size, 25bp-per-pp link of the growth leg), not their sum.
 3. Interest pass-through: the document applies 'nominal interest rate increases by X' but its example shows the effective rate rising gradually (about 25 to 70 percent
    of the shock over 2015-2018). 'full' = whole shock on the effective rate every year (as before); 'gradual' = schedule 0.25,0.40,0.65,0.70,0.75 read off the example.
"""
import importlib.util, os, sys
D = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("g1", D + "/gold_mac_dsa_stress.py"); g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
GRADUAL = [0.25, 0.40, 0.65, 0.70, 0.75]

def path2(iso, g_on=False, i_on=False, sched=None, sd=None):
    sched = sched or [1.0] * 5
    d = g.DEBT[(iso, g.BASE)]; level = 1.0; out = {}
    S = g.interest_shock(iso) if i_on else 0.0
    for n, y in enumerate(range(g.BASE + 1, g.END + 1)):
        gr, pi, i, pb = g.G[(iso, y)], g.infl(iso, y), g.eff_rate(iso, y), g.PB[(iso, y)]
        g2, pi2, pb2, link = gr, pi, pb, 0.0
        if g_on and n < 2:
            g2 = gr - sd; pi2 = pi - 0.25 * sd
            level *= (1 + g2 / 100) * (1 + pi2 / 100) / ((1 + gr / 100) * (1 + pi / 100))
            spend = g.REV[(iso, y)] - pb
            pb2 = pb - spend * (1 / level - 1)
            link = 0.25 * (pb - pb2)
        i2 = i + max(S * sched[n], link)
        d = d * (1 + i2 / 100) / ((1 + g2 / 100) * (1 + pi2 / 100)) - pb2 + g.resid(iso, y)
        out[y] = d
    return out

def run(iso):
    sd = g.sd10(iso); S = g.interest_shock(iso)
    b = path2(iso); gs = path2(iso, True, False, sd=sd); ish = path2(iso, False, True); comb = path2(iso, True, True, sd=sd)
    ishg = path2(iso, False, True, GRADUAL); combg = path2(iso, True, True, GRADUAL, sd=sd)
    e = g.END
    return dict(iso=iso, sd_growth=round(sd, 2), interest_shock_pp=round(S, 2), baseline_check_2030=round(b[e], 1), weo_2030=g.DEBT[(iso, e)],
                growth_shock_2030=round(gs[e], 1), interest_shock_2030=round(ish[e], 1), combined_2030=round(comb[e], 1),
                interest_shock_2030_gradual=round(ishg[e], 1), combined_2030_gradual=round(combg[e], 1))
if __name__ == "__main__":
    for iso in sys.argv[1:]: print(run(iso))
