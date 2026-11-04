"""Method-card arms. Ours-cards2: search_cards / get_card / read_source / run_python (no raw-text search).
Ours-oracle: Ours-cards2 with the method passage in the first message and card search limited to the method document.
Ours-text2: the same prompt with raw document text instead of cards (search_methodology / find_in_document / read_source / run_python).
Cards come from tools/bank (cards_final.jsonl, served by bank_server.py or bank_pg_client.py). Answer reports stay unreachable:
 - no card in the bank has an excluded document as a source (checked: 0 of 6,465), and
 - cards whose primary or any source is a Fiscal Monitor issue that is an answer report for other items (fm_gold_elsewhere) are hidden unless the item is a debt-target item,
 - read_source goes through the document-search service (ra.VM.pages / ra.VM.read), which applies the same exclusions and profile as every other tool.
All model-written Python runs in rb.run_python (sandbox). The orchestrating process only parses text and calls the model."""
import glob, re, sys, json, os, queue, threading, time
sys.path[:0] = [(__import__('os').environ.get('MC_ROOT') or __import__('os').path.abspath(__import__('os').path.join(__import__('os').path.dirname(__file__),'..','..')))+"/experiments/agent", (__import__('os').environ.get('MC_ROOT') or __import__('os').path.abspath(__import__('os').path.join(__import__('os').path.dirname(__file__),'..','..')))+"/tools/bank"]
from run_agent import rb, pr, eq, fmt_read
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../data_blocks'); import data_agent as DA   # data tool (env DATA_TOOL=1)
import run_agent as ra
BH = (__import__('os').environ.get('MC_ROOT') or __import__('os').path.abspath(__import__('os').path.join(__import__('os').path.dirname(__file__),'..','..')))+"/tools/bank/"
_P = json.load(open((__import__('os').environ.get('MC_ROOT') or __import__('os').path.abspath(__import__('os').path.join(__import__('os').path.dirname(__file__),'..','..')))+"/tools/retrieval/params.json"))
EXCL = set(_P["excluded"]); FMG = set(_P["fm_gold_elsewhere"])
CARDS = {}
_CF = BH + os.environ.get("CARDS_FILE", "cards_final.jsonl")
CARDS_MISSING = not os.path.exists(_CF)
if not CARDS_MISSING:
    for l in open(_CF):
        c = json.loads(l); CARDS[c["card_id"]] = c
CFG = {# cards2: card listing with source counts, sources shown first, read_source before compute, the cited card must be one that was opened
       'cards2': dict(card_search=10, get=6, src=6, search=0, find=0, py=4, turns=16, k=5, text=False, v2=True, multi=True),
       # text2: exact copy of cards2 with cards replaced by raw document text (LongDA-like arm). Card tools off; the 10 card searches -> 10 text searches, the 6 get_card -> 6 find_in_document.
       'text2': dict(card_search=0, get=0, src=6, search=10, find=6, py=4, turns=16, k=5, text=True, v2=True, docs=True, multi=True)}
BANK = None          # set by run_main: BankPool

class BankPoolMem:
    """N in-memory card-search servers (each loads the 6,465 cards and their vectors at start, about 30 s each, started in parallel). Env RB_BANK (default 2)."""
    def __init__(self, n=None):
        from bank_client import BankSearch
        n = n or int(os.environ.get("RB_BANK", "2")); t0 = time.time(); self.srv = [None] * n; self.free = queue.Queue()
        def st(i): self.srv[i] = BankSearch()
        th = [threading.Thread(target=st, args=(i,)) for i in range(n)]; [t.start() for t in th]; [t.join() for t in th]
        for s in self.srv: self.free.put(s)
        self.startup_s = round(time.time() - t0, 1); self.info = self.srv[0].info
    def _do(self, name, *a, **k):
        s = self.free.get()
        try: return getattr(s, name)(*a, **k)
        finally: self.free.put(s)
    def search(self, *a, **k): return self._do("search", *a, **k)
    def get_card(self, *a, **k): return self._do("get_card", *a, **k)
    def n_emb(self): return sum(s.n_emb for s in self.srv)
    def close(self):
        for s in self.srv: s.close()

class BankPGPool:
    """Postgres card search (bank_pg_client.BankPG; no card files shipped, no card server startup). Env CARDS_PG_BANK ('cards' default, or '512'), RB_BANKPG pool size (default 8)."""
    def __init__(self, n=None):
        from bank_pg_client import BankPG
        t0 = time.time(); self.b = BankPG(bank=os.environ.get("CARDS_PG_BANK", "cards"), pool=n or int(os.environ.get("RB_BANKPG", "8")))
        self.srv = self.b.s; self.startup_s = round(time.time() - t0, 1); self.info = {"backend": "pg", "bank": self.b.bank}
    def search(self, *a, **k): return self.b.search(*a, **k)
    def get_card(self, *a, **k): return self.b.get_card(*a, **k)
    def n_emb(self): return self.b.n_emb
    def close(self): self.b.close()

def BankPool(n=None):
    """The default backend is Postgres when a database is configured; CARDS_BACKEND=mem selects the in-memory BankSearch servers (the setting of this repository)."""
    if os.environ.get("ON_VM") == "1" and os.environ.get("CARDS_BACKEND", "pg") != "mem": return BankPGPool(n)
    return BankPoolMem(n)

def hidden(card, is_dta):
    docs = {card["doc_id"]} | {s["doc_id"] for s in card["sources"]}
    return bool(docs & EXCL) or (not is_dta and bool(docs & FMG))
