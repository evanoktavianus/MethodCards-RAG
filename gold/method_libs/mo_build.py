# Builds items for the monetary_other cluster (income_velocity VEL-, real_interest_rate RIR-, real_depreciation RDEP-).
# Run: python3 -I scripts/mo_build.py   (from the gold/ directory). Golds come only from frozen_extra/wdi_20261008_monetary_other.psv.
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mo_lib as m
AG = {'WLD','EUU','EMU','ARB','CEB','EAP','EAR','EAS','ECA','ECS','FCS','HIC','HPC','IBD','IBT','IDA','IDB','IDX','LAC','LCN','LDC','LIC','LMC','LMY','LTE','MEA','MIC','MNA','NAC','OED','OSS','PRE','PSS','PST','SAS','SSA','SSF','SST','TEA','TEC','TLA','TMN','TSA','TSS','UMC','AFE','AFW','INX'}
NAME = {'AGO':'Angola','BRA':'Brazil','IND':'India','KEN':'Kenya','JPN':'Japan','HKG':'Hong Kong SAR','MAC':'Macao SAR','ZWE':'Zimbabwe','SDN':'Sudan','PHL':'the Philippines','GBR':'the United Kingdom',
        'MDG':'Madagascar','HUN':'Hungary','NGA':'Nigeria','GMB':'The Gambia','COD':'the Democratic Republic of the Congo','IDN':'Indonesia','ZAF':'South Africa','MEX':'Mexico','PER':'Peru','THA':'Thailand',
        'TUR':'Turkey','ARG':'Argentina','EGY':'Egypt','PAK':'Pakistan','GHA':'Ghana','LKA':'Sri Lanka','ZMB':'Zambia','NGA ':'Nigeria','UKR':'Ukraine','ETH':'Ethiopia','MWI':'Malawi','RUS':'Russia','KAZ':'Kazakhstan','SLE':'Sierra Leone'}
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'items')
GOLD = 'scripts/mo_build.py'
def countries(code, y): return [i for i in m.D[code] if i not in AG and m.g(code, i, y) is not None]
def hidden_set(cond, y, codes):
    return sorted(i for i in countries(codes[0], y) if cond(i))
def claim_text(text, accept):
    return {'id': 'c1', 'kind': 'text', 'importance': 'vital', 'text': text, 'accept': accept}
def write(method, n, style, query, ctext, caccept, comp, ans, data_req, doc_ids, doc_cite, inputs, published, recomputed, tol, subject, distractors, famous, note, hidden_info=None, claim_truth=None, label_formula=''):
    iid = '%s-%02d' % (PFX[method], n)
    it = {'id': iid, 'family': 'methodology', 'pattern': {'named':'M-named','hidden':'M-hidden','claim_check':'M-claim'}[style], 'tier': 'analytical', 'status': 'validated',
          'query': query,
          'claims': {'text': [claim_text(ctext, caccept)],
                     'data': [{'id': 'c2', 'kind': 'data', 'importance': 'okay', 'text': 'Retrieves the input series: ' + ', '.join(i['indicator'] for i in data_req) + '.', 'accept': 'full = all inputs retrieved with values close to the frozen ones; partial = some; no = none.', 'requires': data_req}],
                     'computation': [comp], 'answer': [ans]},
          'grading': {'method': 'claim_recall', 'tolerance': tol, 'note': note},
          'provenance': {'assembled_from': ['WDI 2026-10-08 (frozen_extra/wdi_20261008_monetary_other.psv)'], 'gold_script': GOLD, 'validation': label_formula, 'published_value_source': 'see published_value_note'},
          'method': method, 'validation_label': 'formula-validated', 'method_kind': 'textbook identity',
          'method_doc_ids': doc_ids, 'method_doc_cite': doc_cite, 'gold_report_ids': [],
          'published_value': published[0], 'published_value_note': published[1], 'recomputed_value': recomputed, 'tolerance': tol, 'inputs': inputs,
          'style': style, 'subject': subject, 'distractors': distractors, 'famous_method': famous, 'gold_script': GOLD}
    if hidden_info: it['hidden_condition'] = hidden_info
    if claim_truth is not None: it['claim_truth'] = claim_truth
    os.makedirs(os.path.join(ROOT, method), exist_ok=True)
    json.dump(it, open(os.path.join(ROOT, method, iid + '.json'), 'w'), indent=1, ensure_ascii=False)
    return it
