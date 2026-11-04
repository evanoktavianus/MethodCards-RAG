"""Data tool for the agent arms (env DATA_TOOL=1; default off = nothing changes).
Replaces the data table in the prompt with three actions: search_series, fetch_series, series_table (tools/data/datatool.py, frozen store).
Same text protocol as the other tools (Thought / Action: name / Action Input: JSON), usable in multi-action turns.
Search is hybrid (one embedding call per search) unless env DATA_SEARCH=bm25. The Python sandbox is unchanged (no files, no network):
the agent copies the numbers it fetched into its code. Per run the Session logs n_data_search, n_fetch, series fetched and data_hit."""
import os, re, sys, json, threading
BASE = (__import__('os').environ.get('MC_ROOT') or __import__('os').path.abspath(__import__('os').path.join(__import__('os').path.dirname(__file__),'..','..'))) + '/'
sys.path[:0] = [BASE + 'tools/data']
import datatool as dtool

NAMES = ('search_series', 'fetch_series', 'series_table')
CAP = 20000
def on(): return os.environ.get('DATA_TOOL') == '1'

# Identical words in every arm. DATA_INTRO replaces "the data below"; DATA_LINES is the 3-line description (placed next to the other tool formats).
DATA_INTRO = "a data tool (IMF WEO Oct 2025, World Bank WDI and Public Sector Debt, IMF IIP; series codes can be fetched directly when you know them)"
DATA_LINES = ('Action: search_series, Action Input: {"query": "what the series measures", "limit": 15}  (finds series_id, name, description)\n'
              'Action: fetch_series, Action Input: {"series_id": "<source:code or code>", "country": "GMB" or "EST,LVA,LTU" or "all", "start_year": 2013, "end_year": 2014}  (rows = countries, columns = years)\n'
              'Action: series_table, Action Input: {"series": [{"label": "...", "series_id": "...", "country": "...", "start_year": 2013, "end_year": 2014}]}  (several series side by side)\n')
def head_swap(h):
    """Prompt head with the data table sentence replaced and the data tool lines added before the 'Observation' sentence (no-op when off)."""
    if not on(): return h
    h = h.replace("You have the data below, ", "You have " + DATA_INTRO + ", ", 1).replace("You have the data below and ", "You have " + DATA_INTRO + " and ", 1)
    for mark in ("You then receive an Observation", "You will then receive an Observation"):
        if mark in h: return h.replace(mark, "Data tool actions (same layout as the actions above: Action: <name> on one line, Action Input: <JSON> on the next):\n" + DATA_LINES + "\n" + mark, 1)
    return h

_LOCK = threading.RLock(); _WARM = [False]
def _warm():
    with _LOCK:
        if not _WARM[0]:
            dtool._meta(); dtool._countries(); dtool._catalog(); dtool._bm25_index(); dtool._vectors(); _WARM[0] = True

def parse_actions(t):
    """Every action written before the Final Answer, in order: (name, input text) for run_python and the data actions."""
    i = t.find('Final Answer:'); body = t if i < 0 else t[:i]
    ms = list(re.finditer(r'(?m)^[ \t]*Action:\s*(run_python|search_series|fetch_series|series_table)\b', body)); out = []
    for k, m in enumerate(ms):
        seg = re.split(r'\n[ \t]*Thought:', body[m.end(): ms[k + 1].start() if k + 1 < len(ms) else len(body)])[0]
        out.append((m.group(1), seg.split('Action Input', 1)[1] if 'Action Input' in seg else seg))
    return out

def _json(inp):
    i = inp.find('{')
    if i < 0: raise ValueError('Action Input must be a JSON object')
    try: return json.JSONDecoder().raw_decode(inp[i:])[0]
    except Exception: raise ValueError('Action Input is not valid JSON (use double quotes, no trailing text inside the braces)')
def _int(x, name):
    try: return int(float(x))
    except Exception: raise ValueError('%s must be a whole year' % name)
def _cut(rows_text, head, tail, what):
    """head + table rows + tail, at most CAP characters; rows dropped from the end with a note."""
    out = head; n = 0
    for r in rows_text:
        if len(out) + len(r) + 1 + len(tail) + 200 > CAP: break
        out += '\n' + r; n += 1
    t = out + tail
    if n < len(rows_text): t += '\n[truncated: showing the first %d of %d %s because the observation is capped at %d characters; narrow the countries or the years]' % (n, len(rows_text), what, CAP)
    return t

