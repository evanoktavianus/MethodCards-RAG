"""Generates the extension items CI-21..CI-40 into items/lic_dsf_ci/ from frozen data only (python3 -I). Does NOT touch CI-01..CI-20.
Hidden predicates are rebuilt and asserted to have set size exactly 1 at generation."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from ci_lib import *
import hidden, select_extension as sel
OUT = os.path.join(HERE, '..', '..', 'items', 'lic_dsf_ci')
DOCS = json.load(open(HERE + '/doc_ids_by_country_year.json'))
P0 = {(p['iso3'], p['year']): p for p in json.load(open(HERE + '/published_ci.json'))}
NAME = {'BGD': 'Bangladesh', 'COD': 'the Democratic Republic of the Congo', 'COG': 'the Republic of Congo', 'COM': 'the Comoros', 'CPV': 'Cabo Verde', 'GHA': 'Ghana',
        'GIN': 'Guinea', 'KHM': 'Cambodia', 'MDV': 'the Maldives', 'NIC': 'Nicaragua', 'SLB': 'the Solomon Islands', 'TJK': 'Tajikistan', 'UZB': 'Uzbekistan',
        'VUT': 'Vanuatu', 'WSM': 'Samoa', 'ZMB': 'Zambia'}
def poss(n): return n + ("'" if n.endswith('s') else "'s")
METHOD_DOCS = ['861422e0-253f-45af-857c-4268159edddd', 'd7658e96-9694-4cd0-8f26-465f0f9ab0aa', '968df4c6-cc90-48f9-95c5-af0a8eb49597']
DIST = ['Public DSA for market-access countries (debt-stabilising primary balance, stress tests)', 'IMF reserve adequacy (ARA) metric', 'World Bank CPIA score read on its own', 'External Balance Assessment', 'Debt-to-GDP threshold from memory (e.g. 60 percent)']
IND = [{"indicator": "IQ.CPA.IRAI.XQ", "source": "WDI"}, {"indicator": "NGDP_RPCH", "source": "WEO"}, {"indicator": "FI.RES.TOTL.CD", "source": "WDI"}, {"indicator": "NE.IMP.GNFS.CD", "source": "WDI"}, {"indicator": "BX.TRF.PWKR.DT.GD.ZS", "source": "WDI"}]
# style plan: (iso3, year) -> style. Hidden need a buildable predicate; claim checks carry the statement (stated value, stated class)
NAMED = [('CPV', 2025), ('KHM', 2022), ('UZB', 2024), ('VUT', 2021), ('VUT', 2023), ('WSM', 2023), ('ZMB', 2025)]
HID = [('BGD', 2025), ('COM', 2023), ('KHM', 2025), ('MDV', 2024), ('UZB', 2026), ('SLB', 2026), ('GIN', 2022)]
CHK = {('GHA', 2019): None, ('TJK', 2019): None, ('COD', 2019): None,                      # None: state the published value and class (true)
       ('CPV', 2019): (3.65, 'strong'), ('COG', 2019): (2.85, 'medium'), ('NIC', 2019): (2.61, 'weak')}   # wrong statements (false)
# the existing item each extension item extends: same-country item of the same style if one exists, else next item of that style
EXT_OF = {('named', 'CPV'): 'CI-14', ('named', 'KHM'): 'CI-01', ('named', 'UZB'): 'CI-02', ('named', 'VUT'): 'CI-04', ('named', 'WSM'): 'CI-13', ('named', 'ZMB'): 'CI-11',
          ('hidden', 'BGD'): 'CI-08', ('hidden', 'COM'): 'CI-12', ('hidden', 'KHM'): 'CI-09', ('hidden', 'MDV'): 'CI-10', ('hidden', 'UZB'): 'CI-11', ('hidden', 'SLB'): 'CI-13', ('hidden', 'GIN'): 'CI-14',
          ('claim_check', 'GHA'): 'CI-16', ('claim_check', 'TJK'): 'CI-15', ('claim_check', 'COD'): 'CI-17', ('claim_check', 'CPV'): 'CI-18', ('claim_check', 'COG'): 'CI-19', ('claim_check', 'NIC'): 'CI-20'}
def fmt(k, d, x):
    if 'population' in k: return ('fewer' if d == '<' else 'more') + ' than {:,} people'.format(int(round(x)))
    nm = k.split(' (')[0]; un = {'GDP per capita': 'US dollars', 'real GDP growth': 'percent', 'CPI inflation': 'percent'}.get(nm, 'percent of GDP')
    return '%s %s %g %s' % (nm if nm in ('GDP per capita', 'CPI inflation') else nm[0].lower() + nm[1:], 'below' if d == '<' else 'above', round(x, 2), un)
def conds_text(cs):
    t = [fmt(*c) for c in cs]
    return t[0] if len(t) == 1 else (', '.join(t[:-1]) + (', and ' if len(t) > 2 else ' and ') + t[-1])
def claims(iso, Y, v, parts):
    cat = category(v)
    tc = [{"id": "c1", "kind": "text", "importance": "vital",
           "text": "Identifies the applicable methodology: the IMF-World Bank debt-sustainability framework for low-income countries, in which a composite indicator (CPIA, real growth, reserve import cover, remittances, world growth) classifies debt-carrying capacity as weak, medium or strong.",
           "accept": "full = names the low-income-country debt sustainability framework / composite indicator and its components; partial = says only 'debt capacity classification' with CPIA but no composite; no = uses a market-access DSA, reserve adequacy or other method."}]
    dc = [{"id": "c2", "kind": "data", "importance": "okay", "text": "Uses the composite-indicator inputs for %s: CPIA (10-yr avg to %d), real GDP growth (%d-%d), reserves-to-imports, remittances, world growth." % (iso, Y - 1, Y - 5, Y + 4),
           "accept": "full = cites at least three of the five inputs with values near gold; partial = fewer; no = none.", "requires": [dict(i, iso3=iso, years=[Y - 10, Y + 4]) for i in IND]}]
    cc = [{"id": "c3", "kind": "computation", "importance": "vital", "text": "The composite indicator score is about %.2f." % v,
           "accept": "full = within +/-0.10 of %.3f; partial = within +/-0.25; no = otherwise." % v, "statistic": "CI = 0.385*CPIA + 2.719*g + 4.052*IC - 3.990*IC^2 + 2.022*REM + 13.520*WG",
           "resolves": {"value": round(v, 3), "targets": [{"name": "value", "kind": "number", "value": round(v, 3), "unit": "index", "tolerance": 0.10, "tolerance_source": "validation vs published"}]},
           "components": {k: round(x, 4) for k, x in parts.items()}}]
    ac = [{"id": "c4", "kind": "answer", "importance": "vital", "text": "Debt-carrying capacity is %s (cutoffs: weak below 2.69, strong above 3.05)." % cat, "accept": "full = %s; no = any other class." % cat, "value": cat}]
    return {"text": tc, "data": dc, "computation": cc, "answer": ac}
def base(idx, style, q, iso, Y, pub):
    v, parts, comp = ci(iso, Y)
    gold = DOCS['%s-%d' % (iso, Y)]
    it = {"id": "CI-%02d" % idx, "family": "methodology", "pattern": "M-" + style, "tier": "analytical", "status": "validated", "query": q,
          "claims": claims(iso, Y, v, parts), "grading": {"method": "claim_recall"},
          "provenance": {"assembled_from": ["WEO Oct 2025 (frozen_extra), WDI 2026-10-08 (frozen_extra/wdi_20261008_*)"], "gold_script": "gold_scripts/lic_dsf_ci/make_items_ext.py",
                         "validation": "gold_scripts/lic_dsf_ci/validate.py; gold_scripts/lic_dsf_ci/select_extension.py", "published_value_source": "gold_scripts/lic_dsf_ci/published_ci_extension.json" if (iso, Y) not in P0 else "gold_scripts/lic_dsf_ci/published_ci.json"},
          "method": "lic_dsf_composite_indicator", "method_doc_ids": [d for d in METHOD_DOCS if d not in gold], "gold_report_ids": gold,
          "published_value": pub, "recomputed_value": round(v, 3), "tolerance": 0.10,
          "inputs": ["NGDP_RPCH", "IQ.CPA.IRAI.XQ", "FI.RES.TOTL.CD", "NE.IMP.GNFS.CD", "BX.TRF.PWKR.DT.GD.ZS", "NGDPRPPPPC", "LP"],
          "style": style, "subject": {"iso3": iso, "year": Y, "components": {k: round(x, 4) for k, x in comp.items()}}, "distractors": DIST, "famous_method": False,
          "instance_extension": True, "extension_of": EXT_OF[(style, iso)]}
    return it
ELIG = {(e['iso3'], e['year']): e for e in sel.eligible()}
QN = ["For the {Y} assessment round, how safely could {C} carry additional debt: would you call its capacity weak, medium or strong, and which single score backs that call?",
      "Rate {P} ability to sustain a higher debt load in the {Y} round as weak, medium or strong, and give the one number that justifies the rating.",
      "Where does {C} stand in the {Y} round on the weak-medium-strong scale for debt-bearing capacity, and what score places it there?",
      "In the {Y} assessment round, is {P} debt-bearing capacity weak, medium or strong? Please give the single score on which you base the answer.",
      "How would an analyst classify {P} capacity to take on debt in the {Y} round (weak, medium or strong), and with what score?",
      "Classify {C} for the {Y} round by how much debt it can safely bear, weak, medium or strong, and state the score behind the class.",
      "For {Y}, what is the strength class (weak, medium or strong) of {P} ability to carry debt, and what single score determines it?"]
QH = ["Think of the economy that in 2023 had {S}. For the {Y} assessment round, is its capacity to bear debt weak, medium or strong, and what score decides that?",
      "Take the one economy that in 2023 showed {S}. How would you class its debt-bearing capacity in the {Y} round (weak, medium or strong), and with what score?",
      "Identify the economy that in 2023 recorded {S}, then say whether its capacity to carry debt in the {Y} round is weak, medium or strong and which score supports that.",
      "One economy in 2023 had {S}. Rate its ability to sustain debt for the {Y} round as weak, medium or strong, and give the supporting score.",
      "For the economy that had {S} in 2023, rate its debt-bearing capacity in the {Y} round as weak, medium or strong and cite the score you rely on.",
      "In 2023, exactly one economy had {S}. For the {Y} round, would you call its capacity to take on debt weak, medium or strong, and on what score?",
      "Consider the 2023 economy with {S}. Where does it sit in the {Y} round: weak, medium or strong capacity to carry debt, and what is the score?"]
QC = ["A ministry note says {P} debt-bearing score in the {Y} round was {x:.2f}, which puts it in the {c} class. Does that hold up?",
      "An investor deck states that {C} scored {x:.2f} for debt-carrying strength in {Y}, landing in the {c} class. Is that right?",
      "According to a press summary, {P} capacity score for the {Y} round is {x:.2f} and the class is {c}. Is this claim accurate?",
      "A report excerpt claims {C} received a score of {x:.2f} in the {Y} round and was rated {c} for its ability to carry debt. Is the excerpt correct?",
      "Someone asserts that in the {Y} round {C} scored {x:.2f}, a {c} rating for debt capacity. Is that assertion correct?",
      "A newsletter reports a {Y} debt-capacity score of {x:.2f} for {C}, which it labels {c}. Is the newsletter right?"]
items = []; n = 20
for k, (iso, Y) in enumerate(NAMED):
    n += 1; e = ELIG[(iso, Y)]
    items.append(base(n, 'named', QN[k % len(QN)].format(Y=Y, C=NAME[iso], P=poss(NAME[iso])), iso, Y, e['published_ci']))
for k, (iso, Y) in enumerate(HID):
    n += 1; e = ELIG[(iso, Y)]
    conds, m = hidden.build(iso); assert m == [iso] and len(m) == 1, (iso, m)
    loose = [i for i in hidden.GDPPC if all(hidden.val(c[0], i) is not None and (hidden.val(c[0], i) < c[2] if c[1] == '<' else hidden.val(c[0], i) > c[2]) for c in conds)]
    assert loose == [iso], ('loose universe (any economy with data for the conditions)', iso, loose)
    it = base(n, 'hidden', QH[k % len(QH)].format(Y=Y, S=conds_text(conds)), iso, Y, e['published_ci'])
    it['hidden_predicate'] = {"conditions": [{"feature": c[0], "op": c[1], "threshold": c[2], "year": 2023} for c in conds], "universe": "all WEO Oct 2025 economies with complete data for the features (192)", "set_size": len(m), "members": m}
    items.append(it)
for k, ((iso, Y), st) in enumerate(CHK.items()):
    n += 1; e = ELIG[(iso, Y)]; v = e['recomputed']
    sv, sc = (e['published_ci'], category(e['published_ci'])) if st is None else st
    truth = abs(sv - v) <= 0.10 and sc == category(v)
    assert truth == (st is None), (iso, Y)
    it = base(n, 'claim_check', QC[k % len(QC)].format(Y=Y, C=NAME[iso], P=poss(NAME[iso]), x=sv, c=sc), iso, Y, e['published_ci'])
    it['claim_under_test'] = {"stated_value": sv, "stated_class": sc, "truth": truth}
    it['claims']['answer'] = [{"id": "c4", "kind": "answer", "importance": "vital", "text": "Correct verdict: the statement is %s (recomputed score %.2f, class %s)." % ('TRUE' if truth else 'FALSE', v, category(v)),
                               "accept": "full = verdict %s with recomputed score within +/-0.10; no = wrong verdict." % ('TRUE' if truth else 'FALSE'), "value": truth}]
    items.append(it)
for it in items:
    path = os.path.join(OUT, it['id'] + '.json')
    if os.path.exists(path): assert json.load(open(path)).get('instance_extension'), 'refusing to overwrite ' + path
    assert abs(it['recomputed_value'] - it['published_value']) <= 0.10
    json.dump(it, open(path, 'w'), indent=1)
print(len(items), 'items;', {s: sum(i['style'] == s for i in items) for s in ('named', 'hidden', 'claim_check')}, 'true claim checks:', sum(i['style'] == 'claim_check' and i['claim_under_test']['truth'] for i in items))
for it in items: print(it['id'], it['style'], it['subject']['iso3'], it['subject']['year'], it['published_value'], it['recomputed_value'], it['claims']['answer'][0]['value'], '|', it['query'])
