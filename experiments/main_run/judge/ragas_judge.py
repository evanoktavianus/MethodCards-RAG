"""RAGAS-style method metrics with an LLM judge (deepseek/deepseek-v4.1-flash via OpenRouter, as the score_v2 judge, temperature 0, provider pinned).
Design (EVAL_PLAN section 3, improved design): the reference is the method PIECES of the question's method
(experiments/main_run/method_pieces.json: {method: {pieces:[{id, kind, text, accept, vital}]}}), by content, not by document.
ONE call per answer (metric 'pieces') returns, per piece:
   in_context         is the piece stated in the retrieved method context (ALL observations of the method tools)  -> context recall (method)
   in_answer_correct  does the answer use the piece correctly (true / partial / false)                           -> method correctness
Arms without a method tool (CoT0, CoT1, PoT, ReAct-v2) get no context: only in_answer_correct.
Optional extra metrics (not in the default run): faithfulness, precision (--metrics pieces,faithfulness,precision).
This is the judge that produced the stored outputs in experiments/main_run/metrics/; it is included so that its prompts and settings can be read
(for context precision, each retrieved card or page is cut to its first 1,500 characters). A rerun needs the full answer rows with tool traces,
which are not distributed, and env OPENROUTER_API_KEY.
Usage:  python3 -I experiments/main_run/judge/ragas_judge.py --dry-run [--test] [--limit N]
             ... ragas_judge.py --summary [--out FILE]        (tables from saved results, no calls)
A real run (no --dry-run) makes PAID calls: only with an explicit go. Resumable: finished (group,item,arm,metric) rows in --out are skipped.
--test = the approved-size test: every 23rd item (1-based, order of first appearance) of the hard file x arms ReAct-v2, Ours-text2, Ours-cards2, Ours-oracle."""
import sys, os, json, re, time, argparse, threading, urllib.request, urllib.error
import concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mm_common as M

JUDGE_MODEL = 'deepseek/deepseek-v4.1-flash'   # same model as the score_v2 judge (JUDGE2 in run_baselines.py)
DEFAULT_ARMS = tuple(M.ARM_ORDER)   # all 7 arms; the no-context ones (CoT0, CoT1, PoT, ReAct-v2) get method correctness only
CONTEXT_ARMS = ('Ours-text2', 'Ours-cards2', 'Ours-oracle', 'Cards-fixed', 'Cards-as-text', 'Text-410')   # Text-410 (2026-11-04 control): same context as Ours-text2   # last two: ablation arms (2026-11-03). Cards-fixed context = the 5 cards in its first message (stored in the row as fixed_cards_text); Cards-as-text context = its text-search observations
OUT_TOK = {'pieces': 450, 'faithfulness': 500, 'precision': 200}   # expected output tokens per call (cost estimate)

ap = argparse.ArgumentParser()
ap.add_argument('--dry-run', action='store_true', help='print prompts for 2 answers and a size/cost estimate; NO calls, key not read')
ap.add_argument('--test', action='store_true', help='10 hard items (every 23rd) x all 7 arms = 70 calls')
ap.add_argument('--limit', type=int, default=0, help='first N answers per group and arm (0 = all)')
ap.add_argument('--group', action='append', help='name=path (default hard and easier)')
ap.add_argument('--arms', default=','.join(DEFAULT_ARMS)); ap.add_argument('--metrics', default='pieces')
ap.add_argument('--pieces', default=M.MAIN + 'method_pieces_q.json', help='per-item {item id: {method, pieces}} (or the older per-method {method: {pieces}})')
ap.add_argument('--out', default=None)
ap.add_argument('--workers', type=int, default=16)
ap.add_argument('--providers', default='relace,morph', help='provider.order, as chat2 in run_baselines.py (allow_fallbacks false)')
ap.add_argument('--max-cost', type=float, default=3.0, help='stop submitting new calls above this cumulative USD (this run)')
ap.add_argument('--ctx-chars', type=int, default=48000, help='cap on the retrieved context sent to the judge')
ap.add_argument('--no-search-ctx', action='store_true', help='leave search-result lists out of the context (default: included)')
ap.add_argument('--max-items', type=int, default=20)
ap.add_argument('--price-in', type=float, default=6.4e-7, help='USD per input token for the estimate (fit of judge2_cost on prompt size)')
ap.add_argument('--price-out', type=float, default=1.0e-6)
ap.add_argument('--full', action='store_true', help='dry run: print whole prompts')
ap.add_argument('--summary', action='store_true')
args = ap.parse_args()
if args.out is None:
    args.out = M.MAIN + 'metrics/' + ('ragas_test2_results.jsonl' if args.test else 'ragas_judge_results.jsonl')

