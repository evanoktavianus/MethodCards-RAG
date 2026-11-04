"""Authoring script (reads frozen CSVs only). python3 -I gen_items.py"""
import os, sys, json, random, math
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, 'gold_external.py')).read().split("if __name__")[0])
BPM6 = '712b0ad9-7e38-4e33-afc8-de1de9422d0d'; EBA = '5319b022-7886-44bd-ab1f-b230330aa9df'
os.makedirs(OUT, exist_ok=True)
CTRY = sorted(c for c in S if c in NAME)
def margin_ok(x, th): return abs(x - th) >= 0.2
def find_pred(c, y, specs):
    """specs: [(col, op)]; integer thresholds; return list of (col,op,th) giving exactly country c, loosest."""
    tabs = {'S': S, 'I': I, 'B': B, 'G': G, 'D': D}
    vals = []
    for col, op in specs:
        a = v(tabs[col], c, y)
        if a is None: return None
        vals.append(a / 1e9 if col == 'D' else a)
    cands = []
    for k in range(len(specs)):
        col, op = specs[k]; a = vals[k]; L = []
        for step in range(0, 40):
            th = (math.floor(a) - step) if op == '>' else (math.ceil(a) + step)
            if col == 'D': th = (math.floor(a) - step * 10) if op == '>' else None
            if th is None: break
            if margin_ok(a, th) and ((a > th) if op == '>' else (a < th)): L.append((th, step))
        cands.append(L[:14])
    best = None
    import itertools
    for combo in itertools.product(*cands):
        pr = [(specs[k][0], specs[k][1], combo[k][0]) for k in range(len(specs))]
        x = {'year': y, 'predicate_cols': pr}
        if [k2 for k2 in S if hidden_ok(x, k2)] == [c]:
            score = sum(cb[1] for cb in combo)
            if best is None or score > best[0]: best = (score, pr)
    return best[1] if best else None
def pr_text(pr, kind):
    lab = {'S': 'national saving', 'I': 'gross investment', 'B': 'current account balance', 'G': 'general government net lending'}
    out = []
    for col, op, th in pr:
        if col == 'S': out.append(f"national saving {'above' if op=='>' else 'below'} {th}% of GDP")
        elif col == 'I': out.append(f"gross investment {'above' if op=='>' else 'below'} {th}% of GDP")
        elif col == 'B': out.append(f"an external {'surplus above' if op=='>' else 'deficit wider than'} {th if op=='>' else -th}% of GDP" if (op=='>' or th<0) else f"an external balance {'above' if op=='>' else 'below'} {th}% of GDP")
        elif col == 'G':
            if op == '>': out.append(f"a general government deficit smaller than {-th}% of GDP" if th < 0 else f"a general government surplus above {th}% of GDP")
            else: out.append(f"a general government deficit larger than {-th}% of GDP" if th < 0 else f"a general government balance below {th}% of GDP")
        elif col == 'D': out.append(f"nominal GDP above US$ {th} billion")
    return ' and '.join(out)

def claims(method_text, accept, comp_text, ref, tol, unit, extra_text, data_text, comp_accept):
    txt = [{"id": "c0", "kind": "text", "importance": "vital", "text": method_text, "accept": accept}]
    txt += extra_text
    return {"text": txt,
            "data": [{"id": "c5", "kind": "data", "importance": "okay", "text": data_text}],
            "computation": [{"id": "c1", "kind": "computation", "importance": "vital", "text": comp_text,
                             "reference_value": round(ref, 3), "tolerance": tol, "unit": unit, "accept": comp_accept}]}
def yn(i, tag, truth, text): return {"id": "c2", "kind": "text", "importance": "vital", "text": text,
        "accept": f"full = states the claim is {'consistent with / supported' if truth else 'inconsistent / not supported'} after recomputation"}

