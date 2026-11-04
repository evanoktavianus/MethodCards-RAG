"""Local document search and page reading for the Ours arms: the methodology index (index M) of the corpus, served from files, in this process.

A port of the original search engine (search_server.py, which ran over a PostgreSQL corpus); the logic of search / read / find / pages is the same:
BM25 (k1 1.2, b 0.75) and dense cosine over chunks, best chunk per document, the best 100 documents of each list merged by reciprocal rank fusion (k 60);
chunks of a document are read in (sequence, order) order; profile "dta" hides table chunks of three Fiscal Monitor documents, profile "default" hides two of them entirely.
Files (made by export_corpus_from_postgres.py; NOT distributed with the repository, publishers' terms), in the folder env MC_DOCS_DIR (default data/documents/):
  chunks_M.jsonl.gz (or chunks_M.jsonl), chunk_vectors.f32, bm25_global.json, istbl.json, check.json
If they are absent, LocalDocs() raises DocsMissing with a one-sentence message.
Two small differences from the original, both in the dense list only (BM25, read, pages and find are exact):
  1. the original took the 3,000 most similar chunks of the WHOLE corpus (185,401 chunks) and then kept those in index M; here the 3,000 most similar
     chunks of index M (76,383 chunks) are taken, so a document can enter the dense list from rank 3,000 of index M that the original would have cut;
  2. cosine similarity is computed in float32 with numpy instead of in pgvector.
Optional document filter: if env TEXT_ALLOW_FILE names a file with one document id per line, search (BM25 and dense, the dense list taken
over the chunks of those documents only) returns only those documents (used by the Text-410 control, experiments/main_run/CTL_text410_docs.txt).
No model call is made here; the query vector (qvec) is passed in by the caller. Needs numpy.
"""
import gzip, json, math, os, re, threading
from array import array

import numpy as np

ROOT = os.environ.get('MC_ROOT') or os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STOP = set("a an and are as at be by for from has have in is it its of on or that the this to was were which with their they these those such than then there can may also not but if into per via".split())
TOK = re.compile(r"[a-z0-9]+")
ESC = str.maketrans({'\\': '\\\\', '\b': '\\b', '\f': '\\f', '\n': '\\n', '\r': '\\r', '\t': '\\t', '\v': '\\v'})
K1, B, RRF_K, POOL, DENSE_TOP = 1.2, 0.75, 60, 100, 3000


DOC_FILES = ('bm25_global.json', 'istbl.json', 'check.json', 'chunk_vectors.f32')


def docs_dir():
    """Folder with the document files: env MC_DOCS_DIR, default <repo>/data/documents."""
    return os.environ.get('MC_DOCS_DIR') or os.path.join(ROOT, 'data', 'documents')


def chunks_path(D):
    """chunks_M.jsonl.gz, or chunks_M.jsonl if only that exists; None if neither."""
    for n in ('chunks_M.jsonl.gz', 'chunks_M.jsonl'):
        if os.path.exists(os.path.join(D, n)):
            return os.path.join(D, n)
    return None


def docs_missing(D=None):
    """List of missing document files in D (default docs_dir()); empty if all are there."""
    D = D or docs_dir()
    miss = [n for n in DOC_FILES if not os.path.exists(os.path.join(D, n))]
    if chunks_path(D) is None:
        miss.append('chunks_M.jsonl.gz')
    return miss


def docs_message(D=None):
    return ("Document text is not distributed with this repository (publishers' terms). Put the document files in %s "
            "(see README, section Documents) or set MC_DOCS_DIR." % (D or docs_dir()))


class DocsMissing(RuntimeError):
    """The document files are not there; str(exception) is the message for the user."""


def toks(t):
    out = []
    for w in TOK.findall(t.lower()):
        if w in STOP or len(w) < 2:
            continue
        if len(w) > 4 and w.endswith('ies'):
            w = w[:-3] + 'y'
        elif len(w) > 3 and w.endswith('s') and not w.endswith('ss'):
            w = w[:-1]
        out.append(w)
    return out