arms = args.arms.split(','); metrics = args.metrics.split(',')
groups = dict(g.split('=', 1) for g in args.group) if args.group else {k: M.DEFAULT_FILES[k] for k in ('hard', 'easier')}
if args.test:
    groups = {'hard': M.DEFAULT_FILES['hard']}
items = M.load_items(); oracle = M.load_oracle()
PIECES = json.load(open(args.pieces)) if os.path.exists(args.pieces) else None
PIECES_LC = {k.lower(): v for k, v in (PIECES or {}).items()}
PER_ITEM = bool(PIECES) and any(k in items for k in PIECES)


def pieces_of(r):
    if PER_ITEM:
        return (PIECES.get(r["item"]) or {}).get("pieces") or []
    m = (r.get("method") or items[r["item"]].get("method") or "")
    return (PIECES_LC.get(str(m).lower()) or {}).get("pieces") or []


# ---------------- context and items ----------------
def split_chunks(obs):
    ms = list(M.CHUNK_RE.finditer(obs))
    if not ms:
        return [(0, obs)]
    out = []
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else len(obs)
        out.append((int(m.group(1)), obs[m.start():end].strip()))
    return out


def build_context(r, arm, include_search=True):
    """ALL text the agent received from its method tools (search results, cards, pages, find results), de-duplicated, in order."""
    blocks = []; seen = set()
    def add(key, text):
        if key not in seen:
            seen.add(key); blocks.append(text)
    for tx in (r.get('fixed_cards_text') or []):   # Cards-fixed: the cards given in the first message (same cut as a get_card observation)
        add(('card', tx[:80]), tx[:2500])
    for e in M.method_events(r.get('trace')):
        t, obs = e['tool'], e['obs']
        dm = M.DOC_RE.search(e['inp']); doc = dm.group(1)[:8] if dm else '?'
        if t == 'get_card':
            add(('card', obs[:80]), obs[:2500])
        elif t in ('read_source', 'find_in_document'):
            for no, tx in split_chunks(obs):
                add((doc, no, tx[:60]), '[doc %s] %s' % (doc, tx[:3000]))
        elif include_search:
            add((t, obs[:200]), '[%s result] %s' % (t, obs[:3000]))
    ctx = '\n\n'.join(blocks)
    if arm == 'Ours-oracle':
        ctx = 'GIVEN METHOD PASSAGE (supplied in the agent prompt):\n' + (oracle.get(items[r['item']]['_fold'], '') or '') + ('\n\n' + ctx if ctx else '')
    trunc = len(ctx) > args.ctx_chars
    return ctx[:args.ctx_chars] + ('\n[context cut]' if trunc else ''), trunc


def retrieved_items(r, arm):
    tr = r.get('trace'); out = []
    if arm == 'Cards-fixed':
        ids = r.get('fixed_card_ids') or []
        return [('card ' + cid, tx[:1500]) for cid, tx in zip(ids, r.get('fixed_cards_text') or [])][:args.max_items]
    if arm in M.CARD_ARMS:
        seen = set()
        for e in M.method_events(tr):
            if e['tool'] == 'get_card' and e['obs'].lstrip().startswith('card_id'):
                m = M.CID_RE.search(e['inp']) or M.CID_RE.search(e['obs'][:80])
                cid = m.group(1) if m else e['obs'][:30]
                if cid not in seen:
                    seen.add(cid); out.append(('card ' + cid, e['obs'][:1500]))
    else:
        pages = {}; order = []
        for e in M.method_events(tr):
            if e['tool'] != 'read_source':
                continue
            dm = M.DOC_RE.search(e['inp']); doc = dm.group(1)[:8] if dm else '?'
            for c in split_chunks(e['obs']):
                cm = M.CHUNK_RE.match(c[1])
                if not cm:
                    continue
                key = (doc, int(cm.group(2)))
                if key not in pages:
                    pages[key] = ''; order.append(key)
                if c[1][:200] not in pages[key]:
                    pages[key] += c[1][:1200] + '\n'
        out = [('doc %s p.%d' % k, pages[k][:1500]) for k in order]
    return out[:args.max_items]


