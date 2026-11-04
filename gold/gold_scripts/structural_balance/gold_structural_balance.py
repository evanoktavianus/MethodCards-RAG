"""Gold for structural-balance items. python3 -I gold_structural_balance.py [--write]
Reads only release reference_data + frozen_extra. Prints each item's recomputed value and the hidden-subject set size."""
import sys, os, csv, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sblib import *
from sb_spec import ITEMS as ALL, TOL
ITEMS = [i for i in ALL if i["kind"] in ("cab", "stance", "cab_claim", "cyc_claim") ]
ITEMS.append(dict(id="SB-18", style="claim", kind="cab_claim", c="BEL", y=2022, name="Belgium", claim_value=-4.6,
  query="A report on Belgium states: 'Belgium's general government deficit was 3.6% of GDP in 2022, but with the economy at its normal capacity level the deficit would have been larger, about 4.6% of GDP.' Is that statement accurate?"))
ITEMS = [i for i in ITEMS if i["id"] != "SB-18" or i["c"] == "BEL"]
ITEMS.sort(key=lambda i: i["id"])
# renumber to contiguous ids
for n, it in enumerate(ITEMS, 1): it["id"] = "SB-%02d" % n

D = {k: load(k) for k in ["ngdp_rpch","ggxwdg_ngdp","lur","pcpipch","ggxcnl_ngdp","ggr_ngdp","ggx_ngdp","ngdp_r","ggsb_npgdp","ngap_npgdp"]}
wb = {r["iso3"]: r for r in csv.DictReader(open(REF + "/wb_classifications.csv"))}
econ = [c for c in D["ngdp_r"] if c in wb and wb[c]["income_group"] not in ("Aggregates", "")]
hp = {}
def gap(c, y):
    if c not in hp: hp[c] = hp_gap(D["ngdp_r"][c], 1980, 2030, 100.0)
    return hp[c][y]
def cab(c, y): return cab_pot(D["ggr_ngdp"][c][y], D["ggx_ngdp"][c][y], gap(c, y))

out = []
for it in ITEMS:
    c, y, k = it["c"], it["y"], it["kind"]
    ob = D["ggxcnl_ngdp"][c][y]; sbv = D["ggsb_npgdp"][c][y]
    if it["style"] == "hidden":
        S = [e for e in econ if all(y in D[a].get(e, {}) and d * (D[a][e][y] - t) > 0 for a, d, t, _ in it["pred"])]
        assert S == [c], (it["id"], S)
        it["set_size"] = len(S)
    if k in ("cab", "cab_claim"):
        rec, pub, tol = cab(c, y), sbv, TOL["cab"]
    elif k == "stance":
        rec, pub, tol = cab(c, y) - cab(c, y - 1), sbv - D["ggsb_npgdp"][c][y - 1], TOL["stance"]
    elif k == "cyc_claim":
        rec, pub, tol = (cab(c, y) - ob) / abs(ob), (sbv - ob) / abs(ob), 0.15
    it.update(rec=rec, pub=pub, tol=tol, ob=ob)
    if k in ("cab_claim",): it["truth"] = abs(rec - it["claim_value"]) <= 0.5
    if k == "cyc_claim": it["truth"] = abs(rec - it["claim_share"]) <= 0.15
    assert abs(rec - pub) <= tol, (it["id"], rec, pub)
    print(it["id"], it["style"], k, c, y, "recomputed %.3f published(WEO) %.3f overall %.2f" % (rec, pub, ob), "truth=%s" % it.get("truth"), "set=%s" % it.get("set_size"))

