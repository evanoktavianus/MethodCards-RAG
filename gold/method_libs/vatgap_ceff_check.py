"""C-efficiency = VAT revenue / (standard rate x consumption). Check published figures using the
reports' OWN VAT revenue and rate, with WDI consumption shares, to see if the consumption base can be rebuilt from frozen data."""
import os
H=os.path.dirname(os.path.abspath(__file__))+"/../frozen_extra/"
W={}
for l in open(H+"wdi_taxeff_extract.psv"):
    c,i,p,v=l.rstrip("\n").split("|")
    W[(c,i)]={int(a):float(b) for a,b in zip(p.strip("{}").split(","),v.strip("{}").split(",")) if b not in("NULL","")}
# (country, iso3, year, VAT rev %GDP, std rate, published C-eff, report)
cases=[("Ecuador","ECU",2015,6.3,0.12,0.73,"Ecuador 2016 Art IV Annex V Table 1"),
       ("Namibia","NAM",2019,6.4,0.15,0.49,"Namibia 2022 Art IV Annex VIII (FY2019/20)")]
for n,iso,y,v,r,pub,src in cases:
    pc=W.get(("NE.CON.PRVT.ZS",iso),{}).get(y)
    if pc is None: print(n,"no private consumption"); continue
    ce=v/(r*pc)
    print(f"{n} {y}: implied C-eff with private consumption {ce:.2f} vs published {pub:.2f} (private cons {pc:.1f}% GDP) [{src}]")
