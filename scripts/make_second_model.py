"""Agent-model comparison: robustness tables (no model calls, no key, standard library only). Run from the repository root:

    python3 scripts/make_second_model.py        # prints the tables and writes work/second_model_results.md

Compare with eval/expected_second_model.md (the same text). Three agent models on the 231 institutional procedures in ReAct,
Ours-cards2 and Ours-oracle, with the same prompts, tools and judges: z-ai/glm-5.3-flash (main run), anthropic/claude-haiku-5.5 and
qwen/qwen3.5-397b-a17b. Reads experiments/main_run/results_final_hard.jsonl.gz, results_haiku_{react,cards,oracle}.jsonl.gz,
results_qwen_{react,cards,oracle}.jsonl.gz, metrics/ragas_{judge_results,fp_results}.jsonl.gz, metrics/ragas_haiku_{pieces,fp}.jsonl.gz and
metrics/ragas_qwen_{pieces,fp}.jsonl.gz. Metric definitions and the bootstrap as in scripts/make_ablation.py (paired cluster bootstrap over
methods, 4,000 resamples, 95% percentile interval, seed 1); the sign-flip test is exact over methods (all 2^13 sign patterns)."""
import json, os, random, sys, itertools
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_metrics as mm

ROOT = mm.ROOT + "/"
MAIN = mm.MAIN + "/"
B = 4000
OUT = ROOT + 'work/second_model_results.md'
items = mm.load_items()
IDS = json.load(open(ROOT + 'experiments/splits/hard.json'))['hard']
MET = MAIN + 'metrics/'
rd = lambda p: mm.read_jsonl(p) if os.path.exists(p) else []


def last(path, arm):
    d = {}
    for r in rd(path):
        if r['arm'] == arm:
            d[r['item']] = r
    return d
ARMS = {'react': 'ReAct-v2', 'cards': 'Ours-cards2', 'oracle': 'Ours-oracle'}
SETN = {'react': 'ReAct', 'cards': 'Ours', 'oracle': 'Ours, method given'}
F1 = MAIN + 'results_final_hard.jsonl.gz'
MODELS = [
    ('glm', 'glm-5.3-flash', {k: F1 for k in ARMS}, {k: 'hard' for k in ARMS}),
    ('haiku', 'Claude Haiku 5.5', {k: MAIN + 'results_haiku_%s.jsonl.gz' % k for k in ARMS}, {k: 'haiku_' + k for k in ARMS}),
    ('qwen', 'Qwen 3.5 397B', {k: MAIN + 'results_qwen_%s.jsonl.gz' % k for k in ARMS}, {k: 'qwen_' + k for k in ARMS})]
ROWS = {m: {k: last(f[k], ARMS[k]) for k in ARMS} for m, _, f, _ in MODELS}
GRP = {m: g for m, _, _, g in MODELS}


def last_rows(rows):
    d = {}
    for x in rows:
        d[(x['group'], x['item'], x['arm'], x['metric'])] = x
    return d
RJL = last_rows(rd(MET + 'ragas_judge_results.jsonl.gz') + rd(MET + 'ragas_haiku_pieces.jsonl.gz') + rd(MET + 'ragas_qwen_pieces.jsonl.gz'))
RFL = last_rows(rd(MET + 'ragas_fp_results.jsonl.gz') + rd(MET + 'ragas_haiku_fp.jsonl.gz') + rd(MET + 'ragas_qwen_fp.jsonl.gz'))
METRICS = [('Answer correctness', 'score'), ('Method explained', 'text'), ('Data correctness', 'data'), ('Computation correctness', 'computation'),
           ('Fully correct answers', 'full'), ('Context recall (method)', 'context_recall'), ('Context precision', 'precision'),
           ('Faithfulness', 'faithfulness'), ('Method correctness', 'method_correctness')]


def values(m, k, key):
    rows = ROWS[m][k]; g = GRP[m][k]; arm = ARMS[k]; out = {}
    for i in IDS:
        r = rows.get(i)
        if key == 'score':
            out[i] = mm.score_of(r) if r else 0.0
        elif key == 'full':
            out[i] = 100.0 if (r and r.get('vital_all_v2')) else 0.0
        elif key in ('text', 'data', 'computation'):
            if not (items[i].get('claims') or {}).get(key):
                continue
            v = ((r or {}).get('parts_v2') or {}).get(key)
            out[i] = 100 * (v if v is not None else 0.0) if (r and r.get('parts_v2')) else 0.0
        elif key in ('context_recall', 'method_correctness'):
            x = RJL.get((g, i, arm, 'pieces'))
            if x is None or x.get('skipped') and x.get('score') is None and 'no pieces' in (x.get('skipped') or ''):
                continue
            d = x.get('detail') if isinstance(x.get('detail'), dict) else {}
            if key == 'context_recall' and arm == 'ReAct-v2':
                continue
            out[i] = 100 * (d.get(key) or 0.0)
        elif key in ('faithfulness', 'precision'):
            if arm == 'ReAct-v2':
                continue
            x = RFL.get((g, i, arm, key))
            if x is None or (key == 'precision' and x.get('score') is None):
                continue
            out[i] = 100 * (x.get('score') or 0.0)
    return out


