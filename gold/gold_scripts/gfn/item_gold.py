"""Per-item gold for gross financing needs. Usage (from the gold/ directory): python3 -I gold_scripts/gfn/item_gold.py ISO3 YEAR
Wraps gold_gfn.py (unchanged). Prints JSON: gfn, amortization, overall deficit, all in percent of GDP."""
import importlib.util, json, os, sys
D = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("gold_gfn", D + "/gold_gfn.py"); g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
def item_gold(iso, year):
    a, b, t = g.amort_gdp(iso, year), g.BAL.get((iso, year)), g.gfn(iso, year)
    return dict(iso3=iso, year=year, gfn=round(t, 3), amortization=round(a, 3), overall_deficit=round(-b, 3))
if __name__ == "__main__":
    print(json.dumps(item_gold(sys.argv[1], int(sys.argv[2]))))
