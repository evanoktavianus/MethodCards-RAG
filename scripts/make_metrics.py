#!/usr/bin/env python3
"""Rebuild the full RAGAS-style metrics tables from the stored results.

No model calls, no network, no API key. Standard library only.

    python3 scripts/make_metrics.py              # print Markdown tables
    python3 scripts/make_metrics.py --json out.json   # also write every number

Inputs (relative to the repository root):
  experiments/main_run/results_final_{hard,easier}.jsonl.gz            7 arms per item
  experiments/main_run/results_final_{hard,easier}_datagiven.jsonl.gz  2 arms per item
  experiments/main_run/metrics/ragas_judge_results.jsonl.gz            stored judge output (pieces)
  experiments/main_run/metrics/ragas_fp_results.jsonl.gz               stored judge output (faithfulness, precision)
  dataset/references/  series_equivalents.json, method_node_map.json, method_tree.jsonl
  dataset/items/*/*.json, tools/bank/card_index.jsonl (else tools/bank/cards_final.jsonl)
Result rows carry either the full `trace` or, after scripts/strip_text.py, the text-free `retrieval` record (see
compute_retrieval); the printed numbers are the same.

Rules: a failed or missing answer counts as 0 in every column (score_v2 null = 0; a part counts 0 when
the item has that claim kind; a judge row without a trace = 0). Context precision leaves out only
answers that retrieved nothing (undefined there); failed answers count 0.
"""
import argparse
import glob
import gzip
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(ROOT, 'experiments', 'main_run')
REF = os.path.join(ROOT, 'dataset', 'references')

ARMS = ['CoT0', 'CoT1', 'PoT', 'ReAct-v2', 'Ours-text2', 'Ours-cards2', 'Ours-oracle']
LABEL = {'CoT0': '1. Memory only (CoT)', 'CoT1': '2. Data in prompt', 'PoT': '3. PoT',
         'ReAct-v2': '4. ReAct', 'Ours-text2': '5. LongDA-style', 'Ours-cards2': '6. Ours',
         'Ours-oracle': 'Ours + given method (oracle analysis)'}
COUNT_LABEL = {'CoT0': 'CoT0 (memory only)', 'CoT1': 'CoT1 (data in prompt)', 'PoT': 'PoT',
               'ReAct-v2': 'ReAct', 'Ours-text2': 'Ours-text2 (LongDA-style)',
               'Ours-cards2': 'Ours-cards2 (ours)', 'Ours-oracle': 'Ours-oracle (given method)'}
CARD_ARMS = ('Ours-cards2', 'Ours-oracle')
TEXT_ARMS = ('Ours-text2',)
METHOD_ARMS = TEXT_ARMS + CARD_ARMS
DATA_ARMS = ('ReAct-v2',) + METHOD_ARMS          # arms that fetch data themselves
GROUPS = {'hard': 'results_final_hard.jsonl.gz', 'easier': 'results_final_easier.jsonl.gz',
          'hard_datagiven': 'results_final_hard_datagiven.jsonl.gz',
          'easier_datagiven': 'results_final_easier_datagiven.jsonl.gz'}
N_EXPECTED = {'hard': 231, 'easier': 209, 'hard_datagiven': 231, 'easier_datagiven': 209}
TITLE = {'hard': 'Institutional procedures (231)', 'easier': 'Standard formulas (209)'}
GROUP_NAME = {'hard': 'Institutional procedures', 'easier': 'Standard formulas',
              'hard_datagiven': 'Institutional procedures, data given', 'easier_datagiven': 'Standard formulas, data given'}


# ---------------------------------------------------------------- loading
def read_jsonl(path):
    op = gzip.open if path.endswith('.gz') else open
    with op(path, 'rt', encoding='utf-8') as f:
        return [json.loads(l) for l in f if l.strip()]


def load_results():
    return {g: read_jsonl(os.path.join(MAIN, fn)) for g, fn in GROUPS.items()}


def load_items():
    items = {}
    for f in glob.glob(os.path.join(ROOT, 'dataset', 'items', '*', '*.json')):
        with open(f, encoding='utf-8') as fh:
            d = json.load(fh)
        items[d['id']] = d
    return items


