"""Okun-type OLS from frozen WEO Oct 2025: du_t = a + b*g_t. python3 -I, stdlib only."""
import csv, os
FZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frozen_extra')
def load(code):
    d = {}
    for r in csv.DictReader(open(os.path.join(FZ, 'weo_oct2025_%s.csv' % code))):
        d[r['iso3']] = {int(y): float(v) for y, v in r.items() if y.isdigit() and v not in ('', None)}
    return d
LUR, G = load('lur'), load('ngdp_rpch')
NAMES = {r['iso3']: r['country'] for r in csv.DictReader(open(os.path.join(FZ, 'weo_oct2025_lur.csv')))}
def sample(iso, y0, y1):
    u, g = LUR.get(iso, {}), G.get(iso, {})
    xs = []
    for t in range(y0, y1 + 1):
        if t in u and t - 1 in u and t in g:
            xs.append((t, g[t], u[t] - u[t - 1]))
    return xs
def ols(xs):
    n = len(xs); mx = sum(x[1] for x in xs) / n; my = sum(x[2] for x in xs) / n
    sxx = sum((x[1] - mx) ** 2 for x in xs); sxy = sum((x[1] - mx) * (x[2] - my) for x in xs)
    b = sxy / sxx; a = my - b * mx
    sst = sum((x[2] - my) ** 2 for x in xs); sse = sum((x[2] - a - b * x[1]) ** 2 for x in xs)
    return a, b, 1 - sse / sst if sst else 0.0, n
def fit(iso, y0=1993, y1=2019):
    xs = sample(iso, y0, y1)
    if len(xs) < y1 - y0 + 1: return None
    a, b, r2, n = ols(xs)
    return dict(iso3=iso, alpha=a, beta=b, r2=r2, n=n, neutral_growth=(-a / b if b < 0 else None))
if __name__ == '__main__':
    res = [f for f in (fit(i) for i in LUR) if f]
    print(len(res), 'countries complete 1993-2019')
    for f in sorted(res, key=lambda f: f['beta']): print(f['iso3'], round(f['alpha'],3), round(f['beta'],3), round(f['r2'],2), None if f['neutral_growth'] is None else round(f['neutral_growth'],2))
