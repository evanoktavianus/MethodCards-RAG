"""Standalone data tool for research agents, modelled on a public-finance database connector (search_series, fetch_series, series_table).
Reads only the frozen files in tools/data/store/ plus countries.tsv. No database and no network at run time (except the optional embedding call).
Results are plain-text tables meant to be pasted into an LLM observation.

  search_series(query, limit=15, mode='hybrid'|'bm25') -> text table: series_id | source | name | description
  fetch_series(series_id, country, start_year, end_year) -> text table: country | period | value | is_projection
  series_table(series) -> text table, series = [{label, series_id, country, start_year, end_year}, ...]
  fetch_rows(...) -> (series_id, rows, notes) with rows as dicts, for programs (not capped).

series_id is "source:code" (imf_weo:NGDP_RPCH, wdi:NY.GDP.MKTP.CD, psd:DP.DOD.DSTC.CR.CG, imf_iip:P_MV) or a bare code, resolved across sources in
the order WEO, WDI, PSD, IIP (the answer says which one was used). country is ISO-2 or ISO-3, a comma list, or "all".
Hybrid search embeds the query with ONE OpenRouter call (openai/text-embedding-3-small, the model used for the stored vectors) and fuses the
dense ranking with BM25 by reciprocal rank fusion; with mode='bm25', or when no key / network is available, it uses BM25 alone and says so."""
import json, os, re, math, gzip, zlib, array, sys, urllib.request
try:
    import numpy as _np
except Exception:
    _np = None

HERE = os.path.dirname(os.path.abspath(__file__))
STORE = os.environ.get('DATATOOL_STORE', os.path.join(HERE, 'store'))
SOURCE_ORDER = ['imf_weo', 'wdi', 'psd', 'imf_iip']
SOURCE_NAMES = {'imf_weo': 'IMF World Economic Outlook', 'wdi': 'World Bank WDI', 'psd': 'World Bank Quarterly Public Sector Debt',
                'imf_iip': 'IMF International Investment Position (frozen extract)'}
ALIASES = {'weo': 'imf_weo', 'iip': 'imf_iip', 'imf_weo': 'imf_weo', 'wdi': 'wdi', 'psd': 'psd', 'imf_iip': 'imf_iip'}
ROW_CAP = 60          # rows shown per fetch_series / series_table
SEARCH_MAX = 25       # as in the connector
DESC_CHARS = 240
EMBED_MODEL = 'openai/text-embedding-3-small'
EMBED_CALLS = [0]     # embedding calls made by this process

_S = {}               # lazy state
def _meta():
    if 'meta' not in _S:
        _S['meta'] = json.load(open(os.path.join(STORE, 'meta.json')))
    return _S['meta']

# ------------------------------------------------------------------ countries
def _countries():
    if 'c' not in _S:
        i3, i2, names = {}, {}, {}
        p = os.path.join(HERE, 'countries.tsv')
        for line in open(p, encoding='utf-8'):
            a = line.rstrip('\n').split('\t')
            if len(a) >= 3:
                i3[a[0].upper()] = a[1].lower(); i2[a[1].lower()] = a[0].upper(); names[a[0].upper()] = a[2]
        _S['c'] = (i3, i2, names)
    return _S['c']

def _parse_countries(country):
    """-> (list of ISO-3, list of error strings). 'all' = every country in the connector's list (no aggregates)."""
    i3, i2, _ = _countries()
    parts = [p.strip() for p in str(country).split(',') if p.strip()]
    if not parts:
        return [], ['country is required: an ISO-2/ISO-3 code, a comma-separated list, or "all"']
    if any(p.lower() == 'all' for p in parts):
        return sorted(i3), []
    out, errs = [], []
    for p in parts:
        if len(p) == 2 and p.lower() in i2: c = i2[p.lower()]
        elif len(p) == 3 and p.upper() in i3: c = p.upper()
        elif len(p) == 3 and p.isalpha(): c = p.upper()      # not in the country list (e.g. an aggregate such as WLD): tried against the data
        else:
            errs.append('unknown country code: %s' % p); continue
        if c not in out: out.append(c)
    return out, errs

