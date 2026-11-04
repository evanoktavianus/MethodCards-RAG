"""Card builder, optional step: classify each document with one call (title, first ~2,000 tokens and the list of section headings).
Label 1 = methodology or technical guidance document, 2 = periodic or country report, 3 = neither. One rule for all documents. The label
is kept as a field of the card (`triage_label`) and used to choose the primary source when cards of several documents are merged
(consolidate.py); it is not used to filter documents.

  python3 tools/cards/triage.py --docs-dir DIR            # dry run: counts only
  python3 tools/cards/triage.py --docs-dir DIR --go       # writes work/cards/triage.jsonl (resumable)
"""
import argparse
import concurrent.futures as cf
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import llm

PROMPT = ("Classify this document from its title, its first ~2,000 tokens and its list of section headings.\n"
 "1 = a methodology or technical guidance document, manual, handbook, statistical standard or methods paper whose main purpose is to define procedures, formulas, indicators or classifications.\n"
 "2 = a periodic or country report (World Economic Outlook, Fiscal Monitor, Global Financial Stability Report, Asian Development Outlook, country or sector report) that may contain methodology boxes, annexes or technical notes.\n"
 "3 = neither.\nReply with one JSON object only: {\"label\": 1|2|3, \"reason\": \"one short line\"}.")


def headings(text):
    seen = []; s = set()
    for l in text.split('\n'):
        if l.startswith('## '):
            h = l[3:].split(' > ')[0][:90]
            if h not in s:
                s.add(h); seen.append(h)
    out = []; n = 0
    for h in seen:
        n += len(h) + 1
        if n > 6000:
            break
        out.append(h)
    return '\n'.join(out)


def one(args):
    d, t, title = args
    msg = PROMPT + "\n\nTITLE: %s\n\nSTART OF TEXT:\n%s\n\nSECTION HEADINGS:\n%s" % (title, t[:8000], headings(t))
    err = ''
    for att in range(3):
        try:
            c, cost = llm.chat(msg, 300, 300)
            o = json.loads(re.search(r'\{.*\}', c, re.S).group(0))
            return {'doc_id': d, 'title': title, 'label': int(o['label']), 'reason': str(o.get('reason', ''))[:200], 'cost': cost, 'tokens': len(t) // 4}
        except Exception as e:
            err = str(e)[:100]
    return {'doc_id': d, 'title': title, 'label': None, 'reason': 'ERROR ' + err, 'cost': 0, 'tokens': len(t) // 4}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--docs-dir', default=os.environ.get('MC_CARD_DOCS'))
    ap.add_argument('--go', action='store_true')
    ap.add_argument('--workers', type=int, default=16)
    a = ap.parse_args()
    if not a.docs_dir or not os.path.isdir(a.docs_dir):
        sys.exit('Give --docs-dir (a folder of <doc_id>.txt files).')
    titles = {}
    tp = os.path.join(a.docs_dir, 'titles.tsv')
    if os.path.exists(tp):
        for l in open(tp, encoding='utf-8'):
            p = l.rstrip('\n').split('\t')
            if len(p) >= 2:
                titles[p[0]] = p[1]
    out = os.path.join(llm.WORK, 'triage.jsonl')
    done = set()
    if os.path.exists(out):
        done = {json.loads(l)['doc_id'] for l in open(out) if l.strip() and json.loads(l)['label']}
    docs = [(f[:-4], open(os.path.join(a.docs_dir, f), encoding='utf-8').read()) for f in sorted(os.listdir(a.docs_dir)) if f.endswith('.txt')]
    docs = [(d, t, titles.get(d, '')) for d, t in docs if d not in done]
    print('documents to classify: %d | model %s' % (len(docs), llm.MODEL))
    if not a.go:
        print('DRY RUN: no call made. Add --go to call the model.')
        return
    os.makedirs(llm.WORK, exist_ok=True)
    tot = 0
    with cf.ThreadPoolExecutor(a.workers) as ex, open(out, 'a') as f:
        for o in ex.map(one, docs):
            f.write(json.dumps(o) + '\n'); tot += o['cost']
    print('cost', round(tot, 4))


if __name__ == '__main__':
    main()