META = {
 'EXS': dict(method='saving_investment_gap_current_account', docs=[BPM6, EBA], cls='textbook identity',
   quote="BPM6 ch.14 (doc 712b0ad9, block 3187): \"S - I = CAB. That is, the current account balance is the gap between saving and investment.\" EBA note (doc 5319b022, block 30): \"the current account as the gap between aggregate saving and investment (the so-called 'IS' relation)\".",
   inputs=['NGSD_NGDP', 'NID_NGDP', 'BCA_NGDPD'],
   dist=["trade-balance (net exports) calculation", "external-debt stabilising current account", "EBA regression norm / current account gap", "reserve adequacy metrics", "terms-of-trade effect"],
   famous=True,
   m_text="Identifies that the external balance follows from the national accounts identity: current account balance = gross national saving minus gross investment (the saving-investment gap).",
   acc="full = saving-investment gap / current account identity (CAB = S - I); acceptable alternative: expenditure identity CAB = GNDY - C - G - I; no = trade balance only or regression-based norm"),
 'EXP': dict(method='private_public_sector_balance_split', docs=[BPM6], cls='textbook identity',
   quote="BPM6 ch.14 (doc 712b0ad9, block 3197): \"CAB = (S_p - I_p) + (S_g - I_g).\" (government saving-investment balance = general government net lending).",
   inputs=['BCA_NGDPD', 'GGXCNL_NGDP'], dist=["cyclically adjusted fiscal balance", "debt-stabilising primary balance", "EBA current account gap regression", "fiscal impulse", "trade balance"],
   famous=True,
   m_text="Identifies the sectoral balances identity: current account balance = private saving-investment balance + government saving-investment balance, so the private balance is the current account minus government net lending.",
   acc="full = sectoral balances / twin-deficit identity CAB = (Sp-Ip)+(Sg-Ig); no = single fiscal or external indicator alone"),
 'EXF': dict(method='cumulative_external_financing_need', docs=[BPM6], cls='textbook identity',
   quote="BPM6 ch.14 (doc 712b0ad9, blocks 3204/3214): \"NLB = CAB + KAB = NFA\"; \"the net provision of resources to or from the rest of the world, as measured by the current and capital account balances, must-by definition-be matched by a change in net claims on the rest of the world.\" Capital account balance treated as negligible; current account in US$ = BCA_NGDPD x NGDPD.",
   inputs=['BCA_NGDPD', 'NGDPD'], dist=["debt-stabilising current account", "reserve adequacy / import cover", "gross financing needs of the government", "external debt dynamics", "balance-of-payments adjustment to terms of trade"],
   famous=False,
   m_text="Identifies the balance-of-payments financing identity: a current account deficit must be matched by net external financing (net borrowing from abroad, NLB = CAB + KAB = NFA), so cumulative financing = sum of annual current account balances converted to US dollars.",
   acc="full = BoP financing identity (current account + capital account = net financial account); acceptable alternative: change in net international investment position; no = government financing needs"),
}
def base(pref, n, pat, query, cl, prov_sel, inst, style, val, tol, pub, pubnote, tag):
    m = META[pref]
    return {"id": f"{pref}-{n:02d}", "family": "methodology", "pattern": pat, "tier": "analytical", "status": "validated",
      "query": query, "claims": cl, "grading": {"method": "answer_recall"},
      "provenance": {"assembled_from": [m['quote'], "frozen WEO Oct 2025 (release/official_benchmark/reference_data)"],
                     "gold_script": "gold_scripts/external_sector/gold_external.py", "selection": prov_sel},
      "method": m['method'], "method_doc_ids": m['docs'], "gold_report_ids": [],
      "gold_report_note": "Gold is a printed identity applied to frozen WEO series; no corpus report states these values, nothing to withhold.",
      "published_value": pub, "published_value_note": pubnote, "recomputed_value": round(val, 3), "tolerance": tol,
      "inputs": m['inputs'], "style": style, "distractors": m['dist'], "famous_method": m['famous'],
      "validation_label": "formula-validated", "method_class": m['cls'],
      "formula_quote": m['quote'], "instance": inst, "claim_truth": tag}

def pool(fn, lo=2006, hi=2024):
    return fn, lo, hi
def pick(rng, ok, n, years=range(2006, 2025)):
    cs = CTRY[:]; rng.shuffle(cs); out = []
    for c in cs:
        ys = list(years); rng.shuffle(ys)
        for y in ys:
            if ok(c, y): out.append((c, y)); break
        if len(out) == n: break
    return out
def pubB(c, y): return v(B, c, y)

items = []
# ---------- EXS ----------
rng = random.Random(1101)
def okS(c, y):
    a = ca_si(c, y); b = v(B, c, y)
    return a is not None and b is not None and abs(a - b) < 0.01 and abs(a) >= 2.0
named = pick(rng, okS, 5)
def okS2(c, y): return okS(c, y)
hid = []; used = {c for c, _ in named}
cs = CTRY[:]; rng.shuffle(cs)
for c in cs:
    if c in used or len(hid) == 5: continue
    for y in rng.sample(range(2006, 2025), 19):
        if okS(c, y):
            a = ca_si(c, y); specs = [('S', '>'), ('I', '<')] if a > 0 else [('S', '<'), ('I', '>')]
            pr = find_pred(c, y, specs)
            if pr: hid.append((c, y, pr)); used.add(c); break
