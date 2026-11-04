"""Paired comparisons of the main run (no model calls, no key, standard library only). Run from the repository root:

    python3 scripts/make_comparisons.py         # prints the tables and writes work/comparisons.md

Compare with eval/expected_comparisons.md (the same text). Rebuilds from the stored rows:
 (a) our agent (Ours-cards2) minus ReAct-v2 and minus the LongDA-style baseline (Ours-text2), on every metric of the ladder and the
     retrieval table, in both groups: difference of means with a 95% paired cluster bootstrap over methods;
 (b) the oracle analysis: method given, data given, both given, each minus both found;
 (c) robustness: subsets of questions, leave one method out, numeric tolerances halved and doubled, per-method positive counts with
     the exact sign-flip test over methods;
 (d) the analysis over all 28 methods: Spearman correlation of the gain over ReAct with the memory-only score (permutation test),
     the pooled gain and the sign-flip test over methods.
Bootstrap (the same code and seed as scripts/make_second_model.py): 4,000 resamples of the methods of the compared questions, in the
order of the question list, 95% percentile interval (sorted draws 100 and 3,899, counted from 0), seed 1, mean weighted by questions.
Failed or missing answers count 0; a metric that does not exist for a question (no claim of that kind, no retrieved item) is left out of
that comparison. The permutation test of the Spearman correlation uses random.Random(1) (200,000 permutations).
Context precision in this script is compared over the questions in which both arms completed an answer and retrieved a method item, so
its means differ from Table 8 of the paper, where a failed answer counts 0."""
import itertools
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_metrics as mm

ROOT = mm.ROOT + '/'
B = 4000
OUT = ROOT + 'work/comparisons.md'
ctx = mm.Ctx()
items = ctx.items
IDS = {'hard': json.load(open(ROOT + 'experiments/splits/hard.json'))['hard'],
       'easier': json.load(open(ROOT + 'experiments/splits/easier.json'))['easier']}
GL = {'hard': 'Institutional procedures', 'easier': 'Standard formulas'}
W = {'text': 40, 'data': 20, 'computation': 25, 'answer': 15}


def rows_of(g):
    d = {}
    for r in ctx.results[g]:
        d.setdefault(r['arm'], {})[r['item']] = r
    return d
ROWS = {g: rows_of(g) for g in ctx.results}


def vals(g, arm, key):
    """question -> value (in points, 0-100) of one metric of one arm; None-valued questions are left out."""
    out = {}
    for i in IDS[g.replace('_datagiven', '')]:
        r = ROWS[g][arm].get(i)
        if r is None:
            continue
        if key == 'prec':   # left out when the answer failed or retrieved no method item (as in the paper's paired comparison)
            j = ctx.fp.get(('precision', g, i, arm))
            v = None if j is None or j.get('score') is None else j['score']
        else:
            v = ctx.answer_values(g, r).get(key)
        if v is not None:
            out[i] = 100.0 * v
    return out


def boot(a, b, keys=None, seed=1):
    ks = [k for k in a if k in b and (keys is None or k in keys)]
    by = {}
    for k in ks:
        by.setdefault(items[k]['method'], []).append(a[k] - b[k])
    cl = list(by.values()); n = sum(len(c) for c in cl)
    if not n:
        return None
    est = sum(sum(c) for c in cl) / n
    rnd = random.Random(seed); ds = []
    for _ in range(B):
        s = [cl[rnd.randrange(len(cl))] for _ in cl]
        ds.append(sum(sum(c) for c in s) / sum(len(c) for c in s))
    ds.sort()
    return est, ds[int(0.025 * B)], ds[int(0.975 * B) - 1], n, len(cl)


def fm(t, n=False):
    if t is None:
        return 'n/a'
    s = '%+.1f [%+.1f, %+.1f]' % t[:3]
    return s + (' (n=%d)' % t[3] if n else '')


def mean(d):
    return sum(d.values()) / len(d) if d else None


def f1(x):
    return 'n/a' if x is None else '%.1f' % x


def signflip(d):
    """d: method -> list of differences. Exact two-sided sign-flip over methods, question-weighted mean."""
    meths = sorted(d); allq = [x for k in meths for x in d[k]]; obs = sum(allq) / len(allq)
    cnt = tot = 0
    for signs in itertools.product((1, -1), repeat=len(meths)):
        v = sum(s * sum(d[k]) for s, k in zip(signs, meths)) / len(allq); tot += 1; cnt += abs(v) >= abs(obs) - 1e-12
    return obs, sum(1 for k in meths if sum(d[k]) > 0), len(meths), cnt / tot


def by_method(a, b, keys=None):
    d = {}
    for k in a:
        if k in b and (keys is None or k in keys):
            d.setdefault(items[k]['method'], []).append(a[k] - b[k])
    return d


L = ['# Paired comparisons of the main run', '',
     'Differences in points (0-100) of our agent (Ours-cards2) minus the other arm, with a 95% paired cluster bootstrap over methods '
     '(4,000 resamples, seed 1). Failed answers count 0. n = number of questions that have the metric in both arms.', '']

