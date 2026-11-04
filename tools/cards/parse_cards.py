"""Card builder, step 2 of 3: parse the outputs of compile_cards.py, keep a parameter only if its quote is verbatim in the
document text (page markers removed, white space normalised), and write the cards. No model call, no key.

Input : the same documents folder and titles file as compile_cards.py; work/cards/compiled/*.json
Output: work/cards/cards.jsonl        one card per line, same fields as tools/bank/cards_final.jsonl
        work/cards/cards_stats.json   counts, cost, parse status, share of parameters dropped

  python3 tools/cards/parse_cards.py --docs-dir DIR
"""
import argparse, collections, glob, hashlib, json, os, re, sys, time

ROOT = os.environ.get('MC_ROOT') or os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
WORK = os.path.join(ROOT, 'work', 'cards')
WS = re.compile(r'\s+'); PG = re.compile(r'\[\[page \d+\]\]')
SEP = re.compile(r'[\s,]*')


def norm(s):
    return WS.sub(' ', s).strip()


def parse(c):
    """The first JSON list in the model answer; objects are read one by one, so a truncated answer keeps its complete objects."""
    c = c.strip(); i = c.find('[')
    if i < 0:
        return [], 'noarray'
    dec = json.JSONDecoder(); out = []; j = i + 1; status = 'ok'
    while True:
        m = SEP.match(c, j); j = m.end()
        if j >= len(c) or c[j] == ']':
            break
        try:
            o, j = dec.raw_decode(c, j)
        except Exception:
            status = 'truncated_or_bad'; break
        if isinstance(o, dict):
            out.append(o)
    return out, status


def s(x):
    return x if isinstance(x, str) else ('' if x is None else json.dumps(x, ensure_ascii=False))


def lst(x):
    return [s(y) for y in x] if isinstance(x, list) else ([s(x)] if x else [])


def pages_list(x):
    """Pages as a list of integers (the compiled answer may give an int, a list or a string such as '12-13')."""
    if isinstance(x, list):
        out = []
        for y in x:
            out += pages_list(y)
        return out
    if isinstance(x, bool) or x is None:
        return []
    if isinstance(x, int):
        return [x]
    return [int(n) for n in re.findall(r'\d+', str(x))]


