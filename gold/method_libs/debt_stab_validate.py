"""Validate the implementation against the report's OWN published inputs (DSA baseline tables in country reports).
python3 -I scripts/debt_stab_validate.py  -> writes scripts/debt_stab_validation.json and prints a table.
Published value convention: last projection year; p* = d_{T-1}(r_T-g_T)/(1+g_T) [+ other identified debt-creating flows_T] (IMF footnote 9: 'key variables ... remain at the level of the last projection year').
Tolerance (flow-adjusted variant adds 0.15 because the other-flows term is derived from three rounded rows): 0.05 (rounding of published value) + 0.001*d_prev (r and g published to 0.1pp)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import debt_stab_lib as L
here = os.path.dirname(os.path.abspath(__file__))
inst = json.load(open(os.path.join(here, "debt_stab_instances.json")))
# instances excluded for column-alignment reasons found on manual inspection of the table
EXCLUDE = {"37b14395": "published stabilising balance cell missing in parsed table (-2.1 is the cumulative primary deficit)",
           "d978f18a": "column alignment failed (picked a 2020 column); not re-parsed"}
rows = []
for k in inst:
    k["short"] = k["doc_id"][:8]
    if k["short"] in EXCLUDE:
        rows.append(dict(k, status="EXCLUDED", note=EXCLUDE[k["short"]])); continue
    pure = L.stab_general(k["d_prev"], k["eff_rate"], k["nominal_growth"])
    other = round(k["identified_flows_T"] - k["primary_deficit_T"] - k["rate_growth_term_T"], 1)
    withother = pure + other
    tol = 0.05 + 0.001 * k["d_prev"]
    pub = k["published"]
    m_pure = abs(pure - pub) <= tol
    tol_o = tol + 0.15   # 'other flows' is derived from three rounded table rows (+-0.15)
    m_other = abs(withother - pub) <= tol_o
    if m_pure: st, used = "MATCH", pure
    elif m_other: st, used = "MATCH_WITH_OTHER_FLOWS", withother
    else: st, used = "MISMATCH", pure
    rows.append(dict(k, pure=round(pure, 3), other_flows=other, with_other=round(withother, 3), tol=round(tol, 3), status=st, used=round(used, 3), diff=round(used - pub, 3)))
json.dump(rows, open(os.path.join(here, "debt_stab_validation.json"), "w"), indent=1)
for r in rows:
    if r["status"] == "EXCLUDED": print(r["short"], r["country"], r["year"], "EXCLUDED", r["note"]); continue
    print("%s %-12s %s pub %5.1f pure %6.2f other %5.1f both %6.2f tol %.2f %s" % (r["short"], r["country"], r["year"], r["published"], r["pure"], r["other_flows"], r["with_other"], r["tol"], r["status"]))
c = {}
for r in rows: c[r["status"]] = c.get(r["status"], 0) + 1
print(c)
