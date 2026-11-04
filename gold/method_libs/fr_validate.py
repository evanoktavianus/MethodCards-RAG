"""Self-check for EIR/IREV items: recompute every gold from frozen_extra/long_extract.csv (a different file than fr_lib's wide CSVs),
check hidden uniqueness (answer set size 1) from the long file, check claim truth. python3 -I scripts/fr_validate.py"""
import csv, glob, json, os
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
D = {}
for r in csv.DictReader(open(os.path.join(ROOT, "frozen_extra", "long_extract.csv"))):
    if r["release"].startswith("WEO"):
        D[(r["code"], r["iso3"], int(r["period"]))] = float(r["value"])
g = lambda c, i, t: D.get((c, i, t))
def eir(i, t):
    d0 = g("GGXWDG_NGDP", i, t - 1); pb = g("GGXONLB_NGDP", i, t); ob = g("GGXCNL_NGDP", i, t)
    n1, n0 = g("NGDP", i, t), g("NGDP", i, t - 1); p1, p0 = g("NGDP_D", i, t), g("NGDP_D", i, t - 1)
    gam = n1 / n0 - 1; pi = p1 / p0 - 1; nom = (pb - ob) / d0 * (1 + gam)
    return dict(nominal=100 * nom, real=100 * ((1 + nom) / (1 + pi) - 1), growth=100 * (nom - gam) / (1 + gam))
def irev(i, t):
    rev = g("GGR_NGDP", i, t); return dict(int_rev=100 * (g("GGXONLB_NGDP", i, t) - g("GGXCNL_NGDP", i, t)) / rev, debt_rev=100 * g("GGXWDG_NGDP", i, t) / rev)
isos = sorted({k[1] for k in D if len(k[1]) == 3 and k[0] == "GGXWDG_NGDP"})
bad = 0; n = 0
for f in sorted(glob.glob(os.path.join(ROOT, "items", "eir", "*.json")) + glob.glob(os.path.join(ROOT, "items", "irev", "*.json"))):
    d = json.load(open(f)); gd = d["gold"]; i, t = gd["iso3"], gd["year"]; n += 1
    kind = gd["kind"]; k2 = "nominal" if d["method"] == "eir" and kind in ("nominal", "numeric") and "interest rate of about" in d["query"] else kind
    if d["method"] == "eir":
        k2 = "growth" if (kind in ("growth", "verdict")) else "nominal"
        v = eir(i, t)[k2]
    else:
        k2 = "debt_rev" if ("debt" in d["query"].lower() and ("revenue" in d["query"].lower()) and ("share of" not in d["query"] and "absorbed" not in d["query"])) and "interest payments" not in d["query"] else "int_rev"
        v = irev(i, t)[k2]
    tol = d["claims"]["computation"][0]["tolerance_abs"]
    ok = abs(v - d["recomputed_value"]) <= (0.011 if d["method"] == "eir" else 0.051)
    msg = "ok" if ok else "GOLD MISMATCH %.3f vs %.3f" % (v, d["recomputed_value"])
    if d["style"] == "claim_check" and gd["kind"] == "numeric":
        ok2 = (abs(gd["stated"] - v) <= tol) == gd["truth"]; msg += " truth_ok" if ok2 else " TRUTH WRONG"; ok = ok and ok2
    if d["style"] == "claim_check" and gd["kind"] == "verdict":
        ok2 = ((v < 0) == ("below" in d["query"])) == gd["truth"]; msg += " verdict_ok" if ok2 else " VERDICT WRONG"; ok = ok and ok2
    if d["style"] == "hidden":
        hc = gd["hidden_condition"]; yr = t
        def feat(iso, u):
            if d["method"] == "eir":
                return [g("GGXWDG_NGDP", iso, yr - 1), g("NGDP_RPCH", iso, yr) if D.get(("NGDP_RPCH", iso, yr)) is not None else None, (100 * (g("NGDP_D", iso, yr) / g("NGDP_D", iso, yr - 1) - 1)) if g("NGDP_D", iso, yr) and g("NGDP_D", iso, yr - 1) else None][u]
            return [g("GGR_NGDP", iso, yr), g("GGXWDG_NGDP", iso, yr), g("GGXONLB_NGDP", iso, yr)][u]
        m = []
        for iso in isos:
            vals = [feat(iso, int(u)) for u in hc["windows"]]
            if all(x is not None for x in vals) and all(hc["windows"][u][0] <= feat(iso, int(u)) <= hc["windows"][u][1] for u in hc["windows"]): m.append(iso)
        ok3 = m == [i]; msg += " unique" if ok3 else " NOT UNIQUE %s" % m; ok = ok and ok3
    bad += (not ok); print(d["id"], i, t, round(v, 2), msg)
print("items", n, "problems", bad)