def search_cards(q, is_dta, k=5, mode="hybrid", only_docs=None):
    r = BANK.search(q, k=20, mode=mode)
    hits = [h for h in r.get("hits", []) if not hidden(CARDS[h["card_id"]], is_dta)]
    if only_docs is None: return hits[:k]
    ok = lambda h: ({CARDS[h["card_id"]]["doc_id"]} | {s["doc_id"] for s in CARDS[h["card_id"]]["sources"]}) & only_docs   # Ours-oracle: cards of the method document only, same ranking
    keep = [h for h in hits if ok(h)]
    if not keep:   # none in the top 20: widen the same search, then fall back to the method document's cards in bank order
        try: keep = [h for h in BANK.search(q, k=1000, mode=mode).get("hits", []) if not hidden(CARDS[h["card_id"]], is_dta) and ok(h)]
        except Exception: keep = []
    if not keep: keep = [dict(card_id=cid, rank=j + 1) for j, cid in enumerate(x for x in CARDS if not hidden(CARDS[x], is_dta) and ok(dict(card_id=x)))]
    return [dict(h, rank=j + 1) for j, h in enumerate(keep)][:k]
def fmt_cards(hits):
    out = []
    for h in hits:
        c = CARDS[h["card_id"]]
        out.append(f"[{h['rank']}] card_id={c['card_id']} | {c['name']} | aliases: {'; '.join(c.get('aliases') or [])[:150]} | applies when: {(c.get('applies_when') or '')[:220]} | formula: {(c.get('short_formula') or c.get('formula') or '(none stated)')[:200]} | primary source: {c['doc_title'][:90]}, pages {c.get('pages')}")
    return '\n'.join(out) or '(no cards)'
def fmt_cards2(hits):
    """Listing for cards2: adds the number of sources, whether a source defines the method, and a flag for cards with no verified formula text (pointer cards)."""
    out = []
    for h in hits:
        c = CARDS[h["card_id"]]; srcs = c.get('sources') or []; nd = sum(1 for s in srcs if str(s.get('role', '')).startswith('defines'))
        f = c.get('formula') or ''
        fl = ("formula: " + f[:200]) if f else ("formula: NONE ON THIS CARD (pointer card; paraphrase: " + (c.get('short_formula') or '')[:120] + ")")
        out.append(f"[{h['rank']}] card_id={c['card_id']} | {c['name']} | applies when: {(c.get('applies_when') or '')[:200]} | {fl} | sources: {len(srcs)} ({nd} define the method) | primary: {c['doc_title'][:80]}, pages {c.get('pages')}")
    return '\n'.join(out) or '(no cards)'
def fmt_card2(c):
    """Full card with the sources FIRST (so a cut never loses document ids), conflicts shown, parameters capped."""
    srcs = c.get('sources') or []; srcs = sorted(srcs, key=lambda s: 0 if str(s.get('role', '')).startswith('defines') else 1)
    L = [f"card_id={c['card_id']}  {c['name']}", "aliases: " + '; '.join(c.get('aliases') or [])[:300], "applies when: " + (c.get('applies_when') or ''),
         f"SOURCES ({len(srcs)} in total; the document that defines the method is listed first; use its doc_id with read_source):"]
    for i, s in enumerate(srcs[:6]): L.append(f"  source {i}: doc_id={s['doc_id']} | {s['doc_title']} | pages {s['pages']} | role {s['role']} | quote: \"{(s.get('quote') or '')[:220]}\"")
    if len(srcs) > 6: L.append(f"  ... {len(srcs) - 6} more sources that restate the method (not shown)")
    cf = c.get('conflicts') or []
    if cf: L.append(f"CONFLICTS ({len(cf)}): other documents give different values; first ones: " + ' || '.join(json.dumps(x)[:260] for x in cf[:4]))
    L += ["inputs: " + '; '.join(map(str, c.get('inputs') or [])), "formula: " + (c.get('formula') or 'NONE ON THIS CARD (pointer card: open its source, or search for the paper it cites)')]
    if c.get('procedure'): L.append("procedure: " + ' | '.join(map(str, c['procedure'])))
    ps = c.get('parameters') or []
    for p in ps[:14]: L.append(f"parameter {p.get('name')} = {p.get('value')} (page {p.get('page')}, source {p.get('source')}) quote: \"{str(p.get('quote'))[:200]}\"")
    if len(ps) > 14: L.append(f"... {len(ps) - 14} more parameters not shown")
    if c.get('open_points'): L.append("open points: " + ' | '.join(map(str, c['open_points'])))
    return '\n'.join(L)[:7000]
def fmt_card(c):
    L = [f"card_id={c['card_id']}  {c['name']}", "aliases: " + '; '.join(c.get('aliases') or []), "applies when: " + (c.get('applies_when') or ''),
         "inputs: " + '; '.join(map(str, c.get('inputs') or [])), "formula: " + (c.get('formula') or '(none stated)')]
    if c.get('procedure'): L.append("procedure: " + ' | '.join(map(str, c['procedure'])))
    for p in c.get('parameters') or []: L.append(f"parameter {p.get('name')} = {p.get('value')} (page {p.get('page')}, source {p.get('source')}) quote: \"{p.get('quote')}\"")
    if c.get('open_points'): L.append("open points: " + ' | '.join(map(str, c['open_points'])))
    for i, s in enumerate(c['sources']): L.append(f"source {i}: doc_id={s['doc_id']} | {s['doc_title']} | pages {s['pages']} | role {s['role']} | quote: \"{s.get('quote')}\"")
    return '\n'.join(L)[:9000]
def fmt_hits2(r, snip=700):
    return '\n'.join(f"[{h['rank']}] doc_id={h['doc_id']} | {h['title']} | p.{h['page']} | {h['snippet'][:snip]}" for h in r.get('hits', [])) or '(no results)'