if "--write" in sys.argv:
    od = os.path.join(ROOT, "items", "structural_balance"); os.makedirs(od, exist_ok=True)
    MD = ["afa3529e-c97c-45cb-a668-d1a133131d8c", "9a9aeb9c-3a8b-4e2e-a459-aa8143f05d3f"]
    for it in ITEMS:
        c, y, k = it["c"], it["y"], it["kind"]
        rev = ["GGR_NGDP", "GGX_NGDP", "NGDP_R"]; inputs = rev + ["GGXCNL_NGDP"]
        stance = k == "stance"
        if k == "cab": t = "Underlying (capacity-level) balance %s %d = %.2f %% of potential GDP" % (c, y, it["rec"])
        elif stance: t = "Change in underlying balance %s %d-%d = %.2f pp of GDP" % (c, y - 1, y, it["rec"])
        elif k == "cyc_claim": t = "Cyclical share of the %s %d deficit = %.2f" % (c, y, it["rec"])
        else: t = "Underlying balance %s %d = %.2f %% of potential GDP" % (c, y, it["rec"])
        comp = [{"id": "c1", "kind": "computation", "importance": "vital", "text": t,
                 "reference_value": round(it["rec"], 3), "tolerance": it["tol"], "unit": "pp" if k != "cyc_claim" else "share",
                 "accept": "full = within tolerance; the output gap is the HP-filter (lambda=100) cycle of log real GDP, revenue elasticity 1, expenditure elasticity 0"}]
        verdict = []
        if "truth" in it:
            verdict = [{"id": "c4", "kind": "text", "importance": "vital",
                        "text": "Judges the statement %s." % ("ACCURATE" if it["truth"] else "NOT accurate"), "accept": "verdict must match; reasoning must cite the recomputed value"}]
        if stance:
            verdict = [{"id": "c4", "kind": "text", "importance": "vital", "text": "States whether the underlying fiscal stance %s." % ("tightened" if it["rec"] > 0 else "loosened"),
                        "accept": "direction must match the sign of the change in the underlying balance"}]
        item = {
          "id": it["id"], "family": "methodology", "pattern": "M-" + it["style"], "tier": "analytical", "status": "validated", "query": it["query"],
          "claims": {"text": [{"id": "c0", "kind": "text", "importance": "vital",
                      "text": "Identifies that the answer requires cyclically adjusting the budget balance (potential-output gap from a statistical trend, then removing the cyclical budget component).",
                      "accept": "full = names cyclically adjusted / structural balance approach with an output-gap estimate; acceptable alternatives: OECD or EC semi-elasticity approach, production-function output gap; no = raw balance only"}] + verdict,
                     "data": [{"id": "c5", "kind": "data", "importance": "okay", "text": "Uses general government revenue, expenditure and real GDP series from the WEO (%s)." % ", ".join(inputs)}],
                     "computation": comp},
          "grading": {"method": "answer_recall"},
          "provenance": {"assembled_from": ["Fiscal Monitor Oct 2012 / Oct 2013 data-conventions note (CAB: HP potential output, revenue elasticity 1, expenditure elasticity 0)", "frozen WEO Oct 2025 (+frozen_extra)"],
                         "gold_script": "gold_scripts/structural_balance/gold_structural_balance.py"},
          "method": "cyclically_adjusted_balance_hp_filter",
          "method_doc_ids": MD, "method_doc_alternatives": ["5bc9162b-f850-4bd4-a964-d3632f04cb9b (multivariate filter, alternative output-gap method)"],
          "gold_report_ids": [], "gold_report_note": "No corpus country report states these values; published value is the IMF WEO Oct 2025 GGSB_NPGDP series (frozen), not a corpus document, so nothing needs withholding.",
          "published_value": round(it["pub"], 3), "recomputed_value": round(it["rec"], 3), "tolerance": it["tol"],
          "inputs": inputs, "style": it["style"],
          "distractors": ["debt-stabilising primary balance", "fiscal multiplier / fiscal impulse from multipliers", "revenue buoyancy", "fiscal rule calibration"],
          "famous_method": True, "hidden_set_size": it.get("set_size"), "predicate": [p[3] for p in it["pred"]] if "pred" in it else None}
        json.dump(item, open(os.path.join(od, it["id"] + ".json"), "w"), indent=1)
    print("wrote", len(ITEMS))
