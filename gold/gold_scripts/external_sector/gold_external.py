"""Gold + generator for the external-sector identity methods. python3 -I gold_external.py [--gen | --verify]
Reads only release/official_benchmark/reference_data/ frozen CSVs. No network, no LLM."""
import csv, json, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
REF = os.path.join(ROOT, 'release', 'official_benchmark', 'reference_data')
OUT = os.path.join(HERE, '..', '..', 'items', 'external_sector')
def ld(n):
    return {r['iso3']: r for r in csv.DictReader(open(os.path.join(REF, n)))}
S, I, B, G, D = (ld(f'weo_oct2025_{k}.csv') for k in ('ngsd_ngdp', 'nid_ngdp', 'bca_ngdpd', 'ggxcnl_ngdp', 'ngdpd'))
NAME = {r['iso3']: r['name'] for r in csv.DictReader(open(os.path.join(REF, 'wb_classifications.csv'))) if r['income_group'] != 'Aggregates'}
def v(t, c, y):
    try: return float(t[c][str(y)])
    except (KeyError, ValueError): return None
def ca_si(c, y):  # saving - investment, % GDP
    s, i = v(S, c, y), v(I, c, y)
    return None if s is None or i is None else s - i
def priv_bal(c, y):  # CA - government net lending = (Sp-Ip)
    b, g = v(B, c, y), v(G, c, y)
    return None if b is None or g is None else b - g
def cum_ca_usd_bn(c, y0, y1):
    t = 0.0
    for y in range(y0, y1 + 1):
        b, d = v(B, c, y), v(D, c, y)
        if b is None or d is None: return None
        t += b / 100 * d / 1e9
    return t
def sgn(x): return 'surplus' if x > 0 else 'deficit'
def f1(x): return f"{x:.1f}"

def verify():
    bad = 0; n = 0
    for fn in sorted(os.listdir(OUT)):
        it = json.load(open(os.path.join(OUT, fn))); n += 1
        x = it['instance']; k = it['method']; c = x['iso3']; y = x.get('year')
        if k == 'saving_investment_gap_current_account': val = ca_si(c, y)
        elif k == 'private_public_sector_balance_split': val = priv_bal(c, y)
        else: val = cum_ca_usd_bn(c, x['y0'], x['y1'])
        if x.get('absolute'): val = abs(val)
        ok = abs(val - it['recomputed_value']) < 0.01
        if x.get('predicate_cols'):  # hidden: exactly one country satisfies
            ms = [k2 for k2 in S if hidden_ok(x, k2)]
            ok = ok and ms == [c]
        if not ok: bad += 1; print('MISMATCH', it['id'], val, it['recomputed_value'])
    print(n, 'items checked,', bad, 'mismatches')

def hidden_ok(x, c):
    y = x['year']; vals = []
    for col, op, th in x['predicate_cols']:
        t = {'S': S, 'I': I, 'B': B, 'G': G, 'D': D}[col]
        a = v(t, c, y)
        if a is None: return False
        if col == 'D': a /= 1e9
        if not (a > th if op == '>' else a < th): return False
    return True

if __name__ == '__main__':
    if '--verify' in sys.argv: verify(); sys.exit()
    print('usage: --verify (use gen_items.py to author)')