def fmt_find(d):
    if 'error' in d: return 'ERROR: ' + str(d['error'])
    return '\n\n'.join(f"[chunk {c['chunk_index']}, p.{c['page']}] {c['text']}" for c in d.get('hits', d.get('chunks', []))) or '(no matching passage)'
import uuid, math
_SYN = {}; _SYN_LOCK = threading.Lock()
def syn_id(cid): return str(uuid.uuid5(uuid.NAMESPACE_URL, 'methodcard:' + cid))   # 36-char id so a card passage can go through the same doc_id=... tool formats as a document
def card_of_syn(sid):
    with _SYN_LOCK:
        if not _SYN:
            for cid in CARDS: _SYN[syn_id(cid)] = cid
    return _SYN.get(sid)
def card_page_str(c):
    ps = [int(p) for p in (c.get('pages') or []) if isinstance(p, (int, float))]
    return '?' if not ps else (str(min(ps)) if min(ps) == max(ps) else f"{min(ps)}-{max(ps)}")
def fmt_hits_astext(hits, snip=700):
    """Same layout as fmt_hits2: '[rank] doc_id=<id> | <document title> | p.<page> | <700-character snippet>'; the passage is the card's indexed text."""
    return '\n'.join(f"[{j + 1}] doc_id={syn_id(h['card_id'])} | {CARDS[h['card_id']]['doc_title']} | p.{card_page_str(CARDS[h['card_id']])} | {CARDS[h['card_id']]['card_text'][:snip]}" for j, h in enumerate(hits)) or '(no results)'
def card_read(sid, is_dta):
    """Read tool of Cards-as-text: the single passage (the full card text), in the layout rb/ra read results have."""
    cid = card_of_syn(sid)
    if not cid or hidden(CARDS[cid], is_dta): return {'error': 'document not in the methodology index'}
    c = CARDS[cid]
    return {'title': c['doc_title'], 'total_chunks': 1, 'next_start_chunk': None, 'chunks': [{'chunk_index': 0, 'page': card_page_str(c), 'text': c['card_text']}]}
def card_find(sid, query, is_dta, k=3):
    """In-document search over the single card: BM25 (k1 1.2, b 0.75, same tokenizer as the bank) over ~300-character pieces of the card text."""
    from bank_pg_client import toks
    cid = card_of_syn(sid)
    if not cid or hidden(CARDS[cid], is_dta): return {'error': 'document not in the methodology index'}
    c = CARDS[cid]; sents = re.split(r'(?<=[.;?])\s+', c['card_text']); pieces = []; cur = ''
    for s in sents:
        if cur and len(cur) + len(s) > 300: pieces.append(cur); cur = s
        else: cur = (cur + ' ' + s).strip()
    if cur: pieces.append(cur)
    docs = [toks(p) for p in pieces]; N = len(docs); av = sum(len(x) for x in docs) / max(1, N); qt = set(toks(query)); sc = []
    for i, dt in enumerate(docs):
        s = 0.0
        for t in qt:
            tf = dt.count(t); df = sum(1 for x in docs if t in x)
            if tf: s += math.log(1 + (N - df + 0.5) / (df + 0.5)) * tf * 2.2 / (tf + 1.2 * (0.25 + 0.75 * len(dt) / av))
        sc.append((s, i))
    top = [i for s, i in sorted(sc, key=lambda x: (-x[0], x[1])) if s > 0][:k]
    return {'hits': [{'chunk_index': i, 'page': card_page_str(c), 'text': pieces[i]} for i in top]}
