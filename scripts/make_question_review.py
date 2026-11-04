"""Review of the question set (no model calls, no key, standard library only). Run from the repository root:

    python3 scripts/make_question_review.py     # prints the numbers and writes work/question_review.md

Compare with eval/expected_question_review.md (the same text). Reads eval/question_review/model_review_marks.csv (200 sampled
questions, five checks each, marks Y yes / N no / ? unsure, by the reviewing language-model agents) and author_check_marks.csv (the first
author's marks on 40 of the 200). Checks 1 to 3 (answerable from the frozen data, reference answer follows from the method, claims match
the reference answer) decide whether the reference is wrong: a question with N on any of them. Reports the share of wrong references with
its Wilson 95% interval, and the agreement between the author and the review on checks 1 to 3 of the 40 questions (marks and Cohen's kappa
over the three marks)."""
import csv
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, 'eval', 'question_review')


def read(name):
    with open(os.path.join(D, name), encoding='utf-8') as f:
        return {r['question']: [r[k] for k in ('answerable', 'follows_method', 'claims_match', 'method_not_named', 'no_invented_figure')] for r in csv.DictReader(f)}


def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return 100 * (c - h), 100 * (c + h)
model, author = read('model_review_marks.csv'), read('author_check_marks.csv')
assert len(model) == 200 and len(author) == 40 and set(author) <= set(model)
wrong = sorted(q for q, m in model.items() if 'N' in m[:3])
lo, hi = wilson(len(wrong), len(model))
awrong = sorted(q for q, m in author.items() if 'N' in m[:3])
pairs = [(author[q][k], model[q][k]) for q in sorted(author) for k in range(3)]
agree = sum(a == b for a, b in pairs); n = len(pairs)
cats = ('Y', '?', 'N')
po = agree / n
pe = sum((sum(a == c for a, _ in pairs) / n) * (sum(b == c for _, b in pairs) / n) for c in cats)
kappa = (po - pe) / (1 - pe)
L = ['# Review of the question set', '',
     'Questions reviewed: %d. Wrong reference (N on check 1, 2 or 3): %d (%.1f%%, Wilson 95%% interval %.1f to %.1f): %s.' % (len(model), len(wrong), 100 * len(wrong) / len(model), lo, hi, ', '.join(wrong)),
     'Author check: %d questions; wrong reference found by the author: %d (%s).' % (len(author), len(awrong), ', '.join(awrong)),
     'Agreement of the author with the review on checks 1 to 3 of these %d questions: %d of %d marks; Cohen\'s kappa over Y, ? and N = %.2f.' % (len(author), agree, n, kappa), '']
os.makedirs(os.path.join(ROOT, 'work'), exist_ok=True)
open(os.path.join(ROOT, 'work', 'question_review.md'), 'w').write('\n'.join(L) + '\n')
print('\n'.join(L))
