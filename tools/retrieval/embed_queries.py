"""Embed the 440 item query texts with openai/text-embedding-3-small (via OpenRouter) for the dense search.
`--go`     : 440 single calls (cap 445), writes query_vectors.json {item_id: [1536 floats]}.
The key is read from the environment variable OPENROUTER_API_KEY and never printed."""
import json,sys,math,subprocess,urllib.request,concurrent.futures as cf,threading
ROOT=(__import__('os').environ.get('MC_ROOT') or __import__('os').path.abspath(__import__('os').path.join(__import__('os').path.dirname(__file__),'..','..')))
H=ROOT+'/tools/retrieval/'
import os
key=os.environ.get('OPENROUTER_API_KEY','')
MODEL='openai/text-embedding-3-small'
lock=threading.Lock();calls=[0];CAP=445
RETRIES=[0]
def _uo(r,timeout,tries=6):
    """urlopen with exponential backoff + jitter on HTTP 429 and 5xx; retries counted in RETRIES."""
    import time,random,urllib.error
    for t in range(tries):
        try:return urllib.request.urlopen(r,timeout=timeout)
        except urllib.error.HTTPError as e:
            if (e.code==429 or e.code>=500) and t<tries-1:
                RETRIES[0]+=1;time.sleep(min(30,2**t)*(0.5+random.random()));continue
            raise
def embed(text):
    with lock:
        if calls[0]>=CAP:raise RuntimeError('cap')
        calls[0]+=1
    r=urllib.request.Request(__import__('os').environ.get('OPENROUTER_BASE','https://openrouter.ai/api/v1')+'/embeddings',data=json.dumps({'model':MODEL,'input':text}).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
    return json.load(_uo(r,120))['data'][0]['embedding']
def cos(a,b):
    d=sum(x*y for x,y in zip(a,b));return d/(math.sqrt(sum(x*x for x in a))*math.sqrt(sum(y*y for y in b)))
def go():
    items=json.load(open(H+'params.json'))['items']
    def one(it):return it['id'],embed(it['query'])
    with cf.ThreadPoolExecutor(8) as ex:res=dict(ex.map(one,items))
    json.dump(res,open(H+'query_vectors.json','w'))
    print('embedded',len(res),'queries; calls',calls[0],'dim',len(next(iter(res.values()))))
if __name__=='__main__':
    if '--go' in sys.argv:go()
