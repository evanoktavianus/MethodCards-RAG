"""A scripted stand-in for OpenRouter, for tests that run the whole pipeline without a key, a network or a real model.
Start it, then set OPENROUTER_BASE=http://127.0.0.1:<port> and OPENROUTER_API_KEY=any. It answers
  /embeddings        a fixed unit vector,
  /chat/completions  for the judge model: a JSON verdict (score 1) for every claim id it may be asked about;
                     for the answer model: a fixed script  run_python -> Final Answer  (see ANSWER_SCRIPT).
Nothing here is a model: the scripted answers are not scored for correctness, only for the plumbing around them."""
import hashlib, http.server, json, re, threading

LOCK = threading.Lock()
STEP = {}
IDS_FILL = {'card_id': 'none', 'doc_id': 'none'}

JUDGE_MODEL_PREFIX = 'deepseek/'
IDS = ['c%d' % i for i in range(10)] + ['cv', 'cd', 'T1', 'D1', 'C1', 'c10']
PY = "Thought: compute a number first.\nAction: run_python\nAction Input:\n```python\nprint(2+2)\n```"
FINAL = "Thought: done.\nFinal Answer: The scripted answer is 4.\n\nMethod card: %(card_id)s\nSources: none"
# one step per call of the same conversation; the card and document ids are filled in by start()
SCRIPTS = {
    'cards': ["Thought: look for the method.\nAction: search_cards\nAction Input: debt stabilising primary balance",
              "Thought: read the card.\nAction: get_card\nAction Input: card_id=%(card_id)s",
              "Thought: read the source.\nAction: read_source\nAction Input: doc_id=%(doc_id)s pages=1-3", PY, FINAL],
    'text': ["Thought: search the documents.\nAction: search_methodology\nAction Input: debt stabilising primary balance",
             "Thought: read the source.\nAction: read_source\nAction Input: doc_id=%(doc_id)s pages=1-3",
             "Thought: look inside.\nAction: find_in_document\nAction Input: doc_id=%(doc_id)s query=primary balance", PY, FINAL],
    'plain': [PY, FINAL],
}


CARD_PROMPT_MARK = 'You read a public-finance or macroeconomic document'
PAGE_MARK = re.compile(r'\[\[page (\d+)\]\]')


def hash_vector(text):
    """Deterministic 1536 floats in [-1, 1) derived from a hash of the text (not a real embedding)."""
    v = []
    for j in range(48):
        v.extend((b - 127.5) / 128.0 for b in hashlib.sha256(('%d|%s' % (j, text)).encode('utf-8')).digest())
    return v


def scripted_cards(first):
    """Answer of the card compiler: a JSON list of two cards whose quotes are sentences of the document inside the request itself."""
    head, _, doc = first.partition('=== DOCUMENT START ===')
    m = re.search(r'DOCUMENT TITLE:[ \t]*([^\n]*)', head)
    title = (m.group(1).strip() if m else '') or 'Scripted indicator'
    doc = doc.split('=== DOCUMENT END ===')[0]
    marks = list(PAGE_MARK.finditer(doc))
    quotes = []                                  # (page, first sentence of 40+ characters of that page)
    for i, mk in enumerate(marks):
        seg = doc[mk.end(): marks[i + 1].start() if i + 1 < len(marks) else len(doc)]
        seg = re.sub(r'\s+', ' ', seg).strip()
        s = re.search(r'[^.]{40,}?\.', seg)
        if s:
            quotes.append((int(mk.group(1)), s.group(0).strip()))
    fm = re.search(r'Formula:[ \t]*([^\n]+)', doc)
    formula = fm.group(1).strip() if fm else ''
    params = [{'name': 'quoted statement %d' % p, 'value': '%d' % p, 'verbatim_quote': q, 'page': p} for p, q in quotes]
    cards = [{'name': title, 'aliases': [title + ' (alias)'], 'institution': 'Scripted Institute', 'document_title': title,
              'applies_when': 'The scripted document defines the indicator.', 'inputs': ['series A', 'series B'], 'formula': formula,
              'parameters': params, 'procedure': ['Step one.', 'Step two.'], 'open_points': [], 'pages': [p for p, _ in quotes] or [1]}]
    if quotes:
        p, q = quotes[-1]
        cards.append({'name': title + ' robustness check', 'aliases': [], 'applies_when': 'A second scripted procedure.', 'inputs': ['series A'],
                      'formula': '', 'parameters': [{'name': 'second quote', 'value': '%d' % p, 'verbatim_quote': q, 'page': p}],
                      'procedure': ['Step one.'], 'open_points': [], 'pages': [p]})
    return json.dumps(cards)


class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        if self.path.endswith('/embeddings'):
            inp = body.get('input')
            if isinstance(inp, list) and len(inp) != 1:   # batch: one deterministic vector per input, with its index
                out = {'data': [{'object': 'embedding', 'index': i, 'embedding': hash_vector(str(t))} for i, t in enumerate(inp)],
                       'usage': {'total_tokens': len(inp)}}
            else:                                    # one text (a query, as before also a list of one): the fixed unit vector
                v = [0.0] * 1536
                v[0] = 1.0
                out = {'data': [{'object': 'embedding', 'index': 0, 'embedding': v}], 'usage': {'total_tokens': 1}}
        else:
            first_user = next((m.get('content') for m in body.get('messages', []) if m.get('role') == 'user'), '')
            if isinstance(first_user, list):
                first_user = ' '.join(str(p.get('text', '')) for p in first_user if isinstance(p, dict))
            if CARD_PROMPT_MARK in str(first_user):
                txt = scripted_cards(str(first_user))
            elif str(body.get('model', '')).startswith(JUDGE_MODEL_PREFIX):
                txt = json.dumps({i: {'score': 1, 'reported_value': 0, 'reason': 'scripted'} for i in IDS})
            else:
                first = next(m['content'] for m in body['messages'] if m['role'] == 'user')
                kind = 'cards' if 'Action: search_cards' in first else ('text' if 'Action: search_methodology' in first else 'plain')
                key = hash(first)
                with LOCK:
                    n = STEP[key] = STEP.get(key, -1) + 1
                sc = SCRIPTS[kind]
                txt = sc[min(n, len(sc) - 1)] % IDS_FILL
            out = {'choices': [{'message': {'content': txt}, 'finish_reason': 'stop'}], 'usage': {'prompt_tokens': 10, 'completion_tokens': 10, 'cost': 0.0}}
        b = json.dumps(out).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)


def start(card_id='none', doc_id='none'):
    IDS_FILL.update(card_id=card_id, doc_id=doc_id)
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, 'http://127.0.0.1:%d' % srv.server_address[1]