def load_cards():
    """card_id -> card. Reads tools/bank/card_index.jsonl (ids, bibliographic fields, doc ids and pages only; no card text)
    when present, else tools/bank/cards_final.jsonl. card_cites() gives the same result from either file."""
    cards = {}
    p = os.path.join(ROOT, 'tools', 'bank', 'card_index.jsonl')
    if not os.path.exists(p):
        p = os.path.join(ROOT, 'tools', 'bank', 'cards_final.jsonl')
    for c in read_jsonl(p):
        cards[c['card_id']] = c
    return cards


def load_tree():
    return {t['method_id']: t for t in read_jsonl(os.path.join(REF, 'method_tree.jsonl'))}


def load_node_map():
    with open(os.path.join(REF, 'method_node_map.json'), encoding='utf-8') as f:
        raw = json.load(f)
    return {k.lower(): (v if isinstance(v, dict) else {'nodes': list(v), 'variants': []}) for k, v in raw.items()}


def load_equiv():
    with open(os.path.join(REF, 'series_equivalents.json'), encoding='utf-8') as f:
        raw = json.load(f)
    eq = {}
    for k, v in raw.items():
        eq.setdefault(k, set()).add(k)
        for e in (v.get('equivalent') or []):
            eq.setdefault(k, set()).add(e)
            eq.setdefault(e, set()).add(k)
    return eq


# ---------------------------------------------------------------- method tree and pages
def page_set(pages):
    pages = [int(p) for p in (pages or []) if isinstance(p, (int, float))]
    if not pages:
        return set()
    if len(pages) <= 2:
        return set(range(min(pages), max(pages) + 1))
    return set(pages)


def card_cites(card):
    out = []
    for s in card.get('sources') or []:
        if s.get('doc_id'):
            out.append((s['doc_id'], page_set(s.get('pages'))))
    if not out and card.get('doc_id'):
        out.append((card['doc_id'], page_set(card.get('pages'))))
    return out


def doc_match(a, b):
    if not a or not b:
        return False
    a, b = a.strip().lower(), b.strip().lower()
    return a == b or (len(a) >= 8 and b.startswith(a)) or (len(b) >= 8 and a.startswith(b))


def node_card_ids(tree, node_map, method):
    if method is None:
        return None
    ent = node_map.get(str(method).lower())
    if not ent:
        return None
    nodes = set(ent.get('nodes') or [])
    vars_ = set(ent.get('variants') or [])
    ids = set()
    for mid, t in tree.items():
        for v in t.get('variants', []):
            if mid in nodes or v.get('variant_id') in vars_:
                ids.update(v.get('card_ids', []))
    return ids or None


class NodeIndex:
    def __init__(self, card_ids, cards):
        self.card_ids = set(card_ids)
        self.cites = []
        for cid in self.card_ids:
            c = cards.get(cid)
            if c:
                self.cites.extend(card_cites(c))

    def page_relevant(self, doc, page):
        return any(doc_match(doc, d) and page in ps for d, ps in self.cites)


# ---------------------------------------------------------------- trace parsing
ACT_RE = re.compile(r'Action:\s*([A-Za-z_]+)\s*,?\s*\n?\s*Action Input:\s*(.*?)(?=\n\s*(?:Thought:|Action:|Observation)|\Z)', re.S)
HDR_RE = re.compile(r'\[Action (\d+) of (\d+): ([A-Za-z_]+)\]')
CHUNK_RE = re.compile(r'\[chunk (\d+), p\.(\d+)(?:-(\d+))?\]')
CID_RE = re.compile(r'card_id\s*=\s*([0-9a-f]{8}-\d+)')
DOC_RE = re.compile(r'doc_id\s*=\s*([0-9a-f-]{8,36})')
HIT_RE = re.compile(r'doc_id=([0-9a-f-]{8,36})\s*\|[^\n]*?\|\s*p\.(\d+)(?:-(\d+))?\s*\|')
METHOD_TOOLS = ('search_cards', 'get_card', 'read_source', 'search_methodology', 'find_in_document')


def events(trace):
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


def opened_cards(trace):
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


def seen_cards(trace):
    out = set(opened_cards(trace))
    for e in method_events(trace):
        if e['tool'] == 'search_cards':
            out.update(CID_RE.findall(e['obs']))
    return out


def _chunk_pages(trace, tools):
    out = []
    for e in method_events(trace):
        if e['tool'] not in tools:
            continue
        m = DOC_RE.search(e['inp'])
        if not m:
            continue
        for c in CHUNK_RE.finditer(e['obs']):
            a = int(c.group(2))
            b = int(c.group(3)) if c.group(3) else a
            for p in range(a, b + 1):
                if (m.group(1), p) not in out:
                    out.append((m.group(1), p))
    return out


