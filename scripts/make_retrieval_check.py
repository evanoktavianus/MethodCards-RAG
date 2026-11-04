"""Author's check of the judge on the retrieval metrics and of the method pieces (no model calls, no key, standard library only).
Run from the repository root:

    python3 scripts/make_retrieval_check.py     # prints the numbers and writes work/retrieval_check.md

Compare with eval/expected_retrieval_check.md (the same text). Reads eval/human_check_retrieval/:
- judge_check_marks.csv: 60 decisions of the judge (A1 context recall: is the method piece stated in the retrieved text; A2 context
  precision: does the card or page state the question's method; A3 faithfulness: is the claim backed by the retrieved text), 10 per block
  from each agent (Ours-cards2 = ours, Ours-text2 = LongDA-style). Column judge holds the judge's verdict (yes/no) for A1 and A2 and, for
  A3, the judge's answer-level share of supported claims (its own claims were not stored); column author holds the first author's mark
  (yes / partly / no; n/a = the sampled sentence is not a method claim). The author marked blind to the judge's verdicts.
- piece_marks.csv: the author's verdict (correct / wrong / unsure) on each method piece of 40 questions, against the source pages.
- missing_piece_marks.csv: whether an important piece of the method is missing from the question's pieces."""
import csv
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, 'eval', 'human_check_retrieval')
ARMS = ('Ours-cards2', 'Ours-text2')
SC = {'yes': 1.0, 'partly': 0.5, 'no': 0.0}


def rows(name):
    with open(os.path.join(D, name), encoding='utf-8') as f:
        return list(csv.DictReader(f))


def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return 100 * (c - h), 100 * (c + h)


def kappa(pairs, cats):
    n = len(pairs); po = sum(a == b for a, b in pairs) / n
    pe = sum((sum(a == c for a, _ in pairs) / n) * (sum(b == c for _, b in pairs) / n) for c in cats)
    return (po - pe) / (1 - pe)


A = rows('judge_check_marks.csv'); P = rows('piece_marks.csv'); Q = rows('missing_piece_marks.csv')
assert len(A) == 60 and len(Q) == 40
out = ['# Author check of the judge on the retrieval metrics, and of the method pieces', '']
allp = []
for blk, name in (('A1', 'Context recall (method)'), ('A2', 'Context precision')):
    r = [x for x in A if x['block'] == blk]
    assert len(r) == 20 and all(x['author'] in SC and x['judge'] in ('yes', 'no') for x in r)
    pairs = [(x['author'], x['judge']) for x in r]; allp += pairs
    ag = sum(a == j for a, j in pairs); lo, hi = wilson(ag, len(pairs))
    out += ['## %s (%s)' % (name, blk), '',
            'Agreement %d of %d (%.1f%%, Wilson 95%% interval %.1f to %.1f); Cohen\'s kappa %.2f (yes / partly / no; partly counts as a disagreement).'
            % (ag, len(pairs), 100 * ag / len(pairs), lo, hi, kappa(pairs, ['no', 'partly', 'yes'])), '',
            '| Agent | Decisions | Agreed | Judge more lenient (judge yes, author no or partly) | Judge stricter (judge no, author yes or partly) | Mean author | Mean judge |',
            '|---|---|---|---|---|---|---|']
    for arm in ARMS:
        ra = [x for x in r if x['agent'] == arm]
        out.append('| %s | %d | %d | %d | %d | %.2f | %.2f |' % (
            arm, len(ra), sum(x['author'] == x['judge'] for x in ra),
            sum(x['judge'] == 'yes' and x['author'] != 'yes' for x in ra), sum(x['judge'] == 'no' and x['author'] != 'no' for x in ra),
            sum(SC[x['author']] for x in ra) / len(ra), sum(SC[x['judge']] for x in ra) / len(ra)))
    out.append('')
ag = sum(a == j for a, j in allp); lo, hi = wilson(ag, len(allp))
out += ['## Context recall and context precision together', '',
        'Agreement %d of %d (%.1f%%, Wilson 95%% interval %.1f to %.1f); Cohen\'s kappa %.2f.' % (ag, len(allp), 100 * ag / len(allp), lo, hi, kappa(allp, ['no', 'partly', 'yes'])), '']
r3 = [x for x in A if x['block'] == 'A3']; m3 = [x for x in r3 if x['author'] in SC]
out += ['## Faithfulness (A3)', '',
        'Sampled sentences %d; not a method claim (n/a) %d; author marks on the %d method claims: yes %d, partly %d, no %d.' % (
            len(r3), len(r3) - len(m3), len(m3), *[sum(x['author'] == m for x in m3) for m in ('yes', 'partly', 'no')]),
        'The judge\'s own claims were not stored, so only means can be compared (author mark against the judge\'s answer-level share of supported claims).', '',
        '| Agent | Method claims | Mean author | Mean judge (answer level) |', '|---|---|---|---|']
for arm in ARMS:
    ra = [x for x in m3 if x['agent'] == arm]
    out.append('| %s | %d | %.2f | %.2f |' % (arm, len(ra), sum(SC[x['author']] for x in ra) / len(ra), sum(float(x['judge']) for x in ra) / len(ra)))
out.append('')
cnt = {v: sum(x['author'] == v for x in P) for v in ('correct', 'wrong', 'unsure')}
lo, hi = wilson(cnt['correct'], len(P))
miss = [x['question'] for x in Q if x['important_piece_missing'] == 'yes']
qw = sorted({x['question'] for x in P if x['author'] == 'wrong'})
a1 = [x for x in A if x['block'] == 'A1']
out += ['## Method pieces', '',
        'Questions %d; pieces %d: correct %d, wrong %d, unsure %d; correct %.1f%% (Wilson 95%% interval %.1f to %.1f).' % (
            len({x['question'] for x in P}), len(P), cnt['correct'], cnt['wrong'], cnt['unsure'], 100 * cnt['correct'] / len(P), lo, hi),
        'Questions with a wrong piece: %d (%s). Questions with an important piece missing: %d (%s).' % (len(qw), ', '.join(qw) or 'none', len(miss), ', '.join(miss) or 'none'),
        'Second mark on the 20 pieces of the context recall rows (piece correct for the method?): correct %d, wrong %d, unsure %d.' % tuple(
            sum(x['author_piece_correct'] == v for x in a1) for v in ('correct', 'wrong', 'unsure')), '']
text = '\n'.join(out)
os.makedirs(os.path.join(ROOT, 'work'), exist_ok=True)
open(os.path.join(ROOT, 'work', 'retrieval_check.md'), 'w', encoding='utf-8').write(text)
print(text)
