"""Baselines without method or document search, the code sandbox, the answer-model call and the judge.
  CoT0, CoT1 : one call; CoT0 from memory, CoT1 with the data in the prompt.
  PoT        : data in the prompt, the model writes ONE python program, it is run once, a second call writes the answer.
  ReAct-v2   : data in the prompt, text protocol Thought / Action: run_python / Observation, several actions per turn, up to 16 turns.
All use the same model, data, judge and python tool (numpy, scipy, pandas and statsmodels available).
`--dry` prints a prompt and self-tests the sandbox (no model calls). `--go` runs the arms."""
import json,re,sys,os,subprocess,tempfile,resource,urllib.request,concurrent.futures as cf
sys.path.insert(0,(__import__('os').environ.get('MC_ROOT') or __import__('os').path.abspath(__import__('os').path.join(__import__('os').path.dirname(__file__),'..','..')))+'/experiments/prompts')
import prompt_build as pr
rp=pr.rp
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))+'/../data_blocks');import data_agent as DA   # data tool for the agent arms (env DATA_TOOL=1)
OUT=(__import__('os').environ.get('MC_ROOT') or __import__('os').path.abspath(__import__('os').path.join(__import__('os').path.dirname(__file__),'..','..')))+'/experiments/baselines/'
MAX_TOOL=4          # placeholder sentence in REACT_HEAD, replaced by the turn limit in react_multi
MAXTOK=24000  # identical for every arm; finish reason length is a harness error
rp.CAP=60

GUARD='''import builtins,sys as _s,warnings as _w
with _w.catch_warnings():
    _w.simplefilter("ignore")
    try:
        import numpy,pandas,scipy,scipy.stats,scipy.optimize,statsmodels.api,statsmodels.tsa.filters.hp_filter   # preloaded before the guard
    except Exception as _e: print("library preload failed:",_e)
_r=builtins.__import__;_o=builtins.open;_x=builtins.exec;_v=builtins.eval
_B={"os","subprocess","socket","shutil","sys","pathlib","urllib","http","ctypes","multiprocessing","threading","signal","importlib","requests","pickle","tempfile","glob","asyncio","resource","io"}
def _user(): return _s._getframe(2).f_globals.get("__name__")=="__main__"   # the blocks apply to the model's own code, not to library internals (numpy etc. need open/os to load)
def _i(n,*a,**k):
    if n.split(".")[0] in _B and _user(): raise ImportError("module not allowed: "+n)
    return _r(n,*a,**k)
builtins.__import__=_i
def _mk(f):
    def g(*a,**k):
        if _user(): raise PermissionError("file access not allowed")
        return f(*a,**k)
    return g
builtins.open=_mk(_o);builtins.exec=_mk(_x);builtins.eval=_mk(_v)
'''
def _limits():
    resource.setrlimit(resource.RLIMIT_CPU,(10,10))
    resource.setrlimit(resource.RLIMIT_FSIZE,(0,0))
# Where model-written Python runs (env MC_SANDBOX):
#   local (default): a child process of this machine, `python -I`, with cpu and file-size limits and the import/file guard above.
#                    This is NOT user isolation: run the whole repository inside the Docker image (see README) if you do not trust the model.
#   ssh            : the command below, over ssh to MC_SANDBOX_HOST, as an unprivileged user (this is how the reported runs were made).
#   host           : the same command run directly on this machine (when this machine is the sandbox host).
VM=os.environ.get('MC_SANDBOX_HOST','')
REMOTE="sudo -n -u nobody bash -c 'cd /tmp; ulimit -t 10 -v 600000 -f 0; exec timeout 15 python3 -I -'"
import threading,time
import os
_SEM=threading.Semaphore(int(os.environ.get('RB_PAR','100')))   # trials: RB_PAR=15; confirmed runs: default 100
def _mode():
    m=os.environ.get('MC_SANDBOX') or ('host' if os.environ.get('ON_VM')=='1' else ('ssh' if VM else 'local'))
    if m=='ssh' and not VM:raise RuntimeError('MC_SANDBOX=ssh needs MC_SANDBOX_HOST')
    return m
