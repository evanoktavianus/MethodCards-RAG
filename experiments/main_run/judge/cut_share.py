"""Share of retrieved items longer than the 1,500 characters that the context-precision judge sees (Section 4.6).
The items are built exactly as in ragas_judge.py: each card opened by Ours-cards2, and each page read by the
LongDA-style agent (Ours-text2), at most 20 items per answer. No model calls.

Needs the full answer rows with tool traces, which are not distributed (the released rows have no traces):

    python3 -I experiments/main_run/judge/cut_share.py FULL_ROWS_OURS.jsonl FULL_ROWS_TEXT.jsonl

On the institutional procedures it printed: cards 423 items, 282 longer than 1,500 characters (67%);
pages 858 items, 143 longer (17%)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mm_common as M

CUT = 1500


def split_chunks(obs):
    ms = list(M.CHUNK_RE.finditer(obs))
    if not ms:
        return [obs]
    return [obs[m.start():(ms[i + 1].start() if i + 1 < len(ms) else len(obs))].strip() for i, m in enumerate(ms)]


def items(r, arm):
    out = []
    if arm == 'Ours-cards2':
        seen = set()
        for e in M.method_events(r.get('trace')):
            if e['tool'] == 'get_card' and e['obs'].lstrip().startswith('card_id'):
                k = e['obs'][:80]
                if k not in seen:
                    seen.add(k)
                    out.append(e['obs'])
    else:
        pages, order = {}, []
        for e in M.method_events(r.get('trace')):
            if e['tool'] != 'read_source':
                continue
            dm = M.DOC_RE.search(e['inp'])
            doc = dm.group(1)[:8] if dm else '?'
            for c in split_chunks(e['obs']):
                cm = M.CHUNK_RE.match(c)
                if not cm:
                    continue
                key = (doc, int(cm.group(2)))
                if key not in pages:
                    pages[key] = ''
                    order.append(key)
                if c[:200] not in pages[key]:
                    pages[key] += c[:1200] + '\n'
        out = [pages[k] for k in order]
    return out[:20]


def main():
    for name, path, arm in (('cards (ours)', sys.argv[1], 'Ours-cards2'), ('pages (LongDA-style)', sys.argv[2], 'Ours-text2')):
        n = cut = 0
        for line in open(path):
            r = json.loads(line)
            if r.get('arm') != arm:
                continue
            for t in items(r, arm):
                n += 1
                cut += len(t) > CUT
        print('%-22s items %5d  longer than %d characters: %5d (%.0f%%)' % (name, n, CUT, cut, 100 * cut / n))


if __name__ == '__main__':
    main()
