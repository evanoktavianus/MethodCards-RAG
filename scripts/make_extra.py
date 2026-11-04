"""Extra analyses (no model calls, no key, standard library only). Run from the repository root:

    python3 scripts/make_extra.py               # prints the tables and writes work/extra_analyses.md

Compare with eval/expected_extra_analyses.md (the same text).
(13) answers of ours by whether the cited card's source sentence was verified in the document (tools/bank/card_index.jsonl, field
source_unverified); (14) method found per 1,000 tokens of retrieved method context (ctx_chars of the stored judge rows); (15) per-method
gains of ours over ReAct and over the text-search baseline, with exact sign-flip tests over methods and over questions;
(16) the card named in our answers: from a document of the question's method, and the method's own card in the method tree; (17) the method source named
in each answer on the composite-indicator questions.
Reads experiments/main_run/results_final_{hard,easier}.jsonl.gz and metrics/ragas_judge_results.jsonl.gz."""
import json, itertools, os, random, sys, statistics as st, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_metrics as MM
H = MM.ROOT + '/'; M = MM.MAIN + '/'
cards = MM.load_cards()
ITEMS = MM.load_items()
R = {}
for g in ('hard', 'easier'):
    for r in MM.read_jsonl(M + f'results_final_{g}.jsonl.gz'):
        R[(g, r['item'], r['arm'])] = r
J = {(x['group'], x['item'], x['arm']): x for x in MM.read_jsonl(M + 'metrics/ragas_judge_results.jsonl.gz') if x.get('metric') == 'pieces'}
out=['# Extra analyses','']
# 13
out+=['## 13. Our answers by the cited card: verified source sentence or not','','| Group | Cited card | Answers | Answer correctness | Method explained | Method correctness (judge) |','|---|---|---|---|---|---|']
for g in ('hard','easier'):
    rows=[r for (gg,i,a),r in R.items() if gg==g and a=='Ours-cards2' and r.get('cited_card_id') in cards]
    for lab,sel in (('verified',lambda c: not c.get('source_unverified')),('unverified',lambda c: bool(c.get('source_unverified')))):
        s=[r for r in rows if sel(cards[r['cited_card_id']])]
        if not s: continue
        ac=st.mean(r.get('score_v2') or 0 for r in s); me=st.mean(100*((r.get('parts_v2') or {}).get('text') or 0) for r in s)
        mc=[J[(g,r['item'],'Ours-cards2')]['detail'].get('method_correctness') for r in s if (g,r['item'],'Ours-cards2') in J and J[(g,r['item'],'Ours-cards2')].get('detail')]
        mc=[x for x in mc if x is not None]
        out.append(f'| {g} | {lab} | {len(s)} | {ac:.1f} | {me:.1f} | {100*st.mean(mc):.1f} |' if mc else f'| {g} | {lab} | {len(s)} | {ac:.1f} | {me:.1f} | n/a |')
    # same split, by method: are unverified citations concentrated in some methods?
out+=['','Note: answers are not randomly assigned to verified or unverified cards; the split is descriptive (methods differ in how their cards were built).','']
# 14
out+=['## 14. Method found per 1,000 tokens of retrieved method context','','Per answer: context recall (method, judge, 0-1) divided by the retrieved method context in thousands of tokens (characters / 4, as sent to the judge, capped at 48,000 characters). Higher = more of the method per amount read.','','| Group | Arm | Answers | Mean context (k tokens) | Share capped | Context recall | Recall per 1k tokens (median) | Recall per 1k tokens (mean) |','|---|---|---|---|---|---|---|---|']
for g in ('hard','easier'):
    for a in ('Ours-text2','Ours-cards2'):
        xs=[x for (gg,i,aa),x in J.items() if gg==g and aa==a and x.get('ok') and x.get('ctx_chars')]
        k=[x['ctx_chars']/4000 for x in xs]; rc=[(x['detail'].get('context_recall') if x.get('detail') and x['detail'].get('context_recall') is not None else x.get('score') or 0) for x in xs]
        eff=[r/kk for r,kk in zip(rc,k) if kk>0]
        cap=sum(bool(x.get('ctx_trunc')) for x in xs)/len(xs)
        lab={'Ours-text2':'LongDA-style','Ours-cards2':'Ours'}[a]
        out.append(f'| {g} | {lab} | {len(xs)} | {st.mean(k):.1f} | {100*cap:.0f}% | {100*st.mean(rc):.1f} | {100*st.median(eff):.2f} | {100*st.mean(eff):.2f} |')
out+=['']
# 15
def meth(g):
    return {i: ITEMS[i]['method'] for (gg, i, a) in R if gg == g}