def run_python(code,timeout=30):
  with _SEM:
    for attempt in range(3):
      try:
        m=_mode()
        if m=='local':
            import sys as _sys
            p=subprocess.run([_sys.executable,'-I','-'],input=GUARD+'\n'+code,capture_output=True,text=True,timeout=min(timeout,30),preexec_fn=_limits,cwd=tempfile.gettempdir())
        elif m=='host':   # same sandbox command as the reported runs, run on this machine
            p=subprocess.run(['bash','-c',REMOTE],input=GUARD+'\n'+code,capture_output=True,text=True,timeout=timeout)
        else:
            p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ControlMaster=auto','-o','ControlPath=/tmp/rbssh%d-%%C'%(threading.get_ident()%10),'-o','ControlPersist=300',VM,REMOTE],input=GUARD+'\n'+code,capture_output=True,text=True,timeout=timeout)
        out=(p.stdout+('\n'+p.stderr if p.stderr else '')).strip()
        if p.returncode==255 or 'mux_client' in p.stderr or 'Session open refused' in p.stderr or 'Connection' in p.stderr[:200]:
            time.sleep(1+attempt);continue
        break
      except subprocess.TimeoutExpired:
        if attempt<2:time.sleep(1);continue   # a timeout under heavy ssh load is retried; the remote side kills code after 15 s anyway
        out='ERROR: timeout';break
    else:raise RuntimeError('ERROR ssh sandbox unreachable')
    return out[:2500] if out else '(no output)'
AGENT_MODEL=os.environ.get('AGENT_MODEL','z-ai/glm-5.3-flash')   # agent model; the judge (chat2) is separate
AGENT_PROVIDERS={'z-ai/glm-5.3-flash':['relace','openinference']}.get(AGENT_MODEL,[])
TOK=[0,0,0,0]
def chat(messages,mt=MAXTOK):
    with rp.lock:
        if rp.calls[0]>=rp.CAP:return 'SKIPPED cap','',0,True
        rp.calls[0]+=1
    # temperature 0 is sent for every agent model; anthropic/claude-haiku-5.5 does not support a temperature parameter on OpenRouter,
    # so it is not applied for that model
    body={'model':AGENT_MODEL,'messages':messages,'temperature':0,'max_tokens':mt,'reasoning':{'effort':'minimal'}}
    if AGENT_PROVIDERS:body['provider']={'order':AGENT_PROVIDERS,'allow_fallbacks':False}   # two cheapest providers for the model; a model without a pinned list (any AGENT_MODEL other than the default) is routed by OpenRouter
    r=urllib.request.Request(__import__('os').environ.get('OPENROUTER_BASE','https://openrouter.ai/api/v1')+'/chat/completions',data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+rp.key,'Content-Type':'application/json'})
    try:
        d=json.load(rp.urlopen_retry(r,240));c=d['choices'][0]
        u=d.get('usage') or {}
        with rp.lock:
            TOK[0]+=u.get('prompt_tokens') or 0;TOK[1]+=u.get('completion_tokens') or 0;TOK[2]+=(u.get('completion_tokens_details') or {}).get('reasoning_tokens') or 0;TOK[3]+=1   # agent token tally (prompt, completion, reasoning, calls)
        return c['message'].get('content') or '',c.get('finish_reason') or '',(d.get('usage') or {}).get('cost') or 0,False
    except Exception as e:
        m='ERROR '+type(e).__name__+' '+str(e)[:150]
        with rp.lock:rp.errors.append(m)
        return m,'',0,True
def code_of(text):
    m=re.search(r'```(?:python)?\s*\n(.*?)```',text,re.S)
    return m.group(1) if m else None
def strip_fake_obs(t):
    """Remove Observation text the model wrote itself (from 'Observation:' to the next Thought:/Action:/Final Answer: line) but keep every real action."""
    return re.sub(r'(?ms)^[ \t]*Observation:.*?(?=^[ \t]*(?:Thought:|Action:|Final Answer:)|\Z)','',t) if t else t
