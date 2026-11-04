"""Generic DATA BLOCK builder for the main experiment. build(item_id) -> (item, data_text, (passage_source, passage_text), info).
Same return signature as experiments/prompts/prompt_build.build. No model calls, no web. Reads frozen files only (through data_access.get plus a few
routes for frozen files that data_access.get does not cover). Per-method configuration lives in the single dict CFG below.
The table holds raw series only (never gold values, never computed results). Passage fields are empty (the oracle passage is handled elsewhere)."""
import sys, re, csv, math, json, glob, statistics
sys.path.insert(0, (__import__('os').environ.get('MC_ROOT') or __import__('os').path.abspath(__import__('os').path.join(__import__('os').path.dirname(__file__),'..','..')))+'/experiments/prompts_data')
import data_access as rp

REF = (__import__('os').environ.get('MC_ROOT') or __import__('os').path.abspath(__import__('os').path.join(__import__('os').path.dirname(__file__),'..','..')))+'/data/wb_classifications.csv'
NOTE = "Note on the series: interest paid in a year (% of GDP) = primary net lending/borrowing minus net lending/borrowing.\n"
INF = float('inf')
EU27 = rp.EU27

# ---------------------------------------------------------------- series names (data_access.NAMES plus new codes)
NAMES = dict(rp.NAMES)
NAMES.update({
    'BCA_NGDPD': 'Current account balance, % of GDP', 'NGDPD': 'Nominal GDP, current US$ billions', 'NGDPDPC': 'GDP per capita, current US$',
    'NGDPRPPPPC': 'Real GDP per capita, PPP', 'GGSB_NPGDP': 'General government structural balance, % of potential GDP (WEO)',
    'NY.GNP.PCAP.CD': 'GNI per capita, Atlas method, current US$ (WDI)', 'FR.INR.LEND': 'Lending interest rate, % (WDI)',
    'NY.GDP.DEFL.KD.ZG': 'Inflation, GDP deflator, annual % (WDI)', 'IQ.CPA.IRAI.XQ': 'CPIA IDA resource allocation index, 1 (low) to 6 (high) (WDI)',
    'BX.TRF.PWKR.DT.GD.ZS': 'Personal remittances received, % of GDP (WDI)', 'SP.DYN.TFRT.IN': 'Fertility rate, total births per woman (WDI)',
    'FI.RES.TOTL.CD@F': NAMES['FI.RES.TOTL.CD'],
    'PSD:DP.DOD.DSTC.CR.GG': 'General government short-term debt (World Bank Public Sector Debt), local currency, end of year',
    'PSD:DP.DOD.DLTC.CR.L1.GG': 'General government long-term debt due within one year (World Bank Public Sector Debt), local currency, end of year',
    'PSD:DP.DOD.DECT.CR.GG': 'General government total debt (World Bank Public Sector Debt), local currency, end of year',
    'PSD:DP.DOD.DECF.CR.GG': 'General government foreign-currency debt (World Bank Public Sector Debt), local currency, end of year',
    'FM.LBL.BMNY.ZG': 'Broad money growth, annual % (WDI)', 'LE': 'Employment, persons', 'LP': 'Population, persons', 'NGDPD': 'Nominal GDP, current US dollars',
    'WORLD_G': 'World real GDP growth, % (aggregate of WEO real PPP GDP per capita times population over all economies; used as a raw world aggregate)',
})
ANSWER_LIKE = {'FR.INR.RINR'}      # published series that equals the answer (WDI real interest rate): never shown
INPUT_ALIAS = {'L_P.P_MV': 'IIP:P_MV', 'IIP.P_MV': 'IIP:P_MV'}

# ---------------------------------------------------------------- data access
_extra = {}
def val(code, iso, y):
    """float or None. rp.get plus fallback routes for frozen files not covered by rp.get."""
    y = int(y); code = code.split('@')[0] if code != 'FI.RES.TOTL.CD@F' else code
    if code.startswith('PSD:'): v = rp.get(code, iso, f'{y}Q4')
    elif code == 'FI.RES.TOTL.CD@F': v = rp.wide_csv('wdi_20261008_fires_totl_cd.csv').get(iso, {}).get(str(y))
    elif code == 'IQ.CPA.IRAI.XQ': v = rp.wide_csv('wdi_20261008_cpia_irai.csv').get(iso, {}).get(str(y))
    elif code == 'BX.TRF.PWKR.DT.GD.ZS': v = rp.wide_csv('wdi_20261008_remit_gdp.csv').get(iso, {}).get(str(y))
    elif code in ('NY.GNP.PCAP.CD', 'FR.INR.LEND', 'NY.GDP.DEFL.KD.ZG', 'FM.LBL.BMNY.ZG'):
        f = 'wdi_20261008_ara_ig_extract.psv' if code == 'NY.GNP.PCAP.CD' else 'wdi_20261008_monetary_other.psv'
        v = rp.wide_psv(f).get((code, iso), {}).get(str(y))
    else:
        v = rp.get(code, iso, y)
        if v in (None, '') and '.' in code and not code.startswith(('PA.', 'NE.', 'FM.')):
            v = rp.wide_psv('wdi_20261008_ara_ig_extract.psv').get((code, iso), {}).get(str(y))
    if v in (None, '', 'n/a', 'NaN'): return None
    try: return float(v)
    except ValueError: return None
def raw(code, iso, y):
    """display string of the raw value ('' -> None)"""
    y = int(y)
    if code.startswith('PSD:'): v = rp.get(code, iso, f'{y}Q4')
    elif code in ('FI.RES.TOTL.CD@F', 'IQ.CPA.IRAI.XQ', 'BX.TRF.PWKR.DT.GD.ZS', 'NY.GNP.PCAP.CD', 'FR.INR.LEND', 'NY.GDP.DEFL.KD.ZG', 'FM.LBL.BMNY.ZG'):
        v = val(code, iso, y); return None if v is None else _fmt(code, iso, y)
    else:
        v = rp.get(code, iso, y)
        if v in (None, '') and val(code, iso, y) is not None: return _fmt(code, iso, y)
    return None if v in (None, '', 'n/a', 'NaN') else str(v)
