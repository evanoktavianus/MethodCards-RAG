"""Card builder, step 1 of 3: one chat call per document (or per window of a long document) with ONE generic prompt.
The prompt, the windowing and the cost estimate are those of the code that built the reported bank.

Input : a folder of UTF-8 text files <doc_id>.txt, with the marker [[page N]] at the start of each page,
        and an optional titles file (tab separated: doc_id, title, publisher).
Output: work/cards/compiled/<doc_id>_<window>.json   (resumable: an existing file is never called again)
        work/cards/compiled/<doc_id>_<window>.err    (a window that failed three times)

Safe by default: without --go nothing is called; the script lists documents, windows, tokens and the cost estimate.
The key is read only from the environment variable OPENROUTER_API_KEY (needed for --go only) and is never printed.

  python3 tools/cards/compile_cards.py --docs-dir DIR                 # dry run
  python3 tools/cards/compile_cards.py --docs-dir DIR --docs=ID,ID --go --cap 1.0 --maxcalls 50
"""
import argparse, concurrent.futures as cf, json, os, sys, threading, time, urllib.request

ROOT = os.environ.get('MC_ROOT') or os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
WORK = os.path.join(ROOT, 'work', 'cards')
DEFAULT_MODEL = 'z-ai/glm-5.3-flash'   # the reported cards were extracted and merged with this model
MODEL = os.environ.get('MC_CARD_MODEL') or DEFAULT_MODEL
BASE = os.environ.get('OPENROUTER_BASE', 'https://openrouter.ai/api/v1')
PROMPT = ("You read a public-finance or macroeconomic document. List every quantitative PROCEDURE the document defines or prescribes "
          "(a formula, index, decomposition, filter, threshold rule, classification, projection rule). For each, output a JSON object: "
          "name; aliases (other names used); institution and document title; applies_when (conditions, in one sentence); inputs (series or variables); "
          "formula (as stated, in plain text or LaTeX); parameters (list of {name, value, verbatim_quote, page}); procedure (numbered steps); "
          "open_points (what the document leaves open); pages. Quote parameter values verbatim; if a value is not given, write null. Do not invent. "
          "If the document defines no procedure, return an empty list. Output a single JSON list and nothing else.")
WIN, OVER, SPLIT = 600000, 20000, 700000     # tokens (chars/4)
MAXTOK = 16000


def windows(text, win=None, over=None):
    """Whole document if it has at most SPLIT tokens; otherwise overlapping windows cut at a line break."""
    W_, O_, S_ = WIN, OVER, SPLIT
    if win:
        W_ = win; O_ = over if over is not None else 5000; S_ = W_ + 50000
    n = len(text) // 4
    if n <= S_:
        return [text]
    out = []; s = 0; W = W_ * 4; O = O_ * 4
    while True:
        e = min(len(text), s + W)
        if e < len(text):                       # cut at a line break
            j = text.rfind('\n', s + W - 20000, e); e = j if j > s else e
        out.append(text[s:e])
        if e >= len(text):
            break
        s = e - O
    return out


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


def est_cost(text):
    """Estimated cost in USD of one window (input tokens = chars/4 with 8 percent margin, plus 6000 output tokens)."""
    return len(text) / 4 * 1.08 * 0.0345e-6 + 6000 * 0.0823e-6


