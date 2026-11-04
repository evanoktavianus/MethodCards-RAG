# Extra analyses

## 13. Our answers by the cited card: verified source sentence or not

| Group | Cited card | Answers | Answer correctness | Method explained | Method correctness (judge) |
|---|---|---|---|---|---|
| hard | verified | 142 | 76.4 | 87.0 | 92.7 |
| hard | unverified | 89 | 78.2 | 85.2 | 85.8 |
| easier | verified | 52 | 81.7 | 91.3 | 82.2 |
| easier | unverified | 155 | 82.0 | 92.4 | 92.2 |

Note: answers are not randomly assigned to verified or unverified cards; the split is descriptive (methods differ in how their cards were built).

## 14. Method found per 1,000 tokens of retrieved method context

Per answer: context recall (method, judge, 0-1) divided by the retrieved method context in thousands of tokens (characters / 4, as sent to the judge, capped at 48,000 characters). Higher = more of the method per amount read.

| Group | Arm | Answers | Mean context (k tokens) | Share capped | Context recall | Recall per 1k tokens (median) | Recall per 1k tokens (mean) |
|---|---|---|---|---|---|---|---|
| hard | LongDA-style | 230 | 5.3 | 3% | 57.8 | 10.44 | 14.44 |
| hard | Ours | 231 | 5.1 | 0% | 75.3 | 17.25 | 17.58 |
| easier | LongDA-style | 209 | 4.2 | 0% | 49.6 | 13.07 | 12.68 |
| easier | Ours | 208 | 4.1 | 0% | 73.9 | 20.57 | 20.25 |

## 15. hard: ours minus ReAct, per method

Mean difference +15.7 over 231 questions and 13 methods; methods with a positive mean gain: 10 of 13.
Exact sign-flip test over methods (all 8192 sign patterns, two-sided): p = 0.0024. Sign-flip test over questions (20,000 draws, two-sided): p = 0.0000.

| Method | Questions | Mean difference |
|---|---|---|
| lic_dsf_composite_indicator | 40 | +44.9 |
| ara_em | 12 | +25.4 |
| fsi | 14 | +21.1 |
| mac_dsa_stress | 14 | +16.1 |
| debt_path | 20 | +11.3 |
| debt_target_adjustment | 14 | +10.8 |
| cyclically_adjusted_balance_hp_filter | 34 | +10.3 |
| maastricht_convergence_criteria | 16 | +9.9 |
| gfn | 14 | +9.8 |
| reer_real_dep | 12 | +7.5 |
| okun_gap_cyclical_unemployment | 14 | -0.8 |
| growth_accounting_tfp_residual | 13 | -2.2 |
| reserve_adequacy_traditional_metrics | 14 | -5.0 |

## 15. hard: ours minus LongDA-style, per method

Mean difference +2.2 over 231 questions and 13 methods; methods with a positive mean gain: 6 of 13.
Exact sign-flip test over methods (all 8192 sign patterns, two-sided): p = 0.5757. Sign-flip test over questions (20,000 draws, two-sided): p = 0.1275.

| Method | Questions | Mean difference |
|---|---|---|
| lic_dsf_composite_indicator | 40 | +14.4 |
| reer_real_dep | 12 | +8.1 |
| debt_path | 20 | +5.8 |
| fsi | 14 | +4.5 |
| debt_target_adjustment | 14 | +3.7 |
| maastricht_convergence_criteria | 16 | +0.5 |
| okun_gap_cyclical_unemployment | 14 | +0.0 |
| reserve_adequacy_traditional_metrics | 14 | -0.5 |
| mac_dsa_stress | 14 | -1.1 |
| ara_em | 12 | -2.1 |
| growth_accounting_tfp_residual | 13 | -3.5 |
| cyclically_adjusted_balance_hp_filter | 34 | -6.1 |
| gfn | 14 | -7.0 |

## 15. easier: ours minus ReAct, per method

Mean difference +0.3 over 209 questions and 15 methods; methods with a positive mean gain: 8 of 15.
Exact sign-flip test over methods (all 32768 sign patterns, two-sided): p = 0.8976. Sign-flip test over questions (20,000 draws, two-sided): p = 0.8606.

| Method | Questions | Mean difference |
|---|---|---|
| eir | 16 | +14.0 |
| debt_stab | 20 | +10.7 |
| real_interest_rate | 10 | +8.0 |
| saving_investment_gap_current_account | 16 | +5.2 |
| real_interest_rate_fisher_gdp_deflator | 12 | +4.5 |
| inflation_erosion_of_debt_ratio | 12 | +2.9 |
| world_bank_income_classification_atlas | 14 | +1.1 |
| private_public_sector_balance_split | 15 | +0.9 |
| real_growth_from_nominal_growth_and_deflator | 12 | -2.4 |
| caid | 14 | -2.7 |
| gdp_per_capita_growth_decomposition | 14 | -4.6 |
| income_velocity | 10 | -5.0 |
| irev | 16 | -7.5 |
| okun_difference | 16 | -11.6 |
| cumulative_external_financing_need | 12 | -14.2 |

## 15. easier: ours minus LongDA-style, per method

Mean difference -2.3 over 209 questions and 15 methods; methods with a positive mean gain: 4 of 15.
Exact sign-flip test over methods (all 32768 sign patterns, two-sided): p = 0.2642. Sign-flip test over questions (20,000 draws, two-sided): p = 0.1681.

| Method | Questions | Mean difference |
|---|---|---|
| real_growth_from_nominal_growth_and_deflator | 12 | +8.0 |
| real_interest_rate_fisher_gdp_deflator | 12 | +6.5 |
| debt_stab | 20 | +6.0 |
| caid | 14 | +4.4 |
| saving_investment_gap_current_account | 16 | +0.0 |
| world_bank_income_classification_atlas | 14 | +0.0 |
| eir | 16 | -0.4 |
| real_interest_rate | 10 | -2.0 |
| private_public_sector_balance_split | 15 | -3.8 |
| income_velocity | 10 | -4.0 |
| okun_difference | 16 | -5.5 |
| irev | 16 | -6.1 |
| gdp_per_capita_growth_decomposition | 14 | -9.1 |
| cumulative_external_financing_need | 12 | -9.3 |
| inflation_erosion_of_debt_ratio | 12 | -23.4 |

## 16. The card named in our answers

| Group | Answers naming a known card | From a document of the question's method | The method's own card (method tree) |
|---|---|---|---|
| hard | 231 | 143 (61.9%) | 115 (49.8%) |
| easier | 207 | 112 (54.1%) | 111 (53.6%) |

## 17. Composite indicator of debt-carrying capacity: the method source named in each answer (institutional procedures)

LongDA-style baseline, 40 answers:

- a document that states the method: 34
- no method document named: 6

Ours, 40 answers, card named:

- Composite Indicator (CI) for Debt Carrying Capacity: 40
