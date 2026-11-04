# Data index

`DATA_INDEX.csv` is the catalogue of the frozen series (columns: release, code, name, countries, first_period, last_period); `DATA_OVERVIEW.md` lists the codes by family. Data fetched from outside these releases is frozen in `frozen_extra/` and logged in `frozen_extra/FREEZE_EXTRA.md`.

| Where | What | Size |
|---|---|---|
| `DATA_INDEX.csv`, release WEO_2025_OCT_VINTAGE | IMF WEO Oct 2025 (debt, balances, GDP, inflation, output gap, current account) | 44 codes |
| `DATA_INDEX.csv`, release WDI_2026-10-08 | World Bank WDI (not a frozen vintage; values can change on a later release) | 1,497 codes |
| `DATA_INDEX.csv`, release PSD_2026-10-14 | World Bank Public Sector Debt, quarterly (levels by instrument, creditor, maturity "L1" due within a year) | 564 codes |
| `frozen_extra/` | Frozen extracts used to derive the item gold (WEO long, WDI subsets, PSD maturity, IMF IIP) | see FREEZE_EXTRA.md |

The data tool (`tools/data/store/`, `meta.json`) serves the WDI and Public Sector Debt releases of 2026-10-08. The file `frozen_extra/psd_20261014_maturity_extract.psv` is a separate extract from the 2026-10-14 Public Sector Debt release, read by the prompt builder.

How to read the codes: PSD suffixes `.CG` central government, `.GG` general government, `.BC` budgetary central, `.CD` US$, `.Z1` % of GDP, none = national currency. Definitions beyond the name column are those of the publishing institution.

Not in the index: GFN-style amortisation schedules for loans in all countries, VAT rate schedules, EBA regressors (net foreign assets, demographics), fiscal-multiplier characteristics (exchange-rate regime, labour rigidity), forecast vintages other than Oct 2025.

Regenerate: one `\copy` over `series_data` joined to `series_releases` and `indicator_embeddings`; releases 24 and 106 are WEO, 62 WDI, 107 PSD.

## frozen_extra files
- FREEZE_EXTRA.md
- corpus_ara_text_blocks_20261030.tsv
- corpus_dsa_gfn_tables_20261030.tsv
- debt_path_tables
- fenochietto_pessino_table3.csv
- fm_apr2014_statistical_tables_13a_14.txt
- imf_iip_20261029_portfolio_other_liab.psv
- long_extract.csv
- psd_20261014_maturity_extract.psv
- wdi_20261008_ara_ig_extract.psv
- wdi_20261008_cpia_irai.csv
- wdi_20261008_fires_totl_cd.csv
- wdi_20261008_monetary_other.psv
- wdi_20261008_ne_imp_gnfs_cd.csv
- wdi_20261008_pa_nus_fcrf.csv
- wdi_20261008_remit_gdp.csv
- wdi_20261008_extract.psv
- wdi_taxeff_extract.psv
- weo_oct2025_bca.csv
- weo_oct2025_bca_ngdpd.csv
- weo_oct2025_ggr.csv
- weo_oct2025_ggr_ngdp.csv
- weo_oct2025_ggsb.csv
- weo_oct2025_ggsb_npgdp.csv
- weo_oct2025_ggx.csv
- weo_oct2025_ggx_ngdp.csv
- weo_oct2025_ggxcnl.csv
- weo_oct2025_ggxcnl_ngdp.csv
- weo_oct2025_ggxonlb.csv
- weo_oct2025_ggxonlb_ngdp.csv
- weo_oct2025_ggxwdg.csv
- weo_oct2025_ggxwdg_ngdp.csv
- weo_oct2025_ggxwdn.csv
- weo_oct2025_ggxwdn_ngdp.csv
- weo_oct2025_le.csv
- weo_oct2025_long.csv
- weo_oct2025_lp.csv
- weo_oct2025_lur.csv
- weo_oct2025_ngap_npgdp.csv
- weo_oct2025_ngdp.csv
- weo_oct2025_ngdp_d.csv
- weo_oct2025_ngdp_fy.csv
- weo_oct2025_ngdp_r.csv
- weo_oct2025_ngdp_rpch.csv
- weo_oct2025_ngdpd.csv
- weo_oct2025_ngdpdpc.csv
- weo_oct2025_ngdppc.csv
- weo_oct2025_ngdprpc.csv
- weo_oct2025_ngdprppppc.csv
- weo_oct2025_ngsd_ngdp.csv
- weo_oct2025_nid_ngdp.csv
- weo_oct2025_pcpi.csv
- weo_oct2025_pcpie.csv
- weo_oct2025_pcpiepch.csv
- weo_oct2025_pcpipch.csv
- weo_oct2025_pppex.csv
- weo_oct2025_pppgdp.csv
- weo_oct2025_ppppc.csv
- weo_oct2025_pppsh.csv
- weo_oct2025_tm_rpch.csv
- weo_oct2025_tmg_rpch.csv
- weo_oct2025_tx_rpch.csv
- weo_oct2025_txg_rpch.csv