# (a) every metric of the ladder and the retrieval table
METRICS = [('Method correctness (factual correctness)', 'mc_all'), ('Method explained', 'text'), ('Data correctness', 'data'),
           ('Computation correctness', 'computation'), ('Answer correctness', 'answer'), ('Fully correct answers', 'full'),
           ('Context recall (method)', 'cr'), ('Context precision', 'prec'), ('Context recall (data)', 'dr'), ('Faithfulness', 'faith')]
BASES = (('ReAct-v2', 'ReAct'), ('Ours-text2', 'LongDA-style'))
for g in ('hard', 'easier'):
    L += ['## (a) %s: ours minus ReAct and minus the LongDA-style baseline' % GL[g], '',
          '| Metric | Ours | ReAct | Ours minus ReAct | LongDA-style | Ours minus LongDA-style |', '|---|---|---|---|---|---|']
    for lab, key in METRICS:
        o = vals(g, 'Ours-cards2', key); cells = [f1(mean(o))]
        for arm, _ in BASES:
            b = vals(g, arm, key)
            cells += [f1(mean(b)) if b else 'n/a', fm(boot(o, b) if b and o else None, True)]
        L.append('| %s | %s |' % (lab, ' | '.join(cells)))
    L.append('')

# (b) oracle analysis
L += ['## (b) Oracle analysis (answer correctness; each cell minus both found)', '',
      '| Group | Method given | Data given | Both given | Data given minus method given |', '|---|---|---|---|---|']
for g in ('hard', 'easier'):
    base = vals(g, 'Ours-cards2', 'answer')
    mg = vals(g, 'Ours-oracle', 'answer')
    dg = vals(g + '_datagiven', 'Ours-cards2', 'answer')
    bg = vals(g + '_datagiven', 'Ours-oracle', 'answer')
    L.append('| %s (means %s, %s, %s, %s) | %s | %s | %s | %s |' % (GL[g], f1(mean(base)), f1(mean(mg)), f1(mean(dg)), f1(mean(bg)),
             fm(boot(mg, base)), fm(boot(dg, base)), fm(boot(bg, base)), fm(boot(dg, mg))))
L.append('')


# (c) robustness
def rescore(r, k):
    """Answer correctness with the numeric bands multiplied by k, from the stored claim scores."""
    cs = r.get('claims_v2')
    if not cs:
        return mm.score_of(r)
    it = items[r['item']]; parts = {}
    for kind in W:
        ps = []
        for c in it['claims'].get(kind, []):
            x = cs.get(c['id'])
            if not x or x.get('s') is None:
                continue
            s = x['s']
            if 'target' in x:
                v, t, (f, p) = x.get('reported'), x['target'], x['band']
                if v is None:
                    s = 0.0
                else:
                    d = abs(v - t)
                    s = 1.0 if d <= f * k + 1e-9 else (0.5 if d <= p * k + 1e-9 and (t == 0 or v * t > 0) else 0.0)
            ps.append(s)
        if ps:
            parts[kind] = sum(ps) / len(ps)
    tw = sum(W[q] for q in parts)
    return round(100 * sum(W[q] * v for q, v in parts.items()) / tw, 1) if tw else 0.0


for g in ('hard', 'easier'):
    ids = IDS[g]
    T = {a: {i: mm.score_of(ROWS[g][a][i]) for i in ids if i in ROWS[g][a]} for a in ('Ours-cards2', 'ReAct-v2', 'Ours-text2')}
    L += ['## (c) %s: robustness of the gain in answer correctness' % GL[g], '',
          '| Subset | Questions | Ours minus ReAct | Ours minus LongDA-style |', '|---|---|---|---|']
    subsets = [('All', None),
               ('Reference answer matches a published value', {i for i in ids if items[i].get('validation_tier') == 'published-validated'}),
               ('Named economy and year', {i for i in ids if items[i].get('style') == 'named'}),
               ('Economy described by conditions', {i for i in ids if items[i].get('style') == 'hidden'}),
               ('Claim to check', {i for i in ids if items[i].get('style') in ('claim', 'claim_check')})]
    for nm, ks in subsets:
        if ks is not None and not ks:
            continue
        cells = [fm(boot(T['Ours-cards2'], T[a], ks)) for a in ('ReAct-v2', 'Ours-text2')]
        L.append('| %s | %d | %s | %s |' % (nm, len(ids) if ks is None else len(ks), cells[0], cells[1]))
    meths = sorted({items[i]['method'] for i in ids})
    lo = {}
    for a in ('ReAct-v2', 'Ours-text2'):
        ds = [boot(T['Ours-cards2'], T[a], {i for i in ids if items[i]['method'] != m})[0] for m in meths]
        lo[a] = '%+.1f to %+.1f' % (min(ds), max(ds))
    L.append('| Leave one method out (range over %d runs) | %d less one method | %s | %s |' % (len(meths), len(ids), lo['ReAct-v2'], lo['Ours-text2']))
    chk = sum(abs(rescore(r, 1.0) - mm.score_of(r)) > 0.05 for r in ROWS[g]['Ours-cards2'].values())
    for k, lab in ((0.5, 'halved'), (2.0, 'doubled')):
        R = {a: {i: rescore(ROWS[g][a][i], k) for i in ids if i in ROWS[g][a]} for a in ('Ours-cards2', 'ReAct-v2', 'Ours-text2')}
        L.append('| Numeric tolerances %s | %d | %s | %s |' % (lab, len(ids), fm(boot(R['Ours-cards2'], R['ReAct-v2'])), fm(boot(R['Ours-cards2'], R['Ours-text2']))))
    L += ['', 'Rescoring at tolerance x1 differs from the stored score in %d of the %d rows of ours (should be 0).' % (chk, len(ROWS[g]['Ours-cards2'])), '']
    for a, lab in (('ReAct-v2', 'ReAct'), ('Ours-text2', 'LongDA-style')):
        o, pos, n, p = signflip(by_method(T['Ours-cards2'], T[a]))
        L.append('Ours minus %s: positive for %d of %d methods; exact sign-flip test over methods (all 2^%d patterns, two-sided) p = %.4f.' % (lab, pos, n, n, p))
    L.append('')

