"""Gold script. Method: Fiscal Monitor adjustment needs for a long-term debt target. Doc: FM April 2014 (a9063586), Statistical Table 14 + note 3. Replicates the Fiscal Monitor April 2014 Statistical Table 14 (EM): CAPB needed in 2020-30 to bring debt to 40% of GDP by 2030
(or hold the end-2014 debt ratio if below 40). Published algorithm (table note 3): CAPB follows FM projections to 2015 (here: held at its 2014 value),
adjusts linearly 2016-2020, constant 2020-30; r-g rises linearly from its 2014 level to 1.0 pp by 2028 and stays at 1.0."""
import csv, os, re
H = os.path.dirname(os.path.abspath(__file__)) + "/../../"
FX = H + "frozen_extra/"
NM = dict(Argentina="ARG", Brazil="BRA", Bulgaria="BGR", Chile="CHL", China="CHN", Colombia="COL", Egypt="EGY", Hungary="HUN", India="IND", Indonesia="IDN",
          Jordan="JOR", Kenya="KEN", Lithuania="LTU", Malaysia="MYS", Mexico="MEX", Morocco="MAR", Nigeria="NGA", Pakistan="PAK", Peru="PER", Philippines="PHL",
          Poland="POL", Romania="ROU", Russia="RUS", **{"South Africa": "ZAF"}, Thailand="THA", Turkey="TUR")
def weo(name):
    d = {}
    for r in csv.DictReader(open(FX + name)):
        for k, v in r.items():
            if k.isdigit() and v != "": d[(r["iso3"], int(k))] = float(v)
    return d
DEBT, OB, PB, NG = weo("weo_oct2025_ggxwdg_ngdp.csv"), weo("weo_oct2025_ggxcnl_ngdp.csv"), weo("weo_oct2025_ggxonlb_ngdp.csv"), weo("weo_oct2025_ngdp.csv")
rows = []
txt = open(FX + "fm_apr2014_statistical_tables_13a_14.txt").read().splitlines()
tab = [l for l in txt if l.startswith("950\ttable")][0]
body = "| Argentina" + tab.split("| Argentina")[1].split("| Average")[0]
for cells in re.findall(r"\| ([A-Za-z ]+?)\d? \| (-?[\d.]+) \| (-?[\d.]+) \| ([-\d.]+|\.\.\.) \| (-?[\d.]+) \| (-?[\d.]+) \|", body):
    rows.append(cells)
def solve(iso, d14, capb14):
    target = 40.0 if d14 > 40 else d14
    g = lambda y: 100 * (NG[(iso, y)] / NG[(iso, y - 1)] - 1)
    i14 = (PB[(iso, 2014)] - OB[(iso, 2014)]) / DEBT[(iso, 2013)] * 100  # interest rate on previous debt
    rg14 = i14 - g(2014)  # 2014 r-g: interest on previous-year debt minus nominal growth (WEO Oct 2025 outturn, not the FM 2014 projection)
    def end_debt(p):
        d = d14
        for y in range(2015, 2031):
            rg = rg14 + (1.0 - rg14) * min(1, (y - 2014) / 14.0)
            lam = rg / 100
            pb = capb14 if y == 2015 else (capb14 + (p - capb14) * min(1, (y - 2015) / 5.0))
            d = d * (1 + lam) - pb
        return d
    lo, hi = -30.0, 30.0
    for _ in range(60):
        m = (lo + hi) / 2
        if end_debt(m) > target: lo = m
        else: hi = m
    return (lo + hi) / 2
res = []
for name, d, c, ar, c20, adj in rows:
    iso = NM.get(name.strip())
    if not iso: continue
    try: p = solve(iso, float(d), float(c))
    except KeyError: continue
    res.append((iso, float(c20), round(p, 2)))
print(len(res)); 
ok = [abs(a - b) for _, a, b in res]
print("within 0.5:", sum(x <= .5 for x in ok), "within 1:", sum(x <= 1 for x in ok))
for r in res: print(r)
