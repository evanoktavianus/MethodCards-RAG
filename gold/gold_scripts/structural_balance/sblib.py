"""Shared helpers: frozen WEO readers, HP filter (pure python), cyclically adjusted balance. python3 -I safe via sys.path insert."""
import csv, math, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
EXTRA = os.path.join(ROOT, "frozen_extra")
REF = os.path.abspath(os.path.join(ROOT, "..", "..", "..", "release", "official_benchmark", "reference_data"))

def load(code):
    """returns {iso3: {year: float}} from frozen_extra (superset of release freeze)."""
    p = os.path.join(EXTRA, "weo_oct2025_%s.csv" % code.lower())
    out = {}
    with open(p) as f:
        r = csv.reader(f); h = next(r)
        yrs = [int(x) for x in h[2:]]
        for row in r:
            d = {}
            for y, v in zip(yrs, row[2:]):
                if v not in ("", "n/a"):
                    try: d[y] = float(v)
                    except ValueError: pass
            out[row[0]] = d
    return out

def solve(A, b):
    n = len(b); M = [A[i][:] + [b[i]] for i in range(n)]
    for i in range(n):
        p = max(range(i, n), key=lambda k: abs(M[k][i])); M[i], M[p] = M[p], M[i]
        for k in range(i + 1, n):
            f = M[k][i] / M[i][i]
            if f:
                for j in range(i, n + 1): M[k][j] -= f * M[i][j]
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        x[i] = (M[i][n] - sum(M[i][j] * x[j] for j in range(i + 1, n))) / M[i][i]
    return x

def hp_trend(y, lam=100.0):
    """standard Hodrick-Prescott trend: min sum (y-t)^2 + lam*sum (dd t)^2"""
    n = len(y); A = [[0.0] * n for _ in range(n)]
    for i in range(n): A[i][i] += 1.0
    for i in range(n - 2):
        for (j, c) in ((i, 1.0), (i + 1, -2.0), (i + 2, 1.0)):
            for (k, d) in ((i, 1.0), (i + 1, -2.0), (i + 2, 1.0)):
                A[j][k] += lam * c * d
    return solve(A, list(y))

def hp_gap(rgdp, y0, y1, lam=100.0):
    """output gap in % of potential (100*(Y/Y* -1)) from log real GDP over years y0..y1 inclusive."""
    ys = list(range(y0, y1 + 1)); ly = [math.log(rgdp[y]) for y in ys]
    t = hp_trend(ly, lam)
    return {y: 100.0 * (math.exp(l - tt) - 1.0) for y, l, tt in zip(ys, ly, t)}

def contiguous(d, y0, y1):
    return all(y in d for y in range(y0, y1 + 1))

def cab_pot(rev, exp, gap_pct, e_r=1.0, e_g=0.0):
    """cyclically adjusted balance, % of potential GDP. rev,exp in % of GDP; gap_pct = 100*(Y/Y*-1).
    R* = R*(Y*/Y)^e_r ; G* = G*(Y*/Y)^e_g ; divide by Y*:  R/Y*(Y*/Y)^(e_r)  ...
    in ratios to actual GDP: R*/Y* = (R/Y) (Y*/Y)^(e_r-1) ; G*/Y* = (G/Y)(Y*/Y)^(e_g-1)."""
    q = 1.0 / (1.0 + gap_pct / 100.0)   # Y*/Y
    return rev * q ** (e_r - 1.0) - exp * q ** (e_g - 1.0)

def cab_semi(overall_bal, gap_pct, semi):
    """OECD/EC semi-elasticity form: CAB = overall balance - semi * output gap (pp of GDP)."""
    return overall_bal - semi * gap_pct
