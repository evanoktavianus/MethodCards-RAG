# Builds IG-NN items: World Bank income bracket from Atlas GNI per capita (2011 cut-offs printed in IMF External Debt Statistics Guide)
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
CUT = (1025, 4035, 12475)   # printed: <=1,025 low; 1,026-4,035 lower-middle; upper-middle; >=12,476 high
BR = ['low-income', 'lower-middle-income', 'upper-middle-income', 'high-income']
BRN = ['Low income', 'Lower middle income', 'Upper middle income', 'High income']
UP = {0: 1025, 1: 4035, 2: 12475}
def bracket(x): return 0 if x <= CUT[0] else 1 if x <= CUT[1] else 2 if x <= CUT[2] else 3
def margin(x): return min(abs(x - c) / c for c in CUT)
YEAR = 2011
G = psv('NY.GNP.PCAP.CD'); N = names()
def pool():
    return [k for k, s in G.items() if YEAR in s and k in N and N[k]['income_group'] != 'Aggregates' and margin(s[YEAR]) > 0.08 and k in weo('pcpipch')]
def validate():
    t = {2024: (1135, 4495, 13935)}; ok = tot = 0
    for k, s in G.items():
        if 2024 in s and k in N and N[k]['income_group'] != 'Aggregates':
            tot += 1; b = (0 if s[2024] <= 1135 else 1 if s[2024] <= 4495 else 2 if s[2024] <= 13935 else 3)
            ok += BRN[b] == N[k]['income_group']
    return ok, tot
def build():
    rng = random.Random(11); P = pool(); items = []
    ok, tot = validate()
    styles = split_styles(5, 5, 4); rng.shuffle(P)
    used = set(); n = 0
    hc = hidden_candidates(YEAR, lambda k: k in P, rng)
    for st in styles:
        n += 1; iid = 'IG-%02d' % n
        if st == 'named':
            iso = next(k for k in P if k not in used); pred = None; size = None
            q = 'In %d, did %s count as a low-, lower-middle-, upper-middle- or high-income economy, and how far was it from the nearest dividing line?' % (YEAR, cname(iso)) if n % 2 else \
                'Where did %s sit in the %d income ladder (low, lower-middle, upper-middle, high), and by how much was it above or below the next cut-off?' % (cname(iso), YEAR)
        elif st == 'hidden':
            c = next(c for c in hc if c[0] not in used); iso = c[0]; pred = c[1]; size = 1
            q = 'Take %s. Which income bracket (low, lower-middle, upper-middle, high) did it belong to in %d, and how close was it to the dividing line?' % (pred, YEAR)
        else:
            iso = next(k for k in P if k not in used); pred = None; size = None
        used.add(iso); x = G[iso][YEAR]; b = bracket(x)
        # nearest cut-off distance
        near = min(CUT, key=lambda c: abs(x - c)); dist = round(x - near, 0)
        if st == 'claim':
            truth = (n % 2 == 0)
            claimed = b if truth else (b + 1 if b < 3 else b - 1)
            if not truth and rng.random() < .5 and b > 0: claimed = b - 1
            q = 'A debt-restructuring brief states: "In %d, %s was %s %s economy." Is the brief right?' % (YEAR, cname(iso), 'an' if BR[claimed][0] in 'u' else 'a', BR[claimed])
            vt = 'Judges the statement %s: the %d bracket is %s.' % ('TRUE' if truth else 'FALSE', YEAR, BR[b])
        else:
            vt = 'States the %d bracket: %s (GNI per capita %d US dollars).' % (YEAR, BR[b], round(x))
        comps = [('Atlas-method GNI per capita of %s in %d = %d US dollars' % (cname(iso), YEAR, round(x)), round(x, 1), round(0.03 * x), 'USD', 'full = within 3 percent (vintage revisions of the Atlas series)'),
                 ('Distance to the nearest income cut-off (%d US dollars) = %+d US dollars' % (near, dist), dist, max(round(0.03 * x), 50), 'USD', 'full = within tolerance; sign positive if above the cut-off')]
        cl = mk_claims('Identifies that the answer applies the World Bank country income classification: Atlas-method GNI per capita compared against the annual low / lower-middle / upper-middle / high income cut-offs.',
                       'full = names the World Bank income classification by GNI per capita cut-offs; acceptable alternative: IDA / Paris Club eligibility lens built on the same income tiers; no = ranks by GDP per capita without cut-offs or by IMF advanced/emerging grouping',
                       comps, vt, 'full = bracket matches (%s) and, for claim items, TRUE/FALSE verdict matches' % BR[b],
                       'Uses World Bank Atlas GNI per capita (current US dollars, NY.GNP.PCAP.CD) for %d.' % YEAR)
        it = base_item(iid, {'named': 'M-named', 'hidden': 'M-hidden', 'claim': 'M-claim'}[st], q, 'world_bank_income_classification_atlas',
                       ['bc5f813b-b3a4-4001-8f4a-bab531649fce'], [], ['NY.GNP.PCAP.CD'], st,
                       ['GDP per capita at market prices', 'IMF advanced-vs-emerging grouping', 'PRGT eligibility test', 'debt-carrying-capacity classification'], True, cl,
                       round(x, 1), round(x, 1), round(0.03 * x), 'gold_scripts/ext_procedures/build_income_group.py',
                       'drawn from %d countries with 2011 Atlas GNI per capita at least 8 percent away from every cut-off (robust to data revision); seeded draw; one per country' % len(P),
                       ['IMF External Debt Statistics Guide (2013) glossary: cut-offs for 2011', 'frozen WDI NY.GNP.PCAP.CD (frozen_extra/wdi_20261008_ara_ig_extract.psv)'],
                       size, pred, 'The classification rule is printed in the IMF guide (not a country report); nothing to withhold. Implementation check: same rule with the 2024 cut-offs reproduces the current World Bank grouping for %d of %d countries (wb_classifications.csv); the misses are within 1 percent of a cut-off.' % (ok, tot))
        it['method_class'] = 'institutional procedure'; it['iso3'] = iso; it['year'] = YEAR
        save('income_group_atlas', it)
    return n
if __name__ == '__main__':
    print(build(), validate())
