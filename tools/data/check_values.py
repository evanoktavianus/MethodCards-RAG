"""Value check: datatool.fetch_rows against the values the builder (experiments/data_blocks/data_blocks.py) shows, for the 440 active questions.
Run from the repository root:  python3 -I tools/data/check_values.py   (no key, no model call)
Part A (per question): every (series, year) cell in data_blocks.LAST[item]['needs'] for the item's subject economy.
Part B (grid): for each series code and each year any question uses, all non-aggregate economies the builder knows (covers the candidate tables of
'hidden' questions, which show many economies), plus the EU27 CPI cells, NGDPD 2024 and the world-growth inputs (NGDPRPPPPC, LP) with the world-growth formula.
Mapping: PSD:X -> psd:X period YYYYQ4; IIP:P_MV -> imf_iip:P_MV; X@F -> plain X (wdi); code with '.' -> wdi; otherwise imf_weo.
No model calls, no network. Writes check_values_report.json next to this file."""
import sys, os, json, math, collections
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = (__import__('os').environ.get('MC_ROOT') or __import__('os').path.abspath(__import__('os').path.join(__import__('os').path.dirname(__file__),'..','..'))) + '/'
REPO = BASE
sys.path[:0] = [HERE, REPO + 'experiments/data_blocks', REPO + 'experiments/prompts_data']
import datatool as dt
import data_blocks as db

def sid_of(code):
    if code.startswith('PSD:'): return 'psd:' + code[4:]
    if code.startswith('IIP:'): return 'imf_iip:' + code[4:]
    c = code.split('@')[0]
    return ('wdi:' if '.' in c else 'imf_weo:') + c

_cache = {}
def tool_val(code, iso, y):
    """tool value (float) or None; also returns None when the series is not served"""
    sid = sid_of(code)
    k = (sid, iso)
    if k not in _cache:
        try: _cache[k] = {r['period']: r['value'] for r in dt.fetch_rows(sid, iso, 1900, 2100)[1]}
        except ValueError as e: _cache[k] = e
    d = _cache[k]
    if isinstance(d, Exception): return 'ERR'
    return d.get(('%dQ4' % y) if code.startswith('PSD:') else str(y))

def classify(b, t):
    if b is None and t is None: return 'both_missing'
    if t == 'ERR': return 'unserved'
    if b is None: return 'tool_only'          # tool has a value, builder shows n/a
    if t is None: return 'builder_only'
    rel = abs(b - t) / max(abs(b), abs(t), 1e-300) if b != t else 0.0
    return 'exact' if rel < 1e-9 else ('small' if rel < 1e-6 else 'mismatch')