def call(msgs, key):
    body = {'model': MODEL, 'messages': msgs, 'temperature': 0, 'max_tokens': MAXTOK, 'reasoning': {'effort': 'minimal'}}
    if MODEL == DEFAULT_MODEL:
        body['provider'] = {'order': ['relace'], 'allow_fallbacks': False}
    r = urllib.request.Request(BASE.rstrip('/') + '/chat/completions', data=json.dumps(body).encode(),
                               headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
    return json.load(urllib.request.urlopen(r, timeout=1500))


def out_path(outd, doc, w):
    return os.path.join(outd, '%s_%d.json' % (doc, w))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--docs-dir', default=os.environ.get('MC_CARD_DOCS'), help='folder of <doc_id>.txt files (default: env MC_CARD_DOCS)')
    ap.add_argument('--titles', default=None, help='titles file doc_id<TAB>title<TAB>publisher (default: DOCS_DIR/titles.tsv if present)')
    ap.add_argument('--docs', default=None, help='comma separated doc ids (default: all documents in the folder)')
    ap.add_argument('--go', action='store_true', help='make the model calls (without it: dry run, no call)')
    ap.add_argument('--dry', action='store_true', help='dry run (the default; wins over --go)')
    ap.add_argument('--cap', type=float, default=1.0, help='cost cap in USD (estimate plus cost already paid in this run)')
    ap.add_argument('--maxcalls', type=int, default=50, help='maximum number of model calls in this run')
    ap.add_argument('--workers', type=int, default=16)
    ap.add_argument('--win', type=int, default=None, help='window size in tokens (testing only; default 600000)')
    ap.add_argument('--over', type=int, default=None, help='window overlap in tokens (with --win)')
    a = ap.parse_args()

    if not a.docs_dir or not os.path.isdir(a.docs_dir):
        sys.exit('No documents folder: pass --docs-dir DIR or set MC_CARD_DOCS (a folder of <doc_id>.txt files).')
    D = load_docs(a.docs_dir)
    if not D:
        sys.exit('No .txt files in %s' % a.docs_dir)
    tpath = a.titles or os.path.join(a.docs_dir, 'titles.tsv')
    TIT = load_titles(tpath)
    if a.docs:
        ids = []
        for i in a.docs.split(','):
            i = i.strip()
            if not i:
                continue
            m = [x for x in D if x == i] or [x for x in D if x.startswith(i)]
            if not m:
                sys.exit('Document not found in %s: %s' % (a.docs_dir, i))
            ids.append(m[0])
    else:
        ids = sorted(D, key=lambda d: len(D[d]))
    outd = os.path.join(WORK, 'compiled')
    jobs = [(d, w, t) for d in ids for w, t in enumerate(windows(D[d], a.win, a.over))]
    todo = [j for j in jobs if not os.path.exists(out_path(outd, j[0], j[1]))]

    print('model %s | endpoint %s' % (MODEL, BASE))
    print('documents %d | windows %d | already done %d | to call %d' % (len(ids), len(jobs), len(jobs) - len(todo), len(todo)))
    for d in ids:
        ws = [j for j in jobs if j[0] == d]
        print('  %s  chars %d  windows %d  est input tokens %d  titled %s' % (d, len(D[d]), len(ws), sum(len(j[2]) // 4 for j in ws), d in TIT))
    est_all = sum(est_cost(j[2]) for j in todo)
    print('est input tokens (to call) %d | estimated cost of the windows to call: %.4f USD' % (sum(len(j[2]) // 4 for j in todo), est_all))
    print('limits: --cap %.2f USD, --maxcalls %d%s' % (a.cap, a.maxcalls, ' (windows beyond these limits are skipped)' if (est_all > a.cap or len(todo) > a.maxcalls) else ''))
    if a.dry or not a.go:
        print('DRY RUN: no call made. Add --go to call the model.')
        return
    key = os.environ.get('OPENROUTER_API_KEY')
    if not key:
        sys.exit('OPENROUTER_API_KEY is not set in the environment: nothing was called.')
    os.makedirs(outd, exist_ok=True)

    lock = threading.Lock(); tot = {'cost': 0.0, 'calls': 0, 'reserved': 0.0, 'skipped': 0, 'failed': 0}

    def job(doc, w, text):
        fn = out_path(outd, doc, w)
        if os.path.exists(fn):
            return
        est = est_cost(text)
        with lock:
            if tot['cost'] + tot['reserved'] + est > a.cap or tot['calls'] >= a.maxcalls:
                tot['skipped'] += 1; return
            tot['calls'] += 1; tot['reserved'] += est
        msg = PROMPT + "\n\nDOCUMENT TITLE: %s\n(Page markers look like [[page N]].)\n\n=== DOCUMENT START ===\n%s\n=== DOCUMENT END ===" % (TIT.get(doc, ''), text)
        err = None
        for att in range(3):
            try:
                d = call([{'role': 'user', 'content': msg}], key); c = d['choices'][0]; u = d.get('usage') or {}
                rec = {'doc': doc, 'w': w, 'chars': len(text), 'content': c['message'].get('content') or '', 'finish': c.get('finish_reason'),
                       'prompt_tokens': u.get('prompt_tokens'), 'completion_tokens': u.get('completion_tokens'), 'cost': u.get('cost') or 0, 'attempt': att}
                with open(fn, 'w', encoding='utf-8') as f:
                    json.dump(rec, f)
                with lock:
                    tot['cost'] += rec['cost']; tot['reserved'] -= est
                return
            except Exception as e:
                err = type(e).__name__ + ' ' + str(e)[:120]; time.sleep(5 * (att + 1))
                with lock:
                    tot['calls'] += 1
        with lock:
            tot['reserved'] -= est; tot['failed'] += 1
        with open(os.path.join(outd, '%s_%d.err' % (doc, w)), 'w', encoding='utf-8') as f:
            json.dump({'doc': doc, 'w': w, 'error': err}, f)

    t0 = time.time()
    with cf.ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(lambda j: job(*j), todo))
    print('done in %d s; calls %d; cost %.4f USD; skipped by cap/maxcalls %d; failed windows %d (see *.err)' % (
        round(time.time() - t0), tot['calls'], tot['cost'], tot['skipped'], tot['failed']))


if __name__ == '__main__':
    main()