def codes_before_final(t):
    """Multi-action ReAct: every code block written before the Final Answer, in order."""
    i=t.find('Final Answer:');return re.findall(r'```(?:python)?\s*\n(.*?)```',t if i<0 else t[:i],re.S)
LIB="Python tool: numpy, scipy, pandas and statsmodels are available (for example statsmodels.tsa.filters.hp_filter.hpfilter); no internet, no files. Print what you compute."
def data_of(i):
    """data text for CoT1 and PoT: BROAD_DATA=1 -> all standard series for named questions (db.build_broad); hidden-subject questions keep the
    needed series for every candidate economy (pr.build), since 42 series x many economies is too long; otherwise the needed series only (pr.build)"""
    if os.environ.get('BROAD_DATA')=='1' and pr.item(i).get('style')!='hidden':
        sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))+'/../data_blocks');import data_blocks as db;return db.build_broad(i)[1]
    return pr.build(i)[1]
def pot(i):
    it,info,pm=pr.prompts(i);q=it['query'];d=data_of(i)
    p1=d+"\n"+q+f"\n\nWrite ONE Python program that computes the answer from the data above. Copy the numbers you need into the program. {LIB} Print the key intermediate values and the final result. Reply with only the program in a ```python block."
    t1,f1,c1,e1=chat([{'role':'user','content':p1}]);tr=[('program',t1)];cost=c1;trunc=f1=='length'
    if e1:return dict(answer='',trace=tr,error=t1,cost=cost,truncated=trunc)   # API failure is a harness error, not a missing program
    code=code_of(t1)
    if code is None:return dict(answer='',trace=tr,error='no program',cost=cost,truncated=trunc)
    out=run_python(code);tr.append(('output',out))
    p2=d+"\n"+q+f"\n\nProgram you wrote:\n```python\n{code}\n```\nOutput of running it:\n{out}\n"+rp.SUF
    t2,f2,c2,e2=chat([{'role':'user','content':p2}]);tr.append(('answer',t2))
    return dict(answer='' if e2 else t2,trace=tr,error=t2 if e2 else None,cost=cost+c2,truncated=trunc or f2=='length')
FINAL_FMT="the answer; the procedure you used and its source if you know it; the computation shown step by step."
REACT_HEAD=("You answer public-finance questions. You have the data below and a Python tool. "+LIB+"\n"
"The question does not tell you which method to use. First decide which published procedure applies and state it, then compute with it.\n"
"Use exactly this format.\nTo use the tool:\nThought: your reasoning\nAction: run_python\nAction Input:\n```python\ncode\n```\n"
"You will then receive an Observation with the printed output. When you are ready to answer:\nThought: your reasoning\nFinal Answer: "+FINAL_FMT+"\n"
f"You may use the tool at most {MAX_TOOL} times.\n\n")
FORCE_RULE=("Rule: do every calculation with run_python. Do not calculate in your head or in your reasoning text. "
"Your Final Answer may only report numbers that the tool printed, and you must run the tool at least once before answering.\n\n")
_OP=OUT+'oracle_excerpts.json' if os.path.exists(OUT+'oracle_excerpts.json') else OUT+'oracle_passages.json'
ORACLE=json.load(open(_OP)) if os.path.exists(_OP) else {}
ORACLE={k:'\n'.join(l for l in (v or '').split('\n') if not l.startswith('Source:')).strip() for k,v in ORACLE.items()}
if os.environ.get('ORACLE_SRC')=='both' and os.path.exists(OUT+'oracle_passages.json'):   # key-number excerpt + the full method passage (~2,800 chars) from the method document
    _P=json.load(open(OUT+'oracle_passages.json'))
    ORACLE={k:(ORACLE.get(k,'')+('\n\nFull passage from the method document:\n'+_P[k] if _P.get(k) else '')).strip() for k in set(ORACLE)|set(_P)}
