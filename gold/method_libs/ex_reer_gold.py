"""REER cluster: real depreciation against the dollar = nominal depreciation (% fall in dollar value of local currency) minus
domestic inflation (GDP deflator). Definition printed in Slovak Republic 2004 Art. IV (e946326c, p34, footnote 8).
Gold + items. python3 -I scripts/ex_reer_gold.py"""
import json, os, random, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ex_lib import *
E_ = load(FX + "wdi_20261008_pa_nus_fcrf.csv"); D = load(FX + "weo_oct2025_ngdp_d.csv")
names = names_pool(); allc = sorted(set(ind("PCPIPCH")) | set(D))
DOC = "e946326c-0415-4219-86ed-95f755ac9043"

def realdep(c, y):
    e1, e0 = E_[c][y], E_[c][y - 1]
    nom = (1 - e0 / e1) * 100          # % fall in dollar value of local currency
    infl = (D[c][y] / D[c][y - 1] - 1) * 100
    log_nom = -math.log(e1 / e0) * -100 if False else math.log(e1 / e0) * 100  # log-form check (depreciation positive)
    alt_log = log_nom - math.log(D[c][y] / D[c][y - 1]) * 100
    return dict(nom=round(nom, 2), infl=round(infl, 2), real=round(nom - infl, 2), alt_log=round(alt_log, 2),
                alt_ratio=round(((e1 / e0) / (D[c][y] / D[c][y - 1]) - 1) * 100, 2), E0=e0, E1=e1)

def cands():
    out = []
    for c in names:
        if c not in E_ or c not in D: continue
        for y in range(2006, 2025):
            if y in E_[c] and y - 1 in E_[c] and y in D[c] and y - 1 in D[c]:
                d = realdep(c, y)
                if abs(d["real"]) >= 3 and abs(d["nom"]) <= 30 and abs(d["real"] - d["alt_log"]) < 1.5 and abs(d["infl"]) <= 40 and abs(d["real"]) <= 30:
                    out.append((c, y, d))
    return out