def piece_lines(ps):
    out = []
    for p in ps:
        s = '%s. [%s%s] %s' % (p.get('id', '?'), p.get('kind', ''), ', vital' if p.get('vital') else '', p.get('text', ''))
        if p.get('accept'):
            s += '  (accepted alternatives: %s)' % p['accept']
        out.append(s)
    return '\n'.join(out)


# ---------------- prompts ----------------
JSON_ONLY = 'Reply with ONLY the JSON object, no other text.'

def p_pieces(it, ps, answer, ctx):
    has_ctx = ctx is not None
    head = ("You check, piece by piece, how a calculation method appears in an agent's retrieved text and in its answer.\n"
            f"QUESTION: {it['query']}\n\nPIECES OF THE REFERENCE METHOD (formula, parameter values, applicability rule):\n{piece_lines(ps)}\n\n")
    if has_ctx:
        head += f"RETRIEVED CONTEXT (everything the agent saw from its method tools):\n\"\"\"{ctx}\"\"\"\n\n"
    head += f"ANSWER:\n\"\"\"{answer[:6000]}\"\"\"\n\n"
    task = ""
    if has_ctx:
        task += ("For each piece give in_context: true if the retrieved context states it (a formula piece: the same relationship or procedure; a parameter piece: the same value or choice; "
                 "an accepted alternative counts); false otherwise, including when the context only names the topic. Add a short quote from the context as evidence (empty if false). Use only the retrieved context, never outside knowledge.\n")
    task += ("For each piece give in_answer_correct: true if the answer uses the piece correctly (its formula or value, or an accepted alternative), 'partial' if only partly or approximately, false if it uses something different or does not use it.\n")
    fmt = '{"p1":{' + ('"in_context":true or false,"quote":"...",' if has_ctx else '') + '"in_answer_correct":true or "partial" or false}, "p2":{...}} with one entry per piece id'
    return head + task + 'Format: ' + fmt + '\n' + JSON_ONLY

def p_faith(it, answer, ctx):
    return ("You check whether an answer's statements about the calculation method are supported by the text the agent retrieved (faithfulness).\n"
            f"ANSWER:\n\"\"\"{answer[:6000]}\"\"\"\n\nRETRIEVED CONTEXT:\n\"\"\"{ctx}\"\"\"\n\n"
            "Step 1: extract the answer's method claims: the formula or rule it says it uses, each parameter value, weight, threshold or modelling choice, and any attribution to a source. At most 10 short, self-contained claims. "
            "Do not extract fetched data values, computed results, verdicts or generic wording.\n"
            "Step 2: for each claim say whether it can be inferred directly from the retrieved context (supported) or not. Use only the retrieved context, never outside knowledge.\n"
            'Format: {"claims":[{"claim":"...","supported":true or false}]}\n' + JSON_ONLY)

def p_prec(it, ps, its):
    blocks = '\n\n'.join('ITEM %d (%s):\n"""%s"""' % (i + 1, lab, tx) for i, (lab, tx) in enumerate(its))
    return ("You judge whether each retrieved item is relevant to a reference calculation method (context precision).\n"
            f"REFERENCE METHOD PIECES:\n{piece_lines(ps)}\n\nRETRIEVED ITEMS, in retrieval order:\n{blocks}\n\n"
            "For each item answer true if it states the reference method or part of its formula or parameters; false if it is about a different method, a variant with other parameters, or only general background.\n"
            'Format: {"1":true or false, "2":...} with one entry per item.\n' + JSON_ONLY)


# ---------------- LLM call ----------------
_key = [None]
def api_key():
    if _key[0] is None:
        _key[0] = os.environ['OPENROUTER_API_KEY']
    return _key[0]

def call(prompt, max_tokens=20000):   # as chat2 in run_baselines.py: hidden reasoning can use the budget and leave an empty reply at 4000
    """-> (text, cost, error). Retries 429/5xx; temperature 0; provider pinned; the key is never printed."""
    body = {'model': JUDGE_MODEL, 'messages': [{'role': 'user', 'content': prompt}], 'temperature': 0, 'max_tokens': max_tokens,
            'reasoning': {'effort': 'minimal'}, 'provider': {'order': args.providers.split(','), 'allow_fallbacks': False}}
    data = json.dumps(body).encode(); cost = 0.0; err = ''
    for attempt in range(6):
        req = urllib.request.Request('https://openrouter.ai/api/v1/chat/completions', data=data,
                                     headers={'Authorization': 'Bearer ' + api_key(), 'Content-Type': 'application/json'})
        try:
            d = json.load(urllib.request.urlopen(req, timeout=240))
            cost += (d.get('usage') or {}).get('cost') or 0
            return d['choices'][0]['message'].get('content') or '', cost, ''
        except urllib.error.HTTPError as e:
            err = 'HTTP %d' % e.code
            if e.code not in (408, 429, 500, 502, 503, 504):
                break
        except Exception as e:
            err = type(e).__name__
        time.sleep(2 * (attempt + 1))
    return '', cost, err