PFX = {'income_velocity': 'VEL', 'real_interest_rate': 'RIR', 'real_depreciation': 'RDEP'}
def req(code, src, iso, y0, y1): return {'indicator': code, 'source': src, 'iso3': iso, 'years': [y0, y1]}
def comp(cid, text, val, unit, tol, statistic, accept):
    return {'id': cid, 'kind': 'computation', 'importance': 'vital', 'text': text, 'accept': accept, 'statistic': statistic,
            'resolves': {'value': round(val, 3), 'targets': [{'name': 'value', 'kind': 'number', 'value': round(val, 3), 'unit': unit, 'tolerance': tol, 'tolerance_source': 'identity recomputed from frozen WDI; rounding and vintage'}]}}
def ans(cid, text, accept, value): return {'id': cid, 'kind': 'answer', 'importance': 'vital', 'text': text, 'accept': accept, 'value': value}
report = []

# ---------------- 1. INCOME VELOCITY ----------------
VM = 'income_velocity'
V_DOC = ['eafc73b3-c1d9-4b2c-bc09-4d9d7bd6297a']
V_CITE = 'WEO April 1985, p.130 (Chart 2-2): "Narrow and Broad Money Velocity (Quarterly GNP at annual rates/average stock of money during quarter)"; p.131-132 relate target money growth to expected nominal GDP growth to get the implied change in velocity.'
V_DIST = ['Money multiplier / reserve-money analysis', 'Financial depth ratio read on its own (M2 to GDP) without turning it into turnover', 'Seigniorage or inflation-tax revenue', 'Real money demand regression', 'Credit-to-GDP gap']
V_TEXT = 'Identifies the applicable approach: income velocity of money, i.e. nominal GDP divided by the broad money stock (equivalently 100 divided by broad money as a percent of GDP); change over time = nominal income growth relative to money growth.'
V_ACC = 'full = names income velocity / GDP-to-broad-money turnover and uses nominal GDP over M2; partial = reports only M2/GDP without the inversion; no = unrelated approach (money multiplier, seigniorage, credit gap).'
def v_data(iso, y0, y1): return [req('NY.GDP.MKTP.CN', 'WDI', iso, y0, y1), req('FM.LBL.BMNY.CN', 'WDI', iso, y0, y1)]
V_IN = ['NY.GDP.MKTP.CN', 'FM.LBL.BMNY.CN', 'FM.LBL.BMNY.GD.ZS']
def vel_item(n, style, iso, kind, y0, y1, q, hidden_info=None, stmt=None, truth=None):
    if kind == 'level':
        val = m.velocity(iso, y1); pub = 100 / m.g('FM.LBL.BMNY.GD.ZS', iso, y1); unit = 'turns per year'; tol = round(max(0.03, 0.03 * val), 3)
        c = comp('c3', 'Income velocity of broad money in %d is about %.2f (GDP divided by broad money).' % (y1, val), val, unit, tol, 'V = NY.GDP.MKTP.CN / FM.LBL.BMNY.CN', 'full = within +/-3 percent of %.3f; partial = within +/-10 percent; no = otherwise.' % val)
        a = ans('c4', 'Each unit of broad money supports about %.2f units of annual nominal income (broad money is %.0f percent of GDP).' % (val, 100 / val), 'full = turnover of about %.1f; no = otherwise.' % val, round(val, 2))
        pn = 'Derived from the published WDI series FM.LBL.BMNY.GD.ZS: 100 / (M2 as percent of GDP) = %.3f' % pub
    else:
        val = m.velocity_change(iso, y0, y1); pub = None; unit = 'percent'; tol = 1.0
        a0, b0 = m.velocity(iso, y0), m.velocity(iso, y1)
        c = comp('c3', 'Income velocity changes by about %.1f percent between %d and %d (from %.3f to %.3f).' % (val, y0, y1, a0, b0), val, unit, tol, '100*(V_y1/V_y0 - 1), V = NY.GDP.MKTP.CN / FM.LBL.BMNY.CN', 'full = within +/-1.0 percentage point of %.2f; partial = within +/-3 points; no = otherwise.' % val)
        a = ans('c4', 'Velocity %s (broad money %s nominal income).' % ('rose' if val > 0 else 'fell', 'grew slower than' if val > 0 else 'grew faster than'), 'full = correct direction; no = wrong direction.', 'rose' if val > 0 else 'fell')
        pn = 'Not published as a figure; direction cross-checked against WDI FM.LBL.BMNY.GD.ZS ratio change.'
        # cross-check with published ratio
        r0, r1 = m.g('FM.LBL.BMNY.GD.ZS', iso, y0), m.g('FM.LBL.BMNY.GD.ZS', iso, y1)
        assert r0 and r1 and abs(100 * (r0 / r1 - 1) - val) < 0.5, (iso, val, r0, r1)
        pub = round(100 * (r0 / r1 - 1), 3); pn = 'Derived from published WDI FM.LBL.BMNY.GD.ZS: 100*(ratio_y0/ratio_y1 - 1) = %.3f' % pub
    it = write(VM, n, style, q, V_TEXT, V_ACC, c, a, v_data(iso, y0 if kind != 'level' else y1 - 2, y1), V_DOC, V_CITE, V_IN, (pub, pn), round(val, 3), tol,
               {'iso3': iso, 'kind': kind, 'year0': y0, 'year1': y1}, V_DIST, False,
               'Definition: velocity = nominal GDP / broad money (both LCU). Tolerance 3 percent of level, 1.0 pp for changes.', hidden_info, truth,
               'recompute with scripts/mo_build.py; WDI ratio consistency checked on 8,360 country-years, 0 mismatches above 0.5')
    return it, val
