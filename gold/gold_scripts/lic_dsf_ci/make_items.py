"""Generates items/lic_dsf_ci/CI-NN.json from frozen data only (python3 -I). Hidden predicates are re-verified (set size == 1) at generation."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from ci_lib import *
import hidden
P = {(p['iso3'], p['year']): p for p in json.load(open(os.path.join(os.path.dirname(__file__), 'published_ci.json')))}
OUT = os.path.join(os.path.dirname(__file__), '..', '..', 'items', 'lic_dsf_ci')
os.makedirs(OUT, exist_ok=True)
NAME = {'GHA': 'Ghana', 'GIN': 'Guinea', 'MDV': 'the Maldives', 'VUT': 'Vanuatu', 'COM': 'the Comoros', 'SLB': 'the Solomon Islands', 'HTI': 'Haiti',
        'DJI': 'Djibouti', 'LSO': 'Lesotho', 'NPL': 'Nepal', 'ZMB': 'Zambia', 'TZA': 'Tanzania', 'WSM': 'Samoa', 'CPV': 'Cabo Verde', 'TLS': 'Timor-Leste'}
METHOD_DOCS = [P[('GHA', 2021)]['doc_id'], P[('MRT', 2022)]['doc_id'], P[('LSO', 2025)]['doc_id']]
DIST = ['Public DSA for market-access countries (debt-stabilising primary balance, stress tests)', 'IMF reserve adequacy (ARA) metric', 'World Bank CPIA score read on its own', 'External Balance Assessment', 'Debt-to-GDP threshold from memory (e.g. 60 percent)']
IND = [{"indicator": "IQ.CPA.IRAI.XQ", "source": "WDI"}, {"indicator": "NGDP_RPCH", "source": "WEO"}, {"indicator": "FI.RES.TOTL.CD", "source": "WDI"}, {"indicator": "NE.IMP.GNFS.CD", "source": "WDI"}, {"indicator": "BX.TRF.PWKR.DT.GD.ZS", "source": "WDI"}]
def fmt(k, d, x):
    if 'population' in k: return ('fewer' if d == '<' else 'more') + ' than {:,} people'.format(int(round(x)))
    nm = k.split(' (')[0]; un = {'GDP per capita': 'US dollars', 'real GDP growth': 'percent', 'CPI inflation': 'percent'}.get(nm, 'percent of GDP')
    return '%s %s %g %s' % (nm[0].lower() + nm[1:] if nm != 'GDP per capita' else nm, 'below' if d == '<' else 'above', round(x, 2), un)
def cond_text(conds):
    return '; '.join(fmt(*c) for c in conds)
def claims(iso, Y, v, parts, kind_stmt=None):
    cat = category(v)
    tc = [{"id": "c1", "kind": "text", "importance": "vital",
           "text": "Identifies the applicable methodology: the IMF-World Bank debt-sustainability framework for low-income countries, in which a composite indicator (CPIA, real growth, reserve import cover, remittances, world growth) classifies debt-carrying capacity as weak, medium or strong.",
           "accept": "full = names the low-income-country debt sustainability framework / composite indicator and its components; partial = says only 'debt capacity classification' with CPIA but no composite; no = uses a market-access DSA, reserve adequacy or other method."}]
    dc = [{"id": "c2", "kind": "data", "importance": "okay", "text": "Uses the composite-indicator inputs for %s: CPIA (10-yr avg to %d), real GDP growth (%d-%d), reserves-to-imports, remittances, world growth." % (iso, Y - 1, Y - 5, Y + 4), "accept": "full = cites at least three of the five inputs with values near gold; partial = fewer; no = none.", "requires": [dict(i, iso3=iso, years=[Y - 10, Y + 4]) for i in IND[:5]]}]
    cc = [{"id": "c3", "kind": "computation", "importance": "vital", "text": "The composite indicator score is about %.2f." % v,
           "accept": "full = within +/-0.10 of %.3f; partial = within +/-0.25; no = otherwise." % v, "statistic": "CI = 0.385*CPIA + 2.719*g + 4.052*IC - 3.990*IC^2 + 2.022*REM + 13.520*WG",
           "resolves": {"value": round(v, 3), "targets": [{"name": "value", "kind": "number", "value": round(v, 3), "unit": "index", "tolerance": 0.10, "tolerance_source": "validation vs published"}]},
           "components": {k: round(x, 4) for k, x in parts.items()}}]
    ac = [{"id": "c4", "kind": "answer", "importance": "vital", "text": "Debt-carrying capacity is %s (cutoffs: weak below 2.69, strong above 3.05)." % cat, "accept": "full = %s; no = any other class." % cat, "value": cat}]
    return {"text": tc, "data": dc, "computation": cc, "answer": ac}
def base(idx, style, q, iso, Y, p, **kw):
    r = ci(iso, Y); v, parts, comp = r
    it = {"id": "CI-%02d" % idx, "family": "methodology", "pattern": "M-" + style, "tier": "analytical", "status": "validated", "query": q,
          "claims": claims(iso, Y, v, parts),
          "grading": {"method": "claim_recall"},
          "provenance": {"assembled_from": ["WEO Oct 2025 (frozen_extra), WDI 2026-10-08 (frozen_extra/wdi_20261008_*)"], "gold_script": "gold_scripts/lic_dsf_ci/make_items.py", "validation": "gold_scripts/lic_dsf_ci/validate.py"},
          "method": "lic_dsf_composite_indicator", "method_doc_ids": METHOD_DOCS, "gold_report_ids": [p['doc_id']],
          "published_value": p['published_ci'], "recomputed_value": round(v, 3), "tolerance": 0.10,
          "inputs": ["NGDP_RPCH", "IQ.CPA.IRAI.XQ", "FI.RES.TOTL.CD", "NE.IMP.GNFS.CD", "BX.TRF.PWKR.DT.GD.ZS", "NGDPRPPPPC", "LP"],
          "style": style, "subject": {"iso3": iso, "year": Y, "components": {k: round(x, 4) for k, x in comp.items()}}, "distractors": DIST, "famous_method": False}
    it.update(kw); return it
items = []
n = 0
NAMED = [('GHA', 2021), ('GIN', 2021), ('MDV', 2021), ('VUT', 2025), ('COM', 2025), ('SLB', 2023), ('HTI', 2019)]
QN = ["Looking at the data available up to %d, how would you rate %s's underlying capacity to carry external debt: weak, medium or strong, and what single score supports that rating?",
      "For the %d assessment round, which strength bucket (weak, medium or strong) describes how much debt %s can safely carry, given its institutions, growth, reserves and remittances, and what score puts it there?"]
for k, (iso, Y) in enumerate(NAMED):
    n += 1; items.append(base(n, 'named', QN[k % 2] % (Y, NAME[iso]), iso, Y, P[(iso, Y)]))
HID = [('DJI', 2024), ('LSO', 2024), ('NPL', 2023), ('ZMB', 2023), ('TZA', 2023), ('WSM', 2024), ('CPV', 2023)]
for iso, Y in HID:
    conds, m = hidden.build(iso)
    assert m == [iso], (iso, m)
    n += 1
    q = "Consider the economy that in 2023 had %s. How would you rate its underlying capacity to carry external debt as of the %d assessment round (weak, medium or strong), and what score supports that?" % ((', '.join(fmt(*c) for c in conds[:-1]) + (', and ' if len(conds) > 2 else ' and ') + fmt(*conds[-1]) if len(conds) > 1 else fmt(*conds[0])), Y)
    it = base(n, 'hidden', q, iso, Y, P[(iso, Y)])
    it['hidden_predicate'] = {"conditions": [{"feature": c[0], "op": c[1], "threshold": c[2], "year": 2023} for c in conds], "universe": "all WEO Oct 2025 economies with complete data for the features (192)", "set_size": len(m), "members": m}
    items.append(it)
# claim checks: (iso, Y, stated_value, stated_class, truth)
CHK = [('TLS', 2019, None, None), ('GHA', 2023, 3.15, 'strong'), ('LSO', 2022, None, None), ('WSM', 2019, 2.95, 'medium'), ('GIN', 2024, None, None), ('SLB', 2024, 3.10, 'strong')]
for iso, Y, sv, sc in CHK:
    n += 1; r = ci(iso, Y); v = r[0]
    stated = sv if sv is not None else P[(iso, Y)]['published_ci']
    scl = sc if sc else category(P[(iso, Y)]['published_ci'])
    truth = abs(stated - v) <= 0.10 and scl == category(v)
    q = "A briefing says that for %s, as assessed in %d, the debt-capacity score is %.2f and it is classed as %s. Is that statement correct?" % (NAME[iso], Y, stated, scl)
    it = base(n, 'claim_check', q, iso, Y, P[(iso, Y)])
    it['claim_under_test'] = {"stated_value": stated, "stated_class": scl, "truth": truth}
    it['claims']['answer'] = [{"id": "c4", "kind": "answer", "importance": "vital", "text": "Correct verdict: the statement is %s (recomputed score %.2f, class %s)." % ('TRUE' if truth else 'FALSE', v, category(v)), "accept": "full = verdict %s with recomputed score within +/-0.10; no = wrong verdict." % ('TRUE' if truth else 'FALSE'), "value": truth}]
    items.append(it)
for it in items: json.dump(it, open(os.path.join(OUT, it['id'] + '.json'), 'w'), indent=1)
print(len(items), 'items;', sum(1 for i in items if i['style'] == 'claim_check' and i['claim_under_test']['truth']), 'true claim-checks')
for it in items: print(it['id'], it['style'], it['subject']['iso3'], it['subject']['year'], it['published_value'], it['recomputed_value'], it['claims']['answer'][0]['value'])
