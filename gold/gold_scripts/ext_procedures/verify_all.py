import sys, os, glob, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
cnt = {}
for slug in ('income_group_atlas', 'convergence_criteria', 'reserve_adequacy_traditional'):
    for f in sorted(glob.glob(os.path.join(ROOT, 'dataset/items', slug, '*.json'))):
        d = json.load(open(f)); cnt.setdefault((slug, d['style'], d['validation_label']), 0); cnt[(slug, d['style'], d['validation_label'])] += 1
        assert d['hidden_set_size'] in (1, None) and (d['style'] != 'hidden' or d['hidden_set_size'] == 1), (f, d['style'], d['hidden_set_size'])
        assert all(c['importance'] == 'vital' for c in d['claims']['computation'])
        assert 'Maastricht' not in d['query'] and 'Atlas' not in d['query'] and 'Greenspan' not in d['query']
print(cnt)