def _fmt(code, iso, y):
    # string as stored in the frozen file
    if code == 'FI.RES.TOTL.CD@F': return rp.wide_csv('wdi_20261008_fires_totl_cd.csv')[iso][str(y)]
    if code == 'IQ.CPA.IRAI.XQ': return rp.wide_csv('wdi_20261008_cpia_irai.csv')[iso][str(y)]
    if code == 'BX.TRF.PWKR.DT.GD.ZS': return rp.wide_csv('wdi_20261008_remit_gdp.csv')[iso][str(y)]
    f = 'wdi_20261008_ara_ig_extract.psv' if code == 'NY.GNP.PCAP.CD' else 'wdi_20261008_monetary_other.psv'
    return rp.wide_psv(f)[(code, iso)][str(y)]

_wb = {}
def wb():
    if not _wb:
        for r in csv.DictReader(open(REF)):
            _wb[r['iso3']] = dict(name=r['name'].strip(), group=r['income_group'].strip(), region=r['region'].strip())
    return _wb
def countries():
    """economies in the WEO files that are not aggregates"""
    w = wb(); return sorted(i for i in rp.wide_csv('weo_oct2025_pcpipch.csv') if i in w and w[i]['group'] not in ('Aggregates', ''))
def cname(iso):
    n = wb().get(iso, {}).get('name', iso); return re.sub(r',.*$', '', n) if n.startswith(('Korea', 'Egypt', 'Iran', 'Venezuela', 'Gambia', 'Bahamas', 'Hong Kong', 'Macao', 'Yemen', 'Congo', 'Micronesia', 'Lao', 'Turkiye')) else n

# ---------------------------------------------------------------- year rules; entries: (function(ctx) -> years, completeness mode)
# modes: all = every year must resolve; tol = tolerant window (at least 60 percent of years); lead = required from the first available year on
RULES = {
    'cur': (lambda c: [c['y']], 'all'),
    'prev': (lambda c: [c['y'] - 1, c['y']], 'all'),
    'ends': (lambda c: [c['t0'], c['t1']] if c['t0'] != c['t1'] else [c['t0']], 'all'),
    'span': (lambda c: list(range(c['t0'], c['t1'] + 1)), 'tol'),
    'from1980': (lambda c: list(range(1980, c['t1'] + 1)), 'lead'),
    'hp1980_2030': (lambda c: list(range(1980, 2031)), 'all'),
    'fsi5': (lambda c: list(range(c['y'] - 1, c['y'] + 5)), 'all'),
    'back10': (lambda c: list(range(c['y'] - 10, c['y'])), 'tol'),
    'ci_g': (lambda c: list(range(c['y'] - 5, c['y'] + 5)), 'tol'),
    'mac': (lambda c: list(range(c['y'] - 10, c['horizon'] + 1)), 'all'),
}
W4 = ['GGXWDG_NGDP', 'GGXONLB_NGDP', 'GGXCNL_NGDP', 'NGDP']
# per-method configuration. add/drop adjust the codes taken from item['inputs']; rules maps code -> rule name ('*' = default); opt = codes allowed to be n/a;
# extra = special blocks; interest = print the interest definition note
CFG = {
    'eir': dict(add=['NGDP_D'], rules={'*': 'prev'}, opt=['NGDP_D'], interest=True),
    'irev': dict(add=['GGR_NGDP', 'GGXWDG_NGDP', 'GGXONLB_NGDP', 'GGXCNL_NGDP'], rules={'*': 'prev'}, opt=['GGXONLB_NGDP', 'GGXCNL_NGDP'], interest=True),
    'debt_stab': dict(add=W4, rules={'*': 'prev'}, interest=True),
    'debt_path': dict(add=W4 + ['NGDP_R'], rules={'*': 'prev'}, interest=True),
    'debt_target_adjustment': dict(add=W4, rules={'*': 'prev'}, interest=True),
    'gfn': dict(add=['GGXCNL_NGDP', 'NGDP', 'PSD:DP.DOD.DSTC.CR.CG', 'PSD:DP.DOD.DLTC.CR.L1.CG'], rules={'*': 'prev'}),
    'fsi': dict(add=['GGXWDG_NGDP', 'GGXONLB_NGDP', 'GGXCNL_NGDP', 'GGSB_NPGDP', 'NGDP', 'NGDP_D', 'NGDP_RPCH', 'PSD:DP.DOD.DSTC.CR.GG',
                     'PSD:DP.DOD.DLTC.CR.L1.GG', 'PSD:DP.DOD.DECT.CR.GG', 'PSD:DP.DOD.DECF.CR.GG', 'DT.DOD.DSTC.CD', 'FI.RES.TOTL.CD', 'SP.DYN.TFRT.IN'],
                rules={'*': 'cur', 'GGXWDG_NGDP': 'fsi5', 'GGXONLB_NGDP': 'fsi5', 'GGXCNL_NGDP': 'fsi5', 'NGDP_D': 'fsi5', 'NGDP_RPCH': 'fsi5',
                       'PSD:DP.DOD.DSTC.CR.GG': 'prev', 'PSD:DP.DOD.DLTC.CR.L1.GG': 'prev'},
                opt=['PSD:DP.DOD.DECF.CR.GG', 'PSD:DP.DOD.DECT.CR.GG', 'DT.DOD.DSTC.CD', 'FI.RES.TOTL.CD', 'SP.DYN.TFRT.IN', 'PSD:DP.DOD.DSTC.CR.GG',
                     'PSD:DP.DOD.DLTC.CR.L1.GG', 'GGSB_NPGDP'],
                interest=True, extra=['fsi_group'],
                AE='AUS AUT BEL CAN HRV CYP CZE DNK EST FIN FRA DEU GRC HKG ISL IRL ISR ITA JPN KOR LVA LTU LUX MAC MLT NLD NZL NOR PRT PRI SMR SGP SVK SVN ESP SWE CHE TWN GBR USA AND'.split()),
    'mac_dsa_stress': dict(add=['GGXWDG_NGDP', 'NGDP_RPCH', 'NGDP_D', 'GGXONLB_NGDP', 'GGXCNL_NGDP', 'GGR_NGDP'], rules={'*': 'mac'}, interest=True),
    'ara_em': dict(add=['FI.RES.TOTL.CD', 'DT.DOD.DSTC.CD', 'FM.LBL.BMNY.CN', 'PA.NUS.FCRF', 'BX.GSR.GNFS.CD', 'IIP:P_MV'], rules={'*': 'cur'}),
    'reserve_adequacy_traditional': dict(add=['FI.RES.TOTL.CD', 'NE.IMP.GNFS.CD', 'DT.DOD.DSTC.CD', 'FM.LBL.BMNY.GD.ZS', 'NY.GDP.MKTP.CD'], rules={'*': 'cur'}),
    'convergence_criteria': dict(add=['GGXCNL_NGDP', 'GGXWDG_NGDP', 'PCPIPCH'], rules={'*': 'cur'}, extra=['eu27_cpi']),
    'lic_dsf_ci': dict(add=['NGDP_RPCH', 'IQ.CPA.IRAI.XQ', 'FI.RES.TOTL.CD@F', 'NE.IMP.GNFS.CD', 'BX.TRF.PWKR.DT.GD.ZS'], drop=['NGDPRPPPPC', 'LP', 'FI.RES.TOTL.CD'],
                rules={'*': 'back10', 'NGDP_RPCH': 'ci_g'}, extra=['world_growth']),
    'structural_balance': dict(add=['GGR_NGDP', 'GGX_NGDP', 'GGXCNL_NGDP', 'NGDP_R'], rules={'*': 'prev', 'NGDP_R': 'hp1980_2030'}),
    'caid': dict(add=['NGSD_NGDP', 'NID_NGDP', 'BCA_NGDPD'], rules={'*': 'ends'}, opt=['BCA_NGDPD']),
    'saving_investment_gap_current_account': dict(add=['NGSD_NGDP', 'NID_NGDP', 'BCA_NGDPD'], rules={'*': 'cur'}, opt=['BCA_NGDPD']),
    'private_public_sector_balance': dict(add=['BCA_NGDPD', 'GGXCNL_NGDP'], rules={'*': 'cur'}),
    'cumulative_external_financing_need': dict(add=['BCA_NGDPD', 'NGDPD'], rules={'*': 'span'}),
    'reer_real_dep': dict(add=['PA.NUS.FCRF', 'NGDP_D'], rules={'*': 'prev'}),
    'growth_accounting': dict(add=['NGDP_R', 'NID_NGDP', 'LE'], rules={'*': 'ends', 'NGDP_R': 'from1980', 'NID_NGDP': 'from1980'}),
    'pc_decomp': dict(add=['NGDP_R', 'LE', 'LP'], rules={'*': 'ends'}),
    'income_group_atlas': dict(add=['NY.GNP.PCAP.CD'], rules={'*': 'cur'}),
    'income_velocity': dict(add=['NY.GDP.MKTP.CN', 'FM.LBL.BMNY.CN', 'FM.LBL.BMNY.GD.ZS'], rules={'*': 'ends'}, opt=['FM.LBL.BMNY.GD.ZS']),
    'okun': dict(add=['LUR', 'NGAP_NPGDP'], rules={'*': 'cur'}),
    'okun_difference': dict(add=['LUR', 'NGDP_RPCH'], rules={'*': 'span'}),
    'prices_real_growth': dict(add=['NGDP', 'NGDP_D'], rules={'*': 'prev'}),
    'prices_real_rate': dict(add=['NGDP_D'], rules={'*': 'prev'}),
    'prices_inflation_erosion': dict(add=['GGXWDG_NGDP', 'NGDP', 'NGDP_D'], rules={'*': 'prev'}),
    'real_interest_rate': dict(add=['FR.INR.LEND', 'NY.GDP.DEFL.KD.ZG'], rules={'*': 'cur'}),
}
# sample/method key (item['method'] field) -> CFG key
METHOD_KEY = {
    'cyclically_adjusted_balance_hp_filter': 'structural_balance', 'gdp_per_capita_growth_decomposition': 'pc_decomp',
    'growth_accounting_tfp_residual': 'growth_accounting', 'income_velocity': 'income_velocity', 'inflation_erosion_of_debt_ratio': 'prices_inflation_erosion',
    'lic_dsf_composite_indicator': 'lic_dsf_ci', 'maastricht_convergence_criteria': 'convergence_criteria', 'okun_difference': 'okun_difference',
    'okun_gap_cyclical_unemployment': 'okun', 'real_growth_from_nominal_growth_and_deflator': 'prices_real_growth',
    'real_interest_rate': 'real_interest_rate', 'real_interest_rate_fisher_gdp_deflator': 'prices_real_rate',
    'reserve_adequacy_traditional_metrics': 'reserve_adequacy_traditional', 'world_bank_income_classification_atlas': 'income_group_atlas',
    'saving_investment_gap_current_account': 'saving_investment_gap_current_account', 'private_public_sector_balance_split': 'private_public_sector_balance',
    'cumulative_external_financing_need': 'cumulative_external_financing_need',
}
def cfg_key(it): return METHOD_KEY.get(it['method'], it['method'])

