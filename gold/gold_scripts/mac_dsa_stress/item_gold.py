"""Per-item gold for standardized stress tests. Usage (from the gold/ directory): python3 -I gold_scripts/mac_dsa_stress/item_gold.py ISO3
Wraps run() of gold_mac_dsa_stress_v2.py (cumulative growth-shock effect and combined rule as in the Staff Guidance Note; see its docstring). gold_mac_dsa_stress.py (single-year differential) gives the base paths; its numbers are printed under the key 'v1'. Base year 2025, end year 2030, WEO Oct 2025."""
import importlib.util, json, os, sys
D = os.path.dirname(os.path.abspath(__file__))
def _load(n, f):
    s = importlib.util.spec_from_file_location(n, D + "/" + f); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
g1 = _load("gold_mac", "gold_mac_dsa_stress.py"); g2 = _load("gold_mac_v2", "gold_mac_dsa_stress_v2.py")
def item_gold(iso):
    r = g2.run(iso); r["debt_2025"] = g1.DEBT[(iso, g1.BASE)]
    v = g1.run(iso); r["v1"] = {k: v[k] for k in ("growth_shock_2030", "interest_shock_2030", "combined_2030")}
    return r
if __name__ == "__main__":
    print(json.dumps(item_gold(sys.argv[1])))
