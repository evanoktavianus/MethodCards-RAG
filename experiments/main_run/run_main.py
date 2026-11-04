"""Runs the arms on the questions, high concurrency, resumable (results.jsonl, one line per (item,arm), judged).
usage: python3 -I run_main.py --dry | --go [--arms=A,B] [--items=ID,ID | --limit=N] [--workers=48]"""
import json,sys,os,threading,time,concurrent.futures as cf,traceback
H=(__import__('os').environ.get('MC_ROOT') or __import__('os').path.abspath(__import__('os').path.join(__import__('os').path.dirname(__file__),'..','..')))+'/experiments/'
sys.path[:0]=[H+'data_blocks',H+'agent',H+'baselines',H+'prompts',H+'prompts_data',H+'../tools/retrieval']
import data_blocks as db
import prompt_build as pr
pr.build=db.build            # every module reaches the builder through pr.build / pr.prompts
import run_baselines as rb
import run_agent as ra
import agent_cards as ac
import embed_queries as eq
rp=rb.rp
OUT=H+'main_run/'
def arg0(k,d=None):
    v=[a.split('=',1)[1] for a in sys.argv if a.startswith('--'+k+'=')];return v[0] if v else d
RES=OUT+arg0('out','results.jsonl')
ARMS={'CoT0':rb.ARMS['CoT0'],'CoT1':rb.ARMS['CoT1'],'PoT':rb.ARMS['PoT'],'ReAct-v2':rb.ARMS['ReAct-v2'],'Ours-cards2':lambda i:ac.agent_cards(i,'cards2'),'Cards-fixed':lambda i:ac.agent_cards(i,'fixed'),'Cards-as-text':lambda i:ac.agent_cards(i,'astext'),'Ours-oracle':lambda i:ac.agent_cards(i,'oracle'),'Ours-text2':lambda i:ac.agent_cards(i,'text2'),'Text-410':lambda i:ac.agent_cards(i,'text2'),'ReAct-steps':rb.ARMS['ReAct-steps']}
def arg(k,d=None):
    v=[a.split('=',1)[1] for a in sys.argv if a.startswith('--'+k+'=')];return v[0] if v else d
USE=arg('arms','CoT0,CoT1,PoT,ReAct-v2,Ours-text2,Ours-cards2,Ours-oracle').split(',')
if 'Text-410' in USE:   # the text index is restricted to the documents in TEXT_ALLOW_FILE (tools/retrieval/local_docs.py); the filter is process-wide, so Text-410 runs alone
    assert USE==['Text-410'] and os.environ.get('TEXT_ALLOW_FILE'),'Text-410 runs alone with TEXT_ALLOW_FILE=experiments/main_run/CTL_text410_docs.txt'
elif os.environ.get('TEXT_ALLOW_FILE'):raise SystemExit('TEXT_ALLOW_FILE is set but the arm is not Text-410')
ids=json.load(open(H+'splits/hard.json'))['hard']+json.load(open(H+'splits/easier.json'))['easier']
if arg('set'):
    _f,_k=arg('set').split(':');ids=json.load(open(H+'splits/'+_f))[_k]
if arg('items'):ids=[i for i in ids if i in arg('items').split(',')]
if arg('subset'):ids=[i for i in ids if i in json.load(open(OUT+arg('subset')))]
if arg('limit'):ids=ids[:int(arg('limit'))]
done=set()
if os.path.exists(RES):
    for l in open(RES):
        r=json.loads(l)
        if not r.get('harness_error'):done.add((r['item'],r['arm'],r.get('rep',0)))
REPS=int(arg('reps','1'))
jobs=[(i,a,k) for k in range(REPS) for i in ids for a in USE if (i,a,k) not in done]
per={'ReAct-steps':19,'Text-410':19,'CoT0':2,'CoT1':2,'PoT':4,'ReAct-v2':19,'Ours-cards2':19,'Cards-fixed':19,'Cards-as-text':19,'Ours-oracle':19,'Ours-text2':19}
print('items',len(ids),'arms',USE,'jobs to run',len(jobs),'| max chat calls',sum(per[a] for i,a,k in jobs))
_OURS=[a for a in USE if a.startswith('Ours') or a=='Text-410']
_NODOCS=None   # message if the Ours arms need document files that are not there
if _OURS and not(os.environ.get('PAGES_PG')=='1' and os.environ.get('ON_VM')=='1' and set(_OURS)<={'Ours-cards2','Ours-oracle'}):
    try:
        import local_docs as _ld
        if _ld.docs_missing():_NODOCS=_ld.docs_message()
    except ImportError:pass   # numpy missing: the import of the index fails later with its own message
if (_OURS or any(a in('Cards-fixed','Cards-as-text') for a in USE)) and ac.CARDS_MISSING:_NODOCS=(_NODOCS+' ' if _NODOCS else '')+"The method cards are not distributed with this repository (publishers' terms). Build them from your own documents (tools/cards/README.txt) and set CARDS_FILE, or place cards_final.jsonl in tools/bank/."
ORACLE_FILES=('oracle_methods.json','oracle_passages.json','oracle_excerpts.json')   # method passages quoted from the documents; not distributed
if 'Ours-oracle' in USE:
    _miss=[f for f in ORACLE_FILES if not os.path.exists(H+'baselines/'+f)]
    if _miss:_NODOCS=(_NODOCS+' ' if _NODOCS else '')+"The Ours-oracle arm puts the method passage in the first message and needs "+', '.join('experiments/baselines/'+f for f in _miss)+" (the three files oracle_methods.json, oracle_passages.json and oracle_excerpts.json quote the documents and are not distributed; see Documents in the README). Run the other arms without Ours-oracle, or add the files."
