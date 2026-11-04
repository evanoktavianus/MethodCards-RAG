"""Parse published debt-creating-flows tables (from corpus tables dumped to frozen_extra/debt_path_tables/dcf_tables.txt).
Output: frozen_extra/debt_path_tables/parsed.json : list of {doc, seq, title, years:[..], rows:{label:[vals aligned to years]}}"""
import re, json, os
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
SRC = ROOT + "/frozen_extra/debt_path_tables/dcf_tables.txt"
def num(s):
    s = s.strip().replace('−', '-').replace('−', '-')
    if re.fullmatch(r'-?\d+(\.\d+)?', s): return float(s)
    return None
def norm(l):
    l = re.sub(r'<br>', ' ', l); l = re.sub(r'\d+/', '', l)
    return re.sub(r'[^a-z]+', ' ', l.lower()).strip()
out = []
cur = None; buf = []
raw = open(SRC).read().split('\n')
recs = []
for line in raw:
    if re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-.*?§\d+§', line): 
        recs.append(line)
    elif recs: recs[-1] += '\n' + line
for r in recs:
    doc, seq, title, text = r.split('§', 3)
    rows = [[c.strip() for c in l.strip().strip('|').split('|')] for l in text.replace('\\n', '\n').split('\n') if l.strip().startswith('|')]
    rows = [x for x in rows if not all(set(c) <= set('- ') for c in x)]
    # header: row with >=4 year cells
    hdr = None
    for i, x in enumerate(rows[:6]):
        ys = [c for c in x if re.fullmatch(r'20\d\d|19\d\d', c)]
        if len(ys) >= 4: hdr = i; break
    if hdr is None: continue
    H = rows[hdr]
    years = []
    for j, c in enumerate(H):
        if re.fullmatch(r'(19|20)\d\d', c): years.append((j, int(c)))
    data = {}
    for x in rows[hdr+1:]:
        lab = norm(x[0])
        if not lab or lab in data: continue
        if len(x) != len(H): continue
        data[lab] = {y: num(x[j]) for j, y in years}
    if any('real gdp growth' in k for k in data):
        out.append(dict(doc=doc, seq=int(seq), title=title, years=[y for _, y in years], rows=data))
json.dump(out, open(ROOT + "/frozen_extra/debt_path_tables/parsed.json", 'w'))
print(len(recs), len(out))
