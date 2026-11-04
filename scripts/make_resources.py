"""Resources per question (no model calls, no key, standard library only). Run from the repository root:

    python3 scripts/make_resources.py           # prints the tables and writes work/resources.md

Compare with eval/expected_resources.md (the same text). Mean model turns (`turns`), tool calls (`tool_actions`) and agent cost
(`cost`, USD, model calls of the answering agent without the judge) per question and row, by group of questions; the number of failed or
unfinished answers per row (an error, an empty answer or no score; all count 0); and the mean cost of the other two agent models.
`turns` and `tool_actions` are counts stored in each row of the agent arms (the traces they were counted from are not distributed)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_metrics as mm

ROOT = mm.ROOT + '/'
OUT = ROOT + 'work/resources.md'
R = mm.load_results()
LAB = {'CoT0': '1. Memory only (CoT)', 'CoT1': '2. Data in prompt', 'PoT': '3. PoT', 'ReAct-v2': '4. ReAct', 'Ours-text2': '5. LongDA-style',
       'Ours-cards2': '6. Ours', 'Ours-oracle': 'Ours, method given (oracle)'}
NOLOOP = {'CoT0': ('1 call', '0'), 'CoT1': ('1 call', '0'), 'PoT': ('2 calls', '1 program')}


def failed(r):
    return bool(r.get('harness_error') or r.get('error') or not (r.get('answer') or '').strip() or r.get('score_v2') is None)


def counts(r):
    """(turns, tool actions) of a row: the stored fields; rows that still carry the full trace are counted from it."""
    if 'turns' in r:
        return r['turns'], r['tool_actions']
    tr = r.get('trace') or []
    return sum(1 for t in tr if t[0] == 'model'), len(mm.events(tr))


def mean(x):
    return sum(x) / len(x)
L = ['# Resources per question', '', 'Agent model glm-5.3-flash. Cost in USD per question (agent calls only). Failed or unfinished answers count 0 in every metric.', '',
     '| Row | Institutional procedures: turns | Tool calls | Cost (USD) | Standard formulas: turns | Tool calls | Cost (USD) |', '|---|---|---|---|---|---|---|']
fail = {}
for a, lab in LAB.items():
    cells = []
    for g in ('hard', 'easier'):
        x = [r for r in R[g] if r['arm'] == a]
        fail[a] = fail.get(a, 0) + sum(failed(r) for r in x)
        t, c = NOLOOP[a] if a in NOLOOP else ('%.1f' % mean([counts(r)[0] for r in x]), '%.1f' % mean([counts(r)[1] for r in x]))
        cells += [t, c, '%.4f' % mean([r.get('cost') or 0 for r in x])]
    L.append('| %s | %s |' % (lab, ' | '.join(cells)))
L += ['', 'Failed or unfinished answers per row, both groups together (440 answers per row): ' + '; '.join('%s %d' % (LAB[a], n) for a, n in fail.items()) + '.', '']
L += ['## Other agent models (institutional procedures, 231 questions)', '', '| Model and setting | Mean cost (USD) | Mean turns | Mean tool calls | Failed |', '|---|---|---|---|---|']
for m, name in (('haiku', 'Claude Haiku 5.5'), ('qwen', 'Qwen 3.5 397B')):
    for k, lab in (('react', 'ReAct'), ('cards', 'Ours'), ('oracle', 'Ours, method given')):
        x = mm.read_jsonl(mm.MAIN + '/results_%s_%s.jsonl.gz' % (m, k))
        L.append('| %s, %s | %.4f | %.1f | %.1f | %d |' % (name, lab, mean([r.get('cost') or 0 for r in x]), mean([counts(r)[0] for r in x]), mean([counts(r)[1] for r in x]), sum(failed(r) for r in x)))
L.append('')
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, 'w').write('\n'.join(L) + '\n')
print('\n'.join(L))