FINAL = rb.FINAL_FMT + "\nThe Final Answer must end with these two lines:\nMethod card: <card_id> (<name>)\nSources: <document title, pages>\nIf no card fits your question, write 'Method card: none' and explain why in one sentence."
FINAL_DOCS = rb.FINAL_FMT + "\nThe Final Answer must end with these two lines:\nMethod document: <doc_id> (<document title>), pages <first>-<last>\nSources: <document title, pages>\nIf no document fits your question, write 'Method document: none' and explain why in one sentence."
TURN_LINE = "You have {} turns. You may write several actions in one turn; all of them will be run in the order written and their results come back together in one Observation.\n\n"
def head_for(c): return DA.head_swap(_head_for(c))   # DATA_TOOL=1: data tool sentence + 3 action lines instead of the table
def _head_for(c):
    if c.get('fixed'): return head_for_fixed(c)
    if c.get('docs'): return head_for_docs(c)
    h = ("You answer public-finance questions. You have the data below, a bank of method cards (each card summarises one published methodology, with the document and pages it comes from), the documents themselves, and a Python tool. " + rb.LIB + "\n"
         "The question does not tell you which method to use.\n"
         "Work in this order. (1) Name two or three published methodologies that could answer the question (method names and the institutions that publish them); keep countries and years out of your searches. "
         "(2) search_cards for them by method name and typical words. (3) get_card for the best candidates and compare: when_applies, inputs, formula, parameters. "
         "(4) read_source to open the cited pages and check the formula and parameter values in the document itself. "
         "(5) Before you compute, quote the formula and the parameter values exactly as the document states them; if the document gives no value for a parameter, say so and state the convention you use. (6) Then compute with run_python and check the result against those stated values.\n")
    if c.get('v2'):
        i0 = h.index("Work in this order.")
        h = h[:i0] + (
            "Work in this order. (1) Name two or three published methodologies that could answer the question (method names and the institutions that publish them); keep countries and years out of your searches. "
            "(2) search_cards for them by method name, acronym and typical words; if the top cards look like reports that only use a method, search again with the name of the paper that defines it. "
            "(3) get_card for the best candidates. A card marked 'NONE ON THIS CARD' or 'pointer card' has no formula: it cannot be used alone, so open its source or follow the paper it cites. When several cards describe different versions of the method (different weights or years), compare them and say which version you use and why; if the question does not decide between them, compute both. "
            "(4) You MUST open the cited pages with read_source (use the doc_id of the source whose role is 'defines') before you compute, and check the formula and every parameter value against the document text. "
            "(5) Before you compute, quote the formula and each parameter value exactly as an observation shows it. Never take a weight, threshold or formula from memory: if no observation gives a value, search again or say plainly that you cannot compute it. "
            "(6) Then compute with run_python. Use the full data series for any filter or fit unless the source says otherwise, and check that the result is plausible for the country; if it is absurd or a read_source call failed, say so and fix it before answering. Use those libraries instead of hand-written maths. Report only numbers that your code printed in an Observation; if the code failed, fix it or say that you could not compute it. Do not use a different method (for example a linear trend instead of the filter the method names). Keep a step in reserve: you must write the Final Answer before the turns run out. In the Final Answer, give one clear verdict and number (no hedging), and 'Method card:' must name the card whose formula and parameters you actually used.\n"
            + ("Never write the Observation yourself.\n" if c.get('multi') else "Send ONE action per turn and then wait for the Observation: never write the Observation or later steps yourself.\n"))
    if c['text']: h += "If no card fits, you may fall back to searching the document text with search_methodology and find_in_document.\n"
    h += "Use exactly one of these formats per step.\nThought: your reasoning\nAction: search_cards\nAction Input: your query on one line\n\n"
    h += "Thought: your reasoning\nAction: get_card\nAction Input: card_id=<id from a search result>\n\n"
    h += "Thought: your reasoning\nAction: read_source\nAction Input: doc_id=<id of a card source> pages=<first>-<last>   (or: doc_id=<id> start=<chunk number>)\n\n"
    if c['text']:
        h += "Thought: your reasoning\nAction: search_methodology\nAction Input: your query on one line\n\n"
        h += "Thought: your reasoning\nAction: find_in_document\nAction Input: doc_id=<id> query=<words to look for inside that document>\n\n"
    h += "Thought: your reasoning\nAction: run_python\nAction Input:\n```python\ncode\n```\n\n"
    h += "You then receive an Observation. When you are ready to answer:\nThought: your reasoning\nFinal Answer: " + FINAL + "\n"
    if c.get('multi'): return h + TURN_LINE.format(c['turns']) + rb.FORCE_RULE
    h += f"Limits: at most {c['card_search']} card searches, {c['get']} get_card calls, {c['src']} read_source calls" + (f", {c['search']} text searches, {c['find']} find_in_document calls" if c['text'] else "") + f" and {c['py']} Python runs.\n\n" + rb.FORCE_RULE
    return h
def head_for_fixed(c):
    """Cards-fixed: the cards2 prompt with only the method-tool sentences changed (the five cards are already in the message; no search_cards / get_card / read_source)."""
    h = ("You answer public-finance questions. You have the data below, five method cards already retrieved for your question (each card summarises one published methodology, with the document and pages it comes from), and a Python tool. " + rb.LIB + "\n"
         "The question does not tell you which method to use.\n"
         "Work in this order. (1) Read the five method cards in the first message and choose the card whose method answers the question; the cards were retrieved automatically and some may describe other methods. "
         "(2) A card marked 'NONE ON THIS CARD' or 'pointer card' has no formula: it cannot be used alone. When several cards describe different versions of the method (different weights or years), compare them and say which version you use and why; if the question does not decide between them, compute both. "
         "(3) Before you compute, quote the formula and each parameter value exactly as the card shows it. Never take a weight, threshold or formula from memory: if no card gives a value, say plainly that you cannot compute it. "
         "(4) Then compute with run_python. Use the full data series for any filter or fit unless the card says otherwise, and check that the result is plausible for the country; if it is absurd, say so and fix it before answering. Use those libraries instead of hand-written maths. Report only numbers that your code printed in an Observation; if the code failed, fix it or say that you could not compute it. Do not use a different method (for example a linear trend instead of the filter the method names). Keep a step in reserve: you must write the Final Answer before the turns run out. In the Final Answer, give one clear verdict and number (no hedging), and 'Method card:' must name the card whose formula and parameters you actually used.\n"
         "Never write the Observation yourself.\n")
    h += "Use exactly one of these formats per step.\nThought: your reasoning\nAction: run_python\nAction Input:\n```python\ncode\n```\n\n"
    h += "You then receive an Observation. When you are ready to answer:\nThought: your reasoning\nFinal Answer: " + FINAL + "\n"
    return h + TURN_LINE.format(c['turns']) + rb.FORCE_RULE
