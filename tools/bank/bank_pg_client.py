"""Runs on the host of the database (plain python3, no third-party packages). Persistent card search in Postgres schema method_cards (read-only role method_cards_ro).
    from bank_pg_client import BankPG
    b = BankPG()                      # bank='cards' (country+512 bank), bank='512' or bank='fold' (cards_fold: country cards folded into library cards); pool of persistent psql sessions (default 4); no other startup
    b.search("how to split a change in the current account", k=5, mode='hybrid')   # embeds the query here (key from OPENROUTER_API_KEY, never printed)
    b.get_card(card_id)
Same output format as bank_client.BankSearch / bank_server.Bank: {'hits': [{rank, card_id, name, doc_id, doc_title, pages, short_formula, central, kind, conflicts, sources, score}]}.
Search = BM25 (same tokenizer, k1 1.2, b 0.75, computed in SQL from method_cards.<bank>_terms), dense cosine (pgvector, HNSW ef_search 200), RRF 1/(60+rank) over the top 100 of each, optional central_boost / other_penalty."""
import json, re, os, subprocess, threading, queue, urllib.request
STOP = set("a an and are as at be by for from has have in is it its of on or that the this to was were which with their they these those such than then there can may also not but if into per via".split())
TOK = re.compile(r"[a-z0-9]+")
def toks(t):
    out = []
    for w in TOK.findall(t.lower()):
        if w in STOP or len(w) < 2: continue
        if len(w) > 4 and w.endswith("ies"): w = w[:-3] + "y"
        elif len(w) > 3 and w.endswith("s") and not w.endswith("ss"): w = w[:-1]
        out.append(w)
    return out
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
    key = os.environ["OPENROUTER_API_KEY"]
    r = urllib.request.Request(__import__('os').environ.get('OPENROUTER_BASE','https://openrouter.ai/api/v1')+'/embeddings', data=json.dumps({'model': 'openai/text-embedding-3-small', 'input': text}).encode(), headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
    return json.load(_uo(r, 120))['data'][0]['embedding']
class _Sess:
    def __init__(self):
        self.p = subprocess.Popen(['sudo', '-n', '-u', 'postgres', 'psql', '-At', '-q', '-d', os.environ.get('MC_PG_DB', 'methodcards')], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.q("set role method_cards_ro; set default_transaction_read_only = on;")
    def q(self, sql):
        self.p.stdin.write(sql + "\n\\echo @@END\n"); self.p.stdin.flush(); out = []
        while True:
            l = self.p.stdout.readline()
            if not l or l.strip() == '@@END': break
            out.append(l.rstrip('\n'))
        return '\n'.join(out)
class BankPG:
    def __init__(self, bank='cards', pool=4):
        self.bank = 'fold' if str(bank) in ('fold', 'cards_fold') else ('512' if str(bank) in ('512', 'cards_512') else 'cards'); self.n_emb = 0; self.free = queue.Queue(); self.s = [_Sess() for _ in range(pool)]
        for s in self.s: self.free.put(s)
    def _run(self, sql):
        s = self.free.get()
        try: return s.q(sql)
        finally: self.free.put(s)
    def search(self, query, k=5, mode="hybrid", qvec=None, central_boost=0.0, other_penalty=0.0, prefer=0, w=0.002):
        if mode in ("dense", "hybrid") and qvec is None: qvec = embed(query); self.n_emb += 1
        terms = '{' + ','.join(sorted(set(toks(query)))) + '}'
        qv = "'[" + ",".join(repr(float(x)) for x in qvec) + "]'" if qvec is not None else 'null'
        out = self._run(("select method_cards.search_fold('%s'::text, '%s'::text[], %s, '%s', %d, %r, %r, %d, %r)::text;" if self.bank == 'fold' else "select method_cards.search('%s', '%s'::text[], %s, '%s', %d, %r, %r, %d, %r)::text;") % (self.bank, terms, qv, mode, int(k), float(central_boost), float(other_penalty), int(prefer), float(w)))
        try: return json.loads(out)
        except Exception: return {"error": out[:300]}
    def get_card(self, card_id):
        if not re.fullmatch(r'[0-9A-Za-z_.-]{3,40}', card_id): return {"error": "bad card_id"}
        out = self._run("select method_cards.get_card_fold('%s')::text;" % card_id if self.bank == 'fold' else "select method_cards.get_card('%s', '%s')::text;" % (self.bank, card_id))
        try: return json.loads(out) if out.strip() else {"error": "unknown card_id"}
        except Exception: return {"error": out[:300]}
    def close(self):
        for s in self.s:
            try: s.p.stdin.close()
            except Exception: pass
