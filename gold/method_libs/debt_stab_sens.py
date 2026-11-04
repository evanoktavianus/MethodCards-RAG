"""Interest-definition sensitivity for the debt-stabilising primary balance (frozen WEO Oct 2025).
a: r = interest / previous-year debt (canonical, validated against published DSA tables)
b: r = interest / average of previous-year and current-year debt (levels)
c: r = interest / current-year debt (levels; same ratio of GDP-shares)
d: real-rate form: real rate from effective nominal rate and GDP-deflator growth (NGDP_D index), real growth NGDP_RPCH
Run with python3 -I; imported by debt_stab_items.py."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import debt_stab_lib as L
DEFL = L.load("ngdp_d")
LAB = dict(a="interest / previous-year debt (canonical)", b="interest / average of previous- and current-year debt",
           c="interest / current-year debt", d="real-rate form with GDP-deflator growth and real growth (WEO NGDP_RPCH, NGDP_D)")

def lams(iso, t):
    x = L.inputs(iso, t); g = x["gamma"]; d0 = x["d_prev"]; d1 = x["d_t"]; i = x["interest"]
    out = {}
    ra = i * (1 + g) / d0;                     out["a"] = (ra - g) / (1 + g)
    rb = i / ((d0 / (1 + g) + d1) / 2);        out["b"] = (rb - g) / (1 + g)
    rc = i / d1;                               out["c"] = (rc - g) / (1 + g)
    gr = L.RG[iso][t] / 100.0; defl = DEFL[iso][t] / DEFL[iso][t - 1] - 1.0
    rreal = (1 + ra) / (1 + defl) - 1.0;       out["d"] = (rreal - gr) / (1 + gr)
    return x, out

def outcome(kind, x, lam, ex, shown=None):
    d0 = x["d_prev"]; p = lam * d0; gap = x["pb"] - p
    if kind in ("required", "numeric"): return p
    if kind in ("gap", "verdict"): return gap
    if kind == "path": return L.project(x["d_t"], x["pb"], lam, ex["n"])[-1]
    if kind == "target": return L.balance_for_target(x["d_t"], ex["target"], lam, ex["n"])

def sensitivity(iso, t, kind, ex, shown=None):
    x, lm = lams(iso, t)
    vals = {k: outcome(kind, x, v, ex) for k, v in lm.items()}
    out = dict(values={k: round(v, 3) for k, v in vals.items()}, lambda_by_definition={k: round(v, 5) for k, v in lm.items()},
               definitions=LAB, spread=round(max(vals.values()) - min(vals.values()), 3),
               max_abs_dev_from_canonical=round(max(abs(v - vals["a"]) for v in vals.values()), 3))
    if kind == "verdict":
        out["verdict_flips"] = sorted(k for k, v in vals.items() if (v > 0) != (vals["a"] > 0))
    if kind == "numeric" and shown is not None:
        out["stated_within_0.25"] = {k: abs(shown - v) <= 0.25 for k, v in vals.items()}
    if kind == "path":
        out["direction_flips"] = sorted(k for k, v in vals.items() if (v > x["d_t"]) != (vals["a"] > x["d_t"]))
    return out
