"""Build the document files of the system from plain-text documents you obtain yourself (standard library only).

The original ingestion (parsing and chunking of the publishers' documents) is not part of this release. This script is a documented,
simpler replacement so that a reader with their own documents can run Ours-text2 (text search), the page reading (read_source) and the quote check.
A folder built this way is NOT the reported corpus: chunk boundaries, statistics and vectors differ, so results are not comparable number by number.

Input : DOCS_DIR with one UTF-8 file <doc_id>.txt per document, a page starts with the marker [[page N]] on its own line (same format as
        tools/cards/README.txt), and an optional DOCS_DIR/titles.tsv (doc_id TAB title TAB publisher; the title becomes the breadcrumb).
        For the quote check (agent_cards._doctext) the doc_id must look like a UUID (36 characters of 0-9, a-f and '-'); other ids are
        indexed and searchable but are skipped by that reader (a warning is printed).
Output: OUT (default data/documents)    chunks_M.jsonl, chunk_vectors.f32, bm25_global.json, istbl.json (empty list), check.json
        TEXTS_OUT (default tools/bank/data/texts.jsonl)   one JSON line per document: {"id", "n_chunks", "n_table_dropped", "text"}

Chunker: each page is cut on blank lines (paragraphs) and the paragraphs are packed into chunks of 200 to 350 words (a paragraph above 350 words is
cut at sentence ends, a sentence above 350 words at a word); a chunk never crosses a page. The text of a chunk is  <title> + blank line + body
(the title is the breadcrumb b; both are empty if no title is known). Chunk id = <doc_id>-<seq>, q = running number in the document, p = page, s = 'body'.
Text before the first marker is page 0. BM25 statistics (N, total_dlen, df) are counted over the chunks built here, with the tokeniser of local_docs.py.

Embeddings: openai/text-embedding-3-small through OpenRouter (1536 numbers per chunk). Key only from OPENROUTER_API_KEY, endpoint from OPENROUTER_BASE.
Safe by default: without --go nothing is called (dry run: documents, chunks, tokens, estimated cost). --go needs the key; --cap (USD) is enforced.

  python3 tools/retrieval/build_index.py --docs-dir DIR                       # dry run
  OPENROUTER_API_KEY=... python3 tools/retrieval/build_index.py --docs-dir DIR --go --cap 1.0
"""
import argparse, array, json, os, re, sys, time, urllib.request

ROOT = os.environ.get('MC_ROOT') or os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
BASE = os.environ.get('OPENROUTER_BASE', 'https://openrouter.ai/api/v1')
MODEL = 'openai/text-embedding-3-small'
PRICE = 0.02e-6          # USD per token
DIM = 1536
MINW, MAXW = 200, 350

# tokeniser: copied verbatim from tools/retrieval/local_docs.py (which imports numpy, so it is not imported here)
STOP = set("a an and are as at be by for from has have in is it its of on or that the this to was were which with their they these those such than then there can may also not but if into per via".split())
TOK = re.compile(r"[a-z0-9]+")
ESC = str.maketrans({'\\': '\\\\', '\b': '\\b', '\f': '\\f', '\n': '\\n', '\r': '\\r', '\t': '\\t', '\v': '\\v'})


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


PAGE = re.compile(r'(?m)^\[\[page (\d+)\]\][ \t]*\r?\n?')
UUID = re.compile(r'^[0-9a-f-]{36}$')


def load_docs(docs_dir):
    D = {}
    for fn in sorted(os.listdir(docs_dir)):
        if fn.endswith('.txt') and fn != 'titles.txt':
            with open(os.path.join(docs_dir, fn), encoding='utf-8') as f:
                D[fn[:-4]] = f.read()
    return D


def load_titles(path):
    T = {}
    if path and os.path.exists(path):
        for l in open(path, encoding='utf-8'):
            p = l.rstrip('\r\n').split('\t')
            if len(p) < 2 or p[0].startswith('#') or p[0] == 'doc_id':
                continue
            T[p[0]] = p[1]
    return T


