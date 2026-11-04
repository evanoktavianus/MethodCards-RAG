"""Card search server. Started by bank_client.py as a child process (locally, or on another host over ssh: ssh <host> python3 -c "<this file>"); JSON lines over stdin/stdout. No model call here.
Init line: {"cards": [card dicts], "vecs_b64": base64 float32 [n,1536]}.  Requests: {"op":"search","query":str,"qvec":[..]|null,"mode":"hybrid|bm25|dense","k":5,"central_boost":0}
{"op":"get","card_id":..} / {"op":"quit"}.  Hit = {rank, card_id, name, doc_id, doc_title, pages, short_formula, central, score}. Hybrid = RRF 1/(60+rank) over top-100 of each ranker."""
import sys, json, re, math, base64
from array import array
from operator import mul
STOP = set("a an and are as at be by for from has have in is it its of on or that the this to was were which with their they these those such than then there can may also not but if into per via".split())
TOK = re.compile(r"[a-z0-9]+"); K1, B, RRF_K, POOL = 1.2, 0.75, 60, 100
def toks(t):
    out = []
    for w in TOK.findall(t.lower()):
        if w in STOP or len(w) < 2: continue
        if len(w) > 4 and w.endswith("ies"): w = w[:-3] + "y"
        elif len(w) > 3 and w.endswith("s") and not w.endswith("ss"): w = w[:-1]
        out.append(w)
    return out
class Bank:
    def __init__(self, init):
        self.cards = init["cards"]; self.byid = {c["card_id"]: i for i, c in enumerate(self.cards)}
        a = array("f"); a.frombytes(base64.b64decode(init["vecs_b64"])); d = len(a) // len(self.cards)
        self.vec = [a[i * d:(i + 1) * d] for i in range(len(self.cards))]
        self.post = {}; self.dlen = []
        for i, c in enumerate(self.cards):
            tk = toks(c["card_text"]); self.dlen.append(len(tk)); tf = {}
            for w in tk: tf[w] = tf.get(w, 0) + 1
            for w, n in tf.items(): self.post.setdefault(w, []).append((i, n))
        self.avg = sum(self.dlen) / len(self.dlen)
    def bm25(self, q):
        N = len(self.cards); sc = {}
        for w in set(toks(q)):
            e = self.post.get(w)
            if not e: continue
            idf = math.log(1 + (N - len(e) + 0.5) / (len(e) + 0.5))
            for i, tf in e: sc[i] = sc.get(i, 0.0) + idf * tf * (K1 + 1) / (tf + K1 * (1 - B + B * self.dlen[i] / self.avg))
        return sorted(sc, key=lambda i: -sc[i])[:POOL]
    def dense(self, qv):
        n = math.sqrt(sum(x * x for x in qv)); q = array("f", [x / n for x in qv])
        sc = [sum(map(mul, q, c)) for c in self.vec]
        return sorted(range(len(sc)), key=lambda i: -sc[i])[:POOL]
    def search(self, query, qvec=None, mode="hybrid", k=5, central_boost=0.0, other_penalty=0.0):
        lists = []
        if mode in ("bm25", "hybrid"): lists.append(self.bm25(query))
        if mode in ("dense", "hybrid"):
            if qvec is None: return {"error": "qvec required for dense/hybrid"}
            lists.append(self.dense(qvec))
        f = {}
        for L in lists:
            for r, i in enumerate(L): f[i] = f.get(i, 0.0) + 1.0 / (RRF_K + r + 1)
        if central_boost:
            for i in f: f[i] += central_boost * (3 - self.cards[i].get("central", 2)) / 2
        if other_penalty:
            for i in f:
                if self.cards[i].get("kind") == "other": f[i] -= other_penalty
        hits = []
        for r, i in enumerate(sorted(f, key=lambda i: -f[i])[:min(k, 20)]):
            c = self.cards[i]
            hits.append({"rank": r + 1, "card_id": c["card_id"], "name": c["name"], "doc_id": c["doc_id"], "doc_title": c["doc_title"], "pages": c.get("pages"),
                         "short_formula": c.get("short_formula", ""), "central": c.get("central"), "kind": c.get("kind"), "conflicts": bool(c.get("conflicts")),
                         "sources": [{"doc_id": s["doc_id"], "doc_title": s["doc_title"], "pages": s["pages"], "role": s["role"]} for s in c["sources"]], "score": round(f[i], 5)})
        return {"hits": hits}
def serve():
    b = Bank(json.loads(sys.stdin.readline())); print(json.dumps({"ready": len(b.cards)}), flush=True)
    for line in sys.stdin:
        r = json.loads(line); op = r.get("op")
        if op == "quit": break
        try:
            if op == "search": out = b.search(r["query"], r.get("qvec"), r.get("mode", "hybrid"), r.get("k", 5), r.get("central_boost", 0.0), r.get("other_penalty", 0.0))
            elif op == "get": out = b.cards[b.byid[r["card_id"]]]
            else: out = {"error": "bad op"}
        except Exception as e: out = {"error": str(e)[:200]}
        print(json.dumps(out), flush=True)
if __name__ == "__main__": serve()