# key-number excerpt + full passage, always built (used by Ours-oracle whatever ORACLE_SRC is)
ORACLE_BOTH=dict(ORACLE)
if os.path.exists(OUT+'oracle_passages.json'):
    _P2=json.load(open(OUT+'oracle_passages.json'));_E=json.load(open(_OP)) if os.path.exists(_OP) else {}
    _E={k:'\n'.join(l for l in (v or '').split('\n') if not l.startswith('Source:')).strip() for k,v in _E.items()}
    ORACLE_BOTH={k:(_E.get(k,'')+('\n\nFull passage from the method document:\n'+_P2[k] if _P2.get(k) else '')).strip() for k in set(_E)|set(_P2)}
# ORACLE_SRC=methods: the passage text comes from oracle_methods.json ({folder: text}); the Ours-oracle arm gets this text.
# If the file is missing: warn and use the ORACLE_SRC=both text (excerpt + full passage).
if os.environ.get('ORACLE_SRC')=='methods':
    if os.path.exists(OUT+'oracle_methods.json'):
        ORACLE={k:(v or '').strip() for k,v in json.load(open(OUT+'oracle_methods.json')).items()};ORACLE_BOTH=ORACLE
    else:
        print('WARNING: ORACLE_SRC=methods but '+OUT+'oracle_methods.json is missing; falling back to ORACLE_SRC=both text for the oracle arm',file=sys.stderr);ORACLE=ORACLE_BOTH
STRUCT=("Before you compute, write out the formula and the parameter values you will use, one per line. If you rely on a document, quote the sentence that states them; if you rely on memory or a convention, say so. "
"After computing, check that your result is consistent with those stated values.\n\n")
LAST_STEP="This is your last step. You cannot make any more tool calls. Write your Final Answer now from what you have, in the required format."
EXTRA_MSG="No steps are left and tools are disabled. Write your Final Answer now from what you have."
def step_line(k,N):
    """Shared by the multi-action arms: the step the model is about to take; the last step is a hard answer-now step."""
    return f"Step {k} of {N}. "+(LAST_STEP if k>=N else f"You have {N-k} steps left.")
def extra_answer(t):
    """Answer from the extra call: text after 'Final Answer:' (or the whole reply), with any action text removed."""
    a=t.split('Final Answer:',1)[1] if 'Final Answer:' in t else re.sub(r'```.*?```','',t,flags=re.S)
    return re.split(r'(?m)^[ \t]*(?:Action:|Action Input|Observation:)',a)[0].strip()
QUESTION_LINE="The question does not tell you which method to use. First decide which published procedure applies and state it, then compute with it.\n"
# ReAct-steps (control): the ReAct-v2 head with QUESTION_LINE replaced by the prompt steps of Ours-cards2 that need no method tool (name two or three methods,
# state the formula and the source of each parameter value, compute rules); the steps that use search_cards / get_card / read_source are left out.
STEPS_LINE=("The question does not tell you which method to use.\n"
"Work in this order. (1) Name two or three published methodologies that could answer the question (method names and the institutions that publish them), and say which one you use and why. "
"(2) Before you compute, state the formula and each parameter value you will use, and for each parameter value say where it comes from (the question, the data, or your own knowledge of the method); never use a value without saying where it comes from, and if you cannot give a value, say plainly that you cannot compute it. "
"(3) Then compute with run_python. Use the full data series for any filter or fit unless the method says otherwise, and check that the result is plausible for the country; if it is absurd, say so and fix it before answering. Use those libraries instead of hand-written maths. Report only numbers that your code printed in an Observation; if the code failed, fix it or say that you could not compute it. Do not use a different method from the one you stated (for example a linear trend instead of the filter the method names). Keep a step in reserve: you must write the Final Answer before the turns run out. In the Final Answer, give one clear verdict and number (no hedging).\n"
"Never write the Observation yourself.\n")
def react_multi(i,turns=16,steps=False):
    """ReAct-v2: several actions per turn, all run in written order, one Observation; the only limit is the number of turns.
    With DATA_TOOL=1 the data table is replaced by the data tool (search_series, fetch_series, series_table) and the run logs its data fields."""
    S=DA.Session(i) if DA.on() else None
    r=_react_multi(i,turns,S,steps)
    if S:r.update(S.log())
    return r
