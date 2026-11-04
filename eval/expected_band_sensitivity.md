# Sensitivity to the definition of the groups

Answer correctness, Ours-cards2 minus the other arm, 440 questions of the main run; 95% cluster bootstrap over methods (4,000 resamples, seed 1); p = exact two-sided sign-flip test over methods (question-weighted mean). Failed answers count 0.

| Subset | Questions | Methods | Ours mean | Ours minus ReAct (95% interval) | p | Ours minus LongDA-style (95% interval) | p |
|---|---|---|---|---|---|---|---|
| Band hard (METHODS.md) | 141 | 7 | 75.3 | +21.9 [+9.0, +35.3] | 0.0312 | +2.8 [-3.7, +10.0] | 0.7031 |
| Band medium | 114 | 7 | 81.2 | +3.7 [-3.7, +9.8] | 0.3594 | -0.7 [-5.3, +3.2] | 0.8750 |
| Band easy | 142 | 11 | 79.6 | +1.7 [-1.9, +5.9] | 0.4580 | -0.8 [-6.1, +3.4] | 0.8203 |
| Band easy to medium (external_sector) | 43 | 3 | 86.0 | -1.7 [-14.2, +5.2] | 1.0000 | -3.9 [-9.3, +0.0] | 0.5000 |
| Band hard + medium | 255 | 14 | 78.0 | +13.8 [+4.4, +24.4] | 0.0087 | +1.3 [-3.4, +6.0] | 0.7637 |
| Band easy + easy to medium | 185 | 14 | 81.1 | +0.9 [-2.8, +4.6] | 0.6434 | -1.5 [-5.5, +2.0] | 0.5098 |
| Paper: institutional procedures (hard.json) | 231 | 13 | 77.1 | +15.7 [+6.7, +26.2] | 0.0024 | +2.2 [-2.3, +7.0] | 0.5757 |
| Paper: standard formulas (easier.json) | 209 | 15 | 81.6 | +0.3 [-3.8, +4.3] | 0.8976 | -2.3 [-6.2, +1.1] | 0.2642 |

## Methods by Band and paper group

| Method | Band | Paper group | Questions | Ours minus ReAct | Ours minus LongDA-style |
|---|---|---|---|---|---|
| caid | easy | standard formulas | 14 | -2.7 | +4.4 |
| eir | easy | standard formulas | 16 | +14.0 | -0.4 |
| income_velocity | easy | standard formulas | 10 | -5.0 | -4.0 |
| inflation_erosion_of_debt_ratio | easy | standard formulas | 12 | +2.9 | -23.4 |
| irev | easy | standard formulas | 16 | -7.5 | -6.1 |
| okun_gap_cyclical_unemployment | easy | institutional procedures | 14 | -0.8 | +0.0 |
| real_growth_from_nominal_growth_and_deflator | easy | standard formulas | 12 | -2.4 | +8.0 |
| real_interest_rate | easy | standard formulas | 10 | +8.0 | -2.0 |
| real_interest_rate_fisher_gdp_deflator | easy | standard formulas | 12 | +4.5 | +6.5 |
| reer_real_dep | easy | institutional procedures | 12 | +7.5 | +8.1 |
| world_bank_income_classification_atlas | easy | standard formulas | 14 | +1.1 | +0.0 |
| cumulative_external_financing_need | easy to medium | standard formulas | 12 | -14.2 | -9.3 |
| private_public_sector_balance_split | easy to medium | standard formulas | 15 | +0.9 | -3.8 |
| saving_investment_gap_current_account | easy to medium | standard formulas | 16 | +5.2 | +0.0 |
| ara_em | hard | institutional procedures | 12 | +25.3 | -2.1 |
| cyclically_adjusted_balance_hp_filter | hard | institutional procedures | 34 | +10.3 | -6.1 |
| debt_target_adjustment | hard | institutional procedures | 14 | +10.8 | +3.7 |
| fsi | hard | institutional procedures | 14 | +21.1 | +4.5 |
| growth_accounting_tfp_residual | hard | institutional procedures | 13 | -2.2 | -3.5 |
| lic_dsf_composite_indicator | hard | institutional procedures | 40 | +44.9 | +14.4 |
| mac_dsa_stress | hard | institutional procedures | 14 | +16.1 | -1.1 |
| debt_path | medium | institutional procedures | 20 | +11.3 | +5.8 |
| debt_stab | medium | standard formulas | 20 | +10.7 | +6.0 |
| gdp_per_capita_growth_decomposition | medium | standard formulas | 14 | -4.6 | -9.1 |
| gfn | medium | institutional procedures | 14 | +9.8 | -7.0 |
| maastricht_convergence_criteria | medium | institutional procedures | 16 | +9.9 | +0.5 |
| okun_difference | medium | standard formulas | 16 | -11.6 | -5.5 |
| reserve_adequacy_traditional_metrics | medium | institutional procedures | 14 | -5.0 | -0.5 |