def pages_read(trace):
    return _chunk_pages(trace, ('read_source',))


def pages_returned(trace):
    return _chunk_pages(trace, ('read_source', 'find_in_document'))


def search_hits(trace):
    out = []
    for e in method_events(trace):
        if e['tool'] == 'search_methodology':
            for m in HIT_RE.finditer(e['obs']):
                a = int(m.group(2))
                b = int(m.group(3)) if m.group(3) else a
                for p in range(a, b + 1):
                    if (m.group(1), p) not in out:
                        out.append((m.group(1), p))
    return out


def compute_retrieval(trace):
    """The compact, text-free record of what the metric code needs from a trace (ids and page numbers only):
        opened          card ids opened with get_card, in order, without repeats
        seen            sorted card ids opened or shown in a search_cards result
        pages_read      [doc_id, page] pairs returned by read_source, in order, without repeats
        pages_returned  [doc_id, page] pairs returned by read_source or find_in_document, in order, without repeats
        search_hits     [doc_id, page] pairs listed by search_methodology, in order, without repeats
    Computed from the trace by the functions above; scripts/strip_text.py stores it in the row as `retrieval`."""
    return {'opened': opened_cards(trace),
            'seen': sorted(seen_cards(trace)),
            'pages_read': [list(x) for x in pages_read(trace)],
            'pages_returned': [list(x) for x in pages_returned(trace)],
            'search_hits': [list(x) for x in search_hits(trace)]}


def compute_retrieval_row(r):
    """compute_retrieval(trace) for a full row. The Cards-fixed ablation arm is given its five cards in the first message,
    not through a tool call, so they are not in the trace: the row lists them in `fixed_card_ids` (ids only) and they count
    as opened and seen."""
    rt = compute_retrieval(r.get('trace'))
    fx = r.get('fixed_card_ids') or []
    if fx:
        rt['opened'] = list(dict.fromkeys(rt['opened'] + list(fx)))
        rt['seen'] = sorted(set(rt['seen']) | set(fx))
    return rt


def retrieval_of(r):
    """The row's stored `retrieval` if it has one (stripped release), else computed from its trace."""
    rt = r.get('retrieval')
    return rt if rt is not None else compute_retrieval_row(r)


def score_of(r):
    s = r.get('score_v2')
    return 0.0 if s is None else float(s)


def ap_rank(rel):
    """Rank-weighted average precision: sum_k precision@k * rel_k / number of relevant items."""
    if not rel or not any(rel):
        return 0.0
    hit = 0
    tot = 0.0
    for k, v in enumerate(rel, 1):
        if v:
            hit += 1
            tot += hit / k
    return tot / hit


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


