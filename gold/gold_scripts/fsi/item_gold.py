"""Per-item gold for the reduced fiscal stress index. Usage (from the gold/ directory): python3 -I gold_scripts/fsi/item_gold.py ISO3 YEAR
Wraps fsi() of gold_fsi.py (unchanged). Prints JSON including per-indicator values, thresholds and breaches."""
import importlib.util, json, os, sys
D = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("gold_fsi", D + "/gold_fsi.py"); g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
def item_gold(iso, year): return g.fsi(iso, year)
if __name__ == "__main__":
    print(json.dumps(item_gold(sys.argv[1], int(sys.argv[2]))))
