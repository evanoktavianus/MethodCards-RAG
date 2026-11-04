"""Shared helpers for count_metrics.py and ragas_judge.py (no model calls here).
Paths are relative to the repository root. (-I drops the script folder from sys.path, so the scripts insert it themselves.)"""
import json, os, re, glob

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) + '/'
BASE = os.path.dirname(ROOT.rstrip('/')) + '/'
MAIN = ROOT + 'experiments/main_run/'

DEFAULT_FILES = {  # group name -> result file
    'hard': MAIN + 'results_final_hard.jsonl',
    'easier': MAIN + 'results_final_easier.jsonl',
    'hard_datagiven': MAIN + 'results_final_hard_datagiven.jsonl',
}
ARM_ORDER = ['CoT0', 'CoT1', 'PoT', 'ReAct-v2', 'Ours-text2', 'Ours-cards2', 'Ours-oracle']
ARM_LABEL = {'CoT0': 'CoT0 (memory only)', 'CoT1': 'CoT1 (data in prompt)', 'PoT': 'PoT',
             'ReAct-v2': 'ReAct', 'Ours-text2': 'Ours-text2 (LongDA-style)',
             'Ours-cards2': 'Ours-cards2 (ours)', 'Ours-oracle': 'Ours-oracle (given method)'}
CARD_ARMS = ('Ours-cards2', 'Ours-oracle')   # arms with a card tool
TEXT_ARMS = ('Ours-text2',)                  # arms with document-text search
METHOD_TOOLS = ('search_cards', 'get_card', 'read_source', 'search_methodology', 'find_in_document')


def read_jsonl(path):
    out = []
    with open(path) as f:
        for l in f:
            l = l.strip()
            if l:
                out.append(json.loads(l))
    return out


def load_items():
    """item id -> item dict, with '_fold' = folder name (key of oracle_methods.json)."""
    items = {}
    for f in glob.glob(ROOT + 'dataset/items/*/*.json'):
        d = json.load(open(f))
        d['_fold'] = f.split('/')[-2]
        items[d['id']] = d
    return items


def load_oracle():
    p = ROOT + 'experiments/baselines/oracle_methods.json'
    return json.load(open(p)) if os.path.exists(p) else {}


def load_cards(paths=None):
    """card_id -> {doc_id, sources:[{doc_id,pages}]}. Reads cards_final.jsonl plus any extra card files."""
    paths = paths or [ROOT + 'tools/bank/cards_final.jsonl']
    cards = {}
    for p in paths:
        if not os.path.exists(p):
            continue
        for c in read_jsonl(p):
            cards[c['card_id']] = c
    return cards


# ---------- pages ----------
def page_set(pages):
    """Card source pages: a list of ints. One or two entries = a range (first..last); more = the listed pages."""
    pages = [int(p) for p in (pages or []) if isinstance(p, (int, float))]
    if not pages:
        return set()
    if len(pages) <= 2:
        return set(range(min(pages), max(pages) + 1))
    return set(pages)


def card_cites(card):
    """card -> list of (doc_id, page_set) over its sources (falls back to the card's own doc_id/pages)."""
    out = []
    for s in card.get('sources') or []:
        if s.get('doc_id'):
            out.append((s['doc_id'], page_set(s.get('pages'))))
    if not out and card.get('doc_id'):
        out.append((card['doc_id'], page_set(card.get('pages'))))
    return out


def doc_match(a, b):
    """doc ids as written by the agent may be an 8+ char prefix of the full id."""
    if not a or not b:
        return False
    a, b = a.strip().lower(), b.strip().lower()
    return a == b or (len(a) >= 8 and b.startswith(a)) or (len(b) >= 8 and a.startswith(b))


# ---------- method tree / node map / series equivalents (may be missing) ----------
def load_tree(path=None):
    path = path or ROOT + 'tools/bank/tree/method_tree_v2.jsonl'
    if not os.path.exists(path):
        return None
    return {t['method_id']: t for t in read_jsonl(path)}


def load_node_map(path=None):
    """{method (lower case): {nodes:[method_id], variants:[variant_id]}}; also accepts the old {method: [method_id]} form."""
    path = path or MAIN + 'method_node_map.json'
    if not os.path.exists(path):
        return None
    raw = json.load(open(path))
    out = {}
    for k, v in raw.items():
        out[k.lower()] = v if isinstance(v, dict) else {'nodes': list(v), 'variants': []}
    return out


def node_card_ids(tree, node_map, method):
    """cards under the mapped nodes (all their variants) and the mapped variants; None if unmapped or empty."""
    if tree is None or node_map is None or method is None:
        return None
    ent = node_map.get(str(method).lower())
    if not ent:
        return None
    nodes = set(ent.get('nodes') or []); vars_ = set(ent.get('variants') or [])
    ids = set()
    for mid, t in tree.items():
        for v in t.get('variants', []):
            if mid in nodes or v.get('variant_id') in vars_:
                ids.update(v.get('card_ids', []))
    return ids or None


class NodeIndex:
    """For one node: its cards, and what they cite (doc -> pages)."""
    def __init__(self, card_ids, cards):
        self.card_ids = set(card_ids)
        self.cites = []          # (doc_id, page_set)
        for cid in self.card_ids:
            c = cards.get(cid)
            if c:
                self.cites.extend(card_cites(c))
        self.missing = sum(1 for cid in self.card_ids if cid not in cards)

    def page_relevant(self, doc, page):
        return any(doc_match(doc, d) and (page in ps) for d, ps in self.cites)

    def doc_relevant(self, doc):
        return any(doc_match(doc, d) for d, _ in self.cites)