vel_specs = []
# named
vel_item(1, 'named', 'BRA', 'level', 2019, 2019, 'In 2019, how many units of annual nominal GDP did each unit of Brazil\'s broad money stock support?')
vel_item(2, 'named', 'IND', 'level', 2018, 2018, 'In 2018, how much nominal GDP did India generate per rupee of broad money outstanding?')
vel_item(3, 'named', 'KEN', 'change', 2015, 2019, 'Between 2015 and 2019, did Kenya\'s economy get more or less nominal income out of each shilling of broad money, and by what percentage did that ratio change?')
vel_item(4, 'named', 'JPN', 'change', 2010, 2020, 'Over 2010 to 2020, how did the amount of nominal GDP supported by each yen of broad money change in Japan, in percent?')
# hidden
hid = []
s = hidden_set(lambda i: m.g('FM.LBL.BMNY.GD.ZS', i, 2019) > 400, 2019, ['FM.LBL.BMNY.GD.ZS']); assert s == ['HKG'], s
vel_item(5, 'hidden', 'HKG', 'level', 2019, 2019, 'Exactly one economy had broad money above 400 percent of its GDP in 2019. How many units of annual nominal income did each unit of that economy\'s broad money support in that year?', {'condition': 'FM.LBL.BMNY.GD.ZS (2019) > 400', 'year': 2019, 'set': s})
s = hidden_set(lambda i: 275 < m.g('FM.LBL.BMNY.GD.ZS', i, 2021) < 400, 2021, ['FM.LBL.BMNY.GD.ZS']); assert s == ['MAC'], s
vel_item(6, 'hidden', 'MAC', 'level', 2021, 2021, 'In 2021 only one economy had broad money between 275 and 400 percent of GDP. For that economy, what was nominal GDP per unit of broad money in 2021?', {'condition': '275 < FM.LBL.BMNY.GD.ZS (2021) < 400', 'year': 2021, 'set': s})
s = hidden_set(lambda i: m.g('FM.LBL.BMNY.GD.ZS', i, 2019) < 11, 2019, ['FM.LBL.BMNY.GD.ZS']); assert s == ['ZWE'], s
vel_item(7, 'hidden', 'ZWE', 'level', 2019, 2019, 'One economy had broad money below 11 percent of GDP in 2019. How many units of annual nominal income did each unit of its broad money support that year?', {'condition': 'FM.LBL.BMNY.GD.ZS (2019) < 11', 'year': 2019, 'set': s})
s = hidden_set(lambda i: m.g('FM.LBL.BMNY.ZG', i, 2018) > 100, 2018, ['FM.LBL.BMNY.ZG']); assert s == ['SDN'], s
vel_item(8, 'hidden', 'SDN', 'change', 2017, 2018, 'In 2018 exactly one country saw broad money grow by more than 100 percent. In that country, did nominal income per unit of broad money rise or fall from 2017 to 2018, and by what percentage?', {'condition': 'FM.LBL.BMNY.ZG (2018) > 100', 'year': 2018, 'set': s})
# claim checks: PHL 2018 true, GBR 2019 false
for n, iso, y, factor, truth in ((9, 'PHL', 2018, 1.0, True), (10, 'GBR', 2019, 1.0, False)):
    v = m.velocity(iso, y)
    stated = round(v, 2) if truth else round(v * 1.45, 2)
    q = 'A staff paper states that in %d each unit of broad money in %s supported about %.2f units of annual nominal GDP. Does that hold up against the data?' % (y, NAME[iso], stated)
    it, val = vel_item(n, 'claim_check', iso, 'level', y, y, q, None, None, truth)
    assert (abs(stated - val) <= max(0.03, 0.03 * val)) == truth, (iso, stated, val)
    it['claim_stated'] = stated
    it['claims']['answer'] = [ans('c4', 'The statement is %s on the recomputed value (%s).' % ('true' if truth else 'false', 'recomputed %.3f' % it['recomputed_value']), 'full = verdict %s; no = opposite verdict.' % ('true' if truth else 'false'), 'true' if truth else 'false')]
    json.dump(it, open(os.path.join(ROOT, VM, it['id'] + '.json'), 'w'), indent=1, ensure_ascii=False)