if _NODOCS:print(_NODOCS,flush=True)
if '--go' not in sys.argv:sys.exit(0)
if _NODOCS:sys.exit(_NODOCS)
if not rp.key:sys.exit("OPENROUTER_API_KEY is not set: model runs need it. The key-free tier (scripts/make_tables.py, scripts/judge_agreement.py, pytest) does not.")
_T0=time.time();rp.CAP=10**6;eq.CAP=10**5;eq.calls[0]=0
if set(_OURS)<={'Ours-cards2','Ours-oracle'}:os.environ.setdefault('RB_SEARCH','2')   # cards-only: the text servers serve only read_source, 2 are enough
if any(a in USE for a in('Ours-cards2','Ours-oracle','Ours-text2','Text-410')):
    _PS=None
    if os.environ.get('PAGES_PG')=='1' and os.environ.get('ON_VM')=='1' and set(_OURS)<={'Ours-cards2','Ours-oracle'}:
        try:from client import PagesPG;_PS=PagesPG();print('pages from Postgres',_PS.info,flush=True)   # cards2 only needs pages/read; no index build
        except Exception as e:print('pages-from-Postgres unavailable, using the default servers:',e,flush=True)
    ra.VM=_PS or ra.VMSearch()
if any(a in USE for a in('Ours-cards2','Ours-oracle','Cards-fixed','Cards-as-text')):
    ac.BANK=ac.BankPool();print('bank servers',len(ac.BANK.srv),'ready in',ac.BANK.startup_s,'s',ac.BANK.info,flush=True)
print('startup (text servers + card search) total',round(time.time()-_T0,1),'s',flush=True)
lock=threading.Lock();t0=time.time();n=[0]
MAXC=float(arg('max-cost','0') or 0);SPENT=[0.0]   # optional cumulative USD cap (agent + judge) for this launch; 0 = off. Jobs not yet started are skipped once it is reached (resume later with the same --out).
def work(jb):
    i,a,rep=jb
    if MAXC and SPENT[0]>=MAXC:return
    try:
        r=rb.run_arm(ARMS[a],i);r.update(item=i,arm=a,rep=rep,agent_model=rb.AGENT_MODEL)
        try:r=rb.judge_item_v2(r)   # judge (score_v2) right after each answer
        except Exception as e:r.update(score_v2=None,judge2_failed=True,judge2_error=type(e).__name__+' '+str(e)[:150])
        it=pr.item(i);md=set(it['method_doc_ids']);r['method']=it['method'];r['style']=it['style']
        if a in('Ours-cards2','Ours-oracle','Cards-fixed'):r.update(ac.card_diag(r,it))
        if a.startswith('Ours') or a in('Cards-fixed','Cards-as-text','Text-410'):r['method_doc_in_search']=bool(md&set(r.get('seen',[])));r['method_doc_read']=bool(md&set(r.get('read_ids',[])))
    except Exception as e:
        r=dict(item=i,arm=a,rep=rep,harness_error=True,error="ERROR "+type(e).__name__+" "+str(e)[:200]+" | "+" ".join(x.strip() for x in traceback.format_exc().splitlines()[-3:])[:400],answer='',score=None,vital_all=None)
    with lock:
        open(RES,'a').write(json.dumps(r)+'\n');n[0]+=1;SPENT[0]+=(r.get('cost') or 0)+(r.get('judge2_cost') or 0)
        if n[0]%25==0:print(n[0],'/',len(jobs),round(time.time()-t0),'s',flush=True)
ex=cf.ThreadPoolExecutor(int(arg('workers','48')));futs=[ex.submit(work,j) for j in jobs];last=[time.time()];idle_limit=int(arg('idle','420'))
pending=set(futs)
while pending:
    done_,pending=cf.wait(pending,timeout=15,return_when=cf.FIRST_COMPLETED)
    if done_:last[0]=time.time()
    elif time.time()-last[0]>idle_limit:   # no job finished within the idle limit: record the remaining jobs as non-completions (failed answers)
        left=[j for j,f in zip(jobs,futs) if not f.done()]
        with lock:
            for i,a,k in left:open(RES,'a').write(json.dumps(dict(item=i,arm=a,rep=k,harness_error=True,truncated=True,answer='',score=None,vital_all=None,error='no completion within %d s'%idle_limit))+'\n')
        print('timeout: recorded',len(left),'jobs as non-completions',flush=True);break
if any(a in USE for a in('Ours-cards2','Ours-oracle','Cards-fixed','Cards-as-text')):print('card-search embedding calls',ac.BANK.n_emb(),flush=True)
if _OURS:
    try:ra.VM.close()
    except Exception:pass
print('finished',len(jobs),'jobs in',round(time.time()-t0),'s | chat calls',rp.calls[0],'| embedding calls',eq.calls[0],'| 429/5xx retries chat+judge',rp.retries[0],'embed',eq.RETRIES[0],flush=True)
print('agent model',rb.AGENT_MODEL,'| agent tokens prompt/completion/reasoning/calls',rb.TOK,flush=True)
import os;os._exit(0)