# ---------------------------------------------------------------- resolving subject / years from the item
ALIAS = {'US': 'USA', 'U.S.': 'USA', 'UK': 'GBR', 'Korea': 'KOR', 'South Korea': 'KOR', 'Turkey': 'TUR', 'Russia': 'RUS', 'Egypt': 'EGY', 'Iran': 'IRN',
         'Venezuela': 'VEN', 'The Gambia': 'GMB', 'Gambia': 'GMB', 'The Bahamas': 'BHS', 'Bahamas': 'BHS', 'Hong Kong': 'HKG', 'Cape Verde': 'CPV',
         'Czech Republic': 'CZE', 'Slovakia': 'SVK', 'Kyrgyzstan': 'KGZ', 'Laos': 'LAO', 'Syria': 'SYR', 'Yemen': 'YEM', 'Macao': 'MAC',
         'the Netherlands': 'NLD', 'the United Kingdom': 'GBR', 'the United States': 'USA', 'Swaziland': 'SWZ', 'Burma': 'MMR', 'Vietnam': 'VNM'}
_names = {}
def name_map():
    if not _names:
        for iso, r in wb().items():
            if r['group'] in ('Aggregates', ''): continue
            n = r['name']; _names[n] = iso; _names[re.sub(r',.*$', '', n)] = _names.get(re.sub(r',.*$', '', n), iso)
        _names.update(ALIAS)
    return _names
def names_in(text):
    """economies named in the text, in order of position; longest names first, matched spans are masked"""
    t = text; found = []
    for n in sorted(name_map(), key=len, reverse=True):
        for m in re.finditer(r'(?<![A-Za-z])' + re.escape(n) + r'(?![A-Za-z])', t):
            found.append((m.start(), name_map()[n])); t = t[:m.start()] + ' ' * (m.end() - m.start()) + t[m.end():]
    return [i for _, i in sorted(found)]