def _react_multi(i,turns,S,steps=False):
    it,info,pm=pr.prompts(i);q=it['query'];d=pr.build(i)[1]
    if S:d=DA.ref_notes(i)   # no data table in the prompt (only the 'Reference lists:' note of group memberships); pr.build above fills db.LAST (needs, used for logging)
    head=REACT_HEAD.replace(f"You may use the tool at most {MAX_TOOL} times.\n\n",f"You have {turns} turns. You may write several actions in one turn; all of them will be run in the order written and their results come back together in one Observation.\n\n")
    if steps:
        assert QUESTION_LINE in head;head=head.replace(QUESTION_LINE,STEPS_LINE)
    head=DA.head_swap(head)
    msgs=[{'role':'user','content':head+FORCE_RULE+STRUCT+d+"\n"+q+"\n\n"+step_line(1,turns)}];tr=[];cost=0;used=0;trunc=False
    for turn in range(turns):
        t,f,c,e=chat(msgs);cost+=c;trunc=trunc or f=='length';t=strip_fake_obs(t);tr.append(('model',t));msgs.append({'role':'assistant','content':t or ' '})
        if e:return dict(answer='',trace=tr,error=t,cost=cost,truncated=trunc,tool_calls=used)
        fin='Final Answer:' in t
        if S:
            acts=[(n,code_of(x) if n=='run_python' else x) for n,x in DA.parse_actions(t)]
            if not acts and not fin and code_of(t) is not None:acts=[('run_python',code_of(t))]
        else:
            codes=codes_before_final(t)
            if not codes and not fin and code_of(t) is not None:codes=[code_of(t)]
            acts=[('run_python',cd) for cd in codes]
        if turn==turns-1:   # last step: nothing is run; gates are waived and logged
            w=['no_python'] if used==0 else []
            if fin and not acts:return dict(answer=t.split('Final Answer:',1)[1].strip(),trace=tr,error=None,cost=cost,truncated=trunc,tool_calls=used,final_gate_waived=w,extra_call=False)
            msgs.append({'role':'user','content':EXTRA_MSG});t,f,c,e=chat(msgs);cost+=c;trunc=trunc or f=='length';t=strip_fake_obs(t);tr.append(('model',t))
            if e:return dict(answer='',trace=tr,error=t,cost=cost,truncated=trunc,tool_calls=used)
            return dict(answer=extra_answer(t),trace=tr,error=None,cost=cost,truncated=trunc,tool_calls=used,final_gate_waived=w,extra_call=True)
        if not acts and fin:
            if used==0:
                obs='Rejected: you must compute with run_python before giving a Final Answer. Run the tool now.';tr.append(('observation',obs));msgs.append({'role':'user','content':'Observation:\n'+obs+'\n\n'+step_line(turn+2,turns)});continue
            return dict(answer=t.split('Final Answer:',1)[1].strip(),trace=tr,error=None,cost=cost,truncated=trunc,tool_calls=used)
        if not acts:obs='No valid action. Use the format: Action Input with a ```python block, or Final Answer.'
        else:
            outs=[]
            for k,(nm,x) in enumerate(acts):
                if nm=='run_python':
                    used+=1;outs.append(run_python(x) if x else 'No code block: write the code in a ```python block after Action Input.')
                else:outs.append(S.run(nm,x))
            obs=outs[0] if len(outs)==1 else '\n\n'.join(f'[Action {k+1} of {len(outs)}: {acts[k][0]}]\n{o}' for k,o in enumerate(outs))
            if fin:obs+='\n\nYour Final Answer was ignored because actions in the same turn had not yet returned. Answer in a turn with no actions.'
        tr.append(('observation',obs));msgs.append({'role':'user','content':'Observation:\n'+obs+'\n\n'+step_line(turn+2,turns)})
    return dict(answer='',trace=tr,error='no final answer',cost=cost,truncated=trunc,tool_calls=used)
