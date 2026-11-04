"""Check for tax effort: can the published Table 3 values be reproduced from public series?
Uses the published Table 2 coefficients (col III, TNH) and WDI inputs. Deterministic frontier only
(the composite residual v_it, GOV dummy and corruption term are not observable from public series)."""
import csv, math, os
H = os.path.dirname(os.path.abspath(__file__)) + "/../frozen_extra/"
ISO = dict(Albania="ALB",Argentina="ARG",Armenia="ARM",Australia="AUS",Austria="AUT",Bangladesh="BGD",Belarus="BLR",Belgium="BEL",Brazil="BRA",Bulgaria="BGR",BurkinaFaso="BFA",Canada="CAN",Chile="CHL",**{"China,P.R.M.":"CHN"},Colombia="COL",CostaRica="CRI",Croatia="HRV",Cyprus="CYP",CzechRepublic="CZE",Denmark="DNK",DominicanRepublic="DOM",Egypt="EGY",ElSalvador="SLV",Estonia="EST",Ethiopia="ETH",Finland="FIN",France="FRA",**{"Gambia,The":"GMB"},Germany="DEU",Ghana="GHA",Greece="GRC",Guatemala="GTM",Guinea="GIN",**{"Guinea-Bissau":"GNB"},Guyana="GUY",Honduras="HND",Hungary="HUN",Iceland="ISL",India="IND",Indonesia="IDN",Ireland="IRL",Israel="ISR",Italy="ITA",Jamaica="JAM",Japan="JPN",Jordan="JOR",Kenya="KEN",Korea="KOR",KyrgyzRepublic="KGZ",Latvia="LVA",Lebanon="LBN",Lithuania="LTU",Luxembourg="LUX",Madagascar="MDG",Malawi="MWI",Mali="MLI",Moldova="MDA",Mongolia="MNG",Morocco="MAR",Mozambique="MOZ",Namibia="NAM",Netherlands="NLD",NewZealand="NZL",Nicaragua="NIC",Niger="NER",Norway="NOR",Pakistan="PAK",Panama="PAN",Paraguay="PRY",Peru="PER",Philippines="PHL",Poland="POL",Portugal="PRT",Romania="ROU",Senegal="SEN",SerbiaMontenegro="SRB",Singapore="SGP",SlovakRepublic="SVK",Slovenia="SVN",SouthAfrica="ZAF",Spain="ESP",SriLanka="LKA",Sweden="SWE",Switzerland="CHE",Tanzania="TZA",Thailand="THA",Togo="TGO",Tunisia="TUN",Turkey="TUR",Uganda="UGA",Ukraine="UKR",UnitedKingdom="GBR",UnitedStates="USA",Uruguay="URY",Vietnam="VNM",Zambia="ZMB")
def load():
    d = {}
    for line in open(H + "wdi_taxeff_extract.psv"):
        c, i, p, v = line.rstrip("\n").split("|")
        ps = p.strip("{}").split(","); vs = v.strip("{}").split(",")
        d[(c, i)] = {int(a): float(b) for a, b in zip(ps, vs) if b not in ("NULL", "")}
    return d
def near(s, y, k=3):
    for dy in range(k + 1):
        for yy in (y - dy, y + dy):
            if yy in s: return s[yy], yy
    return None, None
def main():
    W = load()
    rows = list(csv.DictReader(open(H + "fenochietto_pessino_table3.csv")))[:96]
    # Table 2 column III (TNH): frontier coefficients
    b = dict(c=-1.98777, LGD=1.15868, AVA=-0.00364, PE=0.03113, TR=0.00111, GINI=-0.00857, LGD2=-0.05904)
    out = []
    for r in rows:
        iso = ISO[r["country"]]; y = int(r["year"])
        g = lambda code: near(W.get((code, iso), {}), y)[0]
        tax = g("GC.TAX.TOTL.GD.ZS"); soc = g("GC.REV.SOCL.ZS"); rev = g("GC.REV.XGRT.GD.ZS")
        pc = g("NY.GDP.PCAP.PP.KD"); tr = g("NE.TRD.GNFS.ZS"); ava = g("NV.AGR.TOTL.ZS"); pe = g("SE.XPD.TOTL.GD.ZS"); gini = g("SI.POV.GINI")
        if None in (pc, tr, ava, pe, gini): out.append((r["country"], y, None)); continue
        lgd = math.log(pc); 
        xb = b["c"] + b["LGD"]*lgd + b["LGD2"]*lgd**2 + b["AVA"]*ava + b["PE"]*pe + b["TR"]*tr + b["GINI"]*gini
        cap_det = math.exp(xb) * 100 / 100  # tot is in percent: Ltot = ln(tot)
        out.append((r["country"], y, cap_det, float(r["capacity_TNH"]), float(r["total_revenue_pct_gdp"]), float(r["effort_TNH"])))
    ok = [o for o in out if o[2] is not None]
    print("rows with all inputs:", len(ok), "of", len(out))
    within = 0
    for o in ok:
        rel = (o[2] - o[3]) / o[3]
        within += abs(rel) <= 0.10
        print(f"{o[0]:18s}{o[1]} det.frontier {o[2]:6.1f} published capacity {o[3]:5.1f} rel {rel:+.2f}")
    print("capacity within 10 percent:", within, "of", len(ok))
    eerr = [o[4] / o[2] - o[5] for o in ok]  # recomputed effort (published revenue / det. capacity) minus published TNH effort
    print("effort: mean signed error %.3f, mean abs error %.3f" % (sum(eerr)/len(eerr), sum(abs(e) for e in eerr)/len(eerr)))
    for tol in (0.03, 0.05, 0.07, 0.10):
        print("effort within +-%.2f: %d of %d" % (tol, sum(abs(e) <= tol for e in eerr), len(eerr)))
main()