def clean_query(q):
    q = re.sub(r'(October|Oct\.?) 2025( vintage)?', ' ', q)
    q = re.sub(r'by 2024 (dollar )?GDP|2024 dollar GDP|2024 dollars?', ' ', q)
    return re.sub(r'(US\$|\$)\s?\d[\d,.]*', ' ', q)
def qyears(q):
    return sorted({int(x) for x in re.findall(r'(?<![\d.,])(19[5-9]\d|20[0-3]\d)(?!\d|,\d|\.\d)', clean_query(q))})
def g_(d, *path):
    for p in path:
        if not isinstance(d, dict): return None
        d = d.get(p)
    return d
def claim_text(it):
    return ' '.join(c.get('text', '') for k in ('computation', 'text') for c in (it.get('claims') or {}).get(k, []))
def resolve_subject(it):
    """economy code of the item (the true one for hidden items), from structured fields, then names in the query, then the claim text"""
    g = it.get('gold') or {}; pv = it.get('provenance') if isinstance(it.get('provenance'), dict) else {}
    c = [g.get('iso3'), g_(pv, 'subject', 'iso3'), g_(it, 'subject', 'iso3') if isinstance(it.get('subject'), dict) else None, it.get('iso3'), it.get('country_iso3'),
         it.get('answer_country'), it.get('hidden_answer_country'), g_(it, 'hidden_set', 'answer'), it.get('hidden_subject'), g_(it, 'instance', 'iso3')]
    hc = it.get('hidden_condition'); hp = it.get('hidden_predicate')
    if isinstance(hc, dict):
        for k in ('set', 'matches'):
            if hc.get(k): c.append(hc[k][0])
    if isinstance(hp, dict) and hp.get('members'): c.append(hp['members'][0])
    for x in c:
        if isinstance(x, str) and len(x) == 3: return x
    if it['style'] != 'hidden':
        n = names_in(it['query'])
        if n: return n[0]
    m = re.findall(r'\b([A-Z]{3})\b (?:19|20)\d\d', claim_text(it))
    for x in m:
        if x in wb(): return x
    if it['style'] != 'hidden': return None
    return None
def resolve_years(it):
    """ctx: anchor year y, range ends t0..t1, horizon. Structured fields first, then the query, then the claim text."""
    g = it.get('gold') or {}; pv = it.get('provenance') if isinstance(it.get('provenance'), dict) else {}
    sub = it.get('subject') if isinstance(it.get('subject'), dict) else {}; ins = it.get('instance') if isinstance(it.get('instance'), dict) else {}
    hc = it.get('hidden_condition') if isinstance(it.get('hidden_condition'), dict) else {}
    conds = it.get('conditions') or []
    ys = [x for x in (it.get('years') or []) if isinstance(x, int)]
    ys += [x for x in (sub.get('year0'), sub.get('year1'), ins.get('y0'), ins.get('y1')) if isinstance(x, int)]
    y = None
    for x in (g.get('year'), it.get('year'), g_(pv, 'subject', 'year'), sub.get('year'), ins.get('year'), g_(it, 'hidden_set', 'year'), hc.get('year'),
              conds[0].get('year') if conds else None):
        if isinstance(x, int): y = x; break
    q = qyears(it['query']); allq = sorted(set(q) | set(ys))
    if y is None and ys: y = max(ys)
    if y is None and q: y = max(q)
    if len(set(ys) | set(q)) < 2:
        r = re.findall(r'\b[A-Z]{3}\b (19\d\d|20\d\d)-(19\d\d|20\d\d)', claim_text(it))
        if r: allq = sorted(set(allq) | {int(r[0][0]), int(r[0][1])}); y = y or int(r[0][1])
    if y is None: return None
    ends = [a for a in allq if 1950 <= a <= 2035]
    t0, t1 = (min(ends), max(ends)) if len(ends) >= 2 else (y - 1, y)
    hz = g_(pv, 'subject', 'horizon') or max(y + 5, 2030)
    return dict(y=y, t0=t0, t1=t1, horizon=hz, allyears=ends)

# ---------------------------------------------------------------- features for hidden-set conditions
class Cond:
    def __init__(self, label, needs, fn, lo=-INF, hi=INF):
        self.label, self.needs, self.fn, self.lo, self.hi = label, needs, fn, lo, hi
    def __call__(self, iso):
        try: return self.fn(iso)
        except (TypeError, ValueError, ZeroDivisionError): return None
    def ok(self, iso, lo=None, hi=None):
        v = self(iso); lo = self.lo if lo is None else lo; hi = self.hi if hi is None else hi
        return v is not None and lo <= v <= hi
def pct(code, iso, y):
    a, b = val(code, iso, y), val(code, iso, y - 1)
    return None if a is None or b in (None, 0) else 100 * (a / b - 1)
def code_feat(code, y, scale=1.0):
    return Cond(f'{code} {y}', [(code, y)], lambda i: None if val(code, i, y) is None else val(code, i, y) * scale)
LEG = {'debt': ('GGXWDG_NGDP', 0), 'd_prev': ('GGXWDG_NGDP', -1), 'pb': ('GGXONLB_NGDP', 0), 'primary_balance': ('GGXONLB_NGDP', 0), 'bal': ('GGXCNL_NGDP', 0),
       'real_growth': ('NGDP_RPCH', 0), 'rg': ('NGDP_RPCH', 0), 'revenue': ('GGR_NGDP', 0)}
def kind_feat(kind, y):
    """base kinds (prompt_build.field) generalised; any WEO/WDI code string is also accepted"""
    if kind in LEG: c, d = LEG[kind]; return code_feat(c, y + d)
    if kind in ('ng', 'nominal_growth'): return Cond(f'NGDP growth {y}', [('NGDP', y - 1), ('NGDP', y)], lambda i: pct('NGDP', i, y))
    if kind == 'deflator_inflation': return Cond(f'NGDP_D growth {y}', [('NGDP_D', y - 1), ('NGDP_D', y)], lambda i: pct('NGDP_D', i, y))
    if kind == 'du2009': return Cond('LUR change 2008-09', [('LUR', 2008), ('LUR', 2009)], lambda i: val('LUR', i, 2009) - val('LUR', i, 2008))
    if kind in ('min_g', 'avg_g'):
        def _gs(i): return [v for v in (val('NGDP_RPCH', i, t) for t in range(1993, 2020)) if v is not None]
        f = (lambda i: min(_gs(i))) if kind == 'min_g' else (lambda i: sum(_gs(i)) / len(_gs(i)))
        return Cond(f'{kind} 1993-2019', [('NGDP_RPCH', t) for t in range(1993, 2020)], f)
    if kind == 'g2009': return code_feat('NGDP_RPCH', 2009)
    if kind in ('u2000', 'u2019'): return code_feat('LUR', int(kind[1:]))
    if kind == 'maxu':
        return Cond('max LUR 1993-2019', [('LUR', t) for t in range(1993, 2020)], lambda i: max(v for v in (val('LUR', i, t) for t in range(1993, 2020)) if v is not None))
    return code_feat(kind, y)