# ---------------- 2. REAL INTEREST RATE ----------------
RM = 'real_interest_rate'
R_DOC = ['0343a0da-0a3a-4e01-8b5c-408816ccb412']
R_CITE = 'AMRO 2023 Annual Consultation Report on Japan, p.65 (Annex 4, note): "short-term real interest rates are calculated by subtracting ... actual inflation rates from the ... rates". Exact form used by WDI (FR.INR.RINR): (i - pi)/(1 + pi), pi = GDP deflator inflation.'
R_DIST = ['Neutral/natural rate estimation (HLW-type model)', 'Taylor-rule prescription', 'Debt-dynamics interest-growth differential', 'Effective interest rate on public debt', 'Policy-rate stance read in nominal terms']
R_TEXT = 'Identifies the applicable approach: ex post real interest rate, the nominal lending rate deflated by inflation (GDP deflator), r = (i - pi)/(1 + pi) or approximately i - pi.'
R_ACC = 'full = deflates the nominal lending rate by GDP-deflator (or economy-wide) inflation; partial = deflates with CPI inflation or reports the nominal rate only; no = unrelated method (natural rate model, Taylor rule).'
R_IN = ['FR.INR.LEND', 'NY.GDP.DEFL.KD.ZG', 'FR.INR.RINR']
def rr_item(n, style, iso, y, q, hidden_info=None, truth=None, stated=None):
    val = m.real_rate(iso, y); simple = m.real_rate_simple(iso, y); pub = m.g('FR.INR.RINR', iso, y)
    assert abs(val - pub) < 0.05, (iso, y, val, pub)
    tol = max(1.5, round(abs(val - simple) + 0.3, 1))
    i, p = m.g('FR.INR.LEND', iso, y), m.g('NY.GDP.DEFL.KD.ZG', iso, y)
    c = comp('c3', 'The real lending rate in %d is about %.1f percent (lending rate %.1f percent deflated by GDP-deflator inflation %.1f percent).' % (y, val, i, p), val, 'percent', tol, 'r = (FR.INR.LEND - NY.GDP.DEFL.KD.ZG) / (1 + NY.GDP.DEFL.KD.ZG/100)', 'full = within +/-%.1f percentage points of %.2f (the simple difference i - pi = %.2f is therefore also accepted); partial = within +/-3 more; no = otherwise.' % (tol, val, simple))
    sign = 'positive' if val > 0 else 'negative'
    a = ans('c4', 'The real return/cost is %s (borrowers face a %s real rate).' % (sign, 'positive' if val > 0 else 'negative'), 'full = correct sign; no = wrong sign.', sign)
    return write(RM, n, style, q, R_TEXT, R_ACC, c, a, [req('FR.INR.LEND', 'WDI', iso, y, y), req('NY.GDP.DEFL.KD.ZG', 'WDI', iso, y, y)], R_DOC, R_CITE, R_IN,
                 (round(pub, 3), 'WDI FR.INR.RINR (real interest rate, %), published by the World Bank; recomputed identity matches to 0.05 on 4,771 country-years'), round(val, 3), tol,
                 {'iso3': iso, 'year': y, 'lending_rate': i, 'deflator_inflation': p, 'simple_difference': round(simple, 3)}, R_DIST, False,
                 'Definition: r = (i - pi)/(1+pi) with pi = GDP deflator inflation. Tolerance = max(1.5, |exact - simple difference| + 0.3) pp so that both forms are accepted.', hidden_info, truth, 'identity reproduces WDI FR.INR.RINR')