chk = pick(rng, lambda c, y: okS(c, y) and c not in used, 6)
n = 0
for c, y in named:
    n += 1; s, i = v(S, c, y), v(I, c, y); ca = s - i
    q = f"In {y}, {NAME[c]}'s gross national saving came to {f1(s)}% of GDP while gross investment reached {f1(i)}% of GDP. What does that imply for the economy's balance with the rest of the world, as a share of GDP, and was it a net lender or a net borrower?"
    cl = claims(META['EXS']['m_text'], META['EXS']['acc'], f"External balance {NAME[c]} {y} = {ca:.2f} % of GDP ({sgn(ca)})", ca, 0.15, 'pp',
      [{"id": "c2", "kind": "text", "importance": "vital", "text": f"States the economy is a net {'lender' if ca>0 else 'borrower'} to the rest of the world.", "accept": "full = correct sign/direction"}],
      "Uses national saving, gross investment and current account balance series from the WEO (NGSD_NGDP, NID_NGDP, BCA_NGDPD).", "full = within tolerance of saving minus investment")
    items.append(base('EXS', n, 'M-named', q, cl, "seeded draw (seed 1101); WEO identity S-I equals published BCA within 0.01pp; |CA|>=2pp; one per country", {"iso3": c, "year": y}, 'named', ca, 0.15, v(B, c, y), "IMF WEO Oct 2025 BCA_NGDPD (published current account, % GDP); matches S-I within 0.01pp", None))
for c, y, pr in hid:
    n += 1; ca = ca_si(c, y)
    q = f"In {y}, exactly one economy in the IMF's country data combined {pr_text(pr,'S')}. What was that economy's balance with the rest of the world as a share of GDP, and was it a net lender or net borrower?"
    cl = claims(META['EXS']['m_text'], META['EXS']['acc'], f"External balance of the identified economy ({NAME[c]}, {y}) = {ca:.2f} % of GDP", ca, 0.15, 'pp',
      [{"id": "c3", "kind": "text", "importance": "okay", "text": f"Identifies the economy as {NAME[c]}.", "accept": "full = correct country"},
       {"id": "c2", "kind": "text", "importance": "vital", "text": f"States the economy is a net {'lender' if ca>0 else 'borrower'}.", "accept": "full = correct direction"}],
      "Uses WEO saving, investment and current account series.", "full = within tolerance")
    it = base('EXS', n, 'M-hidden', q, cl, "seeded; hidden set size exactly 1 asserted by gold script", {"iso3": c, "year": y, "predicate_cols": pr}, 'hidden', ca, 0.15, v(B, c, y), "IMF WEO Oct 2025 BCA_NGDPD; matches S-I within 0.01pp", None)
    it['hidden_set_size'] = 1; it['predicate'] = pr_text(pr, 'S'); items.append(it)
for k, (c, y) in enumerate(chk):
    n += 1; s, i = v(S, c, y), v(I, c, y); ca = s - i; truth = (k % 2 == 0)
    stated = ca if truth else (ca + rng.choice([-1, 1]) * rng.choice([2.0, 3.0, 4.5]) if k % 4 == 1 else -ca)
    q = f"A report says that in {y} {NAME[c]}'s gross national saving was {f1(s)}% of GDP and gross investment {f1(i)}% of GDP, and that its balance with the rest of the world was therefore an external {'surplus' if stated>0 else 'deficit'} of {f1(abs(stated))}% of GDP. Is that statement correct?"
    cl = claims(META['EXS']['m_text'], META['EXS']['acc'], f"Correct external balance {NAME[c]} {y} = {ca:.2f} % of GDP; stated {stated:.1f}", ca, 0.15, 'pp',
      [yn(0, 'S', truth, f"Judges the statement {'correct' if truth else 'incorrect'} (recomputed balance {ca:.1f}% vs stated {stated:.1f}%).")],
      "Uses WEO saving, investment, current account series.", "full = recomputed within tolerance")
    items.append(base('EXS', n, 'M-claimcheck', q, cl, "seeded; half true, half false by shifted/flipped stated value", {"iso3": c, "year": y, "stated": round(stated, 2)}, 'claim_check', ca, 0.15, v(B, c, y), "IMF WEO Oct 2025 BCA_NGDPD", 'true' if truth else 'false'))
# ---------- EXP ----------
rng = random.Random(2202)
def okP(c, y):
    b, g = v(B, c, y), v(G, c, y)
    return b is not None and g is not None and abs(b) >= 2 and abs(g) >= 1.5 and abs(b - g) >= 1.0