def avg_growth(code, a, b):
    return Cond(f'avg log growth {code} {a}-{b}', [(code, a), (code, b)], lambda i: 100 * (math.log(val(code, i, b)) - math.log(val(code, i, a))) / (b - a))
def window(c, op, thr, thr2=None):
    if op in ('>', '>='): c.lo = thr
    elif op in ('<', '<='): c.hi = thr
    return c
# lexicon for text conditions: (regex, code, sign, scale)   sign -1 flips the threshold (a deficit wider than x is a balance below -x)
LEX = [
    (r'consumer[- ]price inflation|average consumer price inflation|consumer prices? (?:rose|rise|inflation)', 'PCPIPCH', 1, 1),
    (r'output prices|GDP[- ]deflator inflation', 'NGDP_D%', 1, 1),
    (r'current account (?:balance|deficit)?|external deficit|external balance', 'BCA_NGDPD', 1, 1),
    (r'unemployment rate', 'LUR', 1, 1), (r'GDP per capita', 'NGDPDPC', 1, 1), (r'nominal GDP', 'NGDPD', 1, 1),
    (r'(?:general government|gross public|gross) debt|public debt', 'GGXWDG_NGDP', 1, 1),
    (r'general government (?:overall )?balance|overall fiscal balance', 'GGXCNL_NGDP', 1, 1),
    (r'primary balance', 'GGXONLB_NGDP', 1, 1), (r'real (?:GDP|output) growth', 'NGDP_RPCH', 1, 1), (r'broad money', 'FM.LBL.BMNY.GD.ZS', 1, 1),
    (r'lending rate', 'FR.INR.LEND', 1, 1), (r'national saving', 'NGSD_NGDP', 1, 1), (r'gross investment|total investment', 'NID_NGDP', 1, 1),
    (r'population', 'LP', 1, 1), (r'general government revenue', 'GGR_NGDP', 1, 1),
    (r'external surplus', 'BCA_NGDPD', 1, 1), (r'real GDP contraction', 'NGDP_RPCH', 1, 1), (r'(?:general government |fiscal |government )?deficit', 'GGXCNL_NGDP', 1, 1),
]
CMP = r'(above|below|over|under|more than|less than|greater than|fewer than|wider than|larger than|higher than|lower than|exceeding|>|<)'
def cmp_op(w): return '>' if w in ('above', 'over', 'more than', 'greater than', 'wider than', 'larger than', 'higher than', 'exceeding', '>') else '<'
def text_conds(text, default_year):
    """clauses like '<phrase> [in YEAR] [was] above X' -> Cond list; 'deficit wider than x' flips the sign"""
    out = []
    for part in re.split(r',| and (?=[a-z])|;', text):
        m = re.search(CMP + r'\s*(?:US\$\s*)?(-?[\d,]*\.?\d+)\s*(billion|%|percent)?', part)
        if not m: continue
        hit = None
        for rg, code, sg, sc in LEX:
            mm = re.search(rg, part[:m.start()])
            if mm and (hit is None or mm.start() < hit[0]): hit = (mm.start(), code, mm.group(0))
        if hit is None: continue
        y = re.search(r'\b(19\d\d|20[0-3]\d)\b', part); y = int(y.group(1)) if y else default_year
        thr = float(m.group(2).replace(',', '')); op = cmp_op(m.group(1)); code = hit[1]
        if ('deficit' in hit[2] and code in ('BCA_NGDPD', 'GGXCNL_NGDP')) or 'contraction' in hit[2]: thr = -thr; op = '<' if op == '>' else '>'
        if code == 'NGDPD' and m.group(3) == 'billion': thr = thr * 1e9
        c = kind_feat('deflator_inflation', y) if code == 'NGDP_D%' else kind_feat(code, y)
        out.append(window(c, op, thr))
    return out
def cond_string(s, default_year):
    """'275 < FM.LBL.BMNY.GD.ZS (2021) < 400' and 'A (2019) > 30 and B (2019) < 5'"""
    out = []
    for part in s.split(' and '):
        m = re.match(r'\s*(?:(-?[\d.]+)\s*(<|>)\s*)?([A-Za-z_.]+)\s*\((\d{4})\)\s*(?:(<|>)\s*(-?[\d.]+))?', part)
        if not m: continue
        c = kind_feat(m.group(3), int(m.group(4)))
        if m.group(1): window(c, '>' if m.group(2) == '<' else '<', float(m.group(1)))
        if m.group(5): window(c, m.group(5), float(m.group(6)))
        out.append(c)
    return out
_ukind = [None]
def universe_from_text(it, y, text):
    """a named list of economies in the query, a region, EU27, top-N by dollar GDP, or economies with a given series"""
    q = it['query']
    if re.search(r'European Union|EU members?|EU27', text) or 'European Union' in q and 'member' in text: return set(EU27)
    m = re.search(r'top-(\d+) by NGDPD (\d{4})|(?:twenty|(\d+)) largest economies', text + ' ' + q)
    if m:
        n = int(m.group(1)) if m.group(1) else 20
        yy = int(m.group(2)) if m.group(2) else 2024
        v = sorted(((val('NGDPD', i, yy), i) for i in countries() if val('NGDPD', i, yy) is not None), reverse=True)
        return {i for _, i in v[:n]}
    for pat, reg in (('South Asian', 'South Asia'), ('European or Central Asian', 'Europe & Central Asia'), ('East Asian', 'East Asia & Pacific'),
                     ('Sub-Saharan', 'Sub-Saharan Africa'), ('Latin American', 'Latin America & Caribbean')):
        if pat in text or pat in q: _ukind[0] = 'region'; return {i for i in countries() if wb()[i]['region'] == reg}
    m = re.search(r'\(([A-Z][^()]{60,})\)', q)
    if m:
        ns = [name_map()[n] for n in re.split(r',\s*(?:and )?', m.group(1)) if n.strip() in name_map()]
        if len(ns) >= 15: return set(ns)
    if re.search(r'output[- ]gap', text + q): return {i for i in countries() if val('NGAP_NPGDP', i, y) is not None}
    if re.search(r'employment data', text + q): return {i for i in countries() if val('LE', i, y) is not None}
    return None
