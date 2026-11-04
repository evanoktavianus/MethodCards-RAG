# Frozen extras for the methodology items (2026-10-30)

Source: the indicator database (World Bank WDI, WEO and Public Sector Debt releases), tables `series_releases`/`series_data`, read-only SELECT.
Extract file: `long_extract.csv` (columns release,code,iso3,period,value). Extracted 2026-10-30.

| Source | Release (pin) | Codes |
|---|---|---|
| IMF WEO | `WEO_2025_OCT_VINTAGE` (release id 24, status ready) | GGXONLB_NGDP (primary balance % GDP), GGXCNL_NGDP (overall balance), GGXWDG_NGDP and GGXWDG (gross debt, % GDP and national currency), NGDP (nominal GDP, national currency), NGDP_D (GDP deflator), NGDP_R, NGDP_RPCH, GGR_NGDP, GGX_NGDP, GGSB_NPGDP (structural balance), NGAP_NPGDP (output gap), TX_RPCH, TXG_RPCH |
| World Bank WDI | `WDI_2026-10-08` (release id 62, status current at extraction; NOT a frozen vintage, so values may change on a later WDI release; this extract is the freeze) | GC.TAX.TOTL.GD.ZS, GC.TAX.TOTL.CN, GC.REV.XGRT.CN, GC.REV.XGRT.GD.ZS, GC.TAX.GSRV.CN, GC.TAX.YPKG.CN, GC.TAX.INTT.CN, GC.TAX.IMPT.CN, GC.XPN.INTP.CN, GC.XPN.INTP.RV.ZS, GC.DOD.TOTL.GD.ZS, NY.GDP.MKTP.CN/KN/CD, NY.GDP.PCAP.CD/PP.CD, NE.TRD.GNFS.ZS, NV.AGR.TOTL.ZS, SP.POP.TOTL |

Gold derivation for the items may consume only the files in this directory and the reference_data directory of the released benchmark.

## Additional extracts (2026-10-30)
| File | Source / endpoint | Vintage | Extracted | Contents |
|---|---|---|---|---|
| psd_20261014_maturity_extract.psv | indicator database, series_data release 107 (World Bank Public Sector Debt) | PSD_2026-10-14 | 2026-10-30 | Q4 values: DP.DOD.DSTC.CR.CG/GG, DP.DOD.DLTC.CR.L1.CG/GG, DP.DOD.DECT.CR.CG/GG, DP.DOD.DLTC.CR.CG, DP.DOD.DLTC.CR.M1.CG, DP.DOD.DECF.CR.CG/GG |
| wdi_20261008_extract.psv | indicator database, release 62 (WDI) | WDI_2026-10-08 | 2026-10-30 | SP.DYN.TFRT.IN, SP.POP.DPND.OL, FI.RES.TOTL.CD, DT.DOD.DSTC.CD, FM.LBL.BMNY.CN, BX.GSR.GNFS.CD, NY.GDP.MKTP.CN/CD, NE.CON.PRVT.CN (NOT a frozen vintage; this file is the freeze) |
| imf_iip_20261029_portfolio_other_liab.psv | IMF SDMX 2.1 API https://api.imf.org/external/sdmx/2.1/data/IMF.STA,IIP/.L_P.P_MV+O.USD.A?startPeriod=2005 (JSON) | IIP dataflow, response prepared 2026-10-29 | 2026-10-30 | Liabilities positions, portfolio investment (P_MV) and other investment (O), USD, annual, 2005 onward |
| corpus_dsa_gfn_tables_20261030.tsv | corpus database table document_blocks (type table, DSA tables with 'Public gross financing needs') | corpus as of 2026-10-30 | 2026-10-30 | 657 table blocks (document id, sequence, table text with ~ for newlines) |
| corpus_ara_text_blocks_20261030.tsv | corpus, text blocks mentioning percent of the ARA metric | same | same | 347 blocks |
| fm_apr2014_statistical_tables_13a_14.txt | corpus doc a9063586 (Fiscal Monitor April 2014), blocks 935-955 | same | same | Statistical Tables 13a (AE) and 14 (EM) with notes |