named = pick(rng, okP, 5); used = {c for c, _ in named}
hid = []; cs = CTRY[:]; rng.shuffle(cs)
for c in cs:
    if c in used or len(hid) == 5: continue
    for y in rng.sample(range(2006, 2025), 19):
        if okP(c, y):
            specs = [('B', '<'), ('G', '>')] if v(B, c, y) < 0 else [('B', '>'), ('G', '<')]
            pr = find_pred(c, y, specs)
            if pr: hid.append((c, y, pr)); used.add(c); break
chk = pick(rng, lambda c, y: okP(c, y) and c not in used, 5)
def pq(c, y):
    b, g = v(B, c, y), v(G, c, y); return b - g
n = 0
def pcl(c, y, extra, comp_extra=''):
    b, g = v(B, c, y), v(G, c, y); p = b - g
    return claims(META['EXP']['m_text'], META['EXP']['acc'], f"Private-sector saving-investment balance {NAME[c]} {y} = {p:.2f} % of GDP{comp_extra}", p, 0.15, 'pp', extra,
      "Uses WEO current account balance and general government net lending (BCA_NGDPD, GGXCNL_NGDP).", "full = within tolerance of CA minus government balance")
def dir_claim(c, y, cid='c2'):
    p = pq(c, y)
    return {"id": cid, "kind": "text", "importance": "vital", "text": f"States that the private sector is a net {'lender (adds to the external surplus)' if p>0 else 'borrower (adds to the external deficit)'}.", "accept": "full = correct sign"}
for c, y in named:
    n += 1; b, g = v(B, c, y), v(G, c, y)
    q = f"In {y}, {NAME[c]} recorded an external {'surplus' if b>0 else 'deficit'} of {f1(abs(b))}% of GDP while its general government ran a {'surplus' if g>0 else 'deficit'} of {f1(abs(g))}% of GDP. How much of the external balance is accounted for by the private sector, as a share of GDP, and does the private sector add to or offset it?"
    items.append(base('EXP', n, 'M-named', q, pcl(c, y, [dir_claim(c, y)]), "seeded draw (seed 2202); |CA|>=2, |fiscal|>=1.5, |private|>=1pp; one per country", {"iso3": c, "year": y}, 'named', pq(c, y), 0.15, None, "no institutional source publishes the private balance as a series; CA and fiscal inputs are WEO published values", None))
for c, y, pr in hid:
    n += 1
    q = f"In {y}, exactly one economy in the IMF's country data combined {pr_text(pr,'P')}. How much of that economy's external balance was accounted for by its private sector, as a share of GDP, and does the private sector add to or offset the external balance?"
    it = base('EXP', n, 'M-hidden', q, pcl(c, y, [{"id": "c3", "kind": "text", "importance": "okay", "text": f"Identifies the economy as {NAME[c]}.", "accept": "full = correct country"}, dir_claim(c, y)]), "seeded; hidden set size exactly 1 asserted by gold script", {"iso3": c, "year": y, "predicate_cols": pr}, 'hidden', pq(c, y), 0.15, None, "private balance not published", None)
    it['hidden_set_size'] = 1; it['predicate'] = pr_text(pr, 'P'); items.append(it)
for k, (c, y) in enumerate(chk):
    n += 1; b, g = v(B, c, y), v(G, c, y); p = b - g; truth = (k % 2 == 0)
    stated = p if truth else (p + rng.choice([-1, 1]) * rng.choice([2.0, 3.0, 4.0]) if k % 4 == 1 else -p)
    q = f"A report notes that in {y} {NAME[c]} had an external {'surplus' if b>0 else 'deficit'} of {f1(abs(b))}% of GDP and a general government {'surplus' if g>0 else 'deficit'} of {f1(abs(g))}% of GDP, and concludes that the private sector's net lending (saving minus investment) was {f1(stated)}% of GDP. Is that conclusion correct?"
    items.append(base('EXP', n, 'M-claimcheck', q, pcl(c, y, [yn(0, 'P', truth, f"Judges the conclusion {'correct' if truth else 'incorrect'} (recomputed private balance {p:.1f}% vs stated {stated:.1f}%).")], f"; stated {stated:.1f}"), "seeded; half true, half false", {"iso3": c, "year": y, "stated": round(stated, 2)}, 'claim_check', p, 0.15, None, "private balance not published", 'true' if truth else 'false'))