class LocalDocs:
    def __init__(self, data_dir=None, params_file=None, titles_file=None):
        D = data_dir or docs_dir()
        if docs_missing(D):
            raise DocsMissing(docs_message(D))
        params = json.load(open(params_file or os.path.join(ROOT, 'tools', 'retrieval', 'params.json')))
        tf = titles_file or os.path.join(ROOT, 'data', 'corpus_index.json')
        self.titles = {x['id']: x['title'] for x in json.load(open(tf, encoding='utf-8'))}
        self.CLS = params['class']
        self.FMG = set(params['fm_gold_elsewhere'])
        g = json.load(open(os.path.join(D, 'bm25_global.json')))
        self.Nglob, self.avg, self.df = g['N'], g['total_dlen'] / g['N'], g['df']
        istbl = set(json.load(open(os.path.join(D, 'istbl.json'))))
        self.cid, self.doc, self.page, self.seq, self.text = [], [], [], [], []
        self.docs, self.docix, self.dlen, self.post = [], {}, array('I'), {}
        cp = chunks_path(D)
        with (gzip.open(cp, 'rt', encoding='utf-8') if cp.endswith('.gz') else open(cp, 'r', encoding='utf-8')) as f:
            for ci, line in enumerate(f):
                o = json.loads(line)
                d = o['d']
                di = self.docix.get(d)
                if di is None:
                    di = self.docix[d] = len(self.docs)
                    self.docs.append(d)
                tk = toks((o['b'] + ' ' + o['t']).translate(ESC))
                self.cid.append(o['id']); self.doc.append(di); self.page.append(o['p']); self.seq.append(o['q']); self.text.append(o['t'])
                self.dlen.append(len(tk))
                tfc = {}
                for w in tk:
                    tfc[w] = tfc.get(w, 0) + 1
                for w, c in tfc.items():
                    e = self.post.get(w)
                    if e is None:
                        e = self.post[w] = ([], [])
                    e[0].append(ci); e[1].append(min(c, 65535))
        self.N = len(self.cid)
        chk = json.load(open(os.path.join(D, 'check.json')))
        if chk['n_M'] != self.N or sum(self.dlen) != chk['sum_dlen_M']:
            raise RuntimeError('chunk files do not match check.json (n=%d, sum_dlen=%d)' % (self.N, sum(self.dlen)))
        self.cix = {c: i for i, c in enumerate(self.cid)}
        self.chunks_of = {}
        for ci, di in enumerate(self.doc):
            self.chunks_of.setdefault(di, []).append(ci)
        for di in self.chunks_of:
            self.chunks_of[di].sort(key=lambda c: (self.seq[c], c))
        self.istbl = bytearray(self.N)
        for c in istbl:
            if c in self.cix:
                self.istbl[self.cix[c]] = 1
        self.fmg_ix = {self.docix[d] for d in self.FMG if d in self.docix}
        af = os.environ.get('TEXT_ALLOW_FILE')
        allow = {x.strip() for x in open(af, encoding='utf-8') if x.strip()} if af else set()
        self.allow_ci = np.array([ci for ci in range(self.N) if self.docs[self.doc[ci]] in allow], dtype=np.int64) if allow else None
        self.allow_ix = {self.docix[d] for d in allow if d in self.docix} if allow else None
        self.V = np.memmap(os.path.join(D, 'chunk_vectors.f32'), dtype=np.float32, mode='r', shape=(self.N, 1536))
        nv = np.sqrt(np.einsum('ij,ij->i', self.V, self.V, dtype=np.float64)).astype(np.float32)
        self.vnorm = np.where(nv == 0, 1, nv)
        self.lock = threading.Lock()
        self.n_search = self.n_read = self.out_chars = 0
        self.info = {'ready': True, 'local': True, 'chunks_M': self.N, 'docs_M': len(self.chunks_of)}

    def ok(self, ci, profile, index='M'):
        if index != 'M':
            raise ValueError('only index M is available locally')
        if self.allow_ix is not None and self.doc[ci] not in self.allow_ix:
            return False
        if profile == 'dta':
            return not self.istbl[ci]
        return self.doc[ci] not in self.fmg_ix

    def _idf(self, w):
        df = self.df.get(w)
        return math.log(1 + (self.Nglob - df + 0.5) / (df + 0.5)) if df else 0.0

    def _bm25_scores(self, query, only=None):
        sc = {}
        for w in set(toks(query)):
            e = self.post.get(w)
            if not e:
                continue
            idf = self._idf(w)
            for ci, tf in zip(e[0], e[1]):
                if only is not None and ci not in only:
                    continue
                sc[ci] = sc.get(ci, 0.0) + idf * tf * (K1 + 1) / (tf + K1 * (1 - B + B * self.dlen[ci] / self.avg))
        return sc

    def _bm25(self, query, profile, index='M'):
        best = {}
        for ci, s in self._bm25_scores(query).items():
            if not self.ok(ci, profile, index):
                continue
            di = self.doc[ci]
            if s > best.get(di, (0, 0))[0]:
                best[di] = (s, ci)
        return sorted(best.items(), key=lambda x: -x[1][0])[:POOL]

    def _cos(self, qvec, idx=None):
        q = np.asarray(qvec, dtype=np.float32)
        qn = float(np.sqrt(np.dot(q, q))) or 1.0
        V = self.V if idx is None else self.V[idx]
        n = self.vnorm if idx is None else self.vnorm[idx]
        return (V @ q) / (n * qn)

    def _dense(self, qvec, profile, index='M'):
        if self.allow_ci is not None:      # the top chunks are taken among the allowed documents only
            sa = self._cos(qvec, self.allow_ci)
            s = np.full(self.N, -2.0, dtype=np.float32)
            s[self.allow_ci] = sa
        else:
            s = self._cos(qvec)
        top = np.argpartition(-s, min(DENSE_TOP, len(s) - 1))[:DENSE_TOP]
        top = top[np.argsort(-s[top], kind='stable')]
        best = {}
        for ci in top.tolist():
            if not self.ok(ci, profile, index):
                continue
            di = self.doc[ci]
            if di not in best:
                best[di] = (float(s[ci]), ci)
        return sorted(best.items(), key=lambda x: -x[1][0])[:POOL]

    def _texts(self, cis):
        return {self.cid[c]: self.text[c] for c in cis}

    def search(self, query, mode='hybrid', k=5, qvec=None, profile='default', snippet=400, index='M', prior=0, titles=0):
        k = max(1, min(int(k), 10)); lists = {}; snippet = max(100, min(int(snippet), 1500)); cof = self.chunks_of
        if mode in ('bm25', 'hybrid'):
            lists['bm25'] = self._bm25(query, profile, index)
        if mode in ('dense', 'hybrid'):
            if qvec is None:
                return {'error': 'dense/hybrid needs qvec'}
            lists['dense'] = self._dense(qvec, profile, index)
        score, chunk = {}, {}
        if mode == 'hybrid':
            for name in ('dense', 'bm25'):
                for r, (di, (s, ci)) in enumerate(lists[name], 1):
                    score[di] = score.get(di, 0.0) + 1.0 / (RRF_K + r); chunk[di] = ci
        else:
            (name, L), = lists.items()
            for di, (s, ci) in L:
                score[di] = s; chunk[di] = ci
        if titles or prior:
            raise ValueError('titles/prior options are not part of the reported runs and are not available locally')
        top = sorted(score, key=lambda d: -score[d])[:k]
        hits = []
        for rank, di in enumerate(top, 1):
            ci = chunk[di]
            t = ' '.join(self.text[ci].split())
            hits.append({'rank': rank, 'doc_id': self.docs[di], 'title': self.titles.get(self.docs[di], ''), 'page': self.page[ci],
                         'chunk_index': cof[di].index(ci), 'score': round(score[di], 5), 'snippet': t[:snippet]})
        with self.lock:
            self.n_search += 1; self.out_chars += sum(len(h['snippet']) for h in hits)
        return {'mode': mode, 'hits': hits, 'ms': 0}

    def _allc(self, doc_id, profile, index):
        di = self.docix.get(doc_id)
        if di is None or di not in self.chunks_of:
            return None, {'error': 'document not in the methodology index'}
        allc = [c for c in self.chunks_of[di] if self.ok(c, profile, index)]
        if not allc:
            return None, {'error': 'document not available in the methodology index'}
        return allc, None

    def _fin(self, r):
        with self.lock:
            self.n_read += 1; self.out_chars += len(json.dumps(r))
        return r

    def read(self, doc_id, start_chunk=0, n_chunks=3, profile='default', max_tokens=3000, index='M'):
        allc, err = self._allc(doc_id, profile, index)
        if err:
            return self._fin(err)
        start = max(0, int(start_chunk)); sel = allc[start:start + max(1, min(int(n_chunks), 8))]
        budget = max_tokens * 4; parts = []; used = 0; trunc = False
        for i, c in enumerate(sel):
            t = self.text[c]
            if used + len(t) > budget:
                trunc = True
                if not parts:
                    parts.append((start + i, self.page[c], t[:budget]))
                break
            parts.append((start + i, self.page[c], t)); used += len(t)
        nxt = (parts[-1][0] + 1) if parts else start
        return self._fin({'doc_id': doc_id, 'title': self.titles.get(doc_id, ''), 'total_chunks': len(allc),
                          'chunks': [{'chunk_index': a, 'page': p, 'text': t} for a, p, t in parts],
                          'next_start_chunk': nxt if nxt < len(allc) else None, 'truncated': trunc, 'approx_tokens': sum(len(p[2]) for p in parts) // 4})

    def pages(self, doc_id, page_from, page_to=None, profile='default', index='M', max_tokens=3000):
        allc, err = self._allc(doc_id, profile, index)
        if err:
            return self._fin(err)
        a = int(page_from); b = int(page_to if page_to is not None else page_from); sel = []
        for i, c in enumerate(allc):
            nxt = self.page[allc[i + 1]] if i + 1 < len(allc) else 10 ** 9
            if self.page[c] <= b and nxt >= a:
                sel.append((i, c))
        sel = sel[:8]; budget = max_tokens * 4; parts = []; used = 0; trunc = False
        for i, c in sel:
            t = self.text[c]
            if used + len(t) > budget:
                trunc = True
                if not parts:
                    parts.append({'chunk_index': i, 'page': self.page[c], 'text': t[:budget]})
                break
            parts.append({'chunk_index': i, 'page': self.page[c], 'text': t}); used += len(t)
        if not parts:
            return self._fin({'error': 'no chunk of this document covers those pages in the methodology index'})
        return self._fin({'doc_id': doc_id, 'title': self.titles.get(doc_id, ''), 'total_chunks': len(allc), 'chunks': parts, 'truncated': trunc,
                          'next_start_chunk': parts[-1]['chunk_index'] + 1 if parts[-1]['chunk_index'] + 1 < len(allc) else None})

    def find(self, doc_id, query, k=3, mode='bm25', qvec=None, profile='default', index='M'):
        allc, err = self._allc(doc_id, profile, index)
        if err:
            return self._fin(err)
        k = max(1, min(int(k), 8)); pos = {c: i for i, c in enumerate(allc)}
        sc = self._bm25_scores(query, only=pos)
        if mode in ('dense', 'hybrid'):
            if qvec is None:
                return {'error': 'dense/hybrid needs qvec'}
            s = self._cos(qvec, np.array(allc))
            dsc = {c: float(x) for c, x in zip(allc, s)}
            if mode == 'dense':
                sc = dsc
            else:
                rb = {c: r for r, c in enumerate(sorted(sc, key=lambda c: -sc[c]), 1)}
                rd = {c: r for r, c in enumerate(sorted(dsc, key=lambda c: -dsc[c]), 1)}
                sc = {c: (1.0 / (RRF_K + rb[c]) if c in rb else 0) + (1.0 / (RRF_K + rd[c]) if c in rd else 0) for c in set(rb) | set(rd)}
        top = sorted(sc, key=lambda c: -sc[c])[:k]
        return self._fin({'doc_id': doc_id, 'title': self.titles.get(doc_id, ''), 'total_chunks': len(allc), 'mode': mode,
                          'hits': [{'chunk_index': pos[c], 'page': self.page[c], 'score': round(sc[c], 4), 'text': ' '.join(self.text[c].split())[:700]} for c in top]})

    def budget(self):
        return {'searches': self.n_search, 'reads': self.n_read, 'embedding_calls_needed': 0, 'tool_output_tokens_approx': self.out_chars // 4}

    def close(self):
        pass


_SHARED = {}


def LocalDocsPool(*a, **k):
    """Same call as the original client (VMPool(host, n)): one shared in-process index, loaded once."""
    if 'x' not in _SHARED:
        _SHARED['x'] = LocalDocs()
    return _SHARED['x']