def hidden_spec(it, ctx):
    _ukind[0] = None; sp = _hidden_spec(it, ctx)
    if sp is not None: sp['ukind'] = _ukind[0]
    return sp
def _hidden_spec(it, ctx):
    """-> dict(mode='window'|'rank', conds, universe, [rank feature, rule]) or None"""
    y = ctx['y']; g = it.get('gold') or {}; hc = it.get('hidden_condition'); hs = it.get('hidden_set'); pr = it.get('predicate'); hp = it.get('hidden_predicate')
    if it.get('conditions'):
        return dict(mode='window', conds=[window(window(kind_feat(c['kind'], c['year']), '>', c['low']), '<', c['high']) for c in it['conditions']], universe=None)
    if isinstance(g.get('hidden_condition'), dict):
        h = g['hidden_condition']
        return dict(mode='window', conds=[window(window(kind_feat(h['fields'][k], g['year']), '>', h['windows'][str(k)][0]), '<', h['windows'][str(k)][1]) for k in h['used']], universe=None)
    if isinstance(hs, dict) and hs.get('conditions'):
        return dict(mode='window', conds=[window(kind_feat(code, hs['year']), op, thr) for code, op, thr in hs['conditions']], universe=None)
    if isinstance(hc, dict) and hc.get('intervals'):
        iv = hc['intervals']; KM = {'d1': 'd_prev', 'pi': 'deflator_inflation', 'g': 'real_growth', 'd': 'debt'}
        return dict(mode='window', universe=None, conds=[window(window(kind_feat(KM.get(k, k), y), '>', v[0]), '<', v[1]) for k, v in iv.items()])
    if isinstance(hc, dict) and hc.get('condition'): return dict(mode='window', conds=cond_string(hc['condition'], y), universe=None)
    if isinstance(hc, list):
        return dict(mode='window', conds=[window(kind_feat(a, y), b, c) for a, b, c in hc], universe=None)
    if isinstance(hp, dict) and hp.get('conditions'):
        out = []
        for c in hp['conditions']:
            cs = text_conds(f"{c['feature']} {c['year']} {c['op']} {c['threshold']}", c['year']);
            if cs: out.append(cs[0])
        return dict(mode='window', conds=out, universe=None)
    if isinstance(pr, dict):
        series = pr['series']; f = kind_feat('deflator_inflation', pr['year']) if series.endswith('change') else kind_feat(series, pr['year'])
        return dict(mode='rank', feature=f, rule=pr['rule'], universe=universe_from_text(it, y, pr['universe']))
    text = pr if isinstance(pr, str) else ' and '.join(pr) if isinstance(pr, list) else it['query']
    m = re.search(r'(?:with|whose|that had|that recorded) the (lowest|highest|fastest|steepest|lightest|least|largest|smallest|slowest|weakest)\b(?: rise in)? (.+?) in (\d{4})', text)
    if m:
        rule = 'argmin' if m.group(1) in ('lowest', 'lightest', 'least', 'smallest', 'slowest', 'weakest') else 'argmax'
        ft = m.group(2)
        if re.search(r'government deficit|fiscal deficit', ft): ft = 'general government balance'; rule = 'argmin' if rule == 'argmax' else 'argmax'
        cs = text_conds(f'{ft} above 0', int(m.group(3)))
        return dict(mode='rank', feature=cs[0], rule=rule, universe=universe_from_text(it, y, text))
    m = re.search(r'average (?:real )?(?:GDP |output |population )?growth.*?\((\w+)\)\s*([<>])\s*(-?[\d.]+).*?over (\d{4})-(\d{4})', text)
    if m:
        c = avg_growth(m.group(1), int(m.group(4)), int(m.group(5))); window(c, m.group(2), float(m.group(3)))
        return dict(mode='window', conds=[c], universe=universe_from_text(it, y, text))
    m = re.search(r'\((\w+)\)\s*([<>])\s*(-?[\d.]+)\s*in (\d{4})', text)
    if m:
        return dict(mode='window', conds=[window(kind_feat(m.group(1), int(m.group(4))), m.group(2), float(m.group(3)))], universe=universe_from_text(it, y, text))
    cs = text_conds(text, y)
    if cs: return dict(mode='window', conds=cs, universe=None)
    return None
def spec_universe(spec):
    return sorted(spec['universe'] & set(countries())) if spec.get('universe') else countries()
def match_all(spec, uni):
    if spec['mode'] == 'window': return [i for i in uni if all(c.ok(i) for c in spec['conds'])]
    v = sorted(((spec['feature'](i), i) for i in uni if spec['feature'](i) is not None), reverse=(spec['rule'] == 'argmax'))
    return [v[0][1]] if v else []
