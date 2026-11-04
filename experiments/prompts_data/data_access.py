import json,glob,csv,os,re,sys,threading,urllib.request,concurrent.futures as cf
ROOT=(__import__('os').environ.get('MC_ROOT') or __import__('os').path.abspath(__import__('os').path.join(__import__('os').path.dirname(__file__),'..','..')))
REPO=ROOT+'/'
P=REPO+'dataset/'
FE=REPO+'data/frozen_extra/'
OUT=REPO+'experiments/prompts_data/'
CAP=90
key=os.environ.get('OPENROUTER_API_KEY','')   # only the model-run tier needs it
lock=threading.Lock();calls=[0];errors=[]
retries=[0]
def urlopen_retry(r,timeout,counter=retries,tries=6):
    """urlopen with exponential backoff + jitter on HTTP 429 and 5xx (up to `tries` attempts); retries are counted, never scored as model failures."""
    import time,random,urllib.error
    for t in range(tries):
        try:return urllib.request.urlopen(r,timeout=timeout)
        except urllib.error.HTTPError as e:
            if (e.code==429 or e.code>=500) and t<tries-1:
                counter[0]+=1;time.sleep(min(30,2**t)*(0.5+random.random()));continue
            raise
        except (urllib.error.URLError,ConnectionError,OSError) as e:   # network blips (DNS failure, reset, refused); a read timeout is not retried, so one call can't stall a job for minutes
            if t<tries-1 and 'timed out' not in str(e):
                counter[0]+=1;time.sleep(min(30,2**t)*(0.5+random.random()));continue
            raise