def load_equiv(path=None):
    """series id -> set of ids counted as the same (symmetric closure of 'equivalent')."""
    path = path or MAIN + 'series_equivalents.json'
    if not os.path.exists(path):
        return None
    raw = json.load(open(path))
    eq = {}
    for k, v in raw.items():
        eq.setdefault(k, set()).add(k)
        for e in (v.get('equivalent') or []):
            eq.setdefault(k, set()).add(e)
            eq.setdefault(e, set()).add(k)
    return eq


# ---------- trace parsing ----------
ACT_RE = re.compile(r'Action:\s*([A-Za-z_]+)\s*,?\s*\n?\s*Action Input:\s*(.*?)(?=\n\s*(?:Thought:|Action:|Observation)|\Z)', re.S)
HDR_RE = re.compile(r'\[Action (\d+) of (\d+): ([A-Za-z_]+)\]')
CHUNK_RE = re.compile(r'\[chunk (\d+), p\.(\d+)(?:-(\d+))?\]')


def events(trace):
    """Ordered tool events: dict(tool, inp, obs). A model turn may hold several actions; its next
    observation holds one block per executed action, headed '[Action k of n: tool]' when n > 1."""
    ev = []
    trace = trace or []
    n = len(trace)
    for i, (role, text) in enumerate(trace):
        if role != 'model':
            continue
        acts = [(m.group(1), m.group(2).strip()) for m in ACT_RE.finditer(text or '')]
        obs = None
        for j in range(i + 1, n):
            if trace[j][0] == 'observation':
                obs = trace[j][1]
                break
            if trace[j][0] == 'model':
                break
        if obs is None or not acts:
            continue
        hs = list(HDR_RE.finditer(obs))
        if not hs:
            ev.append(dict(tool=acts[0][0], inp=acts[0][1], obs=obs))
            continue
        for k, h in enumerate(hs):
            end = hs[k + 1].start() if k + 1 < len(hs) else len(obs)
            idx = int(h.group(1)) - 1
            inp = acts[idx][1] if 0 <= idx < len(acts) else ''
            ev.append(dict(tool=h.group(3), inp=inp, obs=obs[h.end():end].strip()))
    return ev


def method_events(trace):
    return [e for e in events(trace) if e['tool'] in METHOD_TOOLS]


CID_RE = re.compile(r'card_id\s*=\s*([0-9a-f]{8}-\d+)')
DOC_RE = re.compile(r'doc_id\s*=\s*([0-9a-f-]{8,36})')


def opened_cards(trace):
    """card ids opened with get_card, in order, de-duplicated (observation must show the card)."""
    out = []
    for e in method_events(trace):
        if e['tool'] != 'get_card':
            continue
        m = CID_RE.search(e['inp']) or CID_RE.search(e['obs'][:80])
        if m and e['obs'].lstrip().startswith('card_id') and m.group(1) not in out:
            out.append(m.group(1))
    return out


def cited_cards(answer):
    return set(re.findall(r'\b[0-9a-f]{8}-\d{2}\b', answer or ''))


def pages_read(trace):
    """(doc_prefix, real_page) pairs in reading order from read_source observations (chunk headers give real pages;
    the 'pages=' argument counts chunks, not pages)."""
    out = []
    for e in method_events(trace):
        if e['tool'] != 'read_source':
            continue
        m = DOC_RE.search(e['inp'])
        if not m:
            continue
        for c in CHUNK_RE.finditer(e['obs']):
            a = int(c.group(2)); b = int(c.group(3)) if c.group(3) else a
            for p in range(a, b + 1):
                if (m.group(1), p) not in out:
                    out.append((m.group(1), p))
    return out


def docs_found_in(trace):
    """docs touched by find_in_document, in order."""
    out = []
    for e in method_events(trace):
        if e['tool'] == 'find_in_document':
            m = DOC_RE.search(e['inp'])
            if m and m.group(1) not in out:
                out.append(m.group(1))
    return out


def score_of(r):
    s = r.get('score_v2')
    return 0.0 if s is None else float(s)


def seen_cards(trace):
    """card ids that appeared in search_cards results (with their short formulas) or were opened."""
    out = set(opened_cards(trace))
    for e in method_events(trace):
        if e['tool'] == 'search_cards':
            out.update(CID_RE.findall(e['obs']))
    return out


HIT_RE = re.compile(r'doc_id=([0-9a-f-]{8,36})\s*\|[^\n]*?\|\s*p\.(\d+)(?:-(\d+))?\s*\|')


def pages_returned(trace):
    """(doc_prefix, real_page) from read_source AND find_in_document chunk headers (strict LongDA-style reading)."""
    out = []
    for e in method_events(trace):
        if e['tool'] not in ('read_source', 'find_in_document'):
            continue
        m = DOC_RE.search(e['inp'])
        if not m:
            continue
        for c in CHUNK_RE.finditer(e['obs']):
            a = int(c.group(2)); b = int(c.group(3)) if c.group(3) else a
            for p in range(a, b + 1):
                if (m.group(1), p) not in out:
                    out.append((m.group(1), p))
    return out


def search_hits(trace):
    """(doc_id, page) of search_methodology hits (loose LongDA-style 'seen')."""
    out = []
    for e in method_events(trace):
        if e['tool'] == 'search_methodology':
            for m in HIT_RE.finditer(e['obs']):
                a = int(m.group(2)); b = int(m.group(3)) if m.group(3) else a
                for p in range(a, b + 1):
                    if (m.group(1), p) not in out:
                        out.append((m.group(1), p))
    return out