def load_titles(path):
    T = {}
    if path and os.path.exists(path):
        for l in open(path, encoding='utf-8'):
            p = l.rstrip('\r\n').split('\t')
            if len(p) < 2 or p[0].startswith('#') or p[0] == 'doc_id':
                continue
            T[p[0]] = (p[1], p[2] if len(p) > 2 else '')
    return T


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--docs-dir', default=os.environ.get('MC_CARD_DOCS'), help='folder of <doc_id>.txt files (default: env MC_CARD_DOCS)')
    ap.add_argument('--titles', default=None, help='titles file (default: DOCS_DIR/titles.tsv if present)')
    a = ap.parse_args()
    if not a.docs_dir or not os.path.isdir(a.docs_dir):
        sys.exit('No documents folder: pass --docs-dir DIR or set MC_CARD_DOCS.')
    TIT = load_titles(a.titles or os.path.join(a.docs_dir, 'titles.tsv'))
    texts = {}; raw = {}
    for fn in sorted(os.listdir(a.docs_dir)):
        if fn.endswith('.txt'):
            with open(os.path.join(a.docs_dir, fn), encoding='utf-8') as f:
                t = f.read()
            raw[fn[:-4]] = t; texts[fn[:-4]] = norm(PG.sub(' ', t))
    files = sorted(glob.glob(os.path.join(WORK, 'compiled', '*.json')))
    if not files:
        sys.exit('No compiled outputs in %s (run compile_cards.py --go first).' % os.path.join(WORK, 'compiled'))
    byd = collections.defaultdict(list); st = collections.Counter(); finish = collections.Counter()
    cost = 0; calls = 0; ptok = 0; ctok = 0; missing = set()
    for f in files:
        with open(f, encoding='utf-8') as fh:
            r = json.load(fh)
        if r['doc'] not in texts:
            missing.add(r['doc']); continue
        calls += 1; cost += r.get('cost') or 0; ptok += r.get('prompt_tokens') or 0; ctok += r.get('completion_tokens') or 0
        objs, status = parse(r['content']); st[status] += 1; finish[r.get('finish')] += 1
        byd[r['doc']].extend((r['w'], o) for o in objs)
    docs_sorted = sorted(byd)
    pre = [d[:8] for d in docs_sorted]
    short_ok = len(set(pre)) == len(pre)        # card_id = first 8 characters of the doc id, as in the reported bank, unless that is ambiguous
    cards = []; pt = pk = pd = pnull = 0; dropped_ex = []
    for d in docs_sorted:
        seen = set(); n = 0
        title, publisher = TIT.get(d, ('', ''))
        shash = hashlib.sha1(texts[d].encode('utf-8')).hexdigest(); now = time.strftime('%Y-%m-%dT%H:%M:%S')
        for w, o in sorted(byd[d], key=lambda x: x[0]):
            name = s(o.get('name')).strip()
            if not name or norm(name).lower() in seen:
                continue
            seen.add(norm(name).lower()); params = []
            for p in (o.get('parameters') or []):
                if not isinstance(p, dict):
                    continue
                q = p.get('verbatim_quote'); v = p.get('value'); pt += 1
                if v is None and not q:
                    pnull += 1; params.append({'name': s(p.get('name')), 'value': None, 'quote': None, 'page': p.get('page'), 'source': 0}); continue
                if isinstance(q, str) and q.strip() and norm(q) in texts[d]:
                    pk += 1; params.append({'name': s(p.get('name')), 'value': s(v), 'quote': q, 'page': p.get('page'), 'source': 0})
                else:
                    pd += 1
                    if len(dropped_ex) < 15:
                        dropped_ex.append([d[:8], s(p.get('name'))[:50], s(q)[:100]])
            n += 1
            pv = [p for p in params if p['value'] is not None]
            formula = s(o.get('formula')); fn_ = norm(formula)
            fverified = len(fn_) >= 15 and fn_ in texts[d]
            ct = "%s. Also called: %s. Applies when: %s Inputs: %s. Formula: %s. Parameters: %s" % (
                name, '; '.join(lst(o.get('aliases'))), s(o.get('applies_when')), '; '.join(lst(o.get('inputs'))), formula,
                '; '.join('%s = %s' % (p['name'], p['value']) for p in pv))
            pg = pages_list(o.get('pages'))
            first_q = next((p['quote'] for p in pv if p['quote']), '')
            cid = ('%s-%02d' % (d[:8], n)) if short_ok else ('%s-%02d' % (d, n))
            cards.append({'triage_label': None, 'in_sections': None, 'in_bank': True, 'card_id': cid, 'doc_id': d, 'doc_class': 'unknown',
                          'doc_title': title, 'name': name, 'aliases': lst(o.get('aliases')),
                          'institution': s(o.get('institution')) or publisher, 'document_title': s(o.get('document_title')),
                          'applies_when': s(o.get('applies_when')), 'inputs': lst(o.get('inputs')), 'formula': formula,
                          'procedure': lst(o.get('procedure')), 'open_points': lst(o.get('open_points')), 'pages': pg,
                          'card_text': ct[:2500], 'questions': [], 'central': None, 'kind': None, 'central_flag': False,
                          'short_formula': ('' if not fn_ else (formula[:200] if fverified else '~ ' + formula[:200])),
                          'doc_rank': 1, 'parameters': params, 'formula_paraphrase': formula, 'formula_quote': formula if fverified else None,
                          'sources': [{'doc_id': d, 'doc_title': title, 'pages': pg, 'quote': first_q, 'role': 'defines',
                                       'source_hash': shash, 'compiled_at': now}],
                          'conflicts': [], 'source_unverified': not fverified and not pv})
    os.makedirs(WORK, exist_ok=True)
    with open(os.path.join(WORK, 'cards.jsonl'), 'w', encoding='utf-8') as f:
        for c in cards:
            f.write(json.dumps(c, ensure_ascii=False) + '\n')
    docs_with = {c['doc_id'] for c in cards}
    stats = {'cards': len(cards), 'docs_in_folder': len(texts), 'docs_compiled': len(byd), 'docs_with_cards': len(docs_with),
             'windows_parsed': calls, 'cost_usd': round(cost, 4), 'prompt_tokens': ptok, 'completion_tokens': ctok, 'finish': dict(finish),
             'parse_status': dict(st), 'compiled_docs_without_text_file': sorted(missing), 'card_id_prefix': 8 if short_ok else 'full doc id',
             'params_total': pt, 'params_kept_with_quote': pk, 'params_dropped': pd, 'params_null': pnull,
             'param_drop_share_of_quoted': round(pd / max(1, pk + pd), 4), 'dropped_examples': dropped_ex}
    with open(os.path.join(WORK, 'cards_stats.json'), 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=1)
    print(json.dumps(stats, indent=1))


if __name__ == '__main__':
    main()