# ---------- EXF ----------
rng = random.Random(3303)
def okF(c, y0):
    t = cum_ca_usd_bn(c, y0, y0 + 4)
    if t is None or t > -5: return False
    return all(v(B, c, y) is not None and v(B, c, y) < 0 for y in range(y0, y0 + 5))
def pickF(ex, k):
    cs = CTRY[:]; rng.shuffle(cs); out = []
    for c in cs:
        if c in ex: continue
        for y0 in rng.sample(range(2008, 2021), 13):
            if okF(c, y0): out.append((c, y0)); break
        if len(out) == k: break
    return out
named = pickF(set(), 4); used = {c for c, _ in named}
hid = []; cs = CTRY[:]; rng.shuffle(cs)
for c in cs:
    if c in used or len(hid) == 4: continue
    for y0 in rng.sample(range(2008, 2021), 13):
        if okF(c, y0):
            pr = find_pred(c, y0 + 4, [('D', '>'), ('B', '<')])
            if pr: hid.append((c, y0, pr)); used.add(c); break
chk = pickF(used, 4)
def fcl(c, y0, extra, comp_extra=''):
    t = -cum_ca_usd_bn(c, y0, y0 + 4)
    tol = round(max(0.3, 0.03 * t), 2)
    return claims(META['EXF']['m_text'], META['EXF']['acc'], f"Cumulative net external financing {NAME[c]} {y0}-{y0+4} = US$ {t:.1f} bn{comp_extra}", t, tol, 'US$ billion', extra,
      "Uses WEO current account balance (% GDP) and nominal GDP in US dollars (BCA_NGDPD, NGDPD).", "full = within tolerance (3% relative, floor 0.3)"), tol
n = 0
for c, y0 in named:
    n += 1; t = -cum_ca_usd_bn(c, y0, y0 + 4); cl, tol = fcl(c, y0, [])
    q = f"Roughly how much net foreign financing, in total and in US dollars, did {NAME[c]} have to raise between {y0} and {y0+4} to fund its external deficits?"
    it = base('EXF', n, 'M-named', q, cl, "seeded draw (seed 3303); five consecutive deficit years, cumulative >= US$5 bn; one per country", {"iso3": c, "y0": y0, "y1": y0 + 4, "absolute": True}, 'named', t, tol, None, "no published cumulative; annual BCA and NGDPD are WEO published values", None)
    items.append(it)
for c, y0, pr in hid:
    n += 1; t = -cum_ca_usd_bn(c, y0, y0 + 4); cl, tol = fcl(c, y0, [{"id": "c3", "kind": "text", "importance": "okay", "text": f"Identifies the economy as {NAME[c]}.", "accept": "full = correct country"}])
    q = f"In {y0+4}, exactly one economy in the IMF's country data had {pr_text(pr,'F')}. Roughly how much net foreign financing, in total and in US dollars, did that economy have to raise over the five years {y0} to {y0+4} to fund its external deficits?"
    it = base('EXF', n, 'M-hidden', q, cl, "seeded; hidden set size exactly 1 (evaluated in final year) asserted by gold script", {"iso3": c, "y0": y0, "y1": y0 + 4, "year": y0 + 4, "absolute": True, "predicate_cols": pr}, 'hidden', t, tol, None, "no published cumulative", None)
    it['hidden_set_size'] = 1; it['predicate'] = pr_text(pr, 'F'); items.append(it)
for k, (c, y0) in enumerate(chk):
    n += 1; t = -cum_ca_usd_bn(c, y0, y0 + 4); truth = (k % 2 == 0)
    stated = t if truth else t * rng.choice([0.5, 1.7, 2.2, 0.4])
    cl, tol = fcl(c, y0, [yn(0, 'F', truth, f"Judges the statement {'correct' if truth else 'incorrect'} (recomputed US$ {t:.1f} bn vs stated US$ {stated:.1f} bn).")], f"; stated {stated:.1f}")
    q = f"A report states that {NAME[c]} had to raise a net total of about US$ {stated:.0f} billion of foreign financing over {y0} to {y0+4} to fund its external deficits. Is that figure correct?"
    items.append(base('EXF', n, 'M-claimcheck', q, cl, "seeded; half true, half false", {"iso3": c, "y0": y0, "y1": y0 + 4, "absolute": True, "stated": round(stated, 2)}, 'claim_check', t, tol, None, "no published cumulative", 'true' if truth else 'false'))
for it in items:
    json.dump(it, open(os.path.join(OUT, it['id'] + '.json'), 'w'), indent=1)
from collections import Counter
print(Counter((i['method'], i['style']) for i in items))