rr_item(1, 'named', 'MEX', 2019, 'Adjusted for the rise in the economy-wide price level, what did bank borrowing cost firms and households in Mexico in 2019?')
rr_item(2, 'named', 'IDN', 2019, 'After stripping out price inflation, what interest rate did borrowers from banks in Indonesia actually pay in 2019?')
rr_item(3, 'named', 'PER', 2019, 'Did commercial bank credit in Peru carry a positive or negative return in inflation-adjusted terms in 2019, and how large was it?')
rr_item(4, 'named', 'ZAF', 2018, 'Allowing for the rise in prices, how expensive was commercial bank borrowing in South Africa in 2018?')
def hs(cond, y): return hidden_set(cond, y, ['FR.INR.LEND', 'NY.GDP.DEFL.KD.ZG', 'FR.INR.RINR'])
for n, iso, y, cond, txt, qtxt in (
    (5, 'BRA', 2019, lambda i: m.g('FR.INR.LEND', i, 2019) > 30 and m.g('NY.GDP.DEFL.KD.ZG', i, 2019) < 5, 'FR.INR.LEND (2019) > 30 and NY.GDP.DEFL.KD.ZG (2019) < 5', 'In 2019 exactly one country combined a bank lending rate above 30 percent with GDP-deflator inflation below 5 percent. After allowing for price inflation, what did borrowing cost there that year?'),
    (6, 'COD', 2019, lambda i: m.g('FR.INR.LEND', i, 2019) > 25 and m.g('NY.GDP.DEFL.KD.ZG', i, 2019) < 2, 'FR.INR.LEND (2019) > 25 and NY.GDP.DEFL.KD.ZG (2019) < 2', 'Only one country had a bank lending rate above 25 percent together with GDP-deflator inflation under 2 percent in 2019. What inflation-adjusted rate did its borrowers face?'),
    (7, 'HUN', 2019, lambda i: m.g('FR.INR.LEND', i, 2019) < 2, 'FR.INR.LEND (2019) < 2', 'One country reported a bank lending rate below 2 percent in 2019. Adjusted for inflation, was borrowing there cheap or did it pay borrowers, and by how much?'),
    (8, 'MDG', 2022, lambda i: m.g('FR.INR.LEND', i, 2022) >= 40 and m.g('NY.GDP.DEFL.KD.ZG', i, 2022) < 15, 'FR.INR.LEND (2022) >= 40 and NY.GDP.DEFL.KD.ZG (2022) < 15', 'In 2022 exactly one country had a lending rate of at least 40 percent while GDP-deflator inflation stayed below 15 percent. What was the inflation-adjusted cost of borrowing there?')):
    s_ = hs(cond, y); assert s_ == [iso], (n, s_)
    rr_item(n, 'hidden', iso, y, qtxt, {'condition': txt, 'year': y, 'set': s_})
for n, iso, y, truth in ((9, 'COD', 2018, True), (10, 'KEN', 2019, False)):
    pass
