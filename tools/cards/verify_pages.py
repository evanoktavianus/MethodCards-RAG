"""Card builder, page-level source check (no model call). Keeps a parameter only if its quote occurs verbatim inside ONE page of the
document (the page is then recorded), keeps the formula only if its text (or a variant without $ signs) occurs on one page (otherwise it is
kept as `formula_paraphrase`, shown with '~' in `short_formula`), and records for every card its `sources` entry (pages, quote, role,
sha1 of the cited pages). A card without any verified quote gets `source_unverified` = true. The page of a quote is the page of the
[[page N]] marker that precedes it.

  python3 tools/cards/verify_pages.py --docs-dir DIR [--cards work/cards/cards_q.jsonl] [--triage work/cards/triage.jsonl]
Writes work/cards/cards_v2.jsonl and prints the counts."""
import argparse
import collections
import datetime
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import llm

WS = re.compile(r'\s+'); PGM = re.compile(r'\[\[page (\d+)\]\]')


def norm(s):
    return WS.sub(' ', s).strip()


def pages_of(text):
    """{page: normalised text}; text before the first marker is page 0"""
    parts = PGM.split(text); out = {}
    if parts[0].strip():
        out[0] = norm(parts[0])
    for i in range(1, len(parts), 2):
        p = int(parts[i]); out[p] = (out.get(p, '') + ' ' + norm(parts[i + 1])).strip()
    return out


def find_pages(q, pages):
    """pages (sorted) where the normalised quote occurs inside a single page text; [] if none"""
    nq = norm(q)
    return [p for p in sorted(pages) if nq in pages[p]]


def formula_variants(f):
    f = norm(f); v = [f, f.replace('$', ''), re.sub(r'\s*\$+\s*', '', f)]
    v.append(re.sub(r'^\$+|\$+$', '', f).strip())
    return [norm(x) for x in dict.fromkeys(v) if len(norm(x)) >= 8]


def hash_pages(pages, plist):
    return hashlib.sha1('\n'.join(pages.get(p, '') for p in sorted(set(plist))).encode()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--docs-dir', default=os.environ.get('MC_CARD_DOCS'))
    ap.add_argument('--cards', default=os.path.join(llm.WORK, 'cards_q.jsonl'))
    ap.add_argument('--triage', default=os.path.join(llm.WORK, 'triage.jsonl'))
    ap.add_argument('--out', default=os.path.join(llm.WORK, 'cards_v2.jsonl'))
    a = ap.parse_args()
    if not a.docs_dir or not os.path.isdir(a.docs_dir):
        sys.exit('Give --docs-dir (a folder of <doc_id>.txt files).')
    cards = [json.loads(l) for l in open(a.cards, encoding='utf-8') if l.strip()]
    PG = {d: pages_of(open(os.path.join(a.docs_dir, d + '.txt'), encoding='utf-8').read()) for d in {c['doc_id'] for c in cards}}
    tri = {}
    if os.path.exists(a.triage):
        tri = {json.loads(l)['doc_id']: json.loads(l)['label'] for l in open(a.triage) if l.strip()}
    st = collections.Counter(); out = []; ts = datetime.datetime.now().isoformat(timespec='seconds')
    for c in cards:
        d = c['doc_id']; pg = PG[d]; src_pages = set(); params = []
        c['triage_label'] = tri.get(d, c.get('triage_label'))
        for p in c['parameters']:
            if p['value'] is None:
                continue
            ps = find_pages(p['quote'] or '', pg) if p.get('quote') else []; st['param_total'] += 1
            if not ps:
                st['param_not_in_single_page'] += 1; continue       # fails the page-level verbatim check -> dropped
            st['param_kept'] += 1; st['param_model_page_matches'] += (p.get('page') in ps)
            params.append({'name': p['name'], 'value': p['value'], 'quote': p['quote'], 'page': ps[0], 'source': 0}); src_pages.add(ps[0])
        fq = None; fp = None
        raw = c.get('formula_paraphrase') or c['formula']
        if raw.strip():
            st['formula_total'] += 1
            for v in formula_variants(raw):
                ps = find_pages(v, pg)
                if ps:
                    fq, fp = v, ps[0]; break
        if fq:
            st['formula_verified'] += 1; src_pages.add(fp)
        quote = fq or (params[0]['quote'][:400] if params else None)
        if quote is None:
            st['card_no_quote'] += 1
        if not src_pages and c.get('pages'):
            try:
                src_pages = {int(x) for x in c['pages'] if str(x).isdigit()} & set(pg)
            except Exception:
                pass
        c['parameters_old'] = c.pop('parameters'); c['parameters'] = params
        c['formula_paraphrase'] = None if fq else (raw or None); c['formula'] = fq or ''
        c['formula_quote'] = {'quote': fq, 'page': fp, 'source': 0} if fq else None
        c['short_formula'] = norm(fq)[:160] if fq else ('~ ' + norm(c['formula_paraphrase'])[:157] if c['formula_paraphrase'] else '')
        sp = sorted(src_pages)
        c['pages'] = sp
        c['sources'] = [{'doc_id': d, 'doc_title': c['doc_title'], 'pages': sp, 'quote': quote, 'role': 'defines' if tri.get(d) == 1 else 'restates_or_defines',
                         'source_hash': hash_pages(pg, sp), 'compiled_at': ts}]
        c['conflicts'] = []; c['source_unverified'] = quote is None
        out.append(c)
    with open(a.out, 'w', encoding='utf-8') as f:
        for c in out:
            f.write(json.dumps(c, ensure_ascii=False) + '\n')
    st['cards'] = len(out)
    print(dict(st))


if __name__ == '__main__':
    main()