# ---------------------------------------------------------------- the computation
class Ctx:
    def __init__(self):
        self.results = load_results()
        self.items = load_items()
        self.cards = load_cards()
        self.tree = load_tree()
        self.node_map = load_node_map()
        self.equiv = load_equiv()
        self._nodes = {}
        self.pieces = {}
        for r in read_jsonl(os.path.join(MAIN, 'metrics', 'ragas_judge_results.jsonl.gz')):
            self.pieces[(r['group'], r['item'], r['arm'])] = r
        self.fp = {}
        for r in read_jsonl(os.path.join(MAIN, 'metrics', 'ragas_fp_results.jsonl.gz')):
            self.fp[(r['metric'], r['group'], r['item'], r['arm'])] = r

    def node_index(self, method):
        if method not in self._nodes:
            ids = node_card_ids(self.tree, self.node_map, method)
            self._nodes[method] = NodeIndex(ids, self.cards) if ids else None
        return self._nodes[method]

    def data_recall(self, r):
        needs = r.get('data_needs') or {}
        fetched = set(r.get('data_fetched_ids') or [])
        if not needs or r.get('data_fetched_ids') is None:
            return None, None
        found = 0
        n = 0
        for sid in needs.values():
            if not sid:
                continue
            n += 1
            if self.equiv.get(sid, {sid}) & fetched:
                found += 1
        return (found / n, found == n) if n else (None, None)

    def method_graph(self, r, arm):
        nd = self.node_index(r.get('method'))
        if nd is None:
            return None, None, None
        rt = retrieval_of(r)
        if arm in CARD_ARMS:
            opened = list(rt['opened'])
            got = set(r.get('cards_got') or []) | set(opened)
            got |= {c for c in cited_cards(r.get('answer')) if c in nd.card_ids}
            strict = bool(got & nd.card_ids)
            loose = strict or bool(set(rt['seen']) & nd.card_ids)
            order = list(opened) + [c for c in (r.get('cards_got') or []) if c not in opened]
            return strict, loose, [c in nd.card_ids for c in order]
        if arm in TEXT_ARMS:
            strict = any(nd.page_relevant(d, p) for d, p in rt['pages_returned'])
            loose = strict or any(nd.page_relevant(d, p) for d, p in rt['search_hits'])
            return strict, loose, [nd.page_relevant(d, p) for d, p in rt['pages_read']]
        return None, None, None

    # judge-based per-answer values (failed answers = 0)
    def piece_value(self, g, r, key):
        j = self.pieces.get((g, r['item'], r['arm']))
        if j is None or j.get('score') is None:
            return 0.0
        v = (j.get('detail') or {}).get(key)
        return 0.0 if v is None else float(v)

    def faith_value(self, g, r):
        j = self.fp.get(('faithfulness', g, r['item'], r['arm']))
        if j is None or j.get('score') is None:
            return 0.0
        return float(j['score'])

    def prec_value(self, g, r):
        """None = left out (retrieved nothing); failed answers = 0."""
        j = self.fp.get(('precision', g, r['item'], r['arm']))
        if j is None:
            return 0.0
        if j.get('score') is None:
            return None if j.get('skipped') == 'no items or pieces' else 0.0
        return float(j['score'])

    def part_values(self, r):
        out = {}
        failed = not r.get('parts_v2')
        claims = (self.items.get(r['item'], {}).get('claims') or {})
        for k in ('text', 'data', 'computation'):
            v = (r.get('parts_v2') or {}).get(k)
            if failed and claims.get(k):
                v = 0.0
            out[k] = None if v is None else float(v)
        return out

    def answer_values(self, g, r):
        arm = r['arm']
        parts = self.part_values(r)
        d = {
            'answer': score_of(r) / 100.0,
            'text': parts['text'], 'data': parts['data'], 'computation': parts['computation'],
            'mc_all': self.piece_value(g, r, 'method_correctness'),
            'mc_vital': self.piece_value(g, r, 'method_correctness_vital'),
            'full': 1.0 if r.get('vital_all_v2') else 0.0,
        }
        if arm in METHOD_ARMS:
            d['cr'] = self.piece_value(g, r, 'context_recall')
            d['faith'] = self.faith_value(g, r)
            d['prec'] = self.prec_value(g, r)
            f, fl, rel = self.method_graph(r, arm)
            d['m_strict'] = None if f is None else float(f)
            d['m_loose'] = None if fl is None else float(fl)
            d['g_prec'] = sum(rel) / len(rel) if rel else None
            d['g_ap'] = ap_rank(rel) if rel else None
            d['score'] = score_of(r)
            d['strict_bool'] = f
            d['loose_bool'] = fl
        if arm in DATA_ARMS:
            a, b = self.data_recall(r)
            d['dr'] = a
            d['dr_all'] = None if b is None else (1.0 if b else 0.0)
        return d


def build(ctx):
    """-> {group: {arm: {metric: [per-answer values]}}}"""
    out = {}
    for g, rows in ctx.results.items():
        out[g] = {}
        for r in rows:
            out[g].setdefault(r['arm'], []).append(ctx.answer_values(g, r))
    return out


def col(vals, key):
    return mean([v.get(key) for v in vals])


# ---------------------------------------------------------------- formatting
def pct(x, scale=100.0):
    return 'n/a' if x is None else '%.1f' % (x * scale)


def b(s, bold):
    return '**%s**' % s if bold else s


def table(header, rows):
    out = ['| ' + ' | '.join(header) + ' |', '|' + '---|' * len(header)]
    out += ['| ' + ' | '.join(r) + ' |' for r in rows]
    return out


