#!/usr/bin/env python3
"""Agreement between the automatic judge (judge v2) and the author's marks on 40 blind answers (178 scored claim rows).
No key, no model call, standard library only.

    python3 scripts/judge_agreement.py [eval/human_check/human_check_scores.csv]

Columns of the CSV: case, claim, kind, judge_score, author_score (the author's own score, given before the judge's scores were added).
Two rows have no judge score (the key states no number) and are left out.
Reports raw agreement, Cohen's kappa (0 / 0.5 / 1 as three categories) and linearly weighted kappa.
"""
import csv, os, sys

CATS = (0.0, 0.5, 1.0)


def kappa(pairs, weighted=False):
    n = len(pairs)
    pj = {c: sum(1 for j, _ in pairs if j == c) / n for c in CATS}
    ph = {c: sum(1 for _, h in pairs if h == c) / n for c in CATS}
    w = (lambda a, b: 1 - abs(a - b)) if weighted else (lambda a, b: 1.0 if a == b else 0.0)
    po = sum(w(j, h) for j, h in pairs) / n
    pe = sum(w(a, b) * pj[a] * ph[b] for a in CATS for b in CATS)
    return (po - pe) / (1 - pe)


def main():
    p = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..', 'eval', 'human_check', 'human_check_scores.csv')
    pairs = []
    for r in csv.DictReader(open(p, encoding='utf-8')):
        if r['judge_score'] == '':
            continue
        pairs.append((float(r['judge_score']), float(r['author_score'])))
    n = len(pairs)
    agree = sum(1 for j, h in pairs if j == h)
    print('rows scored: %d' % n)
    print('agreement  : %d / %d = %.1f%%' % (agree, n, 100 * agree / n))
    print("Cohen's kappa          : %.3f" % kappa(pairs))
    print("Cohen's kappa (linear) : %.3f" % kappa(pairs, True))
    print('judge scores 0 / 0.5 / 1 : %s' % ' / '.join(str(sum(1 for j, _ in pairs if j == c)) for c in CATS))
    print('author scores 0 / 0.5 / 1 : %s' % ' / '.join(str(sum(1 for _, h in pairs if h == c)) for c in CATS))


if __name__ == '__main__':
    main()
