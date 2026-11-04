"""Extension parse: finds published CI scores in DSA/Article IV reports that gold_scripts/lic_dsf_ci/published_ci.json
does not yet contain. Input: two pipe-separated dumps from the corpus (a database dump), paths given as argv.
  argv[1]: tables.psv  = document_id|title|sequence|text  for table blocks containing '0.385' and 'CPIA'
  argv[2]: texts.psv   = document_id|title|sequence|type|text for blocks matching CI score phrases
Writes published_ci_extension.json (only country-years / documents NOT already in published_ci.json). Run with python3 -I."""
import re, json, sys, os, collections
HERE = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(HERE, 'published_ci.json')))
KNOWN_DOCS = {p['doc_id'] for p in P}; KNOWN_CY = {(p['iso3'], p['year']) for p in P}
ISO = {'Tuvalu': 'TUV', 'Kiribati': 'KIR', 'Papua New Guinea': 'PNG', 'Guinea-Bissau': 'GNB', 'Guinea': 'GIN', 'Nicaragua': 'NIC', 'Zambia': 'ZMB',
       'Federated States of Micronesia': 'FSM', 'Marshall Islands': 'MHL', 'Tonga': 'TON', 'Solomon Islands': 'SLB', 'Democratic Republic of the Congo': 'COD',
       'Kyrgyz Republic': 'KGZ', 'Cambodia': 'KHM', 'Guyana': 'GUY', 'Nepal': 'NPL', 'Democratic Republic of Timor-Leste': 'TLS', 'Vanuatu': 'VUT',
       'Uzbekistan': 'UZB', 'Ghana': 'GHA', 'Kenya': 'KEN', 'Comoros': 'COM', 'Bangladesh': 'BGD', 'Maldives': 'MDV', 'Honduras': 'HND',
       'Cabo Verde': 'CPV', 'Lesotho': 'LSO', 'Congo': 'COG', 'Samoa': 'WSM', 'Haiti': 'HTI', 'Djibouti': 'DJI', 'Mauritania': 'MRT', 'Tanzania': 'TZA', 'Tajikistan': 'TJK', 'Dominica': 'DMA', 'Zimbabwe': 'ZWE', 'Cameroon': 'CMR'}
def iso_of(title):
    head = title.split(':')[0].split(' Staff')[0]
    for k in sorted(ISO, key=len, reverse=True):
        if k.lower() in head.lower():
            if k == 'Guinea' and 'bissau' in head.lower(): continue
            if k == 'Congo' and 'democratic' in head.lower(): continue
            return ISO[k]
def year_of(title):
    m = re.search(r'(20\d\d) (?:Article|Request|Review|Consult)', title) or re.search(r'(20\d\d)', title); return int(m.group(1)) if m else None
rxt = re.compile(r'(?:CI\)?|composite (?:indicator|index)(?: \(CI\))?)[ )]*(?:score|index|rating)?\s*(?:\$\^\{\d+\}\$\s*)?(?:of|is|was|at|stands at|:|=)\s*(?:about )?([1-3]\.\d{1,3})', re.I)
rxtab = re.compile(r'\|\s*([1-3]\.\d{1,3})\s*\|\s*100%\s*\|')
found = collections.defaultdict(lambda: {'table': set(), 'text': set(), 'title': None})
for l in open(sys.argv[1]):
    p = l.rstrip('\n').split('|', 3)
    if len(p) < 4: continue
    found[p[0]]['title'] = p[1]
    for m in rxtab.finditer(p[3]): found[p[0]]['table'].add(m.group(1))
for l in open(sys.argv[2]):
    p = l.rstrip('\n').split('|', 4)
    if len(p) < 5: continue
    found[p[0]]['title'] = p[1]
    for m in rxt.finditer(p[4]): found[p[0]]['text'].add(m.group(1))
out = []; skipped = []
for d, f in found.items():
    t = f['title']
    if d in KNOWN_DOCS or not t or not re.search(r'Article IV|Debt Sustainability|Staff Report', t) or 'AMRO' in t: continue
    iso, y = iso_of(t), year_of(t)
    vals = f['table'] or f['text']
    if not (iso and y and vals): skipped.append((d, t[:80], sorted(f['table']), sorted(f['text']))); continue
    fl = sorted(float(x) for x in vals)
    if len(fl) > 1 and fl[-1] - fl[0] > 0.011: skipped.append((d, t[:80], 'conflict', sorted(vals))); continue
    v = max(fl, key=lambda x: len(str(x)))
    if not 1.0 < v < 4.0: skipped.append((d, t[:80], 'range', v)); continue
    out.append({'iso3': iso, 'year': y, 'doc_id': d, 'title': t, 'published_ci': v, 'source': 'table' if f['table'] else 'text'})
# manual additions: sentences read by hand from the report text (document-id prefix -> (iso3, value)); verified against the printed sentence
MANUAL = {'5416fe5b': ('DMA', 3.02), 'b26cdd27': ('KHM', 2.99), 'ff394839': ('KHM', 3.02), 'f01719d0': ('NPL', 3.28), '8a836345': ('CMR', 2.76),
          'b91da90e': ('VUT', 2.93), '50b01b30': ('UZB', 3.30), '857055e0': ('UZB', 3.24), '21aee525': ('TJK', 2.832), 'b47d573a': ('TON', 3.09),
          'a279b43e': ('TON', 3.06), '494ba491': ('TON', 3.12), '7035a184': ('KGZ', 3.06), '5b677022': ('NPL', 3.24), '677f9320': ('ZWE', 2.03),
          'bfc2ae83': ('BGD', 3.06), '86c97912': ('CMR', 2.61), 'c5faa177': ('LSO', 2.94), '9f6a7e54': ('SLB', 2.72), '5553db91': ('ZMB', 2.58)}
for d, t in [(k, v['title']) for k, v in found.items() if v['title']]:
    if d[:8] in MANUAL and d not in KNOWN_DOCS:
        iso, v = MANUAL[d[:8]]
        out.append({'iso3': iso, 'year': year_of(t), 'doc_id': d, 'title': t, 'published_ci': v, 'source': 'text-manual'})
        skipped = [s_ for s_ in skipped if s_[0] != d]
# one record per country-year; drop country-years already present in the original list
seen = {}
for r in sorted(out, key=lambda r: (r['source'] != 'table', r['doc_id'])):
    k = (r['iso3'], r['year'])
    if k in KNOWN_CY or k in seen: continue
    seen[k] = r
# every corpus document that prints a CI table/sentence for a country-year (all must be withheld as gold reports later)
byc = collections.defaultdict(list)
for d, f_ in found.items():
    t = f_['title']
    if t and 'AMRO' not in t and iso_of(t) and year_of(t) and (f_['table'] or f_['text'] or d[:8] in MANUAL): byc['%s-%d' % (iso_of(t), year_of(t))].append(d)
for p_ in P: byc.setdefault('%s-%d' % (p_['iso3'], p_['year']), [])
for p_ in P:
    if p_['doc_id'] not in byc['%s-%d' % (p_['iso3'], p_['year'])]: byc['%s-%d' % (p_['iso3'], p_['year'])].append(p_['doc_id'])
json.dump({k: sorted(v) for k, v in byc.items()}, open(os.path.join(HERE, 'doc_ids_by_country_year.json'), 'w'), indent=1)
res = sorted(seen.values(), key=lambda r: (r['iso3'], r['year']))
json.dump(res, open(os.path.join(HERE, 'published_ci_extension.json'), 'w'), indent=1)
print(len(res), 'new country-years;', len(skipped), 'skipped')
for s in skipped: print('SKIP', s)
