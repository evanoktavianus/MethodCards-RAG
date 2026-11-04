# Methods in the benchmark

440 surviving items (status not dropped) in 26 table rows below, which are 28 distinct methods: the `external_sector` row holds three (`saving_investment_gap_current_account` 16 items, `private_public_sector_balance_split` 15, `cumulative_external_financing_need` 12), and the item files label each by its own `method` value. Every surviving item now carries `validation_tier` and `procedure_kind` (where `validation_label` and `validation_tier` differ, `validation_tier` is the one to use, see the rule below). The parameter column was checked against the reference documents; the per-item evidence is in each item's `parameter_notes` and `doc_check` fields.

Tier rule used. published-validated: recomputed value matched a figure printed in an official publication within the item tolerance, 8 or more instances. formula-validated: an institutional document states a multi-parameter procedure and the gold reproduces it on frozen data, no published match. definition-validated: accounting identity or definition, or only partly reproduced (proxies, reduced index, no checkable published figure). Matching a database series that is built from the same identity (WDI real interest rate, WEO current account) does not count as published.

## Table

Band is an earlier grouping of the methods by judgment (easy, medium, hard). The two groups of the paper follow a four-point structure rule instead (+1 multi-step, +1 institutional procedure, +1 loose or free parameter, +1 not famous; 3-4 points = institutional procedures, `experiments/splits/hard.json`; otherwise standard formulas, `experiments/splits/easier.json`; the points of each method are in `experiments/main_run/rule_bands.json`). `scripts/make_band_sensitivity.py` reports the gain of our agent by Band.

Strictness: strict = the document fixes every number; loose = some numbers are ranges or proxies; free = the analyst chooses a key parameter. Famous = could a model do it from memory (item flag, majority).

