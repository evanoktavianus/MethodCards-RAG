"""Control runs: tables (no model calls, no key, standard library only). Run from the repository root:

    python3 scripts/make_controls.py            # prints the tables and writes work/controls_results.md

Compare with eval/expected_controls.md (the same text). Two control runs of glm-5.3-flash on the 231 institutional procedures:
ReAct-steps (ReAct-v2 with the prompt steps of Ours-cards2 that need no method tool) and Text-410 (Ours-text2 with the text search
restricted to the 410 card documents listed in experiments/main_run/CTL_text410_docs.txt). Reads experiments/main_run/results_final_hard.jsonl.gz,
results_control_{reactsteps,text410}.jsonl.gz, metrics/ragas_{judge_results,fp_results}.jsonl.gz and metrics/ragas_control_{pieces,fp}.jsonl.gz.
Metric definitions and the bootstrap as in scripts/make_ablation.py (paired cluster bootstrap over the 13 methods, 4,000 resamples, 95% percentile
interval, seed 1); p = exact two-sided sign-flip test over the 13 methods (all 2^13 patterns, statistic = question-weighted mean difference)."""
import json, os, random, sys, itertools
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_metrics as mm

ROOT = mm.ROOT + "/"
MAIN = mm.MAIN + "/"
B = 4000
OUT = ROOT + 'work/controls_results.md'
items = mm.load_items()
IDS = json.load(open(ROOT + 'experiments/splits/hard.json'))['hard']
MET = MAIN + 'metrics/'
rd = lambda p: mm.read_jsonl(p) if os.path.exists(p) else []
main = rd(MAIN + 'results_final_hard.jsonl.gz')
NEW = {'ReAct-steps': ('control_steps', MAIN + 'results_control_reactsteps.jsonl.gz'), 'Text-410': ('control_text', MAIN + 'results_control_text410.jsonl.gz')}
SETS = {}   # label -> (judge group, arm name in rows and judge files, rows by item)
for a, (g, p) in NEW.items():
    SETS[a] = (g, a, {r['item']: r for r in rd(p)})
for a in ('ReAct-v2', 'Ours-text2', 'Ours-cards2'):
    SETS[a] = ('hard', a, {r['item']: r for r in main if r['arm'] == a})
ORDER = ['ReAct-v2', 'ReAct-steps', 'Ours-text2', 'Text-410', 'Ours-cards2']


def last_rows(rows):
    d = {}
    for x in rows:
        d[(x['group'], x['item'], x['arm'], x['metric'])] = x
    return d
RJL = last_rows(rd(MET + 'ragas_judge_results.jsonl.gz') + rd(MET + 'ragas_control_pieces.jsonl.gz'))
RFL = last_rows(rd(MET + 'ragas_fp_results.jsonl.gz') + rd(MET + 'ragas_control_fp.jsonl.gz'))
METRICS = [('Answer correctness', 'score'), ('Method explained', 'text'), ('Data correctness', 'data'), ('Computation correctness', 'computation'),
           ('Fully correct answers', 'full'), ('Context recall (method)', 'context_recall'), ('Context precision', 'precision'),
           ('Faithfulness', 'faithfulness'), ('Method correctness', 'method_correctness')]


def values(label, key):
    g, arm, rows = SETS[label]; out = {}
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
            if not x.get('ok') and not x.get('skipped'):
                continue
            d = x.get('detail') if isinstance(x.get('detail'), dict) else {}
            if key == 'context_recall' and arm in ('ReAct-v2', 'ReAct-steps'):
                continue   # no method tool, no context
            out[i] = 100 * (d.get(key) or 0.0)
        elif key == 'faithfulness':
            x = RFL.get((g, i, arm, 'faithfulness'))
            if x is None:
                continue
            out[i] = 100 * (x.get('score') or 0.0)
        elif key == 'precision':
            x = RFL.get((g, i, arm, 'precision'))
            if x is None or x.get('score') is None:
                continue
            out[i] = 100 * x['score']
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
    sums = [sum(c) for c in cl]; cnt = tot = 0
    for sg in itertools.product((1, -1), repeat=len(cl)):
        v = sum(s * x for s, x in zip(sg, sums)) / n; tot += 1; cnt += abs(v) >= abs(est) - 1e-12
    return est, ds[int(0.025 * B)], ds[int(0.975 * B) - 1], n, len(cl), cnt / tot


def fm(t):
    return 'n/a' if t is None else '%+.1f [%+.1f, %+.1f] (n=%d, methods=%d); sign-flip p = %.4f' % t


def mean(d):
    return sum(d.values()) / len(d) if d else None


def f1(x):
    return 'n/a' if x is None else '%.1f' % x

L = ['# Control results: institutional procedures (231 questions)', '',
     'Arms: ReAct-steps (ReAct-v2 with the Ours-cards2 prompt steps that need no method tool) and Text-410 (Ours-text2 with the text search restricted to the 410 card documents). '
     'One run per question and arm; main-run arms from results_final_hard.jsonl.gz. Failed or unfinished answers count as 0. Metric definitions as in scripts/make_ablation.py; '
     'context recall, precision and faithfulness exist only for arms with a method tool (n/a otherwise).', '']
V = {lab: {k: values(lab, k) for _, k in METRICS} for lab in ORDER}
L += ['| Arm | answers | failed (=0) | ' + ' | '.join(m for m, _ in METRICS) + ' | mean agent cost / question (USD) | mean judge cost / question (USD) |', '|' + '---|' * (len(METRICS) + 5)]
for lab in ORDER:
    g, arm, rows = SETS[lab]
    rs = [rows[i] for i in IDS if i in rows]
    failed = sum(1 for i in IDS if i not in rows or rows[i].get('score_v2') is None or not (rows[i].get('answer') or '').strip())
    cells = [f1(mean(V[lab][k])) + ('' if len(V[lab][k]) in (len(IDS), 0) or k in ('score', 'full') else ' (n=%d)' % len(V[lab][k])) for _, k in METRICS]
    ac = sum(r.get('cost') or 0 for r in rs) / max(1, len(rs)); jc = sum(r.get('judge2_cost') or 0 for r in rs) / max(1, len(rs))
    L.append('| %s | %d | %d | %s | %.4f | %.4f |' % (lab, len(rs), failed, ' | '.join(cells), ac, jc))
L += ['', 'Cost: result-row `cost` (agent calls) and `judge2_cost`.', '']
for a, b in (('Ours-cards2', 'ReAct-steps'), ('ReAct-steps', 'ReAct-v2'), ('Ours-cards2', 'Text-410'), ('Text-410', 'Ours-text2')):
    L += ['## %s minus %s (paired cluster bootstrap over methods; exact sign-flip test over the 13 methods)' % (a, b), '']
    for m, k in METRICS:
        L.append('- %s: %s %s, %s %s; difference %s' % (m, a, f1(mean(V[a][k])), b, f1(mean(V[b][k])), fm(boot(V[a][k], V[b][k]))))
    L.append('')
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, 'w').write('\n'.join(L) + '\n')
print('\n'.join(L))