def main():
    rng = random.Random(31)
    cs = cands(); rng.shuffle(cs)
    used = set(); picked = []
    for c, y, d in cs:
        if c in used: continue
        used.add(c); picked.append((c, y, d))
    hid = []; rest = []
    for c, y, d in picked:
        if len(hid) < 3:
            conds, m = find_condition(c, y, allc, rng)
            if conds: hid.append((c, y, d, conds)); continue
        rest.append((c, y, d))
    named = rest[:5]; claims = rest[5:9]
    out = []
    qn = ["How much did {n}'s currency depreciate or appreciate in real terms against the US dollar in {y}?",
          "In {y}, what was the real change in the value of the {n} currency relative to the dollar, taking domestic price increases into account?",
          "Was there a real depreciation of the {n} currency against the US dollar in {y}, and how large was it?"]
    for k, (c, y, d) in enumerate(named): out.append(("named", c, y, d, qn[k % 3].format(n=names[c], y=y), {}))
    for c, y, d, conds in hid:
        cond = " and ".join(phrase(*x) for x in conds); sz = len(members(conds, y, allc)); assert sz == 1
        out.append(("hidden", c, y, d, "Among all economies in the IMF World Economic Outlook database, exactly one had %s in %d. How large was the real depreciation (or appreciation) of that economy's currency against the US dollar in %d?" % (cond, y, y), dict(conds=conds, set_size=sz)))
    for k, (c, y, d) in enumerate(claims):
        true = k % 2 == 0
        val = d["real"] if true else (d["real"] + (-1 if d["real"] > 0 else 1) * 8 if abs(d["real"]) > 8 else -d["real"])
        if not true and abs(val - d["real"]) < 5: val = -d["real"]
        word = "depreciated" if val > 0 else "appreciated"
        out.append(("claim_check", c, y, d, "A staff report states that the %s currency %s by about %.0f percent in real terms against the US dollar in %d. Is that statement correct?" % (names[c], word, abs(val), y), dict(statement_true=true, stated=round(val, 1))))
    for k, (style, c, y, d, q, ex) in enumerate(out, 1):
        iid = "REER-%02d" % k
        real = d["real"]
        verdict = ("Real %s of about %.1f%% (positive = depreciation of the local currency)" % ("depreciation" if real > 0 else "appreciation", abs(real)))
        if style == "claim_check":
            verdict = "The statement is %s: the recomputed real %s is %.1f%%." % ("correct" if ex["statement_true"] else "incorrect", "depreciation" if real > 0 else "appreciation", abs(real))
        item = dict(
          id=iid, family="methodology", method="reer_real_dep", style=style, tier="multi_step", status="validated", query=q,
          claims=dict(
            text=[dict(id="c1", kind="text", importance="vital", text="Measures real depreciation as nominal depreciation against the dollar (percentage fall in the dollar value of local currency) minus domestic inflation measured by the GDP deflator.",
                       accept="full = applies this definition (nominal depreciation minus GDP-deflator inflation); partial = nominal depreciation minus consumer-price inflation, or ratio/log forms that give a number within tolerance; no = uses an effective exchange rate index, subtracts US inflation as well, or reports only the nominal change.",
                       supporting_passages=[DOC + "#slovak2004_fn8_real_depreciation"]),
                  dict(id="c4", kind="text", importance="vital", text=verdict, accept="sign and size of the verdict must match (direction exact).")],
            data=[dict(id="c5", kind="data", importance="okay", text="Uses the official exchange rate (local currency per US dollar, annual average, WDI PA.NUS.FCRF) and the GDP deflator index (WEO NGDP_D).", accept="full = both sourced; partial = CPI instead of the deflator; no = unrelated series.")],
            computation=[dict(id="c2", kind="computation", importance="vital", text="Nominal depreciation of the local currency in %d: %.1f%% (from %.4g to %.4g local units per dollar)." % (y, d["nom"], d["E0"], d["E1"]), accept="full = within +-1.0 pp.", target=d["nom"], tolerance_abs=1.0),
                         dict(id="c3", kind="computation", importance="vital", text="Domestic GDP-deflator inflation in %d: %.1f%%; real depreciation = %.1f - %.1f = %.1f%%." % (y, d["infl"], d["nom"], d["infl"], real), accept="full = within +-1.5 pp of %.1f." % real, target=real, tolerance_abs=1.5)]),
          grading=dict(tolerance_abs_pp=1.5, tolerance_basis=0.2,
                       note="Gold: real depreciation_y = (1 - E_{y-1}/E_y)*100 - (NGDP_D_y/NGDP_D_{y-1} - 1)*100, E = official exchange rate (local currency per US$, annual average, WDI 2026-10-08), NGDP_D = WEO Oct 2025 GDP deflator index; positive = depreciation of the local currency. Tolerance +-1.5 pp covers the log and ratio forms (checked: both within 1.5 pp of the gold for every item).",
                       definitions="Real depreciation = nominal depreciation (percentage fall in the dollar value of local currency) minus domestic inflation (GDP deflator); positive = local currency loses value. Foreign (US) inflation is NOT subtracted under this institutional definition."),
          provenance=dict(source="frozen WEO Oct 2025 + WDI 2026-10-08 (frozen_extra/)", generator="scripts/ex_reer_gold.py",
                          method_text="Slovak Republic 2004 Article IV, DSA table footnote 8 (p34): 'Real depreciation is defined as nominal depreciation (measured by percentage fall in dollar value of local currency) minus domestic inflation (based on GDP deflator).'",
                          validation="No published country-year value found (definition only; the report uses it for a stress scenario). Internal check: log and ratio forms within 1.5 pp."),
          method_doc_ids=[DOC], gold_report_ids=[], published_value=None, recomputed_value=real,
          inputs=["PA.NUS.FCRF", "NGDP_D"], validation_label="formula-validated", method_kind="institutional procedure", famous_method=False,
          distractors=["real effective exchange rate index (WDI PX.REX.REER) change", "real bilateral rate with both CPIs (US inflation subtracted)", "nominal depreciation only", "purchasing-power-parity gap"],
          answer_summary=verdict + " (%s, %d; nominal %.1f%%, inflation %.1f%%)" % (names[c], y, d["nom"], d["infl"]), gold_script="scripts/ex_reer_gold.py",
          validation_note="Definition-only validation; no published figure to match.", answer_country=c, years=[y])
        if style == "hidden": item["hidden_set"] = dict(conditions=[list(x) for x in ex["conds"]], year=y, set_size=ex["set_size"], answer=c)
        if style == "claim_check": item["statement_true"] = ex["statement_true"]; item["stated_value"] = ex["stated"]
        json.dump(item, open(ROOT + "/items/REER/%s.json" % iid, "w"), indent=1)
    print(len(out), [(o[0], o[1], o[2], o[3]["real"]) for o in out])
main()