def hs(cond, y): return hidden_set(cond, y, ['FR.INR.LEND', 'NY.GDP.DEFL.KD.ZG', 'FR.INR.RINR'])
# RIR claim checks
for n, iso, y, truth in ((9, 'PHL', 2018, True), (10, 'THA', 2019, False)):
    v = m.real_rate(iso, y)
    stated = round(v, 1) if truth else round(v + 6.0, 1)
    q = 'A report says that in %d bank borrowers in %s faced an inflation-adjusted interest rate of roughly %.1f percent. Is that consistent with the data?' % (y, NAME[iso], stated)
    it = rr_item(n, 'claim_check', iso, y, q, None, truth)
    assert (abs(stated - v) <= it['tolerance']) == truth
    it['claim_stated'] = stated
    it['claims']['answer'] = [ans('c4', 'The statement is %s on the recomputed value (%s).' % ('true' if truth else 'false', 'recomputed %.3f' % it['recomputed_value']), 'full = verdict %s; no = opposite verdict.' % ('true' if truth else 'false'), 'true' if truth else 'false')]
    json.dump(it, open(os.path.join(ROOT, RM, it['id'] + '.json'), 'w'), indent=1, ensure_ascii=False)

# ---------------- 3. REAL DEPRECIATION (against the US dollar) ----------------
DM = 'real_depreciation'
D_DOC = ['9879c7bb-835e-4738-bfd1-ce12867b8b24', 'e946326c-0415-4219-86ed-95f755ac9043']
D_CITE = 'Russian Federation 2004 Article IV staff report p.33 (footnote 7/) and Slovak Republic 2004 Article IV staff report p.34 (footnote 8/): "Real depreciation is defined as nominal depreciation (measured by percentage fall in dollar value of local currency) minus domestic inflation (based on GDP deflator)".'
D_DIST = ['Real effective exchange rate (trade-weighted, CPI-based)', 'Exchange-market-pressure index', 'External Balance Assessment REER gap', 'Nominal depreciation read on its own', 'Pass-through of depreciation to inflation']
D_TEXT = 'Identifies the applicable approach: real depreciation against the US dollar defined as nominal depreciation (percentage fall in the dollar value of the local currency, 1 - E_{t-1}/E_t with E in local currency per dollar) minus domestic GDP-deflator inflation.'
D_ACC = 'full = nets GDP-deflator inflation out of the nominal fall in the currency\'s dollar value; partial = nets out CPI inflation or computes nominal depreciation as E_t/E_{t-1}-1 with the right netting; no = reports nominal change only or a trade-weighted REER.'
D_IN = ['PA.NUS.FCRF', 'NY.GDP.DEFL.KD.ZG']
def rd_item(n, style, iso, y, q, hidden_info=None, truth=None):
    nd = m.nominal_dep(iso, y); p = m.g('NY.GDP.DEFL.KD.ZG', iso, y); val = nd - p
    c = comp('c3', 'Real depreciation in %d is about %.1f percent (nominal fall in dollar value %.1f percent minus GDP-deflator inflation %.1f percent).' % (y, val, nd, p), val, 'percent', 1.0, 'rd = 100*(1 - E_t-1/E_t) - NY.GDP.DEFL.KD.ZG; E = PA.NUS.FCRF', 'full = within +/-1.0 percentage point of %.2f; partial = within +/-3; no = otherwise.' % val)
    word = 'depreciation' if val > 0 else 'appreciation'
    a = ans('c4', 'In real terms against the dollar the currency recorded a %s (value %.1f).' % (word, val), 'full = correct direction (positive = depreciation, negative = appreciation); no = wrong direction.', word)
    return write(DM, n, style, q, D_TEXT, D_ACC, c, a, [req('PA.NUS.FCRF', 'WDI', iso, y - 1, y), req('NY.GDP.DEFL.KD.ZG', 'WDI', iso, y, y)], D_DOC, D_CITE, D_IN,
                 (None, 'No published country figure matched (the footnoted definition appears in external-sustainability tables of the two reports; those use own country-year data).'), round(val, 3), 1.0,
                 {'iso3': iso, 'year': y, 'nominal_depreciation': round(nd, 3), 'deflator_inflation': p}, D_DIST, False,
                 'Definition per the document footnote: nominal depreciation = percentage fall in dollar value of local currency = 100*(1 - E_{t-1}/E_t). Positive = real depreciation. Alternative convention (E_t/E_{t-1}-1) gives different numbers and is only partial credit.',
                 hidden_info, truth, 'definition from two staff reports; inputs public WDI')
