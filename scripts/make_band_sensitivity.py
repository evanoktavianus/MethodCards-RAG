"""Sensitivity of the gain of our agent to the definition of the question groups (no model calls, no key, standard library only).
Run from the repository root:

    python3 scripts/make_band_sensitivity.py     # prints the tables and writes work/band_sensitivity.md

Compare with eval/expected_band_sensitivity.md (the same text). The paper's groups follow a four-point structure rule
(experiments/splits/hard.json and easier.json). dataset/METHODS.md holds an earlier grouping by judgment (column Band: easy, medium,
hard). This script gives answer correctness of Ours-cards2 minus ReAct-v2 and minus Ours-text2 (the LongDA-style baseline) on the
questions of each Band and of the paper's groups, over the 440 questions of the main run (experiments/main_run/results_final_*.jsonl.gz).
Bootstrap as in scripts/make_second_model.py (4,000 resamples of the methods, order of the question lists, seed 1, 95% percentile
interval, mean weighted by questions); p = exact two-sided sign-flip test over methods (all 2^k patterns). Failed answers count 0."""
import glob
import itertools
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_metrics as mm

ROOT = mm.ROOT + '/'
B = 4000
OUT = ROOT + 'work/band_sensitivity.md'
items = mm.load_items()
folder = {}
for f in glob.glob(ROOT + 'dataset/items/*/*.json'):
    folder[os.path.basename(f)[:-5]] = os.path.basename(os.path.dirname(f))
HARD = json.load(open(ROOT + 'experiments/splits/hard.json'))['hard']
EASIER = json.load(open(ROOT + 'experiments/splits/easier.json'))['easier']
ORDER = HARD + EASIER
hardset = set(HARD)
T = {}
for g in ('hard', 'easier'):
    for r in mm.read_jsonl(mm.MAIN + '/results_final_%s.jsonl.gz' % g):
        T.setdefault(r['arm'], {})[r['item']] = mm.score_of(r)
T = {a: {i: d[i] for i in ORDER if i in d} for a, d in T.items()}

# Band of each folder, from the table of dataset/METHODS.md (first word of the Method cell = folder name or its prefix)
band = {}
for l in open(ROOT + 'dataset/METHODS.md', encoding='utf-8'):
    if l.startswith('| ') and not l.startswith('| Method') and not l.startswith('|---'):
        c = [x.strip() for x in l.strip().strip('|').split('|')]
        if len(c) >= 8:
            band[c[0].split(' ')[0]] = c[6].lower()
fold_of = {}
for i in ORDER:
    f = folder[i]
    cands = [f] if f in band else [k for k in band if f.startswith(k) or k.startswith(f)]
    assert cands, ('no Band for folder', f)
    fold_of[i] = cands[0]
band_of = lambda i: band[fold_of[i]]


def boot(a, b, keys):
    ks = [k for k in ORDER if k in a and k in b and k in keys]
    by = {}
    for k in ks:
        by.setdefault(items[k]['method'], []).append(a[k] - b[k])
    cl = list(by.values()); n = sum(len(c) for c in cl); est = sum(sum(c) for c in cl) / n
    rnd = random.Random(1); ds = []
    for _ in range(B):
        s = [cl[rnd.randrange(len(cl))] for _ in cl]
        ds.append(sum(sum(c) for c in s) / sum(len(c) for c in s))
    ds.sort()
    return est, ds[int(0.025 * B)], ds[int(0.975 * B) - 1], n, len(cl), by


def flip(by):
    ms = sorted(by); allq = sum(len(by[m]) for m in ms); obs = sum(sum(by[m]) for m in ms) / allq
    sm = [sum(by[m]) for m in ms]; cnt = tot = 0
    for sg in itertools.product((1, -1), repeat=len(ms)):
        v = sum(s * x for s, x in zip(sg, sm)) / allq; tot += 1; cnt += abs(v) >= abs(obs) - 1e-12
    return cnt / tot


allk = set(T['Ours-cards2'])
S = [('Band hard (METHODS.md)', {i for i in allk if band_of(i) == 'hard'}),
     ('Band medium', {i for i in allk if band_of(i) == 'medium'}),
     ('Band easy', {i for i in allk if band_of(i) == 'easy'}),
     ('Band easy to medium (external_sector)', {i for i in allk if band_of(i) == 'easy to medium'}),
     ('Band hard + medium', {i for i in allk if band_of(i) in ('hard', 'medium')}),
     ('Band easy + easy to medium', {i for i in allk if band_of(i) in ('easy', 'easy to medium')}),
     ('Paper: institutional procedures (hard.json)', {i for i in allk if i in hardset}),
     ('Paper: standard formulas (easier.json)', {i for i in allk if i not in hardset})]
O = ['# Sensitivity to the definition of the groups', '',
     'Answer correctness, Ours-cards2 minus the other arm, 440 questions of the main run; 95% cluster bootstrap over methods (4,000 resamples, seed 1); '
     'p = exact two-sided sign-flip test over methods (question-weighted mean). Failed answers count 0.', '',
     '| Subset | Questions | Methods | Ours mean | Ours minus ReAct (95% interval) | p | Ours minus LongDA-style (95% interval) | p |', '|---|---|---|---|---|---|---|---|']
for nm, ks in S:
    cells = []
    for b in ('ReAct-v2', 'Ours-text2'):
        e, lo, hi, n, k, by = boot(T['Ours-cards2'], T[b], ks); cells.append('%+.1f [%+.1f, %+.1f] | %.4f' % (e, lo, hi, flip(by)))
    O.append('| %s | %d | %d | %.1f | %s |' % (nm, len(ks), k, sum(T['Ours-cards2'][i] for i in ks) / len(ks), ' | '.join(cells)))
O += ['', '## Methods by Band and paper group', '', '| Method | Band | Paper group | Questions | Ours minus ReAct | Ours minus LongDA-style |', '|---|---|---|---|---|---|']
ml = {}
for i in allk:
    ml.setdefault(items[i]['method'], []).append(i)
for m, ii in sorted(ml.items(), key=lambda x: (band_of(x[1][0]), x[0])):
    g = 'institutional procedures' if ii[0] in hardset else 'standard formulas'
    d1 = sum(T['Ours-cards2'][i] - T['ReAct-v2'][i] for i in ii) / len(ii); d2 = sum(T['Ours-cards2'][i] - T['Ours-text2'][i] for i in ii) / len(ii)
    O.append('| %s | %s | %s | %d | %+.1f | %+.1f |' % (m, band_of(ii[0]), g, len(ii), d1, d2))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, 'w').write('\n'.join(O) + '\n')
print('\n'.join(O))