def cot(i,key):
    it,info,pm=pr.prompts(i)
    if key=='R2' and os.environ.get('BROAD_DATA')=='1':pm[key]=data_of(i)+"\n"+it['query']+rp.SUF   # CoT1 with the broad table
    t,f,c,e=chat([{'role':'user','content':pm[key]}])
    return dict(answer='' if e else t,trace=[('answer',t)],error=t if e else None,cost=c,truncated=f=='length',tool_calls=0)
ARMS={'CoT0':lambda i:cot(i,'R1'),'CoT1':lambda i:cot(i,'R2'),'PoT':pot,'ReAct-v2':lambda i:react_multi(i,int(os.environ.get('AGENT_TURNS','16'))),'ReAct-steps':lambda i:react_multi(i,int(os.environ.get('AGENT_TURNS','16')),True)}   # AGENT_TURNS: same step limit as the card and text arms
sel=[x.split('=',1)[1] for x in sys.argv if x.startswith('--arms=')]
USE=sel[0].split(',') if sel else ['CoT0','CoT1','PoT','ReAct-v2']
def run_arm(fn,i):
    """One attempt; infrastructure faults and output-limit hits are harness errors: repeat once (same prompt).
    A run that still ends as a harness error is flagged and never scored as a model failure."""
    r=fn(i)
    if str(r.get('error') or '').startswith('ERROR') or r.get('truncated'):
        c0=r.get('cost',0);r=fn(i);r['cost']=r.get('cost',0)+c0
    r['harness_error']=bool(str(r.get('error') or '').startswith('ERROR') or r.get('truncated'))
    return r
def py_trace(tr,cap=8000):
    """Computation record shown to the judge: Python code and its printed output only (tool names, searches and reads stripped)."""
    rec=[];n=0;pending=False;dt=[]   # dt: with DATA_TOOL=1, the run_python codes of the last turn that also held data actions (their outputs are picked out of the combined Observation)
    for kind,text in tr:
        if DA.on() and kind=='model' and text and re.search(r'(?m)^[ \t]*Action:\s*(search_series|fetch_series|series_table)\b',text):
            dt=[code_of(x) for nm,x in DA.parse_actions(text) if nm=='run_python'];pending='dt';dt_k=[nm for nm,x in DA.parse_actions(text)];continue
        if pending=='dt' and kind=='observation':
            segs=re.split(r'(?m)^\[Action \d+ of \d+: (\w+)\]\n',text or '')   # ['', name1, text1, name2, text2, ...]; a one-action Observation has no header
            outs=[segs[j+1] for j in range(1,len(segs),2) if segs[j]=='run_python'] if len(segs)>1 else ([text] if dt else [])
            for k,cd in enumerate(dt):
                n+=1;rec.append(f"Run {n} code:\n{cd}" if cd else f"Run {n} code:\n(no code block)");rec.append("Printed output:\n"+(outs[k].strip() if k<len(outs) else '(none)'))
            pending=False;dt=[];continue
        if kind=='program':
            c=code_of(text or '')
            if c:n+=1;rec.append(f"Run {n} code:\n{c}");pending=True
        elif kind=='model':
            c=code_of(text.split('Action Input',1)[-1]) if text and 'Action: run_python' in text and 'Action Input' in text else None
            if c:n+=1;rec.append(f"Run {n} code:\n{c}");pending=True
            else:pending=False
        elif kind=='output' or (kind=='observation' and pending):
            rec.append("Printed output:\n"+str(text));pending=False
        elif kind=='observation':pending=False
    s='\n'.join(rec)
    return s[:cap]+('\n[record cut]' if len(s)>cap else '')
