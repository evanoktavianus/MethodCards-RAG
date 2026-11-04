"""Export, read-only, standard library only. Writes the vectors of the method cards (table method_cards.cards_512) in card order:
  card_vectors_final.f32   float32, n_cards x 1536, row i = card with idx i
  card_ids.json            card_id of each row (compare with tools/bank/cards_final.jsonl)
Usage:  MC_PG_DB=<database> python3 export_cards_from_postgres.py OUTDIR"""
import array, json, os, subprocess, sys
DB = os.environ.get('MC_PG_DB', 'methodcards')
out = sys.argv[1]
os.makedirs(out, exist_ok=True)
sql = "select idx || '|' || card_id || '|' || emb::text from method_cards.cards_512 order by idx;"
p = subprocess.Popen(['sudo', '-n', '-u', 'postgres', 'psql', '-At', '-d', DB, '-f', '-'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
p.stdin.write(sql); p.stdin.close()
ids = []
with open(os.path.join(out, 'card_vectors_final.f32'), 'wb') as f:
    for l in p.stdout:
        i, cid, v = l.rstrip('\n').split('|', 2)
        assert int(i) == len(ids)
        vec = json.loads(v)
        assert len(vec) == 1536
        f.write(array.array('f', vec).tobytes())
        ids.append(cid)
p.wait()
json.dump(ids, open(os.path.join(out, 'card_ids.json'), 'w'))
print('cards', len(ids))