# ------------------------------------------------------------------ catalog
def _catalog():
    if 'cat' not in _S:
        _S['cat'] = [json.loads(l) for l in open(os.path.join(STORE, 'catalog.jsonl'), encoding='utf-8')]
        _S['by_id'] = {c['series_id'].lower(): i for i, c in enumerate(_S['cat'])}
    return _S['cat']

_STOP = set("a an and are as at be by for from has have in is it its of on or that the this to was were which with their they these those such than then there can may also not but if into per via".split())
def _toks(t):
    out = []
    for w in re.findall(r'[a-z0-9]+', (t or '').lower()):
        if w in _STOP or len(w) < 2: continue
        if len(w) > 4 and w.endswith('ies'): w = w[:-3] + 'y'
        elif len(w) > 3 and w.endswith('s') and not w.endswith('ss'): w = w[:-1]
        out.append(w)
    return out

def _bm25_index():
    if 'bm' not in _S:
        cat = _catalog(); post = {}; dl = []
        for i, c in enumerate(cat):
            tk = _toks(c['name']) * 3 + _toks(c['description'])      # name counts three times, as in the connector's token search
            dl.append(len(tk)); tf = {}
            for w in tk: tf[w] = tf.get(w, 0) + 1
            for w, n in tf.items(): post.setdefault(w, []).append((i, n))
        _S['bm'] = (post, dl, sum(dl) / max(1, len(dl)))
    return _S['bm']

def _bm25(query, k1=1.2, b=0.75):
    post, dl, avg = _bm25_index(); N = len(dl); sc = {}
    for w in set(_toks(query)):
        pl = post.get(w)
        if not pl: continue
        idf = math.log(1 + (N - len(pl) + 0.5) / (len(pl) + 0.5))
        for i, n in pl:
            sc[i] = sc.get(i, 0.0) + idf * n * (k1 + 1) / (n + k1 * (1 - b + b * dl[i] / avg))
    return sorted(sc.items(), key=lambda x: -x[1])

def _vectors():
    if 'vec' not in _S:
        n = len(_catalog()); raw = open(os.path.join(STORE, 'catalog_vectors.f32'), 'rb').read()
        dim = _meta()['embedding_dim']
        if _np is not None:
            v = _np.frombuffer(raw, dtype=_np.float32).reshape(n, dim)
            norms = _np.linalg.norm(v, axis=1); norms[norms == 0] = 1.0
            _S['vec'] = (v / norms[:, None], _np.linalg.norm(v, axis=1) > 0)
        else:
            a = array.array('f'); a.frombytes(raw)
            rows = []; ok = []
            for i in range(n):
                r = a[i * dim:(i + 1) * dim]; nr = math.sqrt(sum(x * x for x in r))
                ok.append(nr > 0); rows.append([x / nr for x in r] if nr > 0 else r)
            _S['vec'] = (rows, ok)
    return _S['vec']

def _api_key():
    k = os.environ.get('OPENROUTER_API_KEY')
    if k: return k
    return None

