"""Export, read-only, standard library only. Run on the machine that holds the corpus database (PostgreSQL with pgvector).
It writes the files that tools/retrieval/local_docs.py needs, so that the document search and page reading of the Ours arms run without the database:

  chunks_M.jsonl   one line per searchable chunk (index M): {id, d: document id, s: struct type, p: page, q: sequence, b: breadcrumb, t: text}
  chunk_vectors.f32  the 1536-d embedding of each chunk of chunks_M.jsonl, float32, same order
  bm25_global.json  N, total_dlen and df of every term that occurs in an index-M chunk, counted over ALL chunks of the corpus, as the original engine did
  istbl.json        ids of table chunks of the three Fiscal Monitor documents (hidden for most questions)
  check.json        counts and token sums used by local_docs.py to verify the export

Index M = every chunk of core and global documents and of the documents listed in method_docs27.txt (the documents that state an evaluated method), plus annex / box / technical_note chunks of other country documents; documents in params.json "excluded" are left out.
Usage:  python3 export_corpus_from_postgres.py params.json OUTDIR      (env MC_PG_DB = database name, default methodcards)
The original engine (search_server.py) tokenised the text in PostgreSQL COPY text format (tab, newline, backslash escaped); this script does the same on purpose.
"""
import array, json, os, re, sqlite3, subprocess, sys

DB = os.environ.get('MC_PG_DB', 'methodcards')
TABLES = ['document_chunks_w_026c434aff56410f9b83f6559000f73c', 'document_chunks_w_08f70ca9ed844baba08d115429884a28']
STOP = set("a an and are as at be by for from has have in is it its of on or that the this to was were which with their they these those such than then there can may also not but if into per via".split())
TOK = re.compile(r"[a-z0-9]+")
ESC = str.maketrans({'\\': '\\\\', '\b': '\\b', '\f': '\\f', '\n': '\\n', '\r': '\\r', '\t': '\\t', '\v': '\\v'})


def toks(t):
    out = []
    for w in TOK.findall(t.lower()):
        if w in STOP or len(w) < 2:
            continue
        if len(w) > 4 and w.endswith('ies'):
            w = w[:-3] + 'y'
        elif len(w) > 3 and w.endswith('s') and not w.endswith('ss'):
            w = w[:-1]
        out.append(w)
    return out


def psql_stream(sql):
    p = subprocess.Popen(['sudo', '-n', '-u', 'postgres', 'psql', '-At', '-F', '|', '-d', DB, '-f', '-'], stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, text=True, errors='replace', bufsize=1 << 20)
    p.stdin.write(sql)
    p.stdin.close()
    return p