def parse_json(txt):
    try:
        return json.loads(re.search(r'\{.*\}', txt, re.S).group(0))
    except Exception:
        return None


# ---------------- tasks ----------------
def make_task(r, metric):
    arm = r['arm']; it = items[r['item']]; ans = r.get('answer') or ''
    if r.get('harness_error') or not r.get('trace'):
        return dict(skip='no trace')
    ps = pieces_of(r)
    if metric == 'pieces':
        if not ps:
            return dict(skip="no pieces for item %s" % r["item"])
        if not ans.strip():
            return dict(skip='empty answer', score=0.0)
        if arm in CONTEXT_ARMS:
            ctx, trunc = build_context(r, arm, not args.no_search_ctx)
        else:
            ctx, trunc = None, False
        return dict(prompt=p_pieces(it, ps, ans, ctx), ctx_trunc=trunc, ctx_chars=len(ctx or ''), piece_ids=[p.get('id') for p in ps],
                    vital={p.get('id'): bool(p.get('vital')) for p in ps}, has_ctx=ctx is not None)
    if arm not in CONTEXT_ARMS:
        return dict(skip='no method context for this arm')
    ctx, trunc = build_context(r, arm, not args.no_search_ctx)
    if metric == 'faithfulness':
        if not ans.strip():
            return dict(skip='empty answer')
        if not ctx.strip():
            return dict(skip='no context', score=0.0)
        return dict(prompt=p_faith(it, ans, ctx), ctx_trunc=trunc, ctx_chars=len(ctx))
    its = retrieved_items(r, arm)
    if not its or not ps:
        return dict(skip='no items or pieces')
    return dict(prompt=p_prec(it, ps, its), n_items=len(its), ctx_trunc=trunc, ctx_chars=len(ctx))


def pc(v):
    """one piece entry -> dict, whatever the judge returned (dict, "true"/"partial" string, bool, list)."""
    if isinstance(v, dict):
        return v
    if isinstance(v, list):
        for x in v:
            if isinstance(x, dict):
                return x
        return {}
    if isinstance(v, (bool, str)):
        return {"in_answer_correct": v}
    return {}


def tv(v):
    if v is True or (isinstance(v, str) and v.lower() == 'true'):
        return 1.0
    if isinstance(v, str) and v.lower() == 'partial':
        return 0.5
    return 0.0

def score_result(metric, js, task):
    """-> (main score, detail dict)."""
    if not isinstance(js, dict):
        return None, None
    if metric == 'pieces':
        ids = task['piece_ids']; vit = task['vital']
        det = {}
        corr = [tv(pc(js.get(i)).get('in_answer_correct')) for i in ids]
        det['correct'] = {i: c for i, c in zip(ids, corr)}
        det['method_correctness'] = sum(corr) / len(corr) if corr else None
        vc = [c for i, c in zip(ids, corr) if vit.get(i)]
        det['method_correctness_vital'] = sum(vc) / len(vc) if vc else None
        if task['has_ctx']:
            ctxf = [tv(pc(js.get(i)).get('in_context')) == 1.0 for i in ids]
            det['in_context'] = {i: c for i, c in zip(ids, ctxf)}
            det['quotes'] = {i: (pc(js.get(i)).get('quote') or '')[:200] for i in ids}
            det['context_recall'] = sum(ctxf) / len(ctxf) if ctxf else None
            vf = [c for i, c in zip(ids, ctxf) if vit.get(i)]
            det['context_recall_vital'] = sum(vf) / len(vf) if vf else None
            det['all_vital_in_context'] = all(vf) if vf else None
        return det['context_recall'] if task['has_ctx'] else det['method_correctness'], det
    if metric == 'faithfulness':
        cl = js.get('claims') or []
        sup = [bool(c.get('supported')) for c in cl if isinstance(c, dict)]
        return (sum(sup) / len(sup) if sup else None), dict(n_claims=len(sup), supported=sup)
    rel = [bool(js.get(str(i + 1))) for i in range(task.get('n_items', 0))]
    if not rel:
        return None, None
    hit = 0; tot = 0.0
    for k, v in enumerate(rel, 1):
        if v:
            hit += 1; tot += hit / k
    return (tot / hit if hit else 0.0), dict(rel=rel, share=sum(rel) / len(rel))


