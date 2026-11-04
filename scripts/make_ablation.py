"""Ablation tables (no model calls, no key, standard library only). Run from the repository root:

    python3 scripts/make_ablation.py            # prints the tables and writes work/ablation_results.md

Compare with eval/expected_ablation.md (the same text). Reads experiments/main_run/results_final_hard.jsonl.gz and
results_ablation_{fixed,astext,control}.jsonl.gz, the judge files metrics/ragas_{judge_results,fp_results}.jsonl.gz and
metrics/ragas_ablation_{pieces,fp}.jsonl.gz, dataset/items and experiments/splits/hard.json.
Metric definitions: answer correctness = score_v2 (failed or missing = 0); method explained / data / computation = parts_v2 text / data /
computation (items without that claim kind left out; failed = 0); fully correct = vital_all_v2; RAGAS-style metrics from the judge rows
(failed = 0, precision leaves out None); differences by a paired cluster bootstrap over the 13 methods, 4,000 resamples, 95% percentile
interval, seed 1."""
import json, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_metrics as mm

ROOT = mm.ROOT + "/"
MAIN = mm.MAIN + "/"

B = 4000
OUT = ROOT + 'work/ablation_results.md'
items = mm.load_items()
NEW = {'Cards-fixed': ('ablation_fixed', MAIN + 'results_ablation_fixed.jsonl.gz'),
       'Cards-as-text': ('ablation_astext', MAIN + 'results_ablation_astext.jsonl.gz'),
       'Ours-cards2 (control run)': ('ablation_control', MAIN + 'results_ablation_control.jsonl.gz')}
IDS = json.load(open(ROOT + 'experiments/splits/hard.json'))['hard']
main = mm.read_jsonl(MAIN + 'results_final_hard.jsonl.gz')
SETS = {}   # label -> (group name in ragas files, arm name in rows, rows by item)
for lab, (g, p) in NEW.items():
    rs = mm.read_jsonl(p) if os.path.exists(p) else []
    last = {}
    for r in rs:
        if not r.get('harness_error'):
            last[r['item']] = r
    SETS[lab] = (g, {'Cards-fixed': 'Cards-fixed', 'Cards-as-text': 'Cards-as-text'}.get(lab, 'Ours-cards2'), last)
for a, lab in (('Ours-text2', 'Ours-text2 (main run)'), ('Ours-cards2', 'Ours-cards2 (main run)')):
    SETS[lab] = ('hard', a, {r['item']: r for r in main if r['arm'] == a})


def ragas(path, key):
    return mm.read_jsonl(path) if os.path.exists(path) else []
RJ = ragas(MAIN + 'metrics/ragas_judge_results.jsonl.gz', 0) + ragas(MAIN + 'metrics/ragas_ablation_pieces.jsonl.gz', 0)
RF = ragas(MAIN + 'metrics/ragas_fp_results.jsonl.gz', 0) + ragas(MAIN + 'metrics/ragas_ablation_fp.jsonl.gz', 0)


def last_rows(rows):
    d = {}
    for x in rows:
        d[(x['group'], x['item'], x['arm'], x['metric'])] = x
    return d
RJL, RFL = last_rows(RJ), last_rows(RF)

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
            d = x.get('detail') if isinstance(x.get('detail'), dict) else {}
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
    return est, ds[int(0.025 * B)], ds[int(0.975 * B) - 1], n, len(cl)


def fm(t):
    return 'n/a' if t is None else '%+.1f [%+.1f, %+.1f] (n=%d, methods=%d)' % t


def mean(d):
    return sum(d.values()) / len(d) if d else None


def f1(x):
    return 'n/a' if x is None else '%.1f' % x


L = ['# Ablation results: institutional procedures (hard, 231 questions)', '',
     'Rows: one run per question and arm. Model, prompt steps, data tool, Python sandbox, turn limit and judge as Ours-cards2. Failed or unfinished answers count as 0. Metric definitions as in scripts/make_ablation.py.', '']
V = {lab: {k: values(lab, k) for _, k in METRICS} for lab in SETS}
hdr = '| Arm | answers | failed (=0) | ' + ' | '.join(m for m, _ in METRICS) + ' | mean agent cost / question (USD) | mean judge cost / question (USD) |'
L += [hdr, '|' + '---|' * (len(METRICS) + 5)]
for lab, (g, arm, rows) in SETS.items():
    rs = [rows[i] for i in IDS if i in rows]
    failed = sum(1 for i in IDS if i not in rows or rows[i].get('score_v2') is None or not (rows[i].get('answer') or '').strip())
    cells = [f1(mean(V[lab][k])) + ('' if k in ('score', 'full') or V[lab][k] and len(V[lab][k]) >= 0 and False else '') + ('' if len(V[lab][k]) == len(IDS) or k in ('score', 'full') else ' (n=%d)' % len(V[lab][k])) for _, k in METRICS]
    ac = sum(r.get('cost') or 0 for r in rs) / max(1, len(rs)); jc = sum(r.get('judge2_cost') or 0 for r in rs) / max(1, len(rs))
    L.append('| %s | %d | %d | %s | %.4f | %.4f |' % (lab, len(rs), failed, ' | '.join(cells), ac, jc))
L += ['', 'Cost: result-row `cost` (agent calls, including the first attempt when a run was repeated) and `judge2_cost`; the RAGAS-style judge cost is in the `cost` field of the stored judge rows.', '']
CTRL = 'Ours-cards2 (control run)'
for other in ('Cards-fixed', 'Cards-as-text', 'Ours-text2 (main run)', 'Ours-cards2 (main run)'):
    L += ['## Control minus %s (paired cluster bootstrap over methods)' % other, '']
    for m, k in METRICS:
        L.append('- %s: control %s, %s %s; difference %s' % (m, f1(mean(V[CTRL][k])), other, f1(mean(V[other][k])), fm(boot(V[CTRL][k], V[other][k]))))
    L.append('')
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, 'w').write('\n'.join(L) + '\n')
print('\n'.join(L))