def main():
    params = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    os.makedirs(out, exist_ok=True)
    CLS, EXC, FM = params['class'], set(params['excluded']), set(params['fm_ids'])
    cg = [d for d, c in CLS.items() if c in ('core', 'global') and d not in EXC]
    cy = [d for d, c in CLS.items() if c == 'country' and d not in EXC]
    FULL = set(l.strip() for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'method_docs27.txt')) if l.strip())
    cg = cg + [d for d in cy if d in FULL]      # every chunk of a document that states an evaluated method
    cy = [d for d in cy if d not in FULL]
    q = lambda xs: ','.join("'%s'" % x for x in xs)
    where = "(document_id in (%s) or (document_id in (%s) and struct_type in ('annex','box','technical_note')))" % (q(cg), q(cy))

    # pass 1: statistics over ALL chunks, exactly as search_server.Engine loaded them
    N = tot = 0
    df = {}
    order = []
    sumM = 0
    for T in TABLES:
        sql = ("copy (select id, document_id, coalesce(struct_type,''), coalesce(page_start,0), coalesce(sequence,0), "
               "coalesce(breadcrumb,'')||' '||coalesce(content,'') from %s) to stdout;" % T)
        p = psql_stream(sql)
        for line in p.stdout:
            a = line.rstrip('\n').split('\t', 5)
            if len(a) < 6:
                continue
            d = a[1]
            if d not in CLS or d in EXC:
                continue
            tk = toks(a[5])
            N += 1
            tot += len(tk)
            for w in set(tk):
                df[w] = df.get(w, 0) + 1
            if CLS[d] in ('core', 'global') or d in FULL or a[2] in ('annex', 'box', 'technical_note'):
                order.append(a[0])
                sumM += len(tk)
        p.wait()
    print('pass 1: N=%d total_dlen=%d M chunks=%d sum_dlen_M=%d terms=%d' % (N, tot, len(order), sumM, len(df)), flush=True)

    # pass 2 and 3: text and vectors of the index-M chunks into a temporary sqlite file
    tmp = os.path.join(out, '_tmp.sqlite')
    if os.path.exists(tmp):
        os.remove(tmp)
    db = sqlite3.connect(tmp)
    db.execute('create table c (id text primary key, j text, v blob)')
    for T in TABLES:
        sql = ("select json_build_object('id',id,'d',document_id,'s',coalesce(struct_type,''),'p',coalesce(page_start,0),'q',coalesce(sequence,0),"
               "'b',coalesce(breadcrumb,''),'t',coalesce(content,''))::text from %s where %s;" % (T, where))
        p = psql_stream(sql)
        db.executemany('insert or replace into c (id, j) values (?, ?)', (((lambda s: (json.loads(s)['id'], s))(l.rstrip('\n'))) for l in p.stdout if l.strip()))
        p.wait()
        db.commit()
        sql = "select id || '|' || embedding::text from %s where %s and embedding is not null;" % (T, where)
        p = psql_stream(sql)
        batch = []
        for l in p.stdout:
            i, v = l.rstrip('\n').split('|', 1)
            batch.append((array.array('f', json.loads(v)).tobytes(), i))
            if len(batch) >= 2000:
                db.executemany('update c set v=? where id=?', batch)
                batch = []
        db.executemany('update c set v=? where id=?', batch)
        p.wait()
        db.commit()
    print('pass 2/3 done', db.execute('select count(*), sum(v is not null) from c').fetchone(), flush=True)

    # write the files in the engine's original chunk order; verify the escape rule against pass 1
    terms = set()
    sum_local = 0
    nv = 0
    with open(os.path.join(out, 'chunks_M.jsonl'), 'w', encoding='utf-8') as fj, open(os.path.join(out, 'chunk_vectors.f32'), 'wb') as fv:
        for i in order:
            r = db.execute('select j, v from c where id=?', (i,)).fetchone()
            if r is None or r[1] is None:
                raise SystemExit('missing chunk or vector: ' + i)
            o = json.loads(r[0])
            tk = toks((o['b'] + ' ' + o['t']).translate(ESC))
            sum_local += len(tk)
            terms.update(tk)
            fj.write(json.dumps(o, ensure_ascii=False, separators=(',', ':')) + '\n')
            fv.write(r[1])
            nv += 1
    ok = (sum_local == sumM)
    print('verify: sum_dlen_M pass1=%d local=%d  %s' % (sumM, sum_local, 'OK' if ok else 'MISMATCH'), flush=True)
    json.dump({'N': N, 'total_dlen': tot, 'df': {w: df[w] for w in terms if w in df}}, open(os.path.join(out, 'bm25_global.json'), 'w'))

    # table chunks of the Fiscal Monitor documents
    sql = ("select c.id from %s c join chunk_blocks cb on cb.chunk_id=c.id join document_blocks b on b.id=cb.block_id "
           "where b.type='table' and c.document_id in (%s);" % (TABLES[0], q(sorted(FM))))
    p = psql_stream(sql)
    ids = set(p.stdout.read().split())
    p.wait()
    json.dump(sorted(i for i in ids if i in set(order)), open(os.path.join(out, 'istbl.json'), 'w'))
    json.dump({'N': N, 'total_dlen': tot, 'n_M': len(order), 'sum_dlen_M': sumM, 'sum_dlen_M_local_escape': sum_local, 'escape_rule_ok': ok,
               'dim': 1536, 'n_vectors': nv}, open(os.path.join(out, 'check.json'), 'w'))
    db.close()
    os.remove(tmp)
    print('written to', out, flush=True)


if __name__ == '__main__':
    main()