def cells(A, g, arm):
    """All headline numbers for one arm/group, as floats in [0,1] or strings 'n/a'/'given'."""
    v = A[g][arm]
    has_m = arm in METHOD_ARMS
    d = {
        'context_recall_method': col(v, 'cr') if has_m else None,
        'context_precision': col(v, 'prec') if has_m else None,
        'faithfulness': col(v, 'faith') if has_m else None,
        'method_correctness_all': col(v, 'mc_all'),
        'method_correctness_vital': col(v, 'mc_vital'),
        'method_explained': col(v, 'text'),
        'data_correctness': col(v, 'data'),
        'computation_correctness': col(v, 'computation'),
        'answer_correctness': col(v, 'answer'),
        'fully_correct': col(v, 'full'),
        'graph_recall_strict': col(v, 'm_strict') if has_m else None,
        'graph_recall_loose': col(v, 'm_loose') if has_m else None,
        'graph_precision': col(v, 'g_prec') if has_m else None,
        'graph_precision_rank_weighted': col(v, 'g_ap') if has_m else None,
        'n_with_retrieved_items': len([1 for x in v if x.get('g_ap') is not None]) if has_m else None,
        'n': len(v),
    }
    if arm == 'CoT0':
        d['data_recall_share'] = d['data_recall_all'] = 'n/a'
    elif arm in ('CoT1', 'PoT'):
        d['data_recall_share'] = d['data_recall_all'] = 'given'
    else:
        d['data_recall_share'] = col(v, 'dr')
        d['data_recall_all'] = col(v, 'dr_all')
    return d


def show(x):
    return x if isinstance(x, str) else pct(x)


def full_table(A, g, numbers):
    hdr = ['Row', 'Context recall (method)', 'Context precision', 'Context recall (data)', 'Faithfulness',
           'Method correctness (factual correctness)', 'Method explained', 'Data correctness',
           'Computation correctness', 'Answer correctness']
    rows = []
    for arm in ARMS:
        c = cells(A, g, arm)
        numbers[g][arm] = c
        data = c['data_recall_share'] if arm in ('CoT0', 'CoT1', 'PoT') else c['data_recall_share']
        vals = [show(c['context_recall_method']), show(c['context_precision']), show(data), show(c['faithfulness']),
                show(c['method_correctness_all']), show(c['method_explained']), show(c['data_correctness']),
                show(c['computation_correctness']), show(c['answer_correctness'])]
        vals = ['n/a' if v is None else v for v in vals]
        if arm == 'Ours-cards2':
            rows.append(['**%s**' % LABEL[arm]] + ['**%s**' % x for x in vals])
        else:
            rows.append([LABEL[arm]] + vals)
    return table(hdr, rows)


def sec_fp(A, g_pairs):
    hdr = ['Row'] + [x for g, name in g_pairs for x in ('%s: faithfulness' % name, '%s: precision' % name)]
    rows = []
    for arm in METHOD_ARMS[0:1] + CARD_ARMS:
        r = [LABEL[arm]]
        for g, _ in g_pairs:
            c = cells(A, g, arm)
            r += [pct(c['faithfulness']), pct(c['context_precision'])]
        rows.append(['**%s**' % LABEL[arm]] + ['**%s**' % x for x in r[1:]] if arm == 'Ours-cards2' else r)
    return table(hdr, rows)


def sec_table2(A):
    hdr = ['', 'Institutional procedures: method found', 'Institutional procedures: method given',
           'Standard formulas: method found', 'Standard formulas: method given']
    f = lambda g, arm: pct(col(A[g][arm], 'answer'))
    found = [f('hard', 'Ours-cards2'), f('hard', 'Ours-oracle'), f('easier', 'Ours-cards2'), f('easier', 'Ours-oracle')]
    given = [f('hard_datagiven', 'Ours-cards2'), f('hard_datagiven', 'Ours-oracle'),
             f('easier_datagiven', 'Ours-cards2'), f('easier_datagiven', 'Ours-oracle')]
    return table(hdr, [['data found'] + found, ['data given'] + given])


def sec_ladder(A, g):
    hdr = ['Ladder row', 'Method found', 'Data found', 'Method used correctly', 'Accuracy']
    rows = []
    for arm in ARMS:
        c = cells(A, g, arm)
        mf = show(c['context_recall_method']) if c['context_recall_method'] is not None else 'n/a'
        r = [LABEL[arm], mf, show(c['data_recall_share']), show(c['method_correctness_all']), show(c['answer_correctness'])]
        rows.append(['**%s**' % x for x in r] if arm == 'Ours-cards2' else r)
    return table(hdr, rows)