def _embed(query):
    """One embedding call (cached per process). Returns (vector or None, error text or None). Never prints the key."""
    cache = _S.setdefault('qcache', {})
    if query in cache: return cache[query], None
    key = _api_key()
    if not key: return None, 'no OpenRouter key available'
    err = None
    for attempt in range(2):
        try:
            EMBED_CALLS[0] += 1
            req = urllib.request.Request(__import__('os').environ.get('OPENROUTER_BASE','https://openrouter.ai/api/v1')+'/embeddings', data=json.dumps({'model': EMBED_MODEL, 'input': [query]}).encode(),
                                         headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
            d = json.load(urllib.request.urlopen(req, timeout=20))
            v = d['data'][0]['embedding']; cache[query] = v; return v, None
        except Exception as e:
            err = type(e).__name__
    return None, 'embedding call failed (%s)' % err

def _dense(vec_q, top=100):
    v, ok = _vectors()
    if _np is not None:
        q = _np.asarray(vec_q, dtype=_np.float32); q = q / (_np.linalg.norm(q) or 1.0)
        s = v @ q; s[~ok] = -9
        idx = _np.argsort(-s)[:top]
        return [(int(i), float(s[i])) for i in idx if ok[int(i)]]
    nq = math.sqrt(sum(x * x for x in vec_q)) or 1.0; q = [x / nq for x in vec_q]
    sc = [(i, sum(a * b for a, b in zip(r, q))) for i, r in enumerate(v) if ok[i]]
    return sorted(sc, key=lambda x: -x[1])[:top]

def _cell(s, n=None):
    s = re.sub(r'\s+', ' ', str(s)).strip().replace('|', '/')
    return s if n is None or len(s) <= n else s[:n - 3].rstrip() + '...'

def search_series(query, limit=15, mode='hybrid'):
    """Find series by what they measure. mode 'hybrid' (BM25 + dense, one embedding call) or 'bm25' (no network)."""
    cat = _catalog()
    try: limit = max(1, min(SEARCH_MAX, int(limit)))
    except Exception: limit = 15
    if not str(query).strip(): return 'error: query is empty'
    bm = _bm25(query)[:100]; how = 'bm25'; note = ''
    ranked = [i for i, _ in bm]
    if mode == 'hybrid':
        v, err = _embed(query)
        if v is None:
            note = 'note: dense search unavailable (%s); ranked by BM25 only.\n' % err
        else:
            de = [i for i, _ in _dense(v)]; sc = {}
            for lst in (ranked, de):
                for r, i in enumerate(lst): sc[i] = sc.get(i, 0.0) + 1.0 / (60 + r + 1)
            ranked = sorted(sc, key=lambda i: -sc[i]); how = 'hybrid (BM25 + dense, RRF)'
    ranked = ranked[:limit]
    if not ranked:
        return note + 'no series matches %r. Try other words (what the series measures, e.g. "general government gross debt").' % query
    rows = [[c['series_id'], c['source'], _cell(c['name']), _cell(c['description'], DESC_CHARS)] for c in (cat[i] for i in ranked)]
    return '%sSearch: %r, %s, %d of %d series in the catalog.\n' % (note, query, how, len(rows), len(cat)) + _table(['series_id', 'source', 'name', 'description'], rows)

def _table(header, rows):
    return '\n'.join(['| ' + ' | '.join(header) + ' |', '|' + '---|' * len(header)] + ['| ' + ' | '.join('' if x is None else str(x) for x in r) + ' |' for r in rows])

# ------------------------------------------------------------------ resolve + fetch
def resolve(ref):
    """-> (series_id, note) or raises ValueError with the closest matches. Bare codes: WEO, then WDI, then PSD, then IIP."""
    _catalog(); ref = str(ref).strip()
    if not ref: raise ValueError('a series needs a series_id')
    if ':' in ref:
        s, c = ref.split(':', 1); s = s.strip().lower(); c = c.strip()
        s = ALIASES.get(s, s)
        i = _S['by_id'].get('%s:%s' % (s, c.lower()))
        if i is not None: return _S['cat'][i]['series_id'], ''
        bare = c
    else:
        bare = ref
    hits = [c['series_id'] for c in _S['cat'] if c['code'].lower() == bare.lower()]
    if ':' not in ref and hits:
        hits.sort(key=lambda sid: SOURCE_ORDER.index(sid.split(':', 1)[0]))
        note = 'bare code %r resolved to %s' % (ref, hits[0])
        if len(hits) > 1: note += ' (also in: %s)' % ', '.join(hits[1:])
        return hits[0], note
    close = [_S['cat'][i]['series_id'] + ' (' + _cell(_S['cat'][i]['name'], 60) + ')' for i, _ in _bm25(bare.replace('_', ' ').replace('.', ' '))[:5]]
    raise ValueError('no series matches %r.%s' % (ref, (' Closest: ' + '; '.join(close)) if close else ' Find it with search_series.'))

def _member(source, code):
    """{iso3: [(period, value_text)]} for one stored code, or None."""
    cache = _S.setdefault('mem', {})
    k = (source, code)
    if k in cache: return cache[k]
    ik = 'idx_' + source
    if ik not in _S: _S[ik] = json.load(open(os.path.join(STORE, 'data_%s.idx.json' % source)))
    e = _S[ik].get(code)
    if e is None: return None
    with open(os.path.join(STORE, 'data_%s.csv.gz' % source), 'rb') as f:
        f.seek(e[0]); raw = f.read(e[1])
    out = {}
    for line in zlib.decompress(raw, 31).decode().splitlines():
        a = line.split(',')
        out.setdefault(a[2], []).append((a[3], a[4]))
    if len(cache) > 80: cache.clear()
    cache[k] = out
    return out

def _year(period):
    try: return int(str(period)[:4])
    except ValueError: return None

def fetch_rows(series_id, country, start_year, end_year):
    """-> (series_id, rows, notes). rows = dicts country, period, value (float), value_text, is_projection. Raises ValueError for a bad request."""
    sid, note = resolve(series_id)
    if not (isinstance(start_year, int) and isinstance(end_year, int)): raise ValueError('start_year and end_year must be whole years')
    if start_year > end_year: raise ValueError('start_year %d is after end_year %d' % (start_year, end_year))
    isos, errs = _parse_countries(country)
    if not isos and errs: raise ValueError('; '.join(errs) + _agg_hint(sid))
    source, code = sid.split(':', 1); data = _member(source, code) or {}
    pf = _meta().get('weo_projection_from') if source == 'imf_weo' else None
    rows = []
    for iso in isos:
        for period, vt in data.get(iso, ()):
            y = _year(period)
            if y is not None and start_year <= y <= end_year:
                rows.append(dict(country=iso, period=period, value=float(vt), value_text=vt, is_projection=(y >= pf) if pf else False))
    rows.sort(key=lambda r: (r['country'], r['period']))
    notes = ([note] if note else []) + errs
    return sid, rows, notes

def _src_line(sid):
    s = sid.split(':', 1)[0]; rel = _meta()['releases'].get(s, {}).get('release', '')
    return '%s (%s, release %s)' % (sid, SOURCE_NAMES.get(s, s), rel)

def _agg_hint(sid):
    """Text for a fetch that failed on a country code: which aggregate / world codes the store holds and how to fetch them."""
    i3 = _countries()[0]; source, code = sid.split(':', 1)
    own = sorted(k for k in (_member(source, code) or {}) if k not in i3)
    if 'agg' not in _S:
        found = {}
        for s in ('imf_weo', 'imf_iip'):
            ik = 'idx_' + s
            if ik not in _S: _S[ik] = json.load(open(os.path.join(STORE, 'data_%s.idx.json' % s)))
            for cd in _S[ik]:
                for k in (_member(s, cd) or {}):
                    if k not in i3: found.setdefault(k, []).append('%s:%s' % (s, cd))
        _S['agg'] = found
    t = ' Country codes are ISO-2 or ISO-3 (for example USA, KOR), a comma list, or "all" (all = countries only).'
    if own: t += ' %s holds these aggregate codes besides countries: %s; fetch one with country="%s".' % (sid, ', '.join(own), own[0])
    else: t += ' %s has country rows only, no aggregate or world row.' % sid
    by = {}
    for k, v in sorted(_S['agg'].items()):
        for s in v: by.setdefault(s, []).append(k)
    if by: t += ' Aggregate codes held elsewhere in the store: ' + '; '.join('%s: %s' % (s, ', '.join(ks)) for s, ks in sorted(by.items())) + '. World real GDP growth is imf_weo:WORLD_NGDP_RPCH with country="WLD".'
    return t

def fetch_series(series_id, country, start_year, end_year):
    """One series for one or more countries: country | period | value | is_projection (capped at %d rows)."""
    try:
        sid, rows, notes = fetch_rows(series_id, country, start_year, end_year)
    except ValueError as e:
        return 'error: %s' % e
    head = 'Series %s; country %s; %s-%s.' % (_src_line(sid), country, start_year, end_year)
    if notes: head += '\n' + '\n'.join('note: ' + n for n in notes)
    if not rows:
        i3 = _countries()[0]; odd = [c for c in _parse_countries(country)[0] if c not in i3]
        return head + '\n%s has no data for %s in that range.' % (sid, country) + (_agg_hint(sid) if odd else '')
    shown = rows[:ROW_CAP]
    t = head + '\n' + _table(['country', 'period', 'value', 'is_projection'], [[r['country'], r['period'], r['value_text'], str(r['is_projection']).lower()] for r in shown])
    if len(rows) > len(shown):
        t += '\n[truncated: showing the first %d of %d rows; narrow the countries or the years to see the rest]' % (len(shown), len(rows))
    return t
fetch_series.__doc__ = fetch_series.__doc__ % ROW_CAP

def series_table(series):
    """Several series side by side: year + one column per label (country + year when any series covers several countries)."""
    if not isinstance(series, list) or not series: return 'error: series must be a list with at least one entry'
    cols, skipped = [], []
    for sp in series:
        try:
            sid, rows, notes = fetch_rows(sp['series_id'], sp['country'], sp['start_year'], sp['end_year'])
            if not rows: raise ValueError('%s has no data for %s in that range' % (sid, sp['country']))
            cols.append(dict(label=str(sp['label']), sid=sid, rows=rows, sp=sp, notes=notes))
        except (ValueError, KeyError) as e:
            skipped.append('%s (%s, %s): %s' % (sp.get('label'), sp.get('series_id'), sp.get('country'), 'missing field ' + str(e) if isinstance(e, KeyError) else e))
    if not cols: return 'error: none of the %d series could be fetched: %s' % (len(series), '; '.join(skipped))
    labels = [c['label'] for c in cols]
    multi = any(len({r['country'] for r in c['rows']}) > 1 for c in cols)
    cells = {}
    for c in cols:
        for r in c['rows']:
            key = (r['country'], r['period']) if multi else r['period']
            cells.setdefault(key, {})[c['label']] = r['value_text']
    keys = sorted(cells)
    body = [(list(k) if multi else [k]) + [cells[k].get(l, '') for l in labels] for k in keys]
    header = (['country', 'year'] if multi else ['year']) + labels
    shown = body[:ROW_CAP]
    t = _table(header, shown)
    if len(body) > len(shown): t += '\n[truncated: showing the first %d of %d rows; narrow the countries or the years]' % (len(shown), len(body))
    src = ['%s <- %s' % (c['label'], _src_line(c['sid'])) for c in cols]
    notes = [n for c in cols for n in c['notes']]
    t += '\nSources: ' + '; '.join(src)
    if notes: t += '\n' + '\n'.join('note: ' + n for n in notes)
    if skipped: t += '\nnote: %d of %d series are not in this table: %s' % (len(skipped), len(series), '; '.join(skipped))
    return t

if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['search']: print(search_series(a[1], int(a[2]) if len(a) > 2 and a[2].isdigit() else 15, 'bm25' if '--bm25' in a else 'hybrid'))
    elif a[:1] == ['fetch']: print(fetch_series(a[1], a[2], int(a[3]), int(a[4])))
    else: print('usage: datatool.py search "<query>" [limit] [--bm25] | fetch <series_id> <country> <start_year> <end_year>')