# (d) all 28 methods
T = {}
for g in ('hard', 'easier'):
    for a in ('Ours-cards2', 'ReAct-v2', 'CoT0'):
        T.setdefault(a, {}).update({i: mm.score_of(ROWS[g][a][i]) for i in IDS[g] if i in ROWS[g][a]})
gain, mem, cnt = {}, {}, {}
for i in T['Ours-cards2']:
    m = items[i]['method']
    gain.setdefault(m, []).append(T['Ours-cards2'][i] - T['ReAct-v2'][i]); mem.setdefault(m, []).append(T['CoT0'][i])
meths = sorted(gain)
G = [sum(gain[m]) / len(gain[m]) for m in meths]; M = [sum(mem[m]) / len(mem[m]) for m in meths]


def ranks(x):
    o = sorted(range(len(x)), key=lambda i: x[i]); r = [0.0] * len(x); i = 0
    while i < len(o):
        j = i
        while j + 1 < len(o) and x[o[j + 1]] == x[o[i]]:
            j += 1
        for k in range(i, j + 1):
            r[o[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def pearson(x, y):
    mx, my = sum(x) / len(x), sum(y) / len(y)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    return sxy / (sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y)) ** 0.5
rho = pearson(ranks(M), ranks(G))
rnd = random.Random(1); N = 200000; rk = ranks(M); rg = ranks(G); c = 0
for _ in range(N):
    p = rg[:]; rnd.shuffle(p); c += abs(pearson(rk, p)) >= abs(rho) - 1e-12
allq = [x for m in meths for x in gain[m]]; obs = sum(allq) / len(allq); sums = [sum(gain[m]) for m in meths]


def exact_signflip(sums, total):
    """Exact two-sided sign-flip over all 2^k sign patterns of the method sums (meet in the middle); returns (count, patterns)."""
    import bisect
    h = len(sums) // 2

    def allsums(xs):
        out = [0.0]
        for x in xs:
            out = [o + s * x for o in out for s in (1, -1)]
        return sorted(out)
    A, Bs = allsums(sums[:h]), allsums(sums[h:])
    thr = abs(sum(sums)) - 1e-9; c = 0
    for a in A:
        c += len(Bs) - bisect.bisect_left(Bs, thr - a)       # a + b >= thr
        c += bisect.bisect_right(Bs, -thr - a)                # a + b <= -thr
    return c, len(A) * len(Bs)
c2, tot2 = exact_signflip(sums, len(allq))
L += ['## (d) Gain of ours over ReAct against the memory-only score, all %d methods' % len(meths), '',
      'Spearman rank correlation between the memory-only answer correctness of a method (CoT0) and the gain of ours over ReAct: rho = %+.2f (permutation test, %d permutations, two-sided): p = %.4f (%d of %d permutations at least as extreme).' % (rho, N, c / N, c, N),
      'Pooled over all %d questions: ours minus ReAct = %+.1f; methods with a positive gain: %d of %d; exact sign-flip test over the methods (all 2^%d sign patterns, two-sided): p = %.4f (%d of %d).' % (len(allq), obs, sum(1 for x in G if x > 0), len(meths), len(meths), c2 / tot2, c2, tot2), '',
      '| Method | Memory only | Ours minus ReAct | Questions |', '|---|---|---|---|']
L += ['| %s | %.1f | %+.1f | %d |' % (m, mm_, g_, len(gain[m])) for m, mm_, g_ in sorted(zip(meths, M, G), key=lambda t: t[1])]
L.append('')
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, 'w').write('\n'.join(L) + '\n')
print('\n'.join(L))
