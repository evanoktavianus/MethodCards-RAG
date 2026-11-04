"""Tax buoyancy estimators (Dudine & Jalles 2017, IMF WP/17/4). Pure Python (no numpy needed).
Long run: ln(tax) = a + b*t + theta*ln(GDP) + u, FMOLS (Phillips-Hansen 1990) with linear trend, Bartlett kernel.
Short run: dln(tax)_t = mu + phi*u_hat_{t-1} + gamma*dln(GDP)_t (ECM, p=q=1), OLS; gamma = short-run buoyancy.
"""
import csv, math, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

def load(codes=('GC.TAX.TOTL.CN', 'NY.GDP.MKTP.CN', 'NGDP', 'GC.TAX.TOTL.GD.ZS')):
    d = {}
    for r in csv.DictReader(open(os.path.join(ROOT, 'frozen_extra', 'long_extract.csv'))):
        if r['code'] in codes:
            try: d.setdefault((r['code'], r['iso3']), {})[int(r['period'])] = float(r['value'])
            except ValueError: pass
    return d

def solve(A, b):
    n = len(A); M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for i in range(n):
        p = max(range(i, n), key=lambda r: abs(M[r][i])); M[i], M[p] = M[p], M[i]
        for r in range(i + 1, n):
            f = M[r][i] / M[i][i]
            for c in range(i, n + 1): M[r][c] -= f * M[i][c]
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        x[i] = (M[i][n] - sum(M[i][c] * x[c] for c in range(i + 1, n))) / M[i][i]
    return x

def ols(X, y):
    k = len(X[0])
    A = [[sum(r[i] * r[j] for r in X) for j in range(k)] for i in range(k)]
    b = [sum(r[i] * yy for r, yy in zip(X, y)) for i in range(k)]
    beta = solve(A, b)
    res = [yy - sum(bb * xx for bb, xx in zip(beta, r)) for r, yy in zip(X, y)]
    return beta, res

def fmols(y, x, bw=None):
    """y, x lists of logs. Returns theta, residuals (u_hat from FMOLS levels eq)."""
    T = len(y)
    Z = [[1.0, float(t), x[t]] for t in range(T)]
    beta, u = ols(Z, y)
    de = [x[t] - x[t - 1] for t in range(1, T)]
    mde = sum(de) / len(de); e = [v - mde for v in de]          # drift removed
    u1 = u[1:]; n = len(e)
    if bw is None: bw = int(math.floor(4 * (n / 100.0) ** (2 / 9.0))) + 1   # Newey-West plug-in-ish
    def gam(a, b_, j):  # (1/n) sum a_t b_{t+j}
        return sum(a[t] * b_[t + j] for t in range(n - j)) / n
    wue = wee = due = dee = 0.0
    for j in range(0, bw + 1):
        w = 1 - j / (bw + 1.0)
        g_ue = gam(u1, e, j); g_eu = gam(e, u1, j); g_ee = gam(e, e, j)
        if j == 0:
            wue += g_ue; wee += g_ee
        else:
            wue += w * (g_ue + g_eu); wee += w * 2 * g_ee
        due += w * g_ue; dee += w * g_ee
    ratio = wue / wee
    ystar = [y[0]] + [y[t] - ratio * (x[t] - x[t - 1] - mde) for t in range(1, T)]
    dplus = due - ratio * dee
    # solve normal equations: Z'Z b = Z'y* - [0,0,T*dplus]
    k = 3
    A = [[sum(r[i] * r[j] for r in Z) for j in range(k)] for i in range(k)]
    rhs = [sum(r[i] * yy for r, yy in zip(Z, ystar)) for i in range(k)]
    rhs[2] -= n * dplus
    b = solve(A, rhs)
    uh = [y[t] - b[0] - b[1] * t - b[2] * x[t] for t in range(T)]
    return b[2], uh, b

def ecm_short(y, x, uh):
    X = []; Y = []
    for t in range(1, len(y)):
        X.append([1.0, uh[t - 1], x[t] - x[t - 1]]); Y.append(y[t] - y[t - 1])
    b, _ = ols(X, Y)
    return b[2], b[1]

def estimate(tax, gdp, y0=1980, y1=2014, bw=None):
    yrs = sorted(t for t in tax if t in gdp and y0 <= t <= y1 and tax[t] > 0 and gdp[t] > 0)
    # require contiguous block: keep longest run ending anywhere
    runs = []; cur = []
    for t in yrs:
        if cur and t != cur[-1] + 1: runs.append(cur); cur = []
        cur.append(t)
    if cur: runs.append(cur)
    if not runs: return None
    yrs = max(runs, key=len)
    if len(yrs) < 10: return None
    y = [math.log(tax[t]) for t in yrs]; x = [math.log(gdp[t]) for t in yrs]
    th, uh, _ = fmols(y, x, bw)
    g, phi = ecm_short(y, x, uh)
    return dict(lr=th, sr=g, speed=phi, n=len(yrs), first=yrs[0], last=yrs[-1])

def simple_ratio(tax, gdp, t):
    """Short-run (annual) buoyancy as ratio of growth rates: (dT/T)/(dY/Y)."""
    if t in tax and t - 1 in tax and t in gdp and t - 1 in gdp:
        gt = tax[t] / tax[t - 1] - 1; gy = gdp[t] / gdp[t - 1] - 1
        if abs(gy) > 1e-9: return gt / gy
    return None