def boot(a, b, seed=1):
    ks = [k for k in a if k in b]
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


def fm(t):
    return 'n/a' if t is None else '%+.1f [%+.1f, %+.1f]' % t[:3]


def mean(d):
    return sum(d.values()) / len(d) if d else None


def f1(x):
    return 'n/a' if x is None else '%.1f' % x
V = {m: {k: {key: values(m, k, key) for _, key in METRICS} for k in ARMS} for m, *_ in MODELS}


def answered(m, k, i):
    r = ROWS[m][k].get(i)
    return bool(r and r.get('score_v2') is not None and (r.get('answer') or '').strip())

L = ['# Agent-model comparison (institutional procedures, 231 questions)', '',
     'Three agent models, same prompts, tools, data tool, sandbox, turn limits and judges (score_v2 and RAGAS-style judge: deepseek/deepseek-v4.1-flash). One run per question and setting. '
     'Failed or missing answers count as 0. Metric definitions as in scripts/make_ablation.py. Differences: paired cluster bootstrap over the 13 methods (4,000 resamples, 95% percentile interval). '
     'ReAct has no method tool, so context recall, precision and faithfulness do not apply. A cell with n shows the number of questions that have the metric. '
     'Agent costs are at each model\'s own prices and are not comparable between models.', '']
L += ['## (a) Side by side, per setting', '']
for k in ARMS:
    L += ['### ' + SETN[k] + ' (' + ARMS[k] + ')', '', '| Metric | ' + ' | '.join(n for _, n, _, _ in MODELS) + ' |', '|---|' + '---|' * len(MODELS)]
    for lab, key in METRICS:
        cells = []
        for m, *_ in MODELS:
            v = V[m][k][key]
            cells.append(f1(mean(v)) + ('' if len(v) in (len(IDS), 0) or key in ('score', 'full') else ' (n=%d)' % len(v)))
        L.append('| %s | %s |' % (lab, ' | '.join(cells)))
    L.append('| Failed answers (counted as 0) | ' + ' | '.join('%d of %d' % (sum(1 for i in IDS if not answered(m, k, i)), len(IDS)) for m, *_ in MODELS) + ' |')
    cells = []
    for m, *_ in MODELS:
        rs = [ROWS[m][k][i] for i in IDS if i in ROWS[m][k]]
        cells.append('%.4f' % (sum(r.get('cost') or 0 for r in rs) / max(1, len(rs))))
    L.append('| Mean agent cost / question (USD) | ' + ' | '.join(cells) + ' |')
    L.append('')

cmp_ = lambda m, a, b, key: boot(V[m][a][key], V[m][b][key])
hdr = '| Comparison / metric | ' + ' | '.join(n for _, n, _, _ in MODELS) + ' |\n|---|' + '---|' * len(MODELS)
L += ['## (b) Differences (percentage points, paired cluster bootstrap, 95% interval)', '', hdr]
for tag, a, b, keys in (('Ours minus ReAct', 'cards', 'react', (('Answer correctness', 'score'), ('Fully correct answers', 'full'), ('Method explained', 'text'), ('Method correctness', 'method_correctness'))),
                        ('Method given minus ReAct', 'oracle', 'react', (('Answer correctness', 'score'), ('Method correctness', 'method_correctness'))),
                        ('Method given minus ours', 'oracle', 'cards', (('Answer correctness', 'score'),))):
    for lab, key in keys:
        L.append('| %s: %s | %s |' % (tag, lab, ' | '.join(fm(cmp_(m, a, b, key)) for m, *_ in MODELS)))
L.append('')


def signflip(m, a, b):
    d = {}
    for i in IDS:
        x, y = ROWS[m][a].get(i), ROWS[m][b].get(i)
        d.setdefault(items[i]['method'], []).append((mm.score_of(x) if x else 0.0) - (mm.score_of(y) if y else 0.0))
    meths = sorted(d); allq = [x for k in meths for x in d[k]]; obs = sum(allq) / len(allq)
    cnt = tot = 0
    for signs in itertools.product((1, -1), repeat=len(meths)):
        v = sum(s * sum(d[k]) for s, k in zip(signs, meths)) / len(allq); tot += 1; cnt += abs(v) >= abs(obs) - 1e-12
    pos = sum(1 for k in meths if sum(d[k]) > 0)
    return obs, len(meths), pos, cnt / tot
L += ['### Per-method positive counts and exact sign-flip test over the 13 methods (answer correctness, two-sided, all 2^13 sign patterns)', '',
      '| Comparison | ' + ' | '.join(n for _, n, _, _ in MODELS) + ' |', '|---|' + '---|' * len(MODELS)]
for tag, a, b in (('Ours minus ReAct', 'cards', 'react'), ('Method given minus ReAct', 'oracle', 'react'), ('Method given minus ours', 'oracle', 'cards')):
    cells = []
    for m, *_ in MODELS:
        o, n, pos, p = signflip(m, a, b)
        cells.append('mean %+.1f; methods with positive mean: %d of %d; p = %.4f' % (o, pos, n, p))
    L.append('| %s | %s |' % (tag, ' | '.join(cells)))
L.append('')
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, 'w').write('\n'.join(L) + '\n')
print('\n'.join(L))