JUDGE2='deepseek/deepseek-v4.1-flash'
def chat2(messages,mt=20000):
    """second judge call, same provider pin as chat"""
    with rp.lock:
        if rp.calls[0]>=rp.CAP:return 'SKIPPED cap',0,True
        rp.calls[0]+=1
    body={'model':JUDGE2,'messages':messages,'temperature':0,'max_tokens':mt,'reasoning':{'effort':'minimal'},'provider':{'order':['relace','morph'],'allow_fallbacks':False}}   # judge 2: two cheapest providers (Relace first)
    r=urllib.request.Request(__import__('os').environ.get('OPENROUTER_BASE','https://openrouter.ai/api/v1')+'/chat/completions',data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+rp.key,'Content-Type':'application/json'})
    try:
        d=json.load(rp.urlopen_retry(r,240));c=d['choices'][0]
        return c['message'].get('content') or '',(d.get('usage') or {}).get('cost') or 0,False
    except Exception as e:
        return 'ERROR '+type(e).__name__+' '+str(e)[:150],0,True
def num_spec(c):
    """(target,tol_full,tol_partial) if the claim has a numeric band, else None. Band comes from the item data."""
    t=c.get('target');tol=c.get('tolerance_abs')
    if t is None:t=c.get('reference_value');tol=c.get('tolerance') if tol is None else tol
    if t is None:t=(c.get('resolves') or {}).get('value')
    if t is None:return None
    acc=c.get('accept') or ''
    if tol is None:
        m=re.search(r'full = within \+?/?-?\s*([\d.]+)',acc);tol=float(m.group(1)) if m else None
    if tol is None:return None
    m=re.search(r'partial = (?:correct sign and )?within \+?/?-?\s*([\d.]+)',acc)
    return float(t),float(tol),(float(m.group(1)) if m else 2*float(tol))
def band_score(spec,v):
    t,f,p=spec
    if v is None:return 0.0
    d=abs(v-t)
    if d<=f+1e-9:return 1.0
    if d<=p+1e-9 and (t==0 or v*t>0):return 0.5
    return 0.0
def judge_prompt_v2(it,ans,rec,subj):
    cl=[]
    for kind in('text','data','computation','answer'):
        for c in it['claims'].get(kind,[]):
            d={k:c[k] for k in('id','kind','importance','text','accept','value') if k in c}
            if num_spec(c):d.pop('accept',None);d['numeric']='report the number the answer gives for this claim as "reported_value" (plain number, same unit as the claim, null if none). Do NOT say whether it is inside a band.'
            cl.append(d)
    p=("You are grading an answer to a public-finance methodology question against typed claims. Judge only against the claims.\n"
       "Give each claim a score: 1 = fully met; 0.5 = right idea but a number or detail slightly off, or hedged / only partly stated; 0 = not met or wrong. Use the 'accept' wording where it gives full/partial/no. "
       "kind text = methodology, data = inputs used, answer = interpretation or verdict. A parameter value that differs is a minor deviation unless the claim fixes it. A correct result by a wrong method fails the methodology claim. "
       "For claims with a 'numeric' field, give only reported_value (and score null); the number check is done elsewhere.\n"
       f"QUESTION: {it['query']}\n\nCLAIMS:\n{json.dumps(cl,indent=1)}\n\nANSWER TO GRADE:\n\"\"\"{ans[:12000]}\"\"\"\n\n"
       "COMPUTATION RECORD (empty if none):\n\"\"\"\n"+(rec or '(none)')+"\n\"\"\"\n\n")
    if it['style']=='hidden' and subj:p+=f"The correct economy for this question is {subj}.\n\n"
    return p+'Reply with ONLY a JSON object mapping each claim id to {"score": 0 or 0.5 or 1 (null if numeric), "reported_value": number or null, "reason": "one line"}.'