def pages_of(text):
    """List of (page number, page text). Text before the first marker is page 0; a text without marker is one page 1."""
    parts = PAGE.split(text)
    if len(parts) == 1:
        return [(1, text)]
    out = []
    if parts[0].strip():
        out.append((0, parts[0]))
    for i in range(1, len(parts), 2):
        out.append((int(parts[i]), parts[i + 1]))
    return out


def units(page_text):
    """Paragraphs of a page (blank-line separated); a paragraph above MAXW words is cut at sentence ends, a sentence above MAXW at a word."""
    out = []
    for para in re.split(r'\n\s*\n', page_text):
        para = para.strip()
        if not para:
            continue
        if len(para.split()) <= MAXW:
            out.append(para)
            continue
        cur = []
        n = 0
        for s in re.split(r'(?<=[.!?])\s+', para):
            w = s.split()
            while len(w) > MAXW:
                if cur:
                    out.append(' '.join(cur)); cur = []; n = 0
                out.append(' '.join(w[:MAXW])); w = w[MAXW:]
            if not w:
                continue
            if cur and n + len(w) > MAXW:
                out.append(' '.join(cur)); cur = []; n = 0
            cur += w; n += len(w)
        if cur:
            out.append(' '.join(cur))
    return out


def chunk_page(page_text):
    """Bodies of the chunks of one page: paragraphs packed up to MAXW words; a chunk is closed once it has MINW words."""
    bodies = []
    cur = []
    n = 0
    for u in units(page_text):
        w = len(u.split())
        if cur and (n + w > MAXW or n >= MINW):
            bodies.append('\n\n'.join(cur)); cur = []; n = 0
        cur.append(u); n += w
    if cur:
        bodies.append('\n\n'.join(cur))
    return bodies


def chunk_doc(doc_id, text, title, q0=0):
    """Chunk records of one document, in the format of chunks_M.jsonl."""
    recs = []
    q = q0
    for pg, pt in pages_of(text):
        for body in chunk_page(pt):
            recs.append({'id': '%s-%d' % (doc_id, q), 'd': doc_id, 's': 'body', 'p': pg, 'q': q, 'b': title,
                         't': (title + '\n\n' + body) if title else body})
            q += 1
    return recs