def sec_every_metric(A, g):
    hdr = ['Metric', '1', '2', '3', '4', '5 LongDA-style', '**6 Ours**', 'O']
    C = {arm: cells(A, g, arm) for arm in ARMS}

    def row(name, key):
        out = [name]
        for arm in ARMS:
            v = C[arm][key]
            s = 'n/a' if v is None else show(v)
            out.append('**%s**' % s if arm == 'Ours-cards2' else s)
        return out
    rows = [
        row('Context recall (method), judge', 'context_recall_method'),
        row('Context recall (method), graph strict: opened', 'graph_recall_strict'),
        row('Context recall (method), graph loose: seen', 'graph_recall_loose'),
        row('Context precision, judge', 'context_precision'),
        row('Context precision, graph rank-weighted', 'graph_precision_rank_weighted'),
        row('Context recall (data), share of inputs', 'data_recall_share'),
        row('Context recall (data), all inputs', 'data_recall_all'),
        row('Faithfulness', 'faithfulness'),
        row('Method correctness (factual correctness), all pieces', 'method_correctness_all'),
        row('Method correctness (factual correctness), vital pieces', 'method_correctness_vital'),
        row('Method explained', 'method_explained'),
        row('Data correctness', 'data_correctness'),
        row('Computation correctness', 'computation_correctness'),
        row('Answer correctness', 'answer_correctness'),
        row('Fully correct answers', 'fully_correct'),
    ]
    return table(hdr, rows)


def pooled(A):
    rows = []
    res = {}
    for arm in ('Ours-text2', 'Ours-cards2'):
        vals = A['hard'][arm] + A['easier'][arm]
        d = {'n': len(vals), 'context_recall_method': col(vals, 'cr'), 'context_precision': col(vals, 'prec'),
             'faithfulness': col(vals, 'faith'), 'method_correctness': col(vals, 'mc_all'),
             'answer_correctness': col(vals, 'answer')}
        res[arm] = d
        r = [LABEL[arm]] + [pct(d[k]) for k in ('context_recall_method', 'context_precision', 'faithfulness',
                                                'method_correctness', 'answer_correctness')]
        rows.append(['**%s**' % x for x in r] if arm == 'Ours-cards2' else r)
    hdr = ['Row (both groups pooled, 440 questions)', 'Context recall (method)', 'Context precision',
           'Faithfulness', 'Method correctness (factual correctness)', 'Answer correctness']
    return table(hdr, rows), res


def sec_count(A, g, fname):
    hdr = ['Arm', 'n', 'Data recall (share of inputs)', 'Data recall strict (all inputs)',
           'Method recall strict: opened (%)', 'Method recall loose: seen (%)', 'Method precision, graph (%)',
           'Method precision rank-weighted (%)', 'n with retrieved items', 'Answer correctness', 'text', 'data',
           'computation']
    given_file = g.endswith('datagiven')
    rows = []
    for arm in [a for a in ARMS if a in A[g]]:
        c = cells(A, g, arm)
        if arm == 'CoT0':
            dc = ds = 'n/a'
        elif arm in ('CoT1', 'PoT') or (given_file and arm in CARD_ARMS):
            dc = ds = 'given'
        else:
            dc, ds = pct(c['data_recall_share']), pct(c['data_recall_all'])
        m = arm in METHOD_ARMS
        rows.append([COUNT_LABEL[arm], str(c['n']), dc, ds,
                     pct(c['graph_recall_strict']) if m else 'n/a', pct(c['graph_recall_loose']) if m else 'n/a',
                     pct(c['graph_precision']) if m else 'n/a', pct(c['graph_precision_rank_weighted']) if m else 'n/a',
                     str(c['n_with_retrieved_items']) if m else '-',
                     '%.1f' % (c['answer_correctness'] * 100), pct(c['method_explained']), pct(c['data_correctness']),
                     pct(c['computation_correctness'])])
    return table(hdr, rows)