def head_for_docs(c):
    """text2: the cards2 prompt with only the card sentences reworded to documents."""
    h = ("You answer public-finance questions. You have the data below, a search over the text of published methodology documents (each result shows the document, its title and the page), the documents themselves, and a Python tool. " + rb.LIB + "\n"
         "The question does not tell you which method to use.\n"
         "Work in this order. (1) Name two or three published methodologies that could answer the question (method names and the institutions that publish them); keep countries and years out of your searches. "
         "(2) search_methodology for them by method name, acronym and typical words; if the top results look like reports that only use a method, search again with the name of the paper that defines it. "
         "(3) Choose the best candidate documents. A document that only cites a method without stating its formula cannot be used alone, so open the paper it cites; find_in_document finds passages inside a document you have chosen. When several documents describe different versions of the method (different weights or years), compare them and say which version you use and why; if the question does not decide between them, compute both. "
         "(4) You MUST read the pages of the methodology document you found with read_source (use the doc_id of the document that defines the method) before you compute, and check the formula and every parameter value against the document text. "
         "(5) Before you compute, quote the formula and each parameter value exactly as an observation shows it. Never take a weight, threshold or formula from memory: if no observation gives a value, search again or say plainly that you cannot compute it. "
         "(6) Then compute with run_python. Use the full data series for any filter or fit unless the source says otherwise, and check that the result is plausible for the country; if it is absurd or a read_source call failed, say so and fix it before answering. Use those libraries instead of hand-written maths. Report only numbers that your code printed in an Observation; if the code failed, fix it or say that you could not compute it. Do not use a different method (for example a linear trend instead of the filter the method names). Keep a step in reserve: you must write the Final Answer before the turns run out. In the Final Answer, give one clear verdict and number (no hedging), and 'Method document:' must name the document whose formula and parameters you actually used.\n"
         + ("Never write the Observation yourself.\n" if c.get('multi') else "Send ONE action per turn and then wait for the Observation: never write the Observation or later steps yourself.\n"))
    h += "Use exactly one of these formats per step.\nThought: your reasoning\nAction: search_methodology\nAction Input: your query on one line\n\n"
    h += "Thought: your reasoning\nAction: read_source\nAction Input: doc_id=<id from a search result> pages=<first>-<last>   (or: doc_id=<id> start=<chunk number>)\n\n"
    h += "Thought: your reasoning\nAction: find_in_document\nAction Input: doc_id=<id> query=<words to look for inside that document>\n\n"
    h += "Thought: your reasoning\nAction: run_python\nAction Input:\n```python\ncode\n```\n\n"
    h += "You then receive an Observation. When you are ready to answer:\nThought: your reasoning\nFinal Answer: " + FINAL_DOCS + "\n"
    h += TURN_LINE.format(c['turns']) + rb.FORCE_RULE if c.get('multi') else f"Limits: at most {c['search']} text searches, {c['find']} find_in_document calls, {c['src']} read_source calls and {c['py']} Python runs.\n\n" + rb.FORCE_RULE
    return h
CFG['oracle'] = dict(CFG['cards2'], oracle=True)   # Ours-oracle: cards2 + the method passage in the first message + search_cards limited to the method document (perfect retrieval)
# ---- ablation arms (Cards-fixed, Cards-as-text) ----
# fixed: Ours-cards2 with NO method tools; the top 5 cards of one search_cards call (question text as query, hidden cards dropped) are in the first message and count as opened.
CFG['fixed'] = dict(CFG['cards2'], card_search=0, get=0, src=0, fixed=True)
# astext: Ours-text2 (same prompt, tools, limits) over the text of the cards: each card is one passage, ranked by the card bank's own hybrid search (BM25 + dense, RRF 60, same index as search_cards).
CFG['astext'] = dict(CFG['text2'], astext=True)
ACTS = 'search_cards|get_card|read_source|search_methodology|find_in_document|run_python'
ACT_RE = re.compile(r'(?m)^[ \t]*Action:\s*(' + ACTS + r')\b')
ACT_RE_DT = re.compile(r'(?m)^[ \t]*Action:\s*(' + ACTS + '|' + '|'.join(DA.NAMES) + r')\b')
def parse_multi(t):
    """Multi-action arms: every action written before the Final Answer, in written order, as (name, input). No action but a bare code block counts as run_python."""
    i = t.find('Final Answer:'); body = t if i < 0 else t[:i]
    ms = list((ACT_RE_DT if DA.on() else ACT_RE).finditer(body)); out = []
    for k, m in enumerate(ms):
        seg = re.split(r'\n[ \t]*Thought:', body[m.end(): ms[k + 1].start() if k + 1 < len(ms) else len(body)])[0]
        out.append((m.group(1), seg.split('Action Input', 1)[1] if 'Action Input' in seg else (seg if m.group(1) == 'run_python' or m.group(1) in DA.NAMES else '')))   # no Action Input label: a code block (run_python) or JSON (data tools) right after the action name still counts, as in data_agent.parse_actions
    if not out and 'Action Input' not in body and rb.code_of(body): out = [('run_python', body)]
    return out
def agent_cards(i, variant='cards2', mode='hybrid'):
    S = DA.Session(i) if DA.on() else None
    r = _agent_cards(i, variant, mode, S)
    if S: r.update(S.log())
    return r