def main():
    ids = json.load(open(REPO + 'experiments/splits/hard.json'))['hard'] + json.load(open(REPO + 'experiments/splits/easier.json'))['easier']
    stats = collections.Counter(); by_code = collections.defaultdict(collections.Counter); examples = collections.defaultdict(list)
    unserved_items = {}; item_bad = collections.defaultdict(list); built = 0; nosubj = []; errs = {}
    uniq_cells = {}; years_by_code = collections.defaultdict(set); resolve_diff = {}
    for it in ids:
        try:
            _it, _d, _p, info = db.build(it); built += 1
        except Exception as e:
            errs[it] = '%s: %s' % (type(e).__name__, str(e)[:120]); continue
        L = db.LAST[it]; subj = info.get('subject')
        needs = L['needs']
        for c, ys in needs.items():
            years_by_code[c].update(ys)
            try:
                sid = sid_of(c); got, note = dt.resolve(sid)
                bare = c.split(':')[-1].split('@')[0]
                try: b, _ = dt.resolve(bare); resolve_diff[c] = (b if b != got else None)
                except ValueError: resolve_diff[c] = 'bare code not resolvable'
            except ValueError as e:
                unserved_items.setdefault(it, []).append('%s: %s' % (c, e)); continue
        if not subj:
            nosubj.append(it); continue
        for c, ys in needs.items():
            for y in ys:
                b = db.val(c, subj, y); t = tool_val(c, subj, y); k = classify(b, t)
                stats['A_' + k] += 1; by_code[c]['A_' + k] += 1
                if k in ('mismatch', 'small', 'builder_only', 'unserved', 'tool_only'):
                    item_bad[it].append((c, subj, y, b, t, k))
                    if len(examples[(c, k)]) < 3: examples[(c, k)].append((it, subj, y, b, t))
                uniq_cells[(c, subj, y)] = k
    # Part B grid
    gstats = collections.Counter(); gby = collections.defaultdict(collections.Counter); gex = collections.defaultdict(list)
    isos = db.countries()
    def grid(c, ys):
        for iso in isos:
            for y in ys:
                b = db.val(c, iso, y); t = tool_val(c, iso, y); k = classify(b, t)
                gstats[k] += 1; gby[c][k] += 1
                if k in ('mismatch', 'small', 'builder_only', 'unserved', 'tool_only') and len(gex[(c, k)]) < 3: gex[(c, k)].append((iso, y, b, t))
    for c, ys in sorted(years_by_code.items()): grid(c, sorted(ys))
    grid('NGDPD', [2024]); grid('PCPIPCH', sorted(set(years_by_code.get('PCPIPCH', set())) | {2018}))
    # world growth, same formula as data_blocks.world_growth but on tool values
    # the builder uses every economy in the WEO file that has both series (not only countries()); same universe here
    wg_t = {}
    W = {}
    for iso in list(db.rp.wide_csv('weo_oct2025_ngdprppppc.csv')):
        for y in range(1981, 2031):
            a, bb = tool_val('NGDPRPPPPC', iso, y), tool_val('LP', iso, y)
            if a not in (None, 'ERR') and bb not in (None, 'ERR') and iso in db.rp.wide_csv('weo_oct2025_lp.csv'): W[y] = W.get(y, 0) + a * bb
    for y in W:
        if y - 1 in W: wg_t[y] = round(100 * (W[y] / W[y - 1] - 1), 3)
    wg_ok = sum(1 for y in range(1982, 2031) if db.world_growth(y) == wg_t.get(y)); wg_n = len([y for y in range(1982, 2031) if db.world_growth(y) is not None])
    # the stored series imf_weo:WORLD_NGDP_RPCH (WLD) against the builder
    wg_s = {int(r['period']): r['value'] for r in dt.fetch_rows('imf_weo:WORLD_NGDP_RPCH', 'WLD', 1900, 2100)[1]}
    wg_sok = sum(1 for y in range(1982, 2031) if db.world_growth(y) is not None and wg_s.get(y) == db.world_growth(y))
    # report
    rep = dict(questions=len(ids), built=built, build_errors=errs, no_subject=nosubj, unserved_items=unserved_items,
               A_cells=sum(v for k, v in stats.items()), A=dict(stats), A_unique_cells=len(uniq_cells),
               A_by_code={c: dict(v) for c, v in by_code.items()}, B=dict(gstats), B_cells=sum(gstats.values()), B_by_code={c: dict(v) for c, v in gby.items()},
               world_growth=dict(years_equal=wg_ok, years_builder_has=wg_n, stored_series_years_equal=wg_sok),
               bare_code_resolves_to_other_source={c: v for c, v in resolve_diff.items() if v},
               items_with_a_difference={i: len(v) for i, v in item_bad.items()},
               examples_A={'%s|%s' % k: v for k, v in examples.items()}, examples_B={'%s|%s' % k: v for k, v in gex.items()})
    json.dump(rep, open(os.path.join(HERE, 'check_values_report.json'), 'w'), indent=1, default=str)
    print('questions', len(ids), 'built', built, 'build errors', len(errs), 'no subject economy', len(nosubj), 'with unresolvable series', len(unserved_items))
    print('PART A (subject cells in needs): total', rep['A_cells'], dict(stats), 'unique', len(uniq_cells))
    print('PART B (grid, all economies):    total', rep['B_cells'], dict(gstats))
    print('world growth years equal', wg_ok, 'of', wg_n, '; stored series imf_weo:WORLD_NGDP_RPCH equal', wg_sok, 'of', wg_n)
    print('questions with at least one differing subject cell (small/mismatch/builder_only/unserved/tool_only):', len(item_bad))
    print('--- Part A by code (non-trivial only)')
    for c, v in sorted(by_code.items()):
        if any(k in v for k in ('small', 'mismatch', 'builder_only', 'unserved', 'tool_only')) or True:
            print(' ', c, dict(v))
    print('--- Part B by code with differences')
    for c, v in sorted(gby.items()):
        if any(k in v for k in ('small', 'mismatch', 'builder_only', 'unserved', 'tool_only')): print(' ', c, dict(v))
    print('--- examples A'); [print(' ', k, v) for k, v in rep['examples_A'].items()]
    print('--- examples B'); [print(' ', k, v) for k, v in rep['examples_B'].items()]
    print('--- unserved items', unserved_items); print('--- build errors', errs); print('--- no subject', nosubj[:20], len(nosubj))
    print('--- bare code resolves elsewhere', rep['bare_code_resolves_to_other_source'])

if __name__ == '__main__':
    main()