def _widen(conds, uni, minimum):
    """smallest simultaneous widening (k quarter-spans on every finite side) of the given conditions that admits at least `minimum` economies"""
    sp = []
    for c in conds:
        vals = [x for x in (c(i) for i in uni) if x is not None]
        q = sorted(vals); iqr = (q[3 * len(q) // 4] - q[len(q) // 4]) if len(q) > 3 else 0
        sp.append((c.hi - c.lo) if (c.lo > -INF and c.hi < INF) else (0.2 * iqr or 1.0))
    best = []
    for k in range(0, 161):
        best = [i for i in uni if all(c.ok(i, c.lo - 0.25 * k * s_ if c.lo > -INF else -INF, c.hi + 0.25 * k * s_ if c.hi < INF else INF) for c, s_ in zip(conds, sp))]
        if len(best) >= minimum: break
    return best
def candidates(spec, uni, subject, minimum=8, cap=15):
    """rank rules: the `minimum` most extreme economies of the universe. Window rules: widen the first condition's window until at least `minimum`
    economies fit (prompt_build.first_window_candidates); if that gives more than `cap` economies (loose first condition) widen all conditions together instead.
    A universe with fewer than `minimum` economies is padded with the outside economies closest in value."""
    f0 = spec['feature'] if spec['mode'] == 'rank' else spec['conds'][0]
    if spec['mode'] == 'rank':
        v = sorted(((f0(i), i) for i in uni if f0(i) is not None), reverse=(spec['rule'] == 'argmax')); c = [i for _, i in v[:minimum]]
    else:
        c = _widen(spec['conds'][:1], uni, minimum)
        if len(c) > cap: c = _widen(spec['conds'], uni, minimum)
    if len(c) < minimum:
        ref = f0(subject) if subject and f0(subject) is not None else (f0(c[0]) if c else 0)
        out = sorted((abs(f0(i) - ref), i) for i in countries() if i not in c and f0(i) is not None)
        c += [i for _, i in out[:minimum - len(c)]]
    return sorted(c)

# ---------------------------------------------------------------- needs and tables
def norm_inputs(it):
    out = []
    for x in it.get('inputs') or []:
        c = x if isinstance(x, str) else x.get('code', '')
        c = c.split(' ')[0].rstrip(';')
        c = INPUT_ALIAS.get(c, c)
        if c.startswith('PSD'): continue
        out.append(c)
    return [c for c in out if re.fullmatch(r'[A-Za-z_][\w.]*(:\w+)?(@F)?', c) and c in NAMES and c not in ANSWER_LIKE]
def method_needs(it, ctx):
    cfg = CFG[cfg_key(it)]
    codes = [c for c in norm_inputs(it) if c not in cfg.get('drop', [])]
    for c in cfg['add']:
        if c not in codes: codes.append(c)
    codes = [c for c in codes if c not in cfg.get('drop', [])]
    needs = {}; mode = {}
    for c in codes:
        rule = cfg['rules'].get(c, cfg['rules']['*']); fn, md = RULES[rule]
        needs[c] = sorted(set(fn(ctx))); mode[c] = md
    return needs, mode, cfg
def merge(a, b):
    out = {c: set(v) for c, v in a.items()}
    for c, y in b: out.setdefault(c, set()).add(y)
    return {c: sorted(v) for c, v in out.items()}
def cell(code, iso, y):
    v = raw(code, iso, y); return 'n/a' if v is None else v
def subject_table(iso, needs, order):
    cols = sorted({y for v in needs.values() for y in v})
    t = f"Data for {cname(iso)} ({iso}); IMF World Economic Outlook, October 2025 (WEO) unless marked.\n| series | " + ' | '.join(map(str, cols)) + " |\n|---|" + '---|' * len(cols) + "\n"
    for c in order:
        t += f"| {NAMES[c]} | " + ' | '.join(cell(c, iso, y) if y in needs[c] else '' for y in cols) + " |\n"
    return t
def candidate_table(isos, needs, order):
    pairs = [(c, y) for c in order for y in needs[c]]
    t = f"Candidate economies (IMF World Economic Outlook, October 2025, unless marked). {len(isos)} economies; blank cell = not needed.\n"
    if len(pairs) <= 16:
        t += '| economy | ' + ' | '.join(f"{NAMES[c]} {y}" for c, y in pairs) + ' |\n|---|' + '---|' * len(pairs) + '\n'
        for i in isos: t += f"| {i} | " + ' | '.join(cell(c, i, y) for c, y in pairs) + ' |\n'
        return t
    cols = sorted({y for c in order for y in needs[c]})
    t += '| economy | series | ' + ' | '.join(map(str, cols)) + ' |\n|---|---|' + '---|' * len(cols) + '\n'
    for i in isos:
        for c in order: t += f"| {i} | {NAMES[c]} | " + ' | '.join(cell(c, i, y) if y in needs[c] else '' for y in cols) + ' |\n'
    return t
_wg = {}
def world_growth(y):
    if not _wg:
        rp_, lp = rp.wide_csv('weo_oct2025_ngdprppppc.csv'), rp.wide_csv('weo_oct2025_lp.csv'); W = {}
        for i, row in rp_.items():
            if i not in lp: continue
            for yy in range(1981, 2031):
                a, b = row.get(str(yy)), lp[i].get(str(yy))
                if a not in (None, '') and b not in (None, ''): W[yy] = W.get(yy, 0) + float(a) * float(b)
        for yy in W:
            if yy - 1 in W: _wg[yy] = round(100 * (W[yy] / W[yy - 1] - 1), 3)
    return _wg.get(y)
def extras(it, cfg, ctx, shown):
    t = ''
    for e in cfg.get('extra', []):
        if e == 'eu27_cpi':
            y = ctx['y']; t += f"Annual-average CPI inflation, %, {y}, EU27 members: " + ', '.join(f"{i} {cell('PCPIPCH', i, y)}" for i in sorted(EU27)) + '\n'
        if e == 'world_growth':
            ys = list(range(ctx['y'] - 5, ctx['y'] + 5))
            t += NAMES['WORLD_G'] + '\n| series | ' + ' | '.join(map(str, ys)) + ' |\n|---|' + '---|' * len(ys) + '\n| World real GDP growth, % | ' + ' | '.join(str(world_growth(x)) if world_growth(x) is not None else 'n/a' for x in ys) + ' |\n'
        if e == 'fsi_group':
            ae = [i for i in shown if i in cfg['AE']]
            t += f"Country groups used by the fiscal stress index (IMF WP/11/100): advanced economies among those shown: {', '.join(ae) if ae else 'none'}; the others shown are emerging markets.\n"
    return t

LAST = {}
def build(item_id):
    it = rp.find(item_id); key = cfg_key(it); ctx = resolve_years(it); subj = resolve_subject(it)
    needs, mode, cfg = method_needs(it, ctx); order = list(needs)
    info = dict(subject=subj, year=ctx['y'], t0=ctx['t0'], t1=ctx['t1'])
    if it['style'] == 'hidden':
        spec = hidden_spec(it, ctx)
        if spec is None: raise ValueError(f'{item_id}: hidden predicate not parsed')
        uni = spec_universe(spec); full = match_all(spec, uni)
        if subj is None and len(full) == 1: subj = full[0]; info['subject'] = subj
        cands = candidates(spec, uni, subj)
        cn = []
        for c in ([spec['feature']] if spec['mode'] == 'rank' else spec['conds']): cn += c.needs
        if spec['mode'] == 'rank' and spec.get('universe') is not None and 'top' in str(it.get('predicate')):
            cn += [('NGDPD', 2024)]
        needs2 = merge(needs, cn); order2 = order + [c for c in needs2 if c not in order]
        d = candidate_table(cands, needs2, order2)
        if spec.get('ukind') == 'region':
            d += 'World Bank region of each economy shown: ' + '; '.join(f"{i} {wb()[i]['region']}" for i in cands) + '\n'
        info.update(n_candidates=len(cands), subject_in=subj in cands, set_size_all=len(full), n_match_true=subj in full)
        shown = cands; needs_used = needs2
    else:
        d = subject_table(subj, needs, order) if subj else ''
        shown = [subj]; needs_used = needs
    d += extras(it, cfg, ctx, shown)
    if cfg.get('interest'): d += NOTE
    # completeness of the subject's required cells
    miss = []
    if subj:
        for c in order:
            if c in cfg.get('opt', []): continue
            ys = needs[c]; have = [y for y in ys if val(c, subj, y) is not None]
            if mode[c] == 'all': miss += [(c, y) for y in ys if y not in have]
            elif mode[c] == 'tol':
                if len(have) < 0.6 * len(ys): miss += [(c, y) for y in ys if y not in have]
            elif mode[c] == 'lead':
                first = min(have) if have else None
                miss += [(c, y) for y in ys if (first is None or y >= first) and y not in have]
    LAST[item_id] = dict(missing=miss, needs=needs, ctx=ctx, key=key, shown=list(shown), region=(it['style'] == 'hidden' and spec.get('ukind') == 'region'), extra=list(cfg.get('extra', [])), AE=cfg.get('AE'))
    return it, d, ('', ''), info

# ---------------------------------------------------------------- broad table (CoT1 / PoT when BROAD_DATA=1)
# All series codes used anywhere in the benchmark (union of needs over the 440 active items), fixed order: source, then code.
STANDARD_SERIES = [
    'IIP:P_MV',
    'PSD:DP.DOD.DECF.CR.GG', 'PSD:DP.DOD.DECT.CR.GG', 'PSD:DP.DOD.DLTC.CR.L1.CG', 'PSD:DP.DOD.DLTC.CR.L1.GG', 'PSD:DP.DOD.DSTC.CR.CG', 'PSD:DP.DOD.DSTC.CR.GG',
    'BX.GSR.GNFS.CD', 'BX.TRF.PWKR.DT.GD.ZS', 'DT.DOD.DSTC.CD', 'FI.RES.TOTL.CD', 'FM.LBL.BMNY.CN', 'FM.LBL.BMNY.GD.ZS', 'FR.INR.LEND',
    'IQ.CPA.IRAI.XQ', 'NE.IMP.GNFS.CD', 'NY.GDP.DEFL.KD.ZG', 'NY.GDP.MKTP.CD', 'NY.GDP.MKTP.CN', 'NY.GNP.PCAP.CD', 'PA.NUS.FCRF', 'SP.DYN.TFRT.IN',
    'BCA_NGDPD', 'GGR_NGDP', 'GGSB_NPGDP', 'GGXCNL_NGDP', 'GGXONLB_NGDP', 'GGXWDG_NGDP', 'GGX_NGDP', 'LE', 'LP', 'LUR', 'NGAP_NPGDP', 'NGDP', 'NGDPD',
    'NGDP_D', 'NGDP_R', 'NGDP_RPCH', 'NGSD_NGDP', 'NID_NGDP', 'PCPIPCH']
BROAD_MAX_CHARS = 30000
def _broad_years(needs, restrict):
    ys = sorted({y for v in needs.values() for y in v})
    return list(range(ys[0], ys[-1] + 1)) if (restrict and ys) else ys
def _broad_table(isos, cols, long_format):
    hdr = ' | '.join(map(str, cols)); sep = '---|' * len(cols)
    if not long_format:
        iso = isos[0]
        t = f"Data for {cname(iso)} ({iso}); IMF World Economic Outlook, October 2025 (WEO) unless marked.\n| series | {hdr} |\n|---|{sep}\n"
        for c in STANDARD_SERIES: t += f"| {NAMES[c]} | " + ' | '.join(str(cell(c, iso, y)) for y in cols) + " |\n"
        return t
    t = f"Candidate economies (IMF World Economic Outlook, October 2025, unless marked). {len(isos)} economies; n/a = no data.\n| economy | series | {hdr} |\n|---|---|{sep}\n"
    for i in isos:
        for c in STANDARD_SERIES: t += f"| {i} | {NAMES[c]} | " + ' | '.join(str(cell(c, i, y)) for y in cols) + ' |\n'
    return t
def build_broad(item_id, restrict_years=False):
    """Same signature as build(). Same economies and years as build(), but rows for ALL STANDARD_SERIES (fixed order, nothing marks which are needed).
    restrict_years=True: columns are every year from the first to the last needed year (instead of only the needed years)."""
    it = rp.find(item_id); key = cfg_key(it); ctx = resolve_years(it); subj = resolve_subject(it)
    needs, mode, cfg = method_needs(it, ctx)
    info = dict(subject=subj, year=ctx['y'], t0=ctx['t0'], t1=ctx['t1'], broad=True)
    if it['style'] == 'hidden':
        spec = hidden_spec(it, ctx)
        if spec is None: raise ValueError(f'{item_id}: hidden predicate not parsed')
        uni = spec_universe(spec); full = match_all(spec, uni)
        if subj is None and len(full) == 1: subj = full[0]; info['subject'] = subj
        cands = candidates(spec, uni, subj)
        cn = []
        for c in ([spec['feature']] if spec['mode'] == 'rank' else spec['conds']): cn += c.needs
        if spec['mode'] == 'rank' and spec.get('universe') is not None and 'top' in str(it.get('predicate')): cn += [('NGDPD', 2024)]
        needs2 = merge(needs, cn)
        d = _broad_table(cands, _broad_years(needs2, restrict_years), True)
        if spec.get('ukind') == 'region': d += 'World Bank region of each economy shown: ' + '; '.join(f"{i} {wb()[i]['region']}" for i in cands) + '\n'
        info.update(n_candidates=len(cands), subject_in=subj in cands, set_size_all=len(full), n_match_true=subj in full); shown = cands
    else:
        d = _broad_table([subj], _broad_years(needs, restrict_years), False) if subj else ''
        shown = [subj]
    d += extras(it, cfg, ctx, shown)
    d += NOTE      # general definition note, shown for every item so it does not hint at the needed series
    return it, d, ('', ''), info