def sec_table4(A, g):
    hdr = ['Arm', 'version', 'found: n', 'found: mean score', 'not found: n', 'not found: mean score']
    rows = []
    for arm in METHOD_ARMS:
        for ver in ('strict', 'loose'):
            vals = A[g].get(arm)
            if not vals:
                rows.append([COUNT_LABEL[arm], ver, 'n/a', 'n/a', 'n/a', 'n/a'])
                continue
            fo = [v['score'] for v in vals if v.get(ver + '_bool') is True]
            nf = [v['score'] for v in vals if v.get(ver + '_bool') is False]
            f1 = lambda xs: 'n/a' if not xs else '%.1f' % (sum(xs) / len(xs))
            rows.append([COUNT_LABEL[arm], ver, str(len(fo)), f1(fo), str(len(nf)), f1(nf)])
    return table(hdr, rows)


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--json', default='', help='also write every number to this JSON file')
    args = ap.parse_args()
    ctx = Ctx()
    A = build(ctx)
    numbers = {g: {} for g in A}
    L = []
    L.append('# RAGAS-style metrics from the stored results\n')
    L.append('Failed or missing answers count as 0 in every column. Percent.\n')
    L.append('- Context recall (method): share of the question\'s method pieces stated in what the agent retrieved '
             '(the given passage for the oracle cell).')
    L.append('- Context precision: share of retrieved method items (cards opened, pages read) that state the question\'s '
             'method. Answers that retrieved nothing are left out; failed answers count 0.')
    L.append('- Context recall (data): share of the question\'s needed series fetched, an equivalent series counting.')
    L.append('- Faithfulness: share of the answer\'s method claims supported by what the agent retrieved.')
    L.append('- Method correctness (factual correctness): share of the question\'s method pieces applied correctly in the answer.')
    L.append('- Answer correctness: score_v2, with its parts: Method explained, Data correctness, Computation correctness.')
    L.append('')
    L.append('## Full table (RAGAS names)\n')
    for g in ('hard', 'easier'):
        L.append(TITLE[g]); L.append('')
        L += full_table(A, g, numbers); L.append('')
    L.append('## Faithfulness and context precision\n')
    L += sec_fp(A, [('hard', 'Institutional procedures'), ('easier', 'Standard formulas')]); L.append('')
    L.append('## Table 7: oracle analysis (answer correctness), both groups\n')
    L += sec_table2(A); L.append('')
    pt, pres = pooled(A)
    L.append('## Pooled over both groups (440 questions)\n')
    L += pt; L.append('')
    for g in ('hard', 'easier'):
        L.append('## Ladder, %s\n' % TITLE[g])
        L += sec_ladder(A, g); L.append('')
    L.append('## Complete table, every metric (metrics as rows)\n')
    L.append('Columns: 1 CoT0, 2 Data in prompt, 3 PoT, 4 ReAct, 5 LongDA-style, 6 Ours, O = Ours + given method (oracle analysis). '
             'Percent; failed answers = 0.')
    L.append('Graph versions are judge-free cross-checks from the method tree. Fully correct answers = every vital claim of '
             'the key correct (vital_all_v2).\n')
    for g in ('hard', 'easier'):
        L.append(TITLE[g]); L.append('')
        L += sec_every_metric(A, g); L.append('')
    L.append('## Count-based metrics (no model calls)\n')
    for g in GROUPS:
        L.append('### %s (%d answers)\n' % (GROUP_NAME[g], len(ctx.results[g])))
        L += sec_count(A, g, GROUPS[g]); L.append('')
        L.append('#### Method found vs not found, mean score (graph version), %s\n' % GROUP_NAME[g])
        L += sec_table4(A, g); L.append('')
    L.append('Answer correctness = mean score_v2 (failed or missing = 0); parts (percent) = mean parts_v2 over answers whose '
             'item has that claim kind; failed or missing answers = 0.')
    L.append('Data recall: needed series fetched directly or via an equivalent; "given" = data supplied in the prompt.')
    L.append('Method recall strict (opened): ours/oracle = a card under the question\'s node(s)/variants opened with get_card '
             '(or cited); LongDA-style = a page read with read_source or returned by find_in_document that a node card cites. '
             'Loose (seen): also a card shown in a search result; LongDA-style = also a search_methodology hit that a node '
             'card cites.')
    L.append('Graph precision: share of retrieved items under the node (ours: cards opened; LongDA-style: distinct pages read), '
             'and rank-weighted average precision over the retrieval order; over answers with at least one item.')
    text = '\n'.join(L) + '\n'
    print(text, end='')
    if args.json:
        numbers['table2'] = {g: {a: col(A[g][a], 'answer') for a in CARD_ARMS} for g in A}
        numbers['pooled_440'] = pres
        with open(args.json, 'w', encoding='utf-8') as f:
            json.dump(numbers, f, indent=1)


if __name__ == '__main__':
    main()
