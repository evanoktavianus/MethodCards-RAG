"""Per-item gold for the long-term debt-target adjustment (emerging markets). Usage (from the gold/ directory): python3 -I gold_scripts/debt_target_adjustment/item_gold.py ISO3
Runs gold_debt_target_em.py (unchanged, output suppressed) and returns the published table row and the recomputed constant 2020-30 primary balance."""
import contextlib, io, json, os, runpy, sys
D = os.path.dirname(os.path.abspath(__file__))
def all_rows():
    with contextlib.redirect_stdout(io.StringIO()):
        g = runpy.run_path(D + "/gold_debt_target_em.py")
    out = {}
    for name, d, c, ar, c20, adj in g["rows"]:
        iso = g["NM"].get(name.strip())
        if not iso: continue
        try: p = g["solve"](iso, float(d), float(c))
        except KeyError: continue
        out[iso] = dict(iso3=iso, debt_2014=float(d), capb_2014=float(c), published_capb_2020_30=float(c20), recomputed_capb_2020_30=round(p, 3),
                        improvement_vs_2014=round(p - float(c), 3), target_debt=40.0 if float(d) > 40 else float(d))
    return out
if __name__ == "__main__":
    print(json.dumps(all_rows()[sys.argv[1]]))