def call(prompt,mt):
    with lock:
        if calls[0]>=CAP: return 'SKIPPED cap',0,True
        calls[0]+=1
    body={'model':'z-ai/glm-5.3-flash','messages':[{'role':'user','content':prompt}],'temperature':0,'max_tokens':mt,'reasoning':{'effort':'minimal'}}
    r=urllib.request.Request(__import__('os').environ.get('OPENROUTER_BASE','https://openrouter.ai/api/v1')+'/chat/completions',data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
    try:
        d=json.load(urlopen_retry(r,240))
        return d['choices'][0]['message']['content'] or '',(d.get('usage') or {}).get('cost') or 0,False
    except Exception as e:
        msg='ERROR '+type(e).__name__+' '+str(e)[:150]
        with lock:errors.append(msg)
        return msg,0,True
# ---- data
_cache={}
def load_long(fn,sep=','):
    if fn in _cache:return _cache[fn]
    D={}
    for r in csv.DictReader(open(FE+fn),delimiter=sep):
        D.setdefault((r['code'],r['iso3']),{})[str(r['period'])]=r['value']
    _cache[fn]=D;return D
def wide_csv(fn):
    if fn in _cache:return _cache[fn]
    D={r['iso3']:r for r in csv.DictReader(open(FE+fn))};_cache[fn]=D;return D
def wide_psv(fn):
    if fn in _cache:return _cache[fn]
    D={}
    for l in open(FE+fn):
        p=l.rstrip('\n').split('|')
        if len(p)<4 or p[0]=='release':continue
        ys=p[2].strip('{}').split(',');vs=p[3].strip('{}').split(',')
        D[(p[0],p[1])]=dict(zip(ys,vs))
    _cache[fn]=D;return D
def get(code,iso,yr):
    yr=str(yr)
    if code.startswith('PSD:'):
        return load_long('psd_20261014_maturity_extract.psv','|').get((code[4:],iso),{}).get(yr)
    if code.startswith('IIP:'):
        return load_long('imf_iip_20261029_portfolio_other_liab.psv','|').get((code[4:],iso),{}).get(yr)
    if code=='NE.IMP.GNFS.CD':return wide_csv('wdi_20261008_ne_imp_gnfs_cd.csv').get(iso,{}).get(yr)
    if code=='PA.NUS.FCRF':return wide_csv('wdi_20261008_pa_nus_fcrf.csv').get(iso,{}).get(yr)
    if code=='FM.LBL.BMNY.GD.ZS':return wide_psv('wdi_20261008_monetary_other.psv').get((code,iso),{}).get(yr)
    if '.' in code:
        v=load_long('wdi_20261008_extract.psv','|').get((code,iso),{}).get(yr)
        return v
    return wide_csv(f'weo_oct2025_{code.lower()}.csv').get(iso,{}).get(yr)
NAMES={'GGXWDG_NGDP':'General government gross debt, % of GDP','GGXONLB_NGDP':'General government primary net lending/borrowing, % of GDP','GGXCNL_NGDP':'General government net lending/borrowing (overall balance), % of GDP','NGDP':'Nominal GDP, national currency','NGDP_R':'Real GDP, national currency (constant prices)','NGDP_D':'GDP deflator index','NGDP_RPCH':'Real GDP growth, %','GGR_NGDP':'General government revenue, % of GDP','GGX_NGDP':'General government total expenditure, % of GDP','NGAP_NPGDP':'Output gap, % of potential GDP','LUR':'Unemployment rate, %','NGSD_NGDP':'Gross national saving, % of GDP','NID_NGDP':'Total investment, % of GDP','PCPIPCH':'Inflation, average consumer prices, % change','LE':'Employment, millions of persons','LP':'Population, millions of persons',
'NY.GDP.MKTP.CN':'GDP, current local currency units (WDI)','FM.LBL.BMNY.CN':'Broad money, current local currency units (WDI)','FM.LBL.BMNY.GD.ZS':'Broad money, % of GDP (WDI)','FI.RES.TOTL.CD':'Total reserves including gold, current US$ (WDI)','NE.IMP.GNFS.CD':'Imports of goods and services, current US$ (WDI)','DT.DOD.DSTC.CD':'Short-term external debt stocks, current US$ (WDI)','NY.GDP.MKTP.CD':'GDP, current US$ (WDI)','PA.NUS.FCRF':'Official exchange rate, LCU per US$, period average (WDI)','BX.GSR.GNFS.CD':'Exports of goods and services, current US$ (WDI)',
'PSD:DP.DOD.DSTC.CR.CG':'Central government short-term debt (World Bank Public Sector Debt), local currency, end of year','PSD:DP.DOD.DLTC.CR.L1.CG':'Central government long-term debt due within one year (World Bank Public Sector Debt), local currency, end of year','IIP:P_MV':'Portfolio investment liabilities, IMF IIP, US$'}
def table(iso,country,codes,years,src='IMF World Economic Outlook, October 2025 (WEO) unless marked'):
    cols=list(years)
    t=f"Data for {country} ({iso}); {src}.\n| series | "+" | ".join(map(str,cols))+" |\n|---|"+"---|"*len(cols)+"\n"
    for c in codes:
        vals=[]
        for y in cols:
            yy=f'{y}Q4' if c.startswith('PSD:') else y
            v=get(c,iso,yy);vals.append('n/a' if v in(None,'') else v)
        t+=f"| {NAMES[c]} | "+" | ".join(vals)+" |\n"
    return t
W4=['GGXWDG_NGDP','GGXONLB_NGDP','GGXCNL_NGDP','NGDP']
EU27={'AUT','BEL','BGR','HRV','CYP','CZE','DNK','EST','FIN','FRA','DEU','GRC','HUN','IRL','ITA','LVA','LTU','LUX','MLT','NLD','POL','PRT','ROU','SVK','SVN','ESP','SWE'}
def eu_cpi(y):
    return "Annual-average CPI inflation, %, 2018, EU27 members: "+", ".join(f"{i} {get('PCPIPCH',i,y)}" for i in sorted(EU27))+"\n"
SPEC={ # id: (iso,country,codes,years, extra text)
'EIR-01':('POL','Poland',W4,[2018,2019],''),
'VEL-01':('BRA','Brazil',['NY.GDP.MKTP.CN','FM.LBL.BMNY.CN','FM.LBL.BMNY.GD.ZS'],[2019],''),
'RR-01':('IND','India',['NGDP_D'],[2022,2023],''),
'EXS-01':('GBR','United Kingdom',['NGSD_NGDP','NID_NGDP'],[2020],''),
'OK-11':('KOR','Korea',['NGAP_NPGDP','LUR'],[2020],''),
'DSTAB-15':('GTM','Guatemala',W4,[2021,2022,2023],''),
'DPATH-01':('POL','Poland',W4+['NGDP_R'],[2018,2019],''),
'MC-12':('HUN','Hungary',['GGXCNL_NGDP','GGXWDG_NGDP','PCPIPCH'],[2018],'EU'),
'RA-11':('BLZ','Belize',['FI.RES.TOTL.CD','NE.IMP.GNFS.CD','DT.DOD.DSTC.CD','FM.LBL.BMNY.GD.ZS','NY.GDP.MKTP.CD'],[2016],''),
'PC-11':('ISR','Israel',['NGDP_R','LE','LP'],list(range(2005,2016)),''),
'GFN-01':('PER','Peru',['GGXCNL_NGDP','NGDP','PSD:DP.DOD.DSTC.CR.CG','PSD:DP.DOD.DLTC.CR.L1.CG'],[2019,2020],''),
'DTADJ-01':('POL','Poland',W4,[2013,2014],''),
'MACDSA-01':('BRA','Brazil',['GGXWDG_NGDP','NGDP_RPCH','NGDP_D','GGXONLB_NGDP','GGXCNL_NGDP','GGR_NGDP'],list(range(2015,2031)),''),
'ARAEM-01':('ZAF','South Africa',['FI.RES.TOTL.CD','DT.DOD.DSTC.CD','FM.LBL.BMNY.CN','PA.NUS.FCRF','BX.GSR.GNFS.CD','IIP:P_MV'],[2017],''),
'SB-01':('DEU','Germany',['NGDP_R'],list(range(1980,2031)),'SB'),
}
BAND={'EIR-01':'easy','VEL-01':'easy','RR-01':'easy','EXS-01':'easy','OK-11':'easy','DSTAB-15':'medium','DPATH-01':'medium','MC-12':'medium','RA-11':'medium','PC-11':'medium','GFN-01':'hard','DTADJ-01':'hard','MACDSA-01':'hard','ARAEM-01':'hard','SB-01':'hard'}
PASS={
'EIR-01':('IMF Staff Guidance Note 2013, DSA table footnote 3','"Defined as interest payments divided by debt stock at the end of previous year"'),
'VEL-01':('IMF WEO 1985, table row','"Income velocity of money: GNP/M1, GNP/M2 or M3"'),
'RR-01':('Escolano (2010), IMF Technical Notes and Manuals, Box 1','r = [(1+i)/(1+pi)] - 1, where i is the nominal interest rate and pi the GDP-deflator inflation rate'),
'EXS-01':('IMF BPM6 chapter 14 and EBA note','"S - I = CAB" ; "CAB = (S_p - I_p) + (S_g - I_g)" ; "NLB = CAB + KAB = NFA"'),
'OK-11':('IMF WEO October 2012, Box 4.1','"a 1 percent deviation of output from potential leads to a reduction in cyclical unemployment of about 1/2 percentage point"; u - u* = a(y - y*)'),
'DSTAB-15':('Escolano (2010) and IMF Staff Guidance Note 2013, footnote 3','Debt-stabilizing primary balance: p* = lambda d*, with lambda = (i - gamma)/(1 + gamma), where i is the effective nominal interest rate and gamma the nominal GDP growth rate. Effective interest rate: "Defined as interest payments divided by debt stock at the end of previous year"'),
'DPATH-01':('Escolano (2010) eq. 26-28; IMF Staff Guidance Note 2013 footnotes 4-5','The change in the debt ratio is decomposed into the primary deficit and the terms [i/(1+g)] d(t-1) (interest), [-pi/(1+g)] d(t-1) (inflation), [-g/(1+g)] d(t-1) (real growth), where g is the nominal GDP growth rate = real growth g_r plus inflation pi plus cross term; the real interest rate contribution is [r - pi(1+g_r)] d(t-1) / (1+g_r+pi+g_r*pi) and real growth enters as -g_r'),
'MC-12':('IMF WEO October 1996','"consumer price inflation must not exceed that of the three best-performing countries by more than 1 1/2 percentage points ... deficit at or below 3 percent ... debt ... 60 percent"'),
'RA-11':('IMF, Assessing Reserve Adequacy (2011)','"three months of imports or full cover of short-term debt"; Greenspan-Guidotti rule: "100 percent cover of STD"; for broad money "20 percent is used here as the upper end of the range usually quoted"'),
'PC-11':('IMF San Marino 2023 Article IV','"Delta ln(GDP/population) = Delta ln(labor productivity) + Delta ln(employment rate) + Delta ln(share of working age pop.)"'),
'GFN-01':('IMF (2025), A Guide and Tool for Projecting Public Gross Financing Needs, section III','GFN is "the government\'s debt amortization payment obligations ... not covered by the overall fiscal balance": GFN_t = Amortizations_t - Overall Balance_t = (am + i) D_{t-1} - PB_t, with Amort_t = am_t D_{t-1} (amortization of debt falling due in the year; source may be a schedule, a maturity table or a rate times the stock)'),
'DTADJ-01':('IMF Fiscal Monitor April 2014, Statistical Table 14, note 3','"CAPB needed to bring the debt ratio down to 40 percent in 2030, or to stabilize debt at the end-2014 level by 2030 if the respective debt-to-GDP ratio is less than 40 percent." "The CAPB is assumed to change in line with Fiscal Monitor projections until 2015 and adjust gradually from 2016 until 2020; thereafter it is maintained constant until 2030." "country-specific interest rate-growth differentials are assumed to increase linearly from their 2014 level (from Fiscal Monitor projections) to 1 by 2028. Thereafter, the differential is maintained at 1 percentage point"'),
'MACDSA-01':('IMF Staff Guidance Note 2013, Table 3 (macro-fiscal stress tests)','"Real GDP growth is reduced by 1 standard deviation for 2 consecutive years." "Primary balance deteriorates (the revenue-to-GDP ratio remains the same as in the baseline, but the ratio of non-interest expenditures to GDP increases as the level of spending is kept the same as in the baseline)." "Additional borrowing leads to increase in interest rate of 25 basis points per 1 percent of GDP worsening of the deficit." "Decline in growth leads to lower inflation (0.25 percentage point per 1 percentage point decrease in GDP growth)." The standard deviation is taken over the last 10 years of history.'),
'ARAEM-01':('IMF, Assessing Reserve Adequacy (2011), para 39 and 41','"Fixed: 30% of STD + 15% of OPL + 10% of M2 + 10% of X" ; "Floating: 30% of STD + 10% of OPL + 5% of M2 + 5% of X", where STD is short-term external debt, OPL other portfolio liabilities, M2 broad money, X exports; "coverage in the region of 100-150 percent of the metric might be regarded as adequate for a typical country"'),
'SB-01':('IMF Fiscal Monitor October 2013','"a Hodrick-Prescott filter is used to estimate potential output, and the CAB is estimated assuming growth elasticities of 1 and 0"; the cyclically adjusted balance "assumes an elasticity of revenue to GDP of 1" and of "expenditure to GDP of 0"'),
}
def find(i):return json.load(open(glob.glob(P+f'items/*/{i}.json')[0]))
def data_block(i):
    iso,cn,codes,yrs,ex=SPEC[i]
    t=table(iso,cn,codes,yrs)
    if ex=='EU':t+=eu_cpi(2018)
    if i=='SB-01':
        t+=table(iso,cn,['GGR_NGDP','GGX_NGDP','GGXCNL_NGDP'],[2020])
    if i=='RR-01':t=t  # raw index
    return t
SUF="\n\nGive a final answer in this format: the answer; the procedure you used and its source if you know it; the computation shown step by step."
def prompts(i,q):
    d=data_block(i);s,qt=PASS[i]
    return {'R1':q+SUF,'R2':d+"\n"+q+SUF,'R3':d+f"\nMethod passage ({s}):\n{qt}\n\n"+q+SUF}
def judge_prompt(item,ans):
    cl=[]
    for kind in('text','data','computation','answer'):
        for c in item['claims'].get(kind,[]):
            cl.append({k:c[k] for k in('id','kind','importance','text','accept','target','tolerance_abs','tolerance_rel') if k in c})
    return ("You are grading an answer to a public-finance methodology question against typed claims. Judge only against the claims; do not compute your own values, use the targets and tolerances given.\n"
    "Rules: a claim of kind text is the methodology; data is the inputs used; computation is the numerical result (pass only if the stated number lies inside the tolerance of the target, per 'accept'); answer is the interpretation or verdict. "
    "A parameter value that differs from the claim is a minor deviation and does not fail a methodology claim unless the claim text fixes that value. A correct result reached by a wrong method fails the methodology claim.\n"
    f"QUESTION: {item['query']}\n\nCLAIMS:\n{json.dumps(cl,indent=1)}\n\nANSWER TO GRADE:\n\"\"\"{ans[:12000]}\"\"\"\n\n"
    'Reply with ONLY a JSON object mapping each claim id to {"pass": true/false, "reason": "one line", "failure_type": null or one of "hallucinated_inputs","improvised_procedure","wrong_parameter","slip"}.')
W={'text':40,'data':20,'computation':25,'answer':15}
def score(item,j):
    parts={};vital=True
    for kind in W:
        cs=item['claims'].get(kind,[])
        if not cs:continue
        ps=[1.0 if (j.get(c['id']) or {}).get('pass') is True else 0.0 for c in cs]
        parts[kind]=sum(ps)/len(ps)
        for c,p in zip(cs,ps):
            if c.get('importance')=='vital' and p<1:vital=False
    tw=sum(W[k] for k in parts)
    return round(100*sum(W[k]*v for k,v in parts.items())/tw,1),parts,vital
def main():
    items={i:find(i) for i in SPEC}
    P3={i:prompts(i,items[i]['query']) for i in SPEC}
    if '--dry' in sys.argv:
        for i in SPEC:print(i,[len(v) for v in P3[i].values()],items[i]['style'],list(items[i]['claims'].keys()))
        print(P3['GFN-01']['R3']);return
    jobs=[(i,r) for i in SPEC for r in('R1','R2','R3')]
    def ans(jb):
        i,r=jb;a,c,e=call(P3[i][r],3000);return dict(item=i,rung=r,prompt=P3[i][r],answer=a,answer_error=e,cost=c)
    with cf.ThreadPoolExecutor(45) as ex:res=list(ex.map(ans,jobs))
    def jud(x):
        if x['answer_error']:x.update(judge_raw='',judgement={},score=0.0,parts={},vital_all=False,judge_error=True);return x
        it=items[x['item']];jp=judge_prompt(it,x['answer']);x['judge_prompt']=jp
        a,c,e=call(jp,2500);x['cost']+=c;x['judge_raw']=a;x['judge_error']=e
        try:j=json.loads(re.search(r'\{.*\}',a,re.S).group(0))
        except Exception:j={};x['judge_error']=True
        s,p,v=score(it,j);x.update(judgement=j,score=s,parts=p,vital_all=v);return x
    with cf.ThreadPoolExecutor(45) as ex:res=list(ex.map(jud,res))
    for x in res:x['band']=BAND[x['item']];x['method']=items[x['item']]['method'];x['style']=items[x['item']]['style']
    json.dump(dict(calls_made=calls[0],errors=errors,results=res),open(OUT+'results.json','w'),indent=1)
    print('calls',calls[0],'errors',errors)
if __name__=='__main__':main()