def _agent_cards(i, variant, mode, S):
    c = CFG[variant]; c = dict(c, turns=int(os.environ.get('AGENT_TURNS', c['turns']))) if c.get('multi') else c   # AGENT_TURNS: same step limit for every multi-action arm
    LIM = not c.get('multi'); it, d, _, info = pr.build(i); d = DA.ref_notes(i) if S else d; q = it['query']; is_dta = it['method'] == 'debt_target_adjustment'; prof = 'dta' if is_dta else 'default'
    only = None
    if c.get('oracle'):   # Ours-oracle: the method passage (excerpt + full passage) and card search limited to the method document
        fold = glob.glob(rb.rp.P + f'items/*/{i}.json')[0].split('/')[-2]
        if not rb.ORACLE_BOTH.get(fold): return dict(answer='', trace=[], error='ERROR no oracle excerpt for ' + fold, cost=0, truncated=False, no_oracle=True)
        d += "\nMethod passage (from the correct method document):\n" + rb.ORACLE_BOTH[fold] + "\n"; only = set(it['method_doc_ids'])
    fx = []
    if c.get('fixed'):   # Cards-fixed: one search_cards call with the question text as the query (same hybrid ranking, same hidden-card filter); top 5 cards in full (get_card format) in the first message
        fx = search_cards(q, is_dta, 5, mode)
        d += "\nMethod cards retrieved in advance for your question (the top 5 of one search with your question as the query; full card text):\n\n" + '\n\n'.join(f"[{j + 1}] " + fmt_card2(CARDS[h['card_id']]) for j, h in enumerate(fx)) + "\n"
    msgs = [{'role': 'user', 'content': head_for(c) + d + "\n" + q + (("\n\n" + rb.step_line(1, c['turns'])) if c.get('multi') else '')}]; tr = []; cost = 0; trunc = False; fmtrej = False; citerej = False
    n = dict(card_search=0, get=0, src=0, search=0, find=0, py=0, q=[]); seen = []; read_ids = []; cards_seen = []; cards_got = []; rd_seen = set()
    top_hits = []   # (rank, card_id) of the cards shown by card searches
    card_txt = {}
    for j, h in enumerate(fx): cards_seen.append(h['card_id']); cards_got.append(h['card_id']); top_hits.append((j + 1, h['card_id'])); card_txt[h['card_id']] = fmt_card2(CARDS[h['card_id']])   # the 5 cards count as opened
    V = {}   # final-step gate record (final_gate_waived, extra_call), filled on the last turn
    def res(ans, err=None):
        out = dict(answer=ans, trace=tr, error=err, cost=cost, truncated=trunc, n=n, seen=seen, read_ids=read_ids, cards_seen=cards_seen, cards_got=cards_got)
        out.update(V)
        if c.get('fixed'): out.update(fixed_card_ids=[h['card_id'] for h in fx], fixed_cards_text=[card_txt[h['card_id']] for h in fx], seen=[CARDS[h['card_id']]['doc_id'] for h in fx])
        if c.get('astext'):   # synthetic ids -> the cards' own document ids (primary doc), so method_doc_in_search / method_doc_read mean the same as for Ours-text2
            rd = lambda L: [CARDS[card_of_syn(x)]['doc_id'] for x in L if card_of_syn(x)]
            out.update(seen_syn=seen, read_ids_syn=read_ids, seen=rd(seen), read_ids=rd(read_ids))
        return out
    for turn in range(c['turns']):
        t, f, cc, e = rb.chat(msgs); cost += cc; trunc = trunc or f == 'length'; t = rb.strip_fake_obs(t); tr.append(('model', t))
        msgs.append({'role': 'assistant', 'content': t or ' '})
        if e: return res('', t)
        acts = parse_multi(t) or [(None, '')]
        if (not LIM) and turn == c['turns'] - 1:   # last step: nothing is run; the gates are waived and logged
            def gates(a):
                g = []
                if n['py'] == 0: g.append('no_python')
                if c.get('docs'):
                    if not re.search(r'Method document:', a): g.append('doc_format')
                    mm = re.search(r'Method document:\s*([0-9a-f-]{36})', a)
                    if mm and mm.group(1) not in read_ids: g.append('doc_not_read')
                else:
                    mm = re.search(r'Method card:\s*([0-9a-z]{8,12}-\d+)', a)
                    if not re.search(r'Method card:', a): g.append('card_format')
                    if mm and mm.group(1) not in cards_got: g.append('card_not_opened')
                return g
            if acts[0][0] is None and 'Final Answer:' in t: ans = t.split('Final Answer:', 1)[1].strip(); extra = False
            else:
                msgs.append({'role': 'user', 'content': rb.EXTRA_MSG}); t, f, cc, e = rb.chat(msgs); cost += cc; trunc = trunc or f == 'length'; t = rb.strip_fake_obs(t); tr.append(('model', t))
                if e: return res('', t)
                ans = rb.extra_answer(t); extra = True
            V['final_gate_waived'] = gates(ans); V['extra_call'] = extra; tr.append(('gate_waived', ','.join(V['final_gate_waived'])))
            return res(ans)
        multi_fin = (not LIM) and acts[0][0] is not None and 'Final Answer:' in t; parts = []
        for act, inp in acts:
            if act is None and 'Final Answer:' in t:
                ans = t.split('Final Answer:', 1)[1].strip()
                if n['py'] == 0: obs = 'Rejected: you must compute with run_python before giving a Final Answer. Run the tool now.'
                elif c.get('docs') and not re.search(r'Method document:', ans) and not fmtrej:
                    fmtrej = True; obs = 'Rejected: end the Final Answer with the lines "Method document: <doc_id> (<document title>), pages <first>-<last>" and "Sources: <document title, pages>" (or "Method document: none" and why).'
                elif c.get('docs') and not citerej and (lambda mm: bool(mm) and mm.group(1) not in read_ids)(re.search(r'Method document:\s*([0-9a-f-]{36})', ans)):
                    citerej = True; obs = 'Rejected: the document named on the "Method document:" line must be a document you read (read_source or find_in_document) and whose formula and parameters you actually used. Name that document, or read it first.'
                elif not c.get('docs') and not re.search(r'Method card:', ans) and not fmtrej:
                    fmtrej = True; obs = 'Rejected: end the Final Answer with the lines "Method card: <card_id> (<name>)" and "Sources: <document title, pages>" (or "Method card: none" and why).'
                elif c.get('v2') and not citerej and (lambda mm: bool(mm) and mm.group(1) not in cards_got)(re.search(r'Method card:\s*([0-9a-z]{8,12}-\d+)', ans)):
                    citerej = True; obs = 'Rejected: the card named on the "Method card:" line must be a card you opened with get_card and whose formula and parameters you actually used. Name that card, or open it first.'
                else:
                    return res(ans)
            elif (c.get('fixed') and act in ('search_cards', 'get_card', 'read_source', 'search_methodology', 'find_in_document')) or (c.get('astext') and act in ('search_cards', 'get_card')): obs = 'No valid action. Use one of the formats, or Final Answer.'   # tools this ablation arm does not have
            elif act == 'search_cards':
                qq = inp.lstrip(': \n').split('\n', 1)[0].strip().strip('"')
                if (LIM and n['card_search'] >= c['card_search']) or not qq: obs = 'Card search limit reached or empty query.'
                else:
                    n['card_search'] += 1; n['q'].append(qq); hits = search_cards(qq, is_dta, c['k'], mode, only); cards_seen += [h['card_id'] for h in hits]; top_hits += [(h['rank'], h['card_id']) for h in hits]; obs = (fmt_cards2 if c.get('v2') else fmt_cards)(hits)
                    if n['card_search'] == 1 and c.get('v2') and c.get('multi') and not c.get('text'):   # Ours-cards2 / Ours-oracle: after the FIRST card search, up to 3 more cards found with the question text itself as the query (same search, same document filter, not repeated)
                        try:
                            shown = {h['card_id'] for h in hits}; ex = [h for h in search_cards(q, is_dta, c['k'] + 3, mode, only) if h['card_id'] not in shown][:3]
                            ex = [dict(h, rank=j + 1) for j, h in enumerate(ex)]
                            if ex: cards_seen += [h['card_id'] for h in ex]; top_hits += [(h['rank'], h['card_id']) for h in ex]; obs += "\n\nCards matching the question's own words:\n" + fmt_cards2(ex)
                        except Exception: pass
            elif act == 'get_card':
                mc = re.search(r'card_id\s*=\s*([0-9a-z]{8,12}-\d+)', inp)
                if (LIM and n['get'] >= c['get']) or not mc: obs = 'get_card limit reached or format: card_id=<id>.'
                elif mc.group(1) not in CARDS or hidden(CARDS[mc.group(1)], is_dta): obs = 'ERROR: unknown card_id.'
                else: n['get'] += 1; cards_got.append(mc.group(1)); obs = (fmt_card2 if c.get('v2') else fmt_card)(CARDS[mc.group(1)])
            elif act == 'read_source':
                md = re.search(r'doc_id\s*=\s*([0-9a-f-]{36})', inp); mp = re.search(r'pages?\s*=\s*(\d+)(?:\s*[-–]\s*(\d+))?', inp); ms = re.search(r'start\s*=\s*(\d+)', inp)
                if c.get('v2') and LIM and n['src'] >= c['src']: obs = f"read_source limit reached ({n['src']} of {c['src']} used)."
                elif c.get('docs') and not md: obs = "read_source needs doc_id=<the 36-character document id shown on a search result's 'doc_id=' field> and pages=<a>-<b> (or start=<chunk>)." + ("" if not LIM else " You have " + str(c['src'] - n['src']) + " reads left; this call was not counted.")
                elif c.get('v2') and not md: obs = "read_source needs doc_id=<the 36-character document id shown on a card's 'source i: doc_id=' line> (a card id like e7c9a1d0-01 is NOT a document id) and pages=<a>-<b> (or start=<chunk>)." + ("" if not LIM else " You have " + str(c['src'] - n['src']) + " reads left; this call was not counted.")
                elif c.get('v2') and md and (md.group(1), inp.strip()) in rd_seen: obs = "You already read exactly this: use the text you have, read other pages, or open another source. This call was not counted."
                elif (LIM and n['src'] >= c['src']) or not md: obs = 'read_source limit reached or format: doc_id=<id> pages=<a>-<b> (or start=<chunk>).'
                else:
                    n['src'] += 1; read_ids.append(md.group(1)); rd_seen.add((md.group(1), inp.strip()))
                    if c.get('astext'):
                        dd = card_read(md.group(1), is_dta)
                        if 'error' not in dd: cards_got.append(card_of_syn(md.group(1)))
                    else: dd = ra.VM.pages(md.group(1), int(mp.group(1)), int(mp.group(2) or mp.group(1)), profile=prof) if mp else ra.VM.read(md.group(1), int(ms.group(1)) if ms else 0, 3, profile=prof)
                    obs = fmt_read(dd)[:12000]
            elif act == 'search_methodology' and c['text']:
                qq = inp.lstrip(': \n').split('\n', 1)[0].strip().strip('"')
                if (LIM and n['search'] >= c['search']) or not qq: obs = 'Search limit reached or empty query.'
                else:
                    n['search'] += 1
                    if c.get('astext'):
                        hits = search_cards(qq, is_dta, c['k'], mode); seen += [syn_id(h['card_id']) for h in hits]; cards_seen += [h['card_id'] for h in hits]; obs = fmt_hits_astext(hits)
                    else:
                        qv = eq.embed(qq) if mode in ('hybrid', 'dense') else None
                        r = ra.VM.search(qq, mode=mode, k=c['k'], qvec=qv, profile=prof, snippet=700); seen += [h['doc_id'] for h in r.get('hits', [])]; obs = fmt_hits2(r)
            elif act == 'find_in_document' and c['text']:
                md = re.search(r'doc_id\s*=\s*([0-9a-f-]{36})', inp); mq = re.search(r'query\s*=\s*(.+)', inp)
                if (LIM and n['find'] >= c['find']) or not md or not mq: obs = 'find limit reached or format: doc_id=<id> query=<words>.'
                else:
                    n['find'] += 1; read_ids.append(md.group(1)); dd = (card_find(md.group(1), mq.group(1).strip().split('\n')[0].strip('"'), is_dta, k=3) if c.get('astext') else ra.VM.find(md.group(1), mq.group(1).strip().split('\n')[0].strip('"'), k=3, profile=prof)); obs = fmt_find(dd)[:12000]
            elif act == 'run_python':
                code = rb.code_of(inp)
                if c.get('docs') and n['py'] == 0 and n['src'] + n['find'] == 0: obs = "Rejected: before you compute, read the pages of the methodology document you found with read_source (doc_id from the search result) and quote the formula and parameter values from the document text."
                elif c.get('v2') and not c.get('fixed') and n['py'] == 0 and n['src'] + n['find'] == 0: obs = "Rejected: before you compute, open the cited pages of your chosen card with read_source (doc_id from the card's source line, role 'defines' first) and quote the formula and parameter values from the document text."
                elif code is None: obs = 'No code block: write the code in a ```python block after Action Input.'
                elif LIM and n['py'] >= c['py']: obs = 'Python limit reached.'
                else: n['py'] += 1; obs = rb.run_python(code)
            elif S and act in DA.NAMES: obs = S.run(act, inp)   # data tool (DATA_TOOL=1)
            else: obs = 'No valid action. Use one of the formats, or Final Answer.'
            parts.append(obs)
        obs = parts[0] if len(parts) == 1 else '\n\n'.join(f'[Action {k + 1} of {len(parts)}: {a}]\n{o}' for k, ((a, _), o) in enumerate(zip(acts, parts)))
        if multi_fin: obs += '\n\nYour Final Answer was ignored because actions in the same turn had not yet returned. Answer in a turn with no actions.'
        tr.append(('observation', obs)); msgs.append({'role': 'user', 'content': 'Observation:\n' + obs + (('\n\n' + rb.step_line(turn + 2, c['turns'])) if not LIM else '')})
    return res('', 'no final answer')

