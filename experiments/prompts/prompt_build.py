"""Prompt builder: for an item returns the three prompt variants R1 (question only), R2 (+ data block) and R3 (+ data block + method passage).
Shared by the baseline and agent arms. Makes no model call."""
import json,glob,re,sys,concurrent.futures as cf
sys.path.insert(0,(__import__('os').environ.get('MC_ROOT') or __import__('os').path.abspath(__import__('os').path.join(__import__('os').path.dirname(__file__),'..','..')))+'/experiments/prompts_data')
import data_access as rp
OUT=(__import__('os').environ.get('MC_ROOT') or __import__('os').path.abspath(__import__('os').path.join(__import__('os').path.dirname(__file__),'..','..')))+'/experiments/prompts/'
PASSAGE_FROM={'eir':'EIR-01','debt_stab':'DSTAB-15','debt_path':'DPATH-01','debt_target_adjustment':'DTADJ-01'}
BAND={'eir':'easy','debt_stab':'medium','debt_path':'medium','debt_target_adjustment':'hard'}
CHOSEN=['EIR-07','DSTAB-08','DTADJ-06']  # hidden; named / claim check chosen below
NOTE="Note on the series: interest paid in a year (% of GDP) = primary net lending/borrowing minus net lending/borrowing.\n"
def item(i):return rp.find(i)
def num(code,iso,y):
    try:return float(rp.get(code,iso,y))
    except(TypeError,ValueError):return None
def pct(code,iso,y):
    a,b=num(code,iso,y),num(code,iso,y-1)
    return None if a is None or b in(None,0) else 100*(a/b-1)
def field(f,iso,y):
    return {'d_prev':lambda:num('GGXWDG_NGDP',iso,y-1),'debt':lambda:num('GGXWDG_NGDP',iso,y),
            'pb':lambda:num('GGXONLB_NGDP',iso,y),'bal':lambda:num('GGXCNL_NGDP',iso,y),
            'nominal_growth':lambda:pct('NGDP',iso,y),'ng':lambda:pct('NGDP',iso,y),
            'real_growth':lambda:num('NGDP_RPCH',iso,y),'rg':lambda:num('NGDP_RPCH',iso,y),
            'deflator_inflation':lambda:pct('NGDP_D',iso,y)}[f]()
def conds(it):
    g=it.get('gold') or {}
    if g.get('hidden_condition'):
        h=g['hidden_condition'];return [(h['fields'][k],g['year'],*h['windows'][str(k)]) for k in h['used']],g['iso3'],g['year']
    c=it['conditions'];return [(x['kind'],x['year'],x['low'],x['high']) for x in c],it['hidden_subject'],c[0]['year']
def candidates(cs):
    out=[]
    for iso in rp.wide_csv('weo_oct2025_ggxwdg_ngdp.csv'):
        v=[field(f,iso,y) for f,y,lo,hi in cs]
        if None in v:continue
        if all(lo<=x<=hi for x,(f,y,lo,hi) in zip(v,cs)):out.append(iso)
    return out
def first_window_candidates(cs,minimum=8):
    f,y,lo,hi=cs[0];span=hi-lo
    for k in range(0,41):  # widen the first condition's window until at least `minimum` economies fit
        w=0.25*k*span;c=candidates([(f,y,lo-w,hi+w)])
        if len(c)>=minimum:return c
    return c
def table(isos,y,codes):
    t=f"Candidate economies (IMF World Economic Outlook, October 2025). Each row is one economy; columns are {y-1} and {y}.\n| economy | "+" | ".join(f"{rp.NAMES.get(c,c)} {yy}" for c in codes for yy in(y-1,y))+" |\n|---|"+"---|"*(2*len(codes))+"\n"
    for iso in isos:
        t+=f"| {iso} | "+" | ".join(str(rp.get(c,iso,yy)) if rp.get(c,iso,yy) not in(None,'') else 'n/a' for c in codes for yy in(y-1,y))+" |\n"
    return t
def build(i):
    it=item(i);m=it['method'];ps,pq=rp.PASS[PASSAGE_FROM[m]];g=it.get('gold') or {}
    codes=rp.W4+(['NGDP_R'] if m=='debt_path' else [])
    if it['style']=='hidden':
        cs,subj,y=conds(it);cands=first_window_candidates(cs);full=candidates(cs)
        d=table(cands,y,codes);info=dict(subject=subj,year=y,n_candidates=len(cands),subject_in=subj in cands,set_size_all=len(full))
    else:
        iso=g.get('iso3') or it['provenance']['subject']['iso3'];y=g.get('year') or it['provenance']['subject']['year']
        d=rp.table(iso,iso,codes,[y-1,y]);info=dict(subject=iso,year=y)
    d+=NOTE
    return it,d,(ps,pq),info
def pick_named():
    out=[]
    for m,style in(('eir','named'),('debt_stab','claim_check'),('debt_path','named')):
        for f in sorted(glob.glob(rp.P+f'items/{m}/*.json')):
            d=json.load(open(f))
            if d['style']!=style or str(d.get('status','')).startswith('dropped') or d['id'] in rp.SPEC:continue
            g=d.get('gold') or {};pv=(d.get('provenance') or {}).get('subject')
            if g.get('iso3') or pv:out.append(d['id']);break
    return out
def prompts(i):
    it,d,(ps,pq),info=build(i);q=it['query'];S=rp.SUF
    return it,info,{'R1':q+S,'R2':d+"\n"+q+S,'R3':d+f"\nMethod passage ({ps}):\n{pq}\n\n"+q+S}