| Method | Institution and document | Items | validation_tier | procedure_kind | Parameter strictness (key parameters) | Band | Famous |
|---|---|---|---|---|---|---|---|
| debt_stab (debt-stabilising primary balance) | IMF/Escolano 2010 eq 7, 2013 Staff Guidance Note (2dea3fb1) | 20 | published-validated (28 of 29 report instances) | textbook identity | strict (p* = lambda d*); effective interest definition loose | medium | yes |
| debt_path (debt change decomposition) | Escolano 2010 eq 26-28 (55319ff9); Guidance Note fn 4-5 | 20 | published-validated (74 report country-years) | institutional procedure | strict; two published variants accepted (inflation term separate or folded into real rate) | medium | no |
| gfn (gross financing needs) | IMF 2025 Guide (4315e3d9) eq 1-2 | 14 | published-validated (39 of 353 within 0.5 pp, 79 within 1.0; 34 distinct country-years) | institutional procedure | formula strict; amortisation source loose (schedule, maturity table or rate x stock); perimeter central vs general government | medium | no |
| lic_dsf_ci (LIC DSF composite indicator) | IMF Article IV DSAs (968df4c6, d7658e96) | 40 | published-validated (34 of 40 within 0.10) | institutional procedure | strict (6 coefficients, cutoffs 2.69 and 3.05; 10-year averages) | hard | no |
| structural_balance (cyclically adjusted balance and stance) | Fiscal Monitor Oct 2012 and Oct 2013 (afa3529e, 9a9aeb9c) | 34 | published-validated (228 country-years vs WEO structural balance; items drawn from matching part) | institutional procedure | elasticities strict (1 and 0); HP filter named; lambda and gap source free | hard | yes |
| debt_target_adjustment | Fiscal Monitor Apr 2014, Oct 2014, Oct 2013 (a9063586, 49b36e52, 9a9aeb9c) | 14 | published-validated (21 of 26 within 1.0 pp) | institutional procedure | strict (40 percent target, r-g to 1 by 2028, CAPB path) | hard | no |
| convergence_criteria (Maastricht tests) | WEO Oct 1996 (e3b52b4e) | 16 | formula-validated | institutional procedure | strict (3 percent, 60 percent, 1.5 pp over three best); CPI proxy for HICP, three lowest over EU27 loose | medium | yes |
| income_group_atlas | IMF External Debt Statistics Guide (bc5f813b) | 14 | formula-validated | institutional procedure | strict (2011 cut-offs 1,025 / 4,035 / 12,475); vintage-specific | easy | yes |
| growth_accounting (TFP residual) | Mexico 2004 Art IV box (270b189d); WEO Apr 2015 (3ed94aa0) | 13 | formula-validated | institutional procedure | shares 0.33/0.67 and 10 percent depreciation strict; initial capital stock free | hard | no |
| okun (gap-based cyclical unemployment) | WEO Oct 2012 Box 4.1 (bc66194c) | 14 | formula-validated | institutional procedure | coefficient 0.5 strict (convention given in query); gap source WEO | easy | no |
| okun_difference (first-difference regression) | WEO Apr 2010 ch. 3 (89d05760) | 16 | formula-validated | textbook identity | form strict; sample, intercept and lags free (query fixes them) | medium | yes |
| reserve_adequacy_traditional | IMF 2011 Assessing Reserve Adequacy (e7c9a1d0) | 14 | formula-validated | institutional procedure | strict (3 months, 100 percent STD, 20 percent M2); STD maturity and gold treatment loose | medium | yes |
| mac_dsa_stress | Guidance Note 2013 (2dea3fb1); MAC SRDSF 2021 | 14 | definition-validated | institutional procedure | shock sizes strict; interest pass-through loose; growth SD sample free | hard | no |
| fsi (fiscal stress index) | IMF WP/11/100 (b8ca4b08) | 14 | definition-validated (reduced index) | institutional procedure | thresholds and weights strict; proxies loose | hard | no |
| ara_em (reserve metric) | IMF 2011 (e7c9a1d0) | 12 | definition-validated | institutional procedure | weights strict; STD and portfolio liabilities proxies loose; regime free | hard | no |
| eir (effective interest rate) | Guidance Note fn 3 (2dea3fb1) | 16 | definition-validated | textbook identity | strict | easy | yes |
| irev (interest or debt to revenue) | Guidance Note Annex III (2dea3fb1) | 16 | definition-validated | textbook identity | debt-to-revenue named, interest-to-revenue not defined: loose | easy | yes |
| prices_real_growth | Escolano 2010 (55319ff9) | 12 | definition-validated | textbook identity | strict | easy | yes |
| prices_real_rate | Escolano 2010 Box 1 | 12 | definition-validated | textbook identity | strict (Fisher form) | easy | yes |
| prices_inflation_erosion | Escolano 2010 eq 26 | 12 | definition-validated | textbook identity | strict | easy | yes |
| real_interest_rate | AMRO Japan paper (0343a0da), textbook | 10 | definition-validated | textbook identity | exact vs simple difference loose (tolerance accepts both) | easy | yes |
| income_velocity | WEO 1985 table (eafc73b3), textbook | 10 | definition-validated | textbook identity | strict | easy | yes |
| CAID (current account = saving minus investment) | Romania 2019 Art IV Box 1 (8c217509); WEO Sep 2005 (e5c757ab) | 14 | definition-validated (1 of 2 published periods reproduced) | textbook identity | strict | easy | yes |
| external_sector (3 sub-methods: S-I, sector split, cumulative financing) | BPM6 ch. 14 (712b0ad9); EBA note (5319b022) | 43 | definition-validated | textbook identity | strict; capital account set to zero in cumulative item | easy to medium | mixed (31 yes, 12 no) |
| REER (real depreciation) | Slovak Rep. 2004 Art IV fn 8 (e946326c) | 12 | definition-validated | institutional procedure | definition strict; log vs ratio form loose | easy | no |
| pc_decomp (GDP per capita growth decomposition) | San Marino 2023 Art IV (a507cd39) | 14 | definition-validated | textbook identity | strict | medium | yes |

## Methods validated against published values (institutional)

debt_path (20), gfn (14), lic_dsf_ci (40), debt_target_adjustment (14), structural_balance (34; items were drawn where the recomputed value matches the WEO value). debt_stab (20) is validated against published values but is a textbook identity. Together these are 142 items.

## Easy tier

eir, irev, prices_real_growth, prices_real_rate, prices_inflation_erosion, real_interest_rate, income_velocity, CAID, REER, income_group_atlas, okun, and the S-I part of external_sector. All but REER, okun and income_group_atlas are famous: they test computation more than method retrieval.

## Excluded methods and limits of the keys

- Not in the set: real_depreciation (duplicate of REER); ara_em items 04 and 13; one growth_accounting item. Every method has at least one document that states the formula.
- Limits: irev (interest-to-revenue formula not printed), fsi (reduced index, rescaled), mac_dsa_stress (pass-through undefined, tolerance 5 pp), ara_em (proxies, no published agreement: 7 of 51 within 10 percent), CAID (published 2014-2018 period does not reproduce: data revisions), prices_* and real_interest_rate (identities, only a textbook source), structural_balance (HP lambda not in any document; items were drawn where the recomputed value matches WEO).