def embed_batch(texts, key):
    body = {'model': MODEL, 'input': texts}
    r = urllib.request.Request(BASE.rstrip('/') + '/embeddings', data=json.dumps(body).encode(),
                               headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
    last = None
    for att in range(3):
        try:
            d = json.load(urllib.request.urlopen(r, timeout=300))
            break
        except Exception as e:
            last = e
            time.sleep(2 * (att + 1))
    else:
        sys.exit('Embedding call failed three times (%s: %s); nothing was written.' % (type(last).__name__, str(last)[:200]))
    rows = d.get('data') or []
    if len(rows) != len(texts):
        sys.exit('The embedding endpoint returned %d vectors for %d inputs; nothing was written.' % (len(rows), len(texts)))
    if all(isinstance(x, dict) and 'index' in x for x in rows):
        rows = sorted(rows, key=lambda x: x['index'])
    vecs = [x['embedding'] for x in rows]
    for v in vecs:
        if len(v) != DIM:
            sys.exit('Embedding of length %d, expected %d; nothing was written.' % (len(v), DIM))
    return vecs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--docs-dir', default=os.environ.get('MC_CARD_DOCS') or os.path.join(ROOT, 'work', 'docs'), help='folder of <doc_id>.txt files (default: env MC_CARD_DOCS or work/docs)')
    ap.add_argument('--titles', default=None, help='titles file doc_id<TAB>title<TAB>publisher (default: DOCS_DIR/titles.tsv if present)')
    ap.add_argument('--out', default=os.environ.get('MC_DOCS_DIR') or os.path.join(ROOT, 'data', 'documents'), help='output folder (default: env MC_DOCS_DIR or data/documents)')
    ap.add_argument('--texts-out', default=os.environ.get('MC_TEXTS') or os.path.join(ROOT, 'tools', 'bank', 'data', 'texts.jsonl'), help='full-text file (default: env MC_TEXTS or tools/bank/data/texts.jsonl)')
    ap.add_argument('--batch', type=int, default=64, help='chunks per embedding call')
    ap.add_argument('--go', action='store_true', help='make the embedding calls and write the files (without it: dry run, no call, nothing written)')
    ap.add_argument('--dry', action='store_true', help='dry run (the default; wins over --go)')
    ap.add_argument('--cap', type=float, default=1.0, help='cost cap in USD (estimate, checked before the first call)')
    a = ap.parse_args()

    if not os.path.isdir(a.docs_dir):
        sys.exit('No documents folder: pass --docs-dir DIR or set MC_CARD_DOCS (a folder of <doc_id>.txt files).')
    D = load_docs(a.docs_dir)
    if not D:
        sys.exit('No .txt files in %s' % a.docs_dir)
    TIT = load_titles(a.titles or os.path.join(a.docs_dir, 'titles.tsv'))
    chunks = []
    per_doc = {}
    for d in sorted(D):
        r = chunk_doc(d, D[d], TIT.get(d, ''))
        per_doc[d] = len(r)
        chunks += r
    if not chunks:
        sys.exit('The documents produced no chunk (empty files?).')
    ntok = sum(len(c['t']) // 4 for c in chunks)
    est = ntok * 1.08 * PRICE
    print('model %s | endpoint %s' % (MODEL, BASE))
    print('documents %d | chunks %d | est embedding tokens %d | estimated cost %.5f USD (cap %.2f)' % (len(D), len(chunks), ntok, est, a.cap))
    for d in sorted(D):
        note = '' if UUID.match(d) else '  (not a UUID: skipped by the quote check)'
        print('  %s  chars %d  chunks %d  titled %s%s' % (d, len(D[d]), per_doc[d], d in TIT, note))
    if a.dry or not a.go:
        print('DRY RUN: no call made, nothing written. Add --go to embed and write the files.')
        return
    if est > a.cap:
        sys.exit('Estimated cost %.5f USD is above --cap %.2f: nothing was called.' % (est, a.cap))
    key = os.environ.get('OPENROUTER_API_KEY')
    if not key:
        sys.exit('OPENROUTER_API_KEY is not set in the environment: nothing was called.')
    if a.batch < 1:
        sys.exit('--batch must be at least 1.')

    vecs = []
    for i in range(0, len(chunks), a.batch):
        vecs += embed_batch([c['t'] for c in chunks[i:i + a.batch]], key)
        print('embedded %d / %d' % (len(vecs), len(chunks)), flush=True)

    # statistics, with the escape rule of local_docs.py so that check.json is accepted
    N = len(chunks)
    tot = 0
    df = {}
    for c in chunks:
        tk = toks((c['b'] + ' ' + c['t']).translate(ESC))
        tot += len(tk)
        for w in set(tk):
            df[w] = df.get(w, 0) + 1
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, 'chunks_M.jsonl'), 'w', encoding='utf-8') as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False, separators=(',', ':')) + '\n')
    with open(os.path.join(a.out, 'chunk_vectors.f32'), 'wb') as f:
        for v in vecs:
            f.write(array.array('f', v).tobytes())
    with open(os.path.join(a.out, 'bm25_global.json'), 'w') as f:
        json.dump({'N': N, 'total_dlen': tot, 'df': df}, f)
    with open(os.path.join(a.out, 'istbl.json'), 'w') as f:
        json.dump([], f)
    with open(os.path.join(a.out, 'check.json'), 'w') as f:
        json.dump({'N': N, 'total_dlen': tot, 'n_M': N, 'sum_dlen_M': tot, 'sum_dlen_M_local_escape': tot, 'escape_rule_ok': True,
                   'dim': DIM, 'n_vectors': N}, f)
    tdir = os.path.dirname(os.path.abspath(a.texts_out))
    os.makedirs(tdir, exist_ok=True)
    with open(a.texts_out, 'w', encoding='utf-8') as f:
        for d in sorted(D):
            f.write(json.dumps({'id': d, 'n_chunks': per_doc[d], 'n_table_dropped': 0, 'text': D[d]}) + '\n')
    print('written: %d chunks, %d vectors to %s ; %d document texts to %s' % (N, len(vecs), a.out, len(D), a.texts_out))


if __name__ == '__main__':
    main()
