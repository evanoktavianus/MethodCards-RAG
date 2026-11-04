"""Per-item gold for the reserve adequacy metric for emerging markets. Usage (from the gold/ directory): python3 -I gold_scripts/ara_em/item_gold.py ISO3 YEAR
Wraps ratio() of gold_ara_em.py (unchanged); prints reserves as percent of the metric under the fixed and the floating weights (regime is a free choice)."""
import importlib.util, json, os, sys
D = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("gold_ara", D + "/gold_ara_em.py"); g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
def item_gold(iso, year):
    return dict(iso3=iso, year=year, fixed=round(g.ratio(iso, year, "fixed"), 2), floating=round(g.ratio(iso, year, "floating"), 2),
                reserves_usd=g.D.get(("FI.RES.TOTL.CD", iso, year)), std_usd=g.D.get(("DT.DOD.DSTC.CD", iso, year)), opl_usd=g.D.get(("IIP.P_MV", iso, year)),
                exports_usd=g.D.get(("BX.GSR.GNFS.CD", iso, year)))
if __name__ == "__main__":
    print(json.dumps(item_gold(sys.argv[1], int(sys.argv[2]))))