def judge_item_v2(x):
    """Judge one result row: 0/0.5/1 per claim, numeric bands checked in code. Adds score_v2, parts_v2, vital_all_v2, claims_v2, judge2_cost, judge2_failed."""
    it=pr.item(x['item'])
    if x.get('harness_error') or not x.get('answer','').strip():x.update(score_v2=(None if x.get('harness_error') else 0.0),judge2_cost=0);return x
    subj=pr.build(x['item'])[3].get('subject')
    p=judge_prompt_v2(it,x['answer'],py_trace(x.get('trace',[])),subj);cost=0;j=None
    for attempt in (1,2):
        a,c,e=chat2([{'role':'user','content':p}]);cost+=c
        try:
            if e:raise ValueError(a)
            j=json.loads(re.search(r'\{.*\}',a,re.S).group(0));break
        except Exception:j=None
    if j is None:x.update(score_v2=None,judge2_cost=cost,judge2_failed=True,judge2_raw=(a or '')[-700:]);return x
    parts={};vital=True;cs2={}
    for kind in rp.W:
        cl=it['claims'].get(kind,[])
        if not cl:continue
        ps=[]
        for c in cl:
            r=j.get(c['id']) or {};sp=num_spec(c)
            if sp:
                try:v=float(r.get('reported_value'))
                except Exception:v=None
                if v is None and 'not required' in (c.get('accept') or ''):cs2[c['id']]=dict(s=None,skipped='alternative not required, none stated');continue
                s=band_score(sp,v);cs2[c['id']]=dict(s=s,reported=v,target=sp[0],band=sp[1:],reason=r.get('reason'))
            else:
                try:s=float(r.get('score'))
                except Exception:s=0.0
                s=min([0.0,0.5,1.0],key=lambda q:abs(q-s));cs2[c['id']]=dict(s=s,reason=r.get('reason'))
            ps.append(s)
            if c.get('importance')=='vital' and s<1:vital=False
        if ps:parts[kind]=sum(ps)/len(ps)
    tw=sum(rp.W[k] for k in parts)
    x.update(score_v2=round(100*sum(rp.W[k]*v for k,v in parts.items())/tw,1),parts_v2=parts,vital_all_v2=vital,claims_v2=cs2,judge2_cost=cost,judge2_failed=False)
    return x
def main():
    ids=pr.CHOSEN+pr.pick_named()
    isel=[x.split('=',1)[1] for x in sys.argv if x.startswith('--items=')]
    if isel:ids=isel[0].split(',')
    if '--dry' in sys.argv:
        print('sandbox 2+2:',run_python('print(2+2)'));print('math ok:',run_python('import math\nprint(round(math.sqrt(2),4))'))
        print(REACT_HEAD+pr.build(ids[1])[1][:500]);print('items',ids)
        print('trace test:',py_trace([('model','Thought: x\nAction: run_python\nAction Input:\n```python\nprint(1)\n```'),('observation','1'),('model','Final Answer: 1')]))
        per={'CoT0':2,'CoT1':2,'PoT':4,'ReAct-v2':19}
        print('max model calls per item by arm (answer calls + up to 2 judge tries):',{a:per[a] for a in USE},'| total for',len(ids),'items:',len(ids)*sum(per[a] for a in USE));return
    if '--go' not in sys.argv:return
    jobs=[(i,a) for i in ids for a in USE]
    def one(jb):
        i,a=jb;r=run_arm(ARMS[a],i);r.update(item=i,arm=a);return r
    with cf.ThreadPoolExecutor(6) as ex:res=list(ex.map(one,jobs))
    with cf.ThreadPoolExecutor(6) as ex:res=list(ex.map(judge_item_v2,res))
    for x in res:
        it=pr.item(x['item']);x['method']=it['method'];x['style']=it['style'];x['band']=pr.BAND[it['method']]
    tag='_'.join(USE)+('_subset' if isel else '')
    json.dump(dict(calls_made=rp.calls[0],errors=rp.errors,results=res),open(OUT+'results_'+tag+'.json','w'),indent=1)
    print('calls',rp.calls[0],'errors',rp.errors,'answer cost',round(sum(x.get('cost',0) for x in res),4),'judge cost',round(sum(x.get('judge2_cost',0) for x in res),4))
    for x in res:print(x['item'],x['arm'],x.get('score_v2'),x.get('vital_all_v2'),'tools',x.get('tool_calls','-'),'HARNESS_ERR' if x.get('harness_error') else '')
if __name__=='__main__':main()
