"""Client of bank_server.py (a persistent child process; over ssh if MC_BANK_HOST is set, otherwise local). Query embeddings are made here (openai/text-embedding-3-small via OpenRouter, key read in code).
    from bank_client import BankSearch
    bs = BankSearch(); bs.search("how to split a change in the current account", k=5)   # embeds the query (1 call) for dense/hybrid
    bs.get_card(card_id)"""
import json, subprocess, shlex, base64, os, sys
H = (__import__('os').environ.get('MC_ROOT') or __import__('os').path.abspath(__import__('os').path.join(__import__('os').path.dirname(__file__),'..','..')))+'/tools/bank/'
sys.path.insert(0, H)
from bank_search import embed
class BankSearch:
    def __init__(self, host=None, cards_file="cards_final.jsonl"):
        cards = [json.loads(l) for l in open(H + cards_file)]
        vecs = base64.b64encode(open(H + 'data/card_vectors_final.f32', 'rb').read()).decode()
        _src = open(H + 'bank_server.py').read()
        cmd = ["python3", "-c", _src] if (os.environ.get("ON_VM") == "1" or not (host or os.environ.get("MC_BANK_HOST"))) else ["ssh", "-o", "BatchMode=yes", "-o", "ServerAliveInterval=30", (host or os.environ["MC_BANK_HOST"]), "python3 -c " + shlex.quote(_src)]
        self.p = subprocess.Popen(cmd,
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
        self.p.stdin.write(json.dumps({"cards": cards, "vecs_b64": vecs}) + "\n"); self.p.stdin.flush()
        self.info = json.loads(self.p.stdout.readline()); self.n_emb = 0
    def _call(self, o):
        self.p.stdin.write(json.dumps(o) + "\n"); self.p.stdin.flush(); return json.loads(self.p.stdout.readline())
    def search(self, query, k=5, mode="hybrid", qvec=None, central_boost=0.0, other_penalty=0.0):
        if mode in ("dense", "hybrid") and qvec is None: qvec = embed(query); self.n_emb += 1
        return self._call({"op": "search", "query": query, "qvec": qvec, "mode": mode, "k": k, "central_boost": central_boost, "other_penalty": other_penalty})
    def get_card(self, card_id): return self._call({"op": "get", "card_id": card_id})
    def close(self):
        try: self.p.stdin.write(json.dumps({"op": "quit"}) + "\n"); self.p.stdin.flush()
        except Exception: pass
