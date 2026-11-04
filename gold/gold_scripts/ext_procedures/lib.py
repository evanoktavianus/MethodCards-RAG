import csv, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
REF = os.path.join(ROOT, 'release/official_benchmark/reference_data')
EXTRA = os.path.join(ROOT, 'data/frozen_extra')

def wide(path):
    out = {}
    with open(path) as f:
        r = csv.DictReader(f)
        yrs = [c for c in r.fieldnames if c.isdigit()]
        for row in r:
            out[row['iso3']] = {int(y): float(row[y]) for y in yrs if row[y] not in ('', None)}
    return out

def psv(code):
    out = {}
    with open(os.path.join(EXTRA, 'wdi_20261008_ara_ig_extract.psv')) as f:
        for line in f:
            c, iso, p, v = line.rstrip('\n').split('|')
            if c != code: continue
            ps = p.strip('{}').split(','); vs = v.strip('{}').split(',')
            out[iso] = {int(a): float(b) for a, b in zip(ps, vs) if b not in ('NULL', '')}
    return out

def names():
    d = {}
    with open(os.path.join(REF, 'wb_classifications.csv')) as f:
        for r in csv.DictReader(f): d[r['iso3']] = r
    return d

import json, random
EU27 = "AUT BEL BGR HRV CYP CZE DNK EST FIN FRA DEU GRC HUN IRL ITA LVA LTU LUX MLT NLD POL PRT ROU SVK SVN ESP SWE".split()
EURO_ADOPT = {}  # not used

def weo(code):
    return wide(os.path.join(EXTRA, 'weo_oct2025_%s.csv' % code))

def cname(iso):
    n = names()
    return n[iso]['name'] if iso in n else iso

def region(iso):
    return names()[iso]['region'].strip()

def tol_round(x, d=2):
    return round(x, d)

METRICS = {  # code, phrase for 'highest'/'lowest'
    'ngdp_rpch': ('the fastest real GDP growth', 'the slowest real GDP growth', 'growth'),
    'pcpipch': ('the highest consumer price inflation', 'the lowest consumer price inflation', 'inflation'),
    'ggxwdg_ngdp': ('the highest gross public debt ratio', 'the lowest gross public debt ratio', 'debt'),
    'ggxcnl_ngdp': ('the largest general government surplus', 'the largest general government deficit', 'balance'),
}

def hidden_candidates(year, universe, rng):
    """yield (iso, predicate text, set_size) where a region-wide extremum identifies exactly one country within universe(iso)->bool"""
    out = []
    for m, (hi, lo, _) in METRICS.items():
        W = weo(m)
        regs = {}
        for iso, s in W.items():
            if year in s and iso in names() and names()[iso]['income_group'] != 'Aggregates': regs.setdefault(region(iso), []).append((s[year], iso))
        for rg, lst in regs.items():
            if len(lst) < 4: continue
            lst.sort()
            for which, phr, tgt in (('hi', hi, lst[-1]), ('lo', lo, lst[0])):
                vals = [v for v, _ in lst]
                size = sum(1 for v in vals if v == tgt[0])
                if size == 1 and universe(tgt[1]):
                    out.append((tgt[1], 'the %s economy with %s in %d' % (rg_phrase(rg), phr, year), m, rg, which, len(lst)))
    rng.shuffle(out)
    return out

def rg_phrase(rg):
    return {'Sub-Saharan Africa': 'Sub-Saharan African', 'Latin America & Caribbean': 'Latin American or Caribbean',
            'East Asia & Pacific': 'East Asian or Pacific', 'Europe & Central Asia': 'European or Central Asian',
            'Middle East & North Africa': 'Middle Eastern or North African', 'South Asia': 'South Asian',
            'North America': 'North American', 'Middle East, North Africa, Afghanistan & Pakistan': 'Middle Eastern or North African'}.get(rg, rg)

def save(slug, item):
    d = os.path.join(ROOT, 'dataset/items', slug)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, item['id'] + '.json'), 'w') as f:
        json.dump(item, f, indent=1, ensure_ascii=False)

def base_item(id_, pattern, query, method, docs, alt, inputs, style, distractors, famous, claims, pub, rec, tol, script, selection, assembled, hidden=None, pred=None, note=''):
    return {"id": id_, "family": "methodology", "pattern": pattern, "tier": "analytical", "status": "validated", "query": query,
            "claims": claims, "grading": {"method": "answer_recall"},
            "provenance": {"assembled_from": assembled, "gold_script": script, "selection": selection},
            "method": method, "method_doc_ids": docs, "method_doc_alternatives": alt, "gold_report_ids": [],
            "gold_report_note": note, "published_value": pub, "recomputed_value": rec, "tolerance": tol,
            "inputs": inputs, "style": style, "distractors": distractors, "famous_method": famous,
            "hidden_set_size": hidden, "predicate": pred,
            "method_class": "institutional procedure" if method != 'x' else '', "validation_label": "formula-validated"}

def mk_claims(mtext, macc, comps, vtext, vacc, dtext):
    c = {"text": [{"id": "c0", "kind": "text", "importance": "vital", "text": mtext, "accept": macc},
                  {"id": "cv", "kind": "text", "importance": "vital", "text": vtext, "accept": vacc}],
         "data": [{"id": "cd", "kind": "data", "importance": "okay", "text": dtext}], "computation": []}
    for i, (t, ref, tol, unit, acc) in enumerate(comps, 1):
        c["computation"].append({"id": "c%d" % i, "kind": "computation", "importance": "vital", "text": t,
                                 "reference_value": ref, "tolerance": tol, "unit": unit, "accept": acc})
    return c

def split_styles(n_named, n_hidden, n_claim):
    return ['named'] * n_named + ['hidden'] * n_hidden + ['claim'] * n_claim