def _wide(rows, label_col=None):
    """rows from fetch_rows -> (periods, {key: {period: text}}); key = country or (label, country)."""
    return sorted({r['period'] for r in rows})

def _fetch_text(sid, rows, notes, country, sy, ey):
    names = dtool._countries()[2]
    by = {}
    for r in rows: by.setdefault(r['country'], {})[r['period']] = r['value_text']
    per = sorted({r['period'] for r in rows}); pf = dtool._meta().get('weo_projection_from') if sid.startswith('imf_weo:') else None
    head = 'Series %s; countries %s; %s-%s.' % (dtool._src_line(sid), country, sy, ey)
    for n in notes: head += '\nnote: ' + n
    if pf and any((dtool._year(p) or 0) >= pf for p in per): head += '\nnote: values for years from %d on are IMF projections.' % pf
    head += '\n%d countries have data.\n| iso | country | ' % len(by) + ' | '.join(per) + ' |\n|---|---|' + '---|' * len(per)
    body = ['| %s | %s | ' % (c, dtool._cell(names.get(c, ''), 24)) + ' | '.join(by[c].get(p, 'n/a') for p in per) + ' |' for c in sorted(by)]
    return _cut(body, head, '', 'countries')

def do_fetch(a):
    sid, rows, notes = dtool.fetch_rows(a.get('series_id', ''), a.get('country', ''), _int(a.get('start_year'), 'start_year'), _int(a.get('end_year'), 'end_year'))
    if not rows:
        odd = [c for c in dtool._parse_countries(a.get('country', ''))[0] if c not in dtool._countries()[0]]   # an aggregate or unknown code: say which aggregate codes the store holds
        return sid, 'Series %s has no data for %s in %s-%s.%s' % (sid, a.get('country'), a['start_year'], a['end_year'], ''.join('\nnote: ' + n for n in notes)) + (dtool._agg_hint(sid) if odd else ''), False
    return sid, _fetch_text(sid, rows, notes, a['country'], a['start_year'], a['end_year']), True

def do_table(a):
    sp = a.get('series')
    if not isinstance(sp, list) or not sp: raise ValueError('"series" must be a list with at least one entry')
    cols, skipped = [], []
    for s in sp:
        try:
            sid, rows, notes = dtool.fetch_rows(s.get('series_id', ''), s.get('country', ''), _int(s.get('start_year'), 'start_year'), _int(s.get('end_year'), 'end_year'))
            if not rows: raise ValueError('%s has no data for %s in that range' % (sid, s.get('country')))
            cols.append(dict(label=str(s.get('label') or sid), sid=sid, rows=rows, notes=notes))
        except (ValueError, AttributeError) as e: skipped.append('%s (%s): %s' % ((s.get('label') if isinstance(s, dict) else s), (s.get('series_id') if isinstance(s, dict) else ''), e))
    if not cols: return [], 'error: none of the %d series could be fetched: %s' % (len(sp), '; '.join(skipped))
    multi = any(len({r['country'] for r in c['rows']}) > 1 for c in cols)
    names = dtool._countries()[2]
    if not multi:
        cells = {}
        for c in cols:
            for r in c['rows']: cells.setdefault(r['period'], {})[c['label']] = r['value_text']
        labs = [c['label'] for c in cols]; iso = sorted({r['country'] for c in cols for r in c['rows']})
        head = 'Countries %s.\n| period | ' % ', '.join(iso) + ' | '.join(labs) + ' |\n|---|' + '---|' * len(labs)
        body = ['| %s | ' % p + ' | '.join(cells[p].get(l, 'n/a') for l in labs) + ' |' for p in sorted(cells)]; what = 'periods'
    else:
        per = sorted({r['period'] for c in cols for r in c['rows']}); cells = {}
        for c in cols:
            for r in c['rows']: cells.setdefault((c['label'], r['country']), {})[r['period']] = r['value_text']
        head = '| series | iso | country | ' + ' | '.join(per) + ' |\n|---|---|---|' + '---|' * len(per)
        body = ['| %s | %s | %s | ' % (k[0], k[1], dtool._cell(names.get(k[1], ''), 24)) + ' | '.join(cells[k].get(p, 'n/a') for p in per) + ' |' for k in sorted(cells)]; what = 'rows'
    tail = '\nSources: ' + '; '.join('%s <- %s' % (c['label'], dtool._src_line(c['sid'])) for c in cols)
    tail += ''.join('\nnote: ' + n for c in cols for n in c['notes'])
    if any(c['sid'].startswith('imf_weo:') and any((dtool._year(r['period']) or 0) >= dtool._meta().get('weo_projection_from', 9999) for r in c['rows']) for c in cols):
        tail += '\nnote: IMF WEO values for years from %d on are projections.' % dtool._meta()['weo_projection_from']
    if skipped: tail += '\nnote: %d of %d series are not in this table: %s' % (len(skipped), len(sp), '; '.join(skipped))
    return [c['sid'] for c in cols], _cut(body, head, tail, what)