rd_item(1, 'named', 'TUR', 2018, 'By how much did Turkey\'s currency lose value against the dollar in 2018 once domestic price increases are taken into account?')
rd_item(2, 'named', 'ZMB', 2019, 'Adjusting for domestic inflation, how much weaker was Zambia\'s currency against the US dollar in 2019?')
rd_item(3, 'named', 'PAK', 2019, 'Was the Pakistani rupee weaker or stronger against the dollar in 2019 after allowing for domestic price inflation, and by how many percent?')
rd_item(4, 'named', 'EGY', 2023, 'Net of domestic inflation, how far did Egypt\'s currency fall against the dollar in 2023?')
def ratio(i, y): return m.g('PA.NUS.FCRF', i, y) / m.g('PA.NUS.FCRF', i, y - 1)
def hd(cond, y): return sorted(i for i in m.D['PA.NUS.FCRF'] if i not in AG and m.g('PA.NUS.FCRF', i, y) and m.g('PA.NUS.FCRF', i, y - 1) and m.g('NY.GDP.DEFL.KD.ZG', i, y) is not None and cond(ratio(i, y)))
for n, iso, y, lo, hi, txt, qtxt in (
    (5, 'SDN', 2018, 2.0, 99, 'PA.NUS.FCRF(2018)/PA.NUS.FCRF(2017) > 2', 'In 2018 exactly one country saw its official exchange rate (local currency per dollar) more than double. Allowing for domestic price inflation, how much did its currency lose against the dollar?'),
    (6, 'SYR', 2016, 1.9, 99, 'PA.NUS.FCRF(2016)/PA.NUS.FCRF(2015) > 1.9', 'In 2016 only one country\'s official exchange rate (local currency per US dollar) rose by more than 90 percent. Net of its domestic inflation, what was the currency\'s decline against the dollar?'),
    (7, 'ARG', 2023, 2.0, 4.0, '2.0 < PA.NUS.FCRF(2023)/PA.NUS.FCRF(2022) < 4.0', 'In 2023 exactly one country had an official exchange rate that rose between 100 and 300 percent over the year. After allowing for its domestic inflation, was the currency weaker or stronger against the dollar, and by how much?'),
    (8, 'SUR', 2021, 1.9, 2.1, '1.9 < PA.NUS.FCRF(2021)/PA.NUS.FCRF(2020) < 2.1', 'Exactly one country saw its official exchange rate roughly double (up 90 to 110 percent) in 2021. Adjusting for domestic inflation, what happened to the value of its currency against the dollar?')):
    s_ = hd(lambda r, lo=lo, hi=hi: lo < r < hi, y); assert s_ == [iso], (n, s_)
    rd_item(n, 'hidden', iso, y, qtxt, {'condition': txt, 'year': y, 'set': s_})
for n, iso, y, truth in ((9, 'NGA', 2023, True), (10, 'AGO', 2019, False)):
    v = m.real_dep(iso, y)
    stated = round(v, 1) if truth else round(m.nominal_dep(iso, y), 1)
    q = 'A report says that in %d, after allowing for domestic inflation, %s\'s currency lost about %.1f percent of its value against the US dollar. Does the data support that?' % (y, NAME[iso], stated)
    it = rd_item(n, 'claim_check', iso, y, q, None, truth)
    assert (abs(stated - v) <= 1.0) == truth, (iso, stated, v)
    it['claim_stated'] = stated
    it['claims']['answer'] = [ans('c4', 'The statement is %s on the recomputed value (%s).' % ('true' if truth else 'false', 'recomputed %.3f' % it['recomputed_value']), 'full = verdict %s; no = opposite verdict.' % ('true' if truth else 'false'), 'true' if truth else 'false')]
    json.dump(it, open(os.path.join(ROOT, DM, it['id'] + '.json'), 'w'), indent=1, ensure_ascii=False)
# summary
for meth in (VM, RM, DM):
    fs = sorted(os.listdir(os.path.join(ROOT, meth)))
    print(meth, len(fs))
    for f in fs:
        it = json.load(open(os.path.join(ROOT, meth, f)))
        print(' ', it['id'], it['style'], it['subject']['iso3'], it['recomputed_value'], it['tolerance'], it.get('claim_truth', ''))
