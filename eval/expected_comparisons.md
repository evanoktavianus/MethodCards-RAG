# Paired comparisons of the main run

Differences in points (0-100) of our agent (Ours-cards2) minus the other arm, with a 95% paired cluster bootstrap over methods (4,000 resamples, seed 1). Failed answers count 0. n = number of questions that have the metric in both arms.

## (a) Institutional procedures: ours minus ReAct and minus the LongDA-style baseline

| Metric | Ours | ReAct | Ours minus ReAct | LongDA-style | Ours minus LongDA-style |
|---|---|---|---|---|---|
| Method correctness (factual correctness) | 90.0 | 58.7 | +31.3 [+10.8, +55.4] (n=231) | 86.3 | +3.7 [-0.9, +9.3] (n=231) |
| Method explained | 86.3 | 68.5 | +17.7 [+6.8, +30.6] (n=231) | 85.1 | +1.2 [-1.4, +3.6] (n=231) |
| Data correctness | 69.5 | 56.3 | +13.2 [+6.7, +18.8] (n=231) | 66.9 | +2.6 [-8.6, +12.0] (n=231) |
| Computation correctness | 70.5 | 55.6 | +15.2 [+1.7, +29.0] (n=224) | 66.8 | +3.7 [-4.4, +11.1] (n=229) |
| Answer correctness | 77.1 | 61.4 | +15.7 [+6.7, +26.2] (n=231) | 74.9 | +2.2 [-2.3, +7.0] (n=231) |
| Fully correct answers | 45.0 | 25.1 | +19.9 [+5.3, +31.4] (n=231) | 45.0 | +0.0 [-8.2, +6.1] (n=231) |
| Context recall (method) | 75.3 | n/a | n/a | 57.5 | +17.8 [+0.2, +34.7] (n=231) |
| Context precision | 77.2 | n/a | n/a | 39.1 | +37.8 [+27.0, +47.7] (n=228) |
| Context recall (data) | 71.0 | 59.8 | +11.2 [+2.5, +17.7] (n=231) | 68.0 | +2.9 [-6.5, +11.1] (n=231) |
| Faithfulness | 64.5 | n/a | n/a | 49.8 | +14.6 [+4.8, +24.7] (n=231) |

## (a) Standard formulas: ours minus ReAct and minus the LongDA-style baseline

| Metric | Ours | ReAct | Ours minus ReAct | LongDA-style | Ours minus LongDA-style |
|---|---|---|---|---|---|
| Method correctness (factual correctness) | 89.0 | 84.8 | +4.2 [-3.0, +11.4] (n=209) | 94.2 | -5.1 [-11.4, -0.3] (n=209) |
| Method explained | 91.7 | 89.2 | +2.6 [-1.8, +7.5] (n=209) | 94.7 | -2.9 [-9.4, +1.9] (n=209) |
| Data correctness | 59.1 | 61.0 | -1.9 [-7.0, +3.8] (n=209) | 59.8 | -0.7 [-3.7, +2.5] (n=209) |
| Computation correctness | 83.1 | 84.6 | -1.6 [-8.8, +5.6] (n=209) | 85.7 | -2.6 [-8.3, +2.6] (n=209) |
| Answer correctness | 81.6 | 81.4 | +0.3 [-3.8, +4.3] (n=209) | 83.9 | -2.3 [-6.2, +1.1] (n=209) |
| Fully correct answers | 72.2 | 72.2 | +0.0 [-10.0, +10.5] (n=209) | 77.5 | -5.3 [-10.8, +0.0] (n=209) |
| Context recall (method) | 73.5 | n/a | n/a | 49.6 | +23.9 [+10.6, +37.5] (n=209) |
| Context precision | 81.1 | n/a | n/a | 18.6 | +63.1 [+48.0, +77.7] (n=204) |
| Context recall (data) | 69.4 | 66.3 | +3.3 [-1.9, +9.9] (n=208) | 70.2 | -0.6 [-2.2, +0.8] (n=208) |
| Faithfulness | 62.8 | n/a | n/a | 42.1 | +20.7 [+12.7, +28.8] (n=209) |

## (b) Oracle analysis (answer correctness; each cell minus both found)

| Group | Method given | Data given | Both given | Data given minus method given |
|---|---|---|---|---|
| Institutional procedures (means 77.1, 80.4, 83.4, 84.2) | +3.3 [-0.8, +9.3] | +6.3 [+2.1, +10.7] | +7.1 [-0.8, +15.6] | +3.0 [-2.8, +7.6] |
| Standard formulas (means 81.6, 83.3, 91.0, 89.9) | +1.7 [-2.7, +7.4] | +9.4 [+4.0, +15.3] | +8.2 [+0.9, +16.4] | +7.7 [+3.2, +12.9] |

## (c) Institutional procedures: robustness of the gain in answer correctness