# ---- diagnostics on the cited card (no model call, no gold report) ----
_NORM = re.compile(r'\s+')
def _n(s): return _NORM.sub(' ', s or '').strip()
TEXTS = os.environ.get('MC_TEXTS') or (BH + 'data/texts.jsonl')   # full text of the documents behind the cards; not distributed (publishers' terms)
_off = None; _lock = threading.Lock(); _doc = {}
def _doctext(doc_id):
    global _off
    with _lock:
        if _off is None:
            _off = {}; p = 0
            with open(TEXTS, 'rb') as f:
                for line in f:
                    m = re.match(rb'\{"id": "([0-9a-f-]{36})"', line)
                    if m: _off[m.group(1).decode()] = p
                    p += len(line)
        if doc_id not in _doc:
            if doc_id not in _off: _doc[doc_id] = None
            else:
                with open(TEXTS, 'rb') as f: f.seek(_off[doc_id]); _doc[doc_id] = _n(json.loads(f.readline())['text'])
    return _doc[doc_id]
def card_diag(r, it):
    """cited_card_id from the 'Method card:' line; true-method flags against the item's method_doc_ids; quote check of the cited card."""
    m = re.search(r'Method card:\s*([0-9a-z]{8,12}-\d+)', r.get('answer') or '')
    cid = m.group(1) if m else None; none = bool(re.search(r'Method card:\s*none', r.get('answer') or '', re.I))
    md = set(it['method_doc_ids']); d = dict(cited_card_id=cid, cited_none=none, cited_card_known=cid in CARDS if cid else False)
    d['cited_in_got'] = cid in (r.get('cards_got') or []) if cid else False
    d['cited_in_seen'] = cid in (r.get('cards_seen') or []) if cid else False
    d['any_card_got_true_primary'] = any(CARDS[x]['doc_id'] in md for x in set(r.get('cards_got') or []) if x in CARDS)
    d['any_card_got_true_any'] = any(({s['doc_id'] for s in CARDS[x]['sources']} | {CARDS[x]['doc_id']}) & md for x in set(r.get('cards_got') or []) if x in CARDS)
    if cid in CARDS:
        c = CARDS[cid]; d['cited_card_is_true_method_primary'] = c['doc_id'] in md
        d['cited_card_is_true_method_any'] = bool(({s['doc_id'] for s in c['sources']} | {c['doc_id']}) & md)
        qs = [(s['doc_id'], s['quote']) for s in c['sources'] if s.get('quote')]
        srcs = c['sources']
        for p in c.get('parameters') or []:
            if p.get('quote'): qs.append((srcs[p['source']]['doc_id'] if isinstance(p.get('source'), int) and p['source'] < len(srcs) else c['doc_id'], p['quote']))
        fq = c.get("formula_quote")
        if isinstance(fq, dict):   # some cards store {quote, page, source}
            if fq.get("quote"): qs.append((srcs[fq["source"]]["doc_id"] if isinstance(fq.get("source"), int) and fq["source"] < len(srcs) else c["doc_id"], fq["quote"]))
        elif fq: qs.append((c["doc_id"], fq))
        found = 0
        if qs and not os.path.exists(TEXTS):   # no document text here: the quote check is skipped, not failed
            d['cited_card_quotes'] = len(qs); d['cited_card_quotes_found'] = None; d['cited_card_quotes_ok'] = None
            return d
        for did, qt in qs:
            tx = _doctext(did)
            if tx and _n(qt) in tx: found += 1
        d['cited_card_quotes'] = len(qs); d['cited_card_quotes_found'] = found; d['cited_card_quotes_ok'] = (found == len(qs)) if qs else None
    else: d.update(cited_card_is_true_method_primary=False, cited_card_is_true_method_any=False, cited_card_quotes=0, cited_card_quotes_found=0, cited_card_quotes_ok=None)
    return d