def select_rows():
    sel = []
    for g, path in groups.items():
        if not os.path.exists(path):
            print('missing', path); continue
        rows = M.read_jsonl(path)
        if args.test:
            order = []
            for r in rows:
                if r['item'] not in order:
                    order.append(r['item'])
            test_items = {order[i] for i in range(22, len(order), 23)}
            rows = [r for r in rows if r['item'] in test_items]
        by = {}
        for r in rows:
            if r['arm'] in arms:
                by.setdefault(r['arm'], []).append(r)
        for a in arms:
            rs = by.get(a, [])
            sel += [(g, r) for r in (rs[:args.limit] if args.limit else rs)]
    return sel


def summary():
    if not os.path.exists(args.out):
        print('no results yet'); return
    rows = M.read_jsonl(args.out); agg = {}; cost = sum(x.get("cost") or 0 for x in rows)
    last = {}
    for x in rows:
        last[(x["group"], x["item"], x["arm"], x["metric"])] = x
    rows = list(last.values())
    for x in rows:
        d = x.get('detail') or {}
        a = agg.setdefault((x['group'], x['arm']), {})
        if x['metric'] == 'pieces':
            for k in ('context_recall', 'context_recall_vital', 'method_correctness', 'method_correctness_vital'):
                if d.get(k) is not None:
                    a.setdefault(k, []).append(d[k])
            if d.get('all_vital_in_context') is not None:
                a.setdefault('all_vital', []).append(1.0 if d['all_vital_in_context'] else 0.0)
        elif x.get('score') is not None:
            a.setdefault(x['metric'], []).append(x['score'])
    f = lambda d, k: ('%.1f (n=%d)' % (100 * sum(d[k]) / len(d[k]), len(d[k]))) if d.get(k) else 'n/a'
    print('| Group | Arm | Context recall | Context recall (vital) | All vital in context | Method correctness | Method correctness (vital) | Faithfulness | Precision |'); print('|---|---|---|---|---|---|---|---|---|')
    for (g, a), d in sorted(agg.items()):
        print('| %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (g, a, f(d, 'context_recall'), f(d, 'context_recall_vital'), f(d, 'all_vital'), f(d, 'method_correctness'), f(d, 'method_correctness_vital'), f(d, 'faithfulness'), f(d, 'precision')))
    print("\njudge cost recorded: %.4f USD over %d rows" % (cost, len(rows)))
    print("\nHARNESS CHECK (per arm; rows = last row per item and arm)")
    print("| Arm | rows | empty reply | parse_error | other fail | missing pieces | no trace / empty answer | empty context (ctx arms) | context truncated | pieces judged |"); print("|---|---|---|---|---|---|---|---|---|---|")
    hc = {}
    for x in rows:
        if x["metric"] != "pieces":
            continue
        h = hc.setdefault(x["arm"], dict(rows=0, empty=0, perr=0, fail=0, nop=0, skip=0, noctx=0, trunc=0, np=0))
        h["rows"] += 1
        sk = x.get("skipped") or ""
        if sk.startswith("no pieces"):
            h["nop"] += 1
        elif sk:
            h["skip"] += 1
        elif not x.get("ok"):
            if not x.get("err") and not (x.get("raw") or "").strip():
                h["empty"] += 1
            else:
                h["fail"] += 1
        elif (x.get("detail") or {}).get("parse_error"):
            h["perr"] += 1
        if x.get("has_ctx") and not x.get("ctx_chars"):
            h["noctx"] += 1
        if x.get("ctx_trunc"):
            h["trunc"] += 1
        h["np"] += x.get("n_pieces") or 0
    for a in M.ARM_ORDER:
        if a in hc:
            h = hc[a]; print("| %s | %d | %d | %d | %d | %d | %d | %d | %d | %d |" % (a, h["rows"], h["empty"], h["perr"], h["fail"], h["nop"], h["skip"], h["noctx"], h["trunc"], h["np"]))


def main():
    if args.summary:
        summary(); return
    sel = select_rows()
    if PIECES is None:
        print('NOTE: %s not found: every answer is skipped (use --pieces for a stub in a dry run)' % args.pieces)
    if args.dry_run:
        counts = {m: 0 for m in metrics}; in_chars = {m: 0 for m in metrics}; skipped = {}
        for g, r in sel:
            for m in metrics:
                t = make_task(r, m)
                if 'prompt' not in t:
                    skipped[(m, t['skip'][:40])] = skipped.get((m, t['skip'][:40]), 0) + 1; continue
                counts[m] += 1; in_chars[m] += len(t['prompt'])
        shown = set()
        for want in arms:
            for g, r in sel:
                if r['arm'] == want and r.get('trace') and want not in shown:
                    t = make_task(r, metrics[0])
                    if 'prompt' not in t:
                        continue
                    shown.add(want); pr = t['prompt']
                    print('=' * 100); print('ANSWER: group=%s item=%s arm=%s method=%s' % (g, r['item'], want, r.get('method')))
                    print('--- %s prompt (%d chars, ~%d tokens, context %d chars%s) ---' % (metrics[0], len(pr), len(pr) // 4, t['ctx_chars'], ', CUT' if t['ctx_trunc'] else ''))
                    print(pr if args.full else pr[:700] + "\n[... %d chars omitted ...]\n" % max(0, len(pr) - 1500) + pr[-800:])
                    break
        print('=' * 100); print('DRY RUN SUMMARY (no calls made). answers selected: %d (groups %s, arms %s)' % (len(sel), ','.join(groups), ','.join(arms)))
        tot_c = 0; tot_cost = 0.0
        for m in counts:
            if not counts[m]:
                continue
            itok = in_chars[m] / 4.0; c = itok * args.price_in + OUT_TOK[m] * counts[m] * args.price_out
            print('%-13s calls %5d | mean prompt %6.0f tokens | est cost %.3f USD' % (m, counts[m], itok / counts[m], c)); tot_c += counts[m]; tot_cost += c
        print('TOTAL calls %d | est cost %.3f USD (price-in %.2e/token, price-out %.2e/token, chars/4 = tokens)' % (tot_c, tot_cost, args.price_in, args.price_out))
        if skipped:
            print('answers with no call: ' + '; '.join('%s/%s %d' % (k[0], k[1], v) for k, v in sorted(skipped.items())))
        return
    # ---- real run (paid) ----
    done = set(); cost_total = [0.0]
    if os.path.exists(args.out):
        for x in M.read_jsonl(args.out):
            if x.get("ok") or x.get("skipped"):
                done.add((x["group"], x["item"], x["arm"], x["metric"]))
    lock = threading.Lock()
    def save(rec):
        with lock:
            open(args.out, 'a').write(json.dumps(rec) + '\n'); cost_total[0] += rec.get('cost') or 0
    def do(gr):
        g, r, m = gr
        if cost_total[0] > args.max_cost:
            return
        t = make_task(r, m); key = dict(group=g, item=r['item'], arm=r['arm'], metric=m)
        if 'prompt' not in t:
            save(dict(key, score=t.get("score"), skipped=t["skip"], cost=0))   # every skip is recorded (harness check)
            return
        txt, c, e = call(t['prompt']); js = parse_json(txt)
        if js is None and not e:
            txt, c2, e = call(t['prompt']); c += c2; js = parse_json(txt)
        try:
            s, det = score_result(m, js, t)
        except Exception as ex:
            s, det = None, {"parse_error": type(ex).__name__ + " " + str(ex)[:100]}
        save(dict(key, score=s, detail=det, ok=js is not None, err=e, cost=c, in_chars=len(t["prompt"]), ctx_trunc=t["ctx_trunc"], ctx_chars=t.get("ctx_chars"), n_pieces=len(t.get("piece_ids") or []), has_ctx=t.get("has_ctx"), raw=(txt if js is None else None)))
    jobs = [(g, r, m) for g, r in sel for m in metrics if (g, r['item'], r['arm'], m) not in done]
    print('jobs', len(jobs), 'workers', args.workers, 'max cost', args.max_cost, flush=True)
    with cf.ThreadPoolExecutor(args.workers) as ex:
        list(ex.map(do, jobs))
    print('finished; cost this run %.4f USD' % cost_total[0])

main()