# ---- needs of an item -> store series ids
def need_ids(item_id):
    db = sys.modules.get('data_blocks'); nd = ((getattr(db, 'LAST', {}) or {}).get(item_id) or {}).get('needs') or {}
    out = {}
    for c in nd:
        code = c.split('@')[0]; ref = code
        if code.startswith('IIP:'): ref = 'imf_iip:' + code[4:]
        elif code.startswith('PSD:'): ref = 'psd:' + code[4:]
        try: out[c] = dtool.resolve(ref)[0]
        except Exception: out[c] = None
    return out

class Session:
    """One per agent run. run(name, input text) -> observation text (capped); log() -> fields for the result row."""
    def __init__(self, item_id):
        self.item = item_id; self.n_search = 0; self.n_fetch = 0; self.n_series_table = 0; self.n_error = 0; self.fetched = []
    def run(self, name, inp):
        try:
            a = _json(inp)
            if name == 'search_series':
                self.n_search += 1; q = str(a.get('query', '')); mode = 'bm25' if os.environ.get('DATA_SEARCH') == 'bm25' else 'hybrid'
                _warm()
                if mode == 'hybrid' and q.strip(): dtool._embed(q)   # the one embedding call, outside the lock (cached for the search below)
                with _LOCK: obs = dtool.search_series(q, a.get('limit', 15), mode)
            elif name == 'fetch_series':
                self.n_fetch += 1; _warm()
                with _LOCK: sid, obs, ok = do_fetch(a)
                if ok and sid not in self.fetched: self.fetched.append(sid)
            else:
                self.n_fetch += 1; self.n_series_table += 1; _warm()
                with _LOCK: sids, obs = do_table(a)
                self.fetched += [s for s in sids if s not in self.fetched]
        except ValueError as e: obs = 'error: %s' % e
        except Exception as e: obs = 'error: %s %s' % (type(e).__name__, str(e)[:150])
        if obs.startswith('error'): self.n_error += 1
        if len(obs) > CAP: obs = obs[:CAP] + '\n[truncated at %d characters; narrow the countries or the years]' % CAP
        return obs
    def log(self):
        ni = need_ids(self.item); res = [v for v in ni.values() if v]
        return dict(n_data_search=self.n_search, n_fetch=self.n_fetch, n_series_table=self.n_series_table, n_data_error=self.n_error, data_fetched_ids=list(self.fetched),
                    data_needs=ni, data_hit=bool(res) and all(v in self.fetched for v in res) if ni else None,
                    data_needs_fetched=sum(1 for v in res if v in self.fetched), data_needs_total=len(res))

def ref_notes(item_id):
    """DATA_TOOL=1 only: the group / membership lists the data table carries (classifications, not data values), as a short 'Reference lists:' note.
    Needs data_blocks.build(item_id) to have run (it fills data_blocks.LAST). The interest-paid note (which series to use) is not restored."""
    db = sys.modules.get('data_blocks'); L = (getattr(db, 'LAST', {}) or {}).get(item_id)
    if not L: return ''
    t = []; shown = L.get('shown') or []
    if L.get('region'): t.append('World Bank region of each economy shown: ' + '; '.join(f"{i} {db.wb()[i]['region']}" for i in shown))
    if 'fsi_group' in L.get('extra', []) and L.get('AE') is not None:
        ae = [i for i in shown if i in L['AE']]
        t.append(f"Country groups used by the fiscal stress index (IMF WP/11/100): advanced economies among those shown: {', '.join(ae) if ae else 'none'}; the others shown are emerging markets.")
    if 'eu27_cpi' in L.get('extra', []): t.append('EU27 members: ' + ', '.join(sorted(db.EU27)))
    return ('Reference lists:\n' + '\n'.join(t) + '\n') if t else ''