for g,base_list in (('hard',('ReAct-v2','Ours-text2')),('easier',('ReAct-v2','Ours-text2'))):
    mm=meth(g)
    for base in base_list:
        d=collections.defaultdict(list)
        for (gg,i,a),r in R.items():
            if gg==g and a=='Ours-cards2':
                b=R.get((g,i,base))
                if b: d[mm[i]].append((r.get('score_v2') or 0)-(b.get('score_v2') or 0))
        meths=sorted(d); per=[(m,len(d[m]),st.mean(d[m])) for m in meths]
        allq=[x for m in meths for x in d[m]]; obs=st.mean(allq)
        # exact cluster sign-flip over methods (question-weighted mean)
        cnt=0; tot=0
        for signs in itertools.product((1,-1),repeat=len(meths)):
            v=sum(s*sum(d[m]) for s,m in zip(signs,meths))/len(allq); tot+=1; cnt+= abs(v)>=abs(obs)-1e-12
        p_cl=cnt/tot
        # question-level sign flip, 20000 draws
        random.seed(1); c2=0; N=20000
        for _ in range(N):
            v=sum(x if random.random()<.5 else -x for x in allq)/len(allq); c2+= abs(v)>=abs(obs)-1e-12
        lab={'ReAct-v2':'ReAct','Ours-text2':'LongDA-style'}[base]
        out+=[f'## 15. {g}: ours minus {lab}, per method','',f'Mean difference {obs:+.1f} over {len(allq)} questions and {len(meths)} methods; methods with a positive mean gain: {sum(x[2]>0 for x in per)} of {len(per)}.',
              f'Exact sign-flip test over methods (all {tot} sign patterns, two-sided): p = {p_cl:.4f}. Sign-flip test over questions (20,000 draws, two-sided): p = {c2/N:.4f}.','','| Method | Questions | Mean difference |','|---|---|---|']
        out+=[f'| {m} | {n} | {x:+.1f} |' for m,n,x in sorted(per,key=lambda t:-t[2])]+['']
# 16. the card our agent named: from a document of the question's method, and the method's own card (method tree)
import re as _re
TREE = MM.load_tree(); NMAP = MM.load_node_map()
DOCT = {}
for c in cards.values():
    if c.get('doc_id'): DOCT.setdefault(c['doc_id'], c.get('doc_title') or '')
def _cid(ans):
    m = _re.search(r'Method card:\s*([0-9a-z]{8,12}-\d+)', ans or ''); return m.group(1) if m else None
out += ['## 16. The card named in our answers', '', '| Group | Answers naming a known card | From a document of the question\'s method | The method\'s own card (method tree) |', '|---|---|---|---|']
for g in ('hard', 'easier'):
    n = doc = own = 0
    for (gg, i, a), r in R.items():
        if gg != g or a != 'Ours-cards2': continue
        cid = _cid(r.get('answer'))
        if cid not in cards: continue
        it = ITEMS.get(i) or {}; md = set(it.get('method_doc_ids') or []); c = cards[cid]
        n += 1
        doc += bool(({s['doc_id'] for s in (c.get('sources') or []) if s.get('doc_id')} | {c.get('doc_id')}) & md)
        own += cid in (MM.node_card_ids(TREE, NMAP, it.get('method')) or set())
    out.append(f'| {g} | {n} | {doc} ({100*doc/n:.1f}%) | {own} ({100*own/n:.1f}%) |' if n else f'| {g} | 0 | - | - |')
out += ['']
# 17. composite indicator of debt-carrying capacity: the method source each answer named
out += ['## 17. Composite indicator of debt-carrying capacity: the method source named in each answer (institutional procedures)', '']
ci = [(i, r) for (gg, i, a), r in R.items() if gg == 'hard' and a == 'Ours-text2' and (ITEMS.get(i) or {}).get('method') == 'lic_dsf_composite_indicator']
cnt = collections.Counter()
for i, r in ci:
    md = set((ITEMS.get(i) or {}).get('method_doc_ids') or [])
    m = _re.search(r'Method document:\s*([^\n]*)', r.get('answer') or '')
    s = (m.group(1).strip() if m else '')
    d = _re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', s)
    if not m or not d or s.lower().startswith('none'): cnt['no method document named'] += 1
    elif d.group(0) in md: cnt['a document that states the method'] += 1
    else: cnt['other document: ' + (DOCT.get(d.group(0)) or _re.sub(r'^[0-9a-f-]{36}\s*', '', s)[:80])] += 1
out += [f'LongDA-style baseline, {len(ci)} answers:', ''] + [f'- {k}: {v}' for k, v in cnt.most_common()]
oc = [(i, r) for (gg, i, a), r in R.items() if gg == 'hard' and a == 'Ours-cards2' and (ITEMS.get(i) or {}).get('method') == 'lic_dsf_composite_indicator']
named = collections.Counter((cards.get(_cid(r.get('answer'))) or {}).get('name', 'none') for i, r in oc)
out += ['', f'Ours, {len(oc)} answers, card named:', ''] + [f'- {k}: {v}' for k, v in named.most_common()] + ['']
os.makedirs(H + 'work', exist_ok=True)
open(H + 'work/extra_analyses.md', 'w').write('\n'.join(out)); print('\n'.join(out))
