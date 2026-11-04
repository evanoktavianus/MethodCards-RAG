"""Search over the method-card bank (tools/bank/cards.jsonl). Pure python.
    from bank_search import search_cards, get_card
    search_cards(query, k=5, mode='hybrid')   # mode: 'bm25' | 'dense' | 'hybrid' (RRF, score 1/(60+rank), top-100 per ranker)
    get_card(card_id)                          # full card dict
Dense needs the query embedding (openai/text-embedding-3-small via OpenRouter, 1 call) unless qvec is passed.
No model call other than that embedding."""
import json, re, math, os, urllib.request
from array import array
from operator import mul
ROOT = (__import__('os').environ.get('MC_ROOT') or __import__('os').path.abspath(__import__('os').path.join(__import__('os').path.dirname(__file__),'..','..'))); H = ROOT + '/tools/bank/'
STOP = set("a an and are as at be by for from has have in is it its of on or that the this to was were which with their they these those such than then there can may also not but if into per via".split())
TOK = re.compile(r"[a-z0-9]+"); K1, B, RRF_K, POOL = 1.2, 0.75, 60, 100
def toks(t):
    out = []
    for w in TOK.findall(t.lower()):
        if w in STOP or len(w) < 2: continue
        if len(w) > 4 and w.endswith("ies"): w = w[:-3] + "y"
        elif len(w) > 3 and w.endswith("s") and not w.endswith("ss"): w = w[:-1]
        out.append(w)
    return out
_S = {}
def _load():
    if _S: return _S
    cards = [json.loads(l) for l in open(H + 'cards.jsonl')]
    post = {}; dlen = []
    for i, c in enumerate(cards):
        tk = toks(c['card_text']); dlen.append(len(tk)); tf = {}
        for w in tk: tf[w] = tf.get(w, 0) + 1
        for w, n in tf.items(): post.setdefault(w, []).append((i, n))
    vec = None; vf = H + 'data/card_vectors.f32'
    if os.path.exists(vf):
        a = array('f'); a.frombytes(open(vf, 'rb').read()); d = len(a) // len(cards); vec = [a[i * d:(i + 1) * d] for i in range(len(cards))]
    _S.update(cards=cards, byid={c['card_id']: i for i, c in enumerate(cards)}, post=post, dlen=dlen, avg=sum(dlen) / len(dlen), vec=vec)
    return _S
def get_card(card_id):
    S = _load(); return S['cards'][S['byid'][card_id]]
RETRIES=[0]
def _uo(r,timeout,tries=6):
    """urlopen with exponential backoff + jitter on HTTP 429 and 5xx; retries counted in RETRIES."""
    import time,random,urllib.error
    for t in range(tries):
        try:return urllib.request.urlopen(r,timeout=timeout)
        except urllib.error.HTTPError as e:
            if (e.code==429 or e.code>=500) and t<tries-1:
                RETRIES[0]+=1;time.sleep(min(30,2**t)*(0.5+random.random()));continue
            raise
def embed(text):
    key = __import__('os').environ["OPENROUTER_API_KEY"]
    r = urllib.request.Request(__import__('os').environ.get('OPENROUTER_BASE','https://openrouter.ai/api/v1')+'/embeddings', data=json.dumps({'model': 'openai/text-embedding-3-small', 'input': text}).encode(),
                               headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
    return json.load(_uo(r, 120))['data'][0]['embedding']
def _bm25(q):
    S = _load(); N = len(S['cards']); sc = {}
    for w in set(toks(q)):
        e = S['post'].get(w)
        if not e: continue
        idf = math.log(1 + (N - len(e) + 0.5) / (len(e) + 0.5))
        for i, tf in e: sc[i] = sc.get(i, 0.0) + idf * tf * (K1 + 1) / (tf + K1 * (1 - B + B * S['dlen'][i] / S['avg']))
    return sorted(sc, key=lambda i: -sc[i])[:POOL]
def _dense(qvec):
    S = _load(); v = S['vec']
    if v is None: raise RuntimeError('no card vectors (run embed_cards.py)')
    n = math.sqrt(sum(x * x for x in qvec)); q = array('f', [x / n for x in qvec])
    sc = [sum(map(mul, q, c)) for c in v]
    return sorted(range(len(sc)), key=lambda i: -sc[i])[:POOL]
def search_cards(query, k=5, mode='hybrid', qvec=None, full=False):
    S = _load(); lists = []
    if mode in ('bm25', 'hybrid'): lists.append(_bm25(query))
    if mode in ('dense', 'hybrid'): lists.append(_dense(qvec if qvec is not None else embed(query)))
    f = {}
    for L in lists:
        for r, i in enumerate(L): f[i] = f.get(i, 0.0) + 1.0 / (RRF_K + r + 1)
    out = []
    for r, i in enumerate(sorted(f, key=lambda i: -f[i])[:k]):
        c = S['cards'][i]; o = {'rank': r + 1, 'card_id': c['card_id'], 'name': c['name'], 'doc_id': c['doc_id'], 'applies_when': c['applies_when'], 'pages': c.get('pages'), 'short_formula': c.get('short_formula', ''), 'kind': c.get('kind'),
             'sources': [{'doc_id': x['doc_id'], 'pages': x['pages'], 'role': x['role']} for x in c['sources']], 'score': round(f[i], 5)}
        if full: o['card'] = c
        out.append(o)
    return out