| Subset | Questions | Ours minus ReAct | Ours minus LongDA-style |
|---|---|---|---|
| All | 231 | +15.7 [+6.7, +26.2] | +2.2 [-2.3, +7.0] |
| Reference answer matches a published value | 122 | +21.8 [+10.2, +37.4] | +3.6 [-5.1, +11.3] |
| Named economy and year | 83 | +18.0 [+8.7, +28.0] | +4.1 [+1.1, +7.7] |
| Economy described by conditions | 80 | +12.8 [+2.6, +23.4] | -1.3 [-6.5, +3.6] |
| Claim to check | 68 | +16.2 [+4.5, +28.5] | +4.0 [-3.0, +11.8] |
| Leave one method out (range over 13 runs) | 231 less one method | +9.6 to +17.0 | -0.3 to +3.7 |
| Numeric tolerances halved | 231 | +15.4 [+6.8, +24.7] | +2.0 [-2.1, +6.2] |
| Numeric tolerances doubled | 231 | +15.8 [+6.7, +26.8] | +2.6 [-2.3, +7.7] |

Rescoring at tolerance x1 differs from the stored score in 0 of the 231 rows of ours (should be 0).

Ours minus ReAct: positive for 10 of 13 methods; exact sign-flip test over methods (all 2^13 patterns, two-sided) p = 0.0024.
Ours minus LongDA-style: positive for 6 of 13 methods; exact sign-flip test over methods (all 2^13 patterns, two-sided) p = 0.5757.

## (c) Standard formulas: robustness of the gain in answer correctness

| Subset | Questions | Ours minus ReAct | Ours minus LongDA-style |
|---|---|---|---|
| All | 209 | +0.3 [-3.8, +4.3] | -2.3 [-6.2, +1.1] |
| Reference answer matches a published value | 20 | +10.7 [+10.7, +10.7] | +6.0 [+6.0, +6.0] |
| Named economy and year | 74 | +3.2 [-2.3, +9.2] | -1.2 [-5.2, +2.5] |
| Economy described by conditions | 74 | +0.7 [-7.2, +9.2] | -3.1 [-8.3, +2.0] |
| Claim to check | 61 | -3.8 [-10.9, +3.7] | -2.5 [-10.1, +3.7] |
| Leave one method out (range over 15 runs) | 209 less one method | -0.8 to +1.3 | -3.1 to -1.0 |
| Numeric tolerances halved | 209 | +0.3 [-3.8, +4.0] | -2.5 [-6.5, +1.0] |
| Numeric tolerances doubled | 209 | +0.7 [-3.0, +4.5] | -2.0 [-6.0, +1.2] |

Rescoring at tolerance x1 differs from the stored score in 0 of the 209 rows of ours (should be 0).

Ours minus ReAct: positive for 8 of 15 methods; exact sign-flip test over methods (all 2^15 patterns, two-sided) p = 0.8976.
Ours minus LongDA-style: positive for 4 of 15 methods; exact sign-flip test over methods (all 2^15 patterns, two-sided) p = 0.2642.

## (d) Gain of ours over ReAct against the memory-only score, all 28 methods

Spearman rank correlation between the memory-only answer correctness of a method (CoT0) and the gain of ours over ReAct: rho = -0.59 (permutation test, 200000 permutations, two-sided): p = 0.0012 (240 of 200000 permutations at least as extreme).
Pooled over all 440 questions: ours minus ReAct = +8.4; methods with a positive gain: 18 of 28; exact sign-flip test over the methods (all 2^28 sign patterns, two-sided): p = 0.0099 (2658728 of 268435456).

| Method | Memory only | Ours minus ReAct | Questions |
|---|---|---|---|
| fsi | 23.7 | +21.1 | 14 |
| reer_real_dep | 23.8 | +7.5 | 12 |
| ara_em | 33.3 | +25.3 | 12 |
| lic_dsf_composite_indicator | 33.4 | +44.9 | 40 |
| mac_dsa_stress | 34.5 | +16.1 | 14 |
| eir | 35.3 | +14.0 | 16 |
| inflation_erosion_of_debt_ratio | 40.6 | +2.9 | 12 |
| cyclically_adjusted_balance_hp_filter | 41.6 | +10.3 | 34 |
| gfn | 42.6 | +9.8 | 14 |
| reserve_adequacy_traditional_metrics | 42.9 | -5.0 | 14 |
| real_interest_rate_fisher_gdp_deflator | 46.6 | +4.5 | 12 |
| debt_target_adjustment | 47.1 | +10.8 | 14 |
| cumulative_external_financing_need | 47.1 | -14.2 | 12 |
| real_interest_rate | 51.5 | +8.0 | 10 |
| irev | 54.8 | -7.5 | 16 |
| maastricht_convergence_criteria | 54.9 | +9.9 | 16 |
| okun_difference | 55.0 | -11.6 | 16 |
| debt_path | 56.8 | +11.3 | 20 |
| debt_stab | 59.0 | +10.7 | 20 |
| gdp_per_capita_growth_decomposition | 61.1 | -4.6 | 14 |
| caid | 62.0 | -2.7 | 14 |
| world_bank_income_classification_atlas | 66.7 | +1.1 | 14 |
| private_public_sector_balance_split | 67.3 | +0.9 | 15 |
| saving_investment_gap_current_account | 70.4 | +5.2 | 16 |
| real_growth_from_nominal_growth_and_deflator | 71.1 | -2.4 | 12 |
| okun_gap_cyclical_unemployment | 71.9 | -0.8 | 14 |
| income_velocity | 76.0 | -5.0 | 10 |
| growth_accounting_tfp_residual | 86.5 | -2.2 | 13 |

