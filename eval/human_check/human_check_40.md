# Human check of the judge (40 answers, blind)

Forty answers, with the system that wrote each hidden. For each case the table lists the points the answer key asks for and the author's score for each point (1 = met, 0.5 = partly, 0 = not met; for a point with a target number, 1 if the answer's number is inside the allowed band, else 0; n/a where the key states no number). The judge's scores are not shown here; they are in `eval/human_check/human_check_scores.csv`, next to the author's scores, and `scripts/judge_agreement.py` computes the agreement and Cohen's kappa from that file.

---

## Case 1 (easier)

**Question:** By how many percentage points of GDP did India's primary balance in 2022 exceed, or fall short of, the level needed to stop its debt-to-GDP ratio from rising?

**Answer:**

> India's 2022 primary balance exceeded the debt-stabilizing level by about **1.88 percentage points of GDP** (actual primary deficit −3.882% vs. required −5.758%).
>
> Procedure: standard debt-dynamics condition (as used in IMF debt sustainability analysis): a constant debt ratio requires pb* = d_{t−1} × (i − g)/(1 + g), with i = interest payments/GDP ÷ d_{t−1} (effective nominal rate) and g = nominal GDP growth. Data: IMF WEO Oct 2025 (India, general government).
>
> Computation:
> - Debt/GDP: 2021 = 83.473%, 2022 = 82.166%
> - Nominal GDP growth g = 268,904.7/235,974 − 1 = 13.955%
> - Interest 2022 = primary balance − overall balance = −3.882 − (−8.969) = 5.087% of GDP
> - Effective interest rate i = 5.087/83.473 = 6.094%
> - Debt-stabilizing primary balance pb* = 83.473 × (0.06094 − 0.13955)/1.13955 = −5.758% of GDP
> - Actual primary balance 2022 = −3.882% of GDP
> - Gap = −3.882 − (−5.758) = +1.876 pp
>
> Because nominal growth (13.96%) far exceeded the effective interest rate (6.09%), India could have run a primary deficit of up to 5.76% of GDP and still kept debt stable; its actual deficit of 3.88% was 1.88 pp of GDP smaller, so the debt ratio fell (83.47% → 82.17%).

| Point | Kind | What the key asks for | Author's score |
|---|---|---|---|
| c1 | text | Identifies the debt-dynamics identity d_t=(1+lambda)d_{t-1}-p_t with lambda=(r-g)/(1+g) (the debt-stabilising primary balance p*=lambda*d_{t-1}) as the applicable method. | 1 |
| c3 | text | Concludes the actual balance was above the debt-stabilising level, i.e. the debt ratio was set to fall. | 1 |
| c5 | data | Uses general government gross debt (% GDP), primary balance and overall balance (interest = primary minus overall balance, % GDP), and nominal GDP (WEO Oct 2025: GGXWDG_NGDP, GGXONLB_NGDP, GGXCNL_NGDP, NGDP). | 1 |
| c2 | computation | Gap (actual minus required primary balance, positive = actual above required) is about +1.3 pp of GDP (actual -3.9, required -5.1); required balance p* = lambda x previous-year debt with effective interest rate = interest paid in 2022 / debt at end of 2021 and nominal growth = NGDP_2022/NGDP_2021 - 1. (target 1.3, allowed [0.6, 1.2]) | 1 |

---

## Case 2 (easier)

**Question:** Among the twenty largest economies (by 2024 dollar GDP), take the one with the lightest public debt burden relative to GDP at the end of 2020. Output prices rose 18.2% and nominal output 25.1% in 2021. Holding the nominal debt stock fixed, by how many points of GDP did the price rise alone lower that burden in 2021?

**Answer:**

> **≈ 4.57 percentage points of GDP.**
>
> - Among the twenty largest 2024 economies (USA, China, Germany, Japan, India, UK, France, Italy, Brazil, Canada, Russia, Korea, Mexico, Australia, Spain, Indonesia, Turkey, Netherlands, Saudi Arabia, Switzerland), the lowest end-2020 gross public debt/GDP (IMF WEO, GGXWDG_NGDP) is **Saudi Arabia: 29.663%**.
> - Method: IMF debt dynamics equation d_t = φ_t·d_{t−1} − pb_t + of_t + sf_t, with φ_t = (1+r^w_t)/(1+g_t) and 1+r^w_t = [...]/(1+π_t), where π_t is inflation measured with the GDP deflator. Holding the nominal debt stock fixed (no interest, primary balance, other flows, or FX effects), the ratio evolves as d_t = d_{t−1}/(1+π_t).
> - Computation: d_1 = 29.663/1.182 = 25.0956; drop = 29.663 − 25.0956 = **4.5674 ≈ 4.57 points of GDP**.
>
> Method document: f99d9e25 (A Guide and Tool for Projecting Public Debt and Fiscal Adjustment Paths, IMF), pages 8–9
> Sources: A Guide and Tool for Projecting Public Debt and Fiscal Adjustment Paths, pp. 8–9

| Point | Kind | What the key asks for | Author's score |
|---|---|---|---|
| c0 | text | Identifies that price rises lower the debt ratio through the nominal-growth term gamma/(1+gamma)=pi/(1+gamma)+g/(1+g), so the inflation part is pi/(1+gamma) times last year's debt ratio. | 0 |
| c2 | data | Uses WEO nominal GDP and GDP deflator series and general government gross debt (GGXWDG_NGDP, NGDP, NGDP_D). | 0.5 |
| c1 | computation | Inflation erosion of debt ratio RUS 2021 = 2.79 pp of GDP (target 2.787, allowed [0.15, 0.3]) | 0 |

---

## Case 3 (hard)

**Question:** Consider the economy that in 2023 had general government gross debt above 120 percent of GDP and real GDP growth above 5.3 percent. How would you rate its underlying capacity to carry external debt as of the 2023 assessment round (weak, medium or strong), and what score supports that?

**Answer:**

> **The answer: Zambia — its underlying capacity to carry external debt (the Debt‑Carrying Capacity / Composite Indicator, CI, in the IMF–World Bank LIC Debt Sustainability Framework) is rated "medium," supported by a CI score of about 3.05 (on the 1–6 scale, where weak < 2.84, medium = 2.84–3.34, strong > 3.34).**
>
> **Procedure and source**
>
> 1. **Identify the country.** Using the IMF World Economic Outlook (WEO) database, General Government Gross Debt (% of GDP) and Real GDP Growth for 2023, the country matching both criteria (debt > 120% of GDP and real growth > 5.3%) is **Zambia** (debt roughly 120–125% of GDP in 2023 amid debt-restructuring negotiations; real GDP growth of about 5.3–5.4% in 2023, driven by agriculture and mining).
> 2. **Apply the DSF rule.** Under the joint IMF–World Bank **Debt Sustainability Framework for Low-Income Countries (LIC DSF)**, a country's "underlying capacity to carry debt" is measured by the **Composite Indicator (CI) score**, built from: (i) real GDP growth (3-yr avg), (ii) terms-of-trade volatility, (iii) import compression, (iv) remittances, (v) reserve cover, (vi) external viability (debt-to-exports), and (vii) institutional quality (World Bank CPIA). Classification thresholds: **weak ≤ 2.84; medium > 2.84 and ≤ 3.34; strong > 3.34**.
> 3. **Source:** IMF–World Bank LIC DSF (2023 assessment round); IMF WEO database for the screening variables.
>
> **Computation, step by step**
>
> - Step 1 — Screening: Zambia 2023 general government gross debt ≈ 122% of GDP (> 120% ✓); real GDP growth ≈ 5.3% (> 5.3% ✓).
> - Step 2 — CI components (approximate 2023 values): real GDP growth ≈ 5.3% (adds positively); remittances ≈ 0.5% of GDP (low); reserves ≈ 2–3 months of imports (low); external debt-to-exports elevated; CPIA ≈ 3.2 (moderate).
> - Step 3 — Weighted CI score ≈ **3.05**.
> - Step 4 — Classification: 2.84 < 3.05 ≤ 3.34 → **medium** debt-carrying capacity.
>
> **Caveat:** The exact CI score is published only in the IMF–World Bank DSF country assessments; the ~3.05 figure is an estimate consistent with Zambia's component values. If you have access to the official 2023 DSF assessment for Zambia, that document's CI score is the authoritative number.

| Point | Kind | What the key asks for | Author's score |
|---|---|---|---|
| c1 | text | Identifies the applicable methodology: the IMF-World Bank debt-sustainability framework for low-income countries, in which a composite indicator (CPIA, real growth, reserve import cover, remittances, world growth) classifies debt-carrying capacity as weak, medium or strong. | 0.5 |
| c2 | data | Uses the composite-indicator inputs for ZMB: CPIA (10-yr avg to 2022), real GDP growth (2018-2027), reserves-to-imports, remittances, world growth. | 1 |
| c3 | computation | The composite indicator score is about 2.56. (target 2.565, allowed [0.1, 0.25]) | 0 |
| c4 | answer | Debt-carrying capacity is weak (cutoffs: weak below 2.69, strong above 3.05). | 0 |

---

## Case 4 (hard)

**Question:** South Africa ended 2014 with general government debt of 47.3 percent of GDP and a cyclically adjusted primary balance of -0.8 percent of GDP. Treat it as an emerging market economy. What cyclically adjusted primary balance would it have to reach by 2020 and then maintain through 2030 for its debt to come down to the long-term benchmark for emerging market economies by 2030? Give that level and the change relative to 2014, in percent of GDP. Use IMF World Economic Outlook (October 2025) GDP and fiscal outturns for its growth and interest costs.

**Answer:**

> **Procedure:** IMF Debt Sustainability Analysis for market-access (emerging market) economies. Debt dynamics: d_t = d_{t−1}·(1+i_t)/(1+g_t) − pb_t, where i_t is the effective nominal interest rate (interest payments ÷ lagged debt stock) and g_t is nominal GDP growth, both from WEO October 2025. The long-term public debt benchmark for emerging market economies is **70 percent of GDP** (IMF DSA benchmark for EMs — from memory of the IMF staff guidance; not stated in the question). The constant cyclically adjusted primary balance (CAPB*) for 2020–2030 is solved so that d_2030 = 70.
>
> **Inputs (WEO Oct 2025, South Africa):**
> - Debt end-2014: 47.3% of GDP (given); end-2019 outturn: 56.1% of GDP (WEO).
> - Effective interest rates 2020–2030: 7.20, 6.82, 7.02, 7.34, 7.39, 7.27, 7.18, 7.06, 6.81, 6.64, 6.51%.
> - Nominal GDP growth 2020–2030: −1.11, 11.58, 7.41, 5.57, 4.47, 4.71, 4.86, 4.77, 4.91, 4.87, 4.87%.
>
> **Computation:**
> - Simulate d_t = d_{t−1}(1+i_t)/(1+g_t) − CAPB* for 2020–2030 from d_2019 = 56.101, requiring d_2030 = 70.
> - Solution: **CAPB* = −0.15 percent of GDP** (a near-balance cyclically adjusted position).
> - Implied debt path (% of GDP): 2020: 61.0, 2021: 58.5, 2022: 58.5, 2023: 59.6, 2024: 61.4, 2025: 63.0, 2026: 64.6, 2027: 66.1, 2028: 67.5, 2029: 68.8, 2030: 70.0 ✓.
>
> **Answer:** South Africa would need a cyclically adjusted primary balance of about **−0.1 percent of GDP** (−0.147) by 2020, maintained through 2030. Relative to the 2014 CAPB of −0.8 percent of GDP, that is an improvement (less negative) of about **+0.65 percentage points of GDP**.

| Point | Kind | What the key asks for | Author's score |
|---|---|---|---|
| c1 | text | Identifies the Fiscal Monitor approach to illustrative fiscal adjustment needs for a long-term debt target: solve for the cyclically adjusted primary balance that, held constant over 2020-2030 after a gradual adjustment over 2016-2020 (taken as linear), brings debt to 40 percent of GDP by 2030 for an emerging market economy (or holds it at the end-2014 ratio if that is already lower), using a debt recursion in which the interest-growth differential rises linearly from its 2014 level to 1 percentage point by 2028. | 0.5 |
| c5 | text | Concludes that the country must raise its cyclically adjusted primary balance above its 2014 level (a tightening of about 1.9 points of GDP). | 0.5 |
| c9 | data | Uses nominal GDP (growth) and the interest bill implied by the primary and overall balances relative to previous-year debt from the WEO October 2025 vintage (GGXONLB_NGDP, GGXCNL_NGDP, GGXWDG_NGDP, NGDP) together with the end-2014 debt and CAPB given in the question. | 0.5 |
| c2 | computation | South Africa: a cyclically adjusted primary balance of about 1.1% of GDP held over 2020-30 (published Fiscal Monitor value 1.4). (target 1.069, allowed [1.0, 2.0]) | 0 |
| c3 | computation | South Africa: change of about +1.9 points of GDP relative to the end-2014 CAPB of -0.8%. (target 1.869, allowed [1.0, 2.0]) | 0.5 |
| c4 | computation | Debt target used: 40.0% of GDP in 2030. (target 40.0, allowed [0.1, 0.2]) | 0 |

---

## Case 5 (easier)

**Question:** Among the economies in the IMF World Economic Outlook database, take the one whose general government gross debt at the end of 2017 was between 17.5 and 21.5 percent of GDP, and whose primary balance in 2018 was between -0.5 and 3.5 percent of GDP, and whose nominal GDP growth in 2018 was between 11.5 and 15.5 percent. What primary balance would that economy have needed in 2018 to stop its debt-to-GDP ratio from rising?

**Answer:**

> **Answer: ≈ +2.39% of GDP (2.3915%) — Kazakhstan (KAZ)**
>
> **Procedure:** Filtered the IMF WEO (October 2025) data on three conditions: 2017 gross debt between 17.5–21.5% of GDP, 2018 primary balance between −0.5 and 3.5% of GDP, and 2018 nominal GDP growth between 11.5–15.5%. Only Kazakhstan passed all three. Then applied the standard debt-dynamics identity: with debt ratio d, nominal growth g, and primary balance pb (surplus positive), d_t = (d_{t−1} − pb)/(1+g). Setting d_t = d_{t−1} gives pb* = d·g/(1+g).
>
> **Computation:**
> 1. Nominal GDP growth 2018: 61,819,536 / 54,378,858 − 1 = 13.6830%
> 2. Debt/GDP 2017: 19.869%
> 3. Required primary balance: pb* = 19.869 × 0.136830 / 1.136830 = 2.3915% of GDP
>
> Check: (19.869 − 2.3915)/1.136830 = 15.373%... wait, verify: 19.869/1.136830 = 17.4775; adding back pb: 17.4775 + 2.3915 = 19.869 ✓ (debt ratio unchanged).
>
> Kazakhstan's actual 2018 primary balance was +1.786% of GDP, below the required 2.3915%, which is consistent with its debt ratio rising from 19.869% to 20.259% of GDP.

| Point | Kind | What the key asks for | Author's score |
|---|---|---|---|
| c1 | text | Identifies the debt-dynamics identity d_t=(1+lambda)d_{t-1}-p_t with lambda=(r-g)/(1+g) (the debt-stabilising primary balance p*=lambda*d_{t-1}) as the applicable method. | 0.5 |
| c5 | data | Uses general government gross debt (% GDP), primary balance and overall balance (interest = primary minus overall balance, % GDP), and nominal GDP (WEO Oct 2025: GGXWDG_NGDP, GGXONLB_NGDP, GGXCNL_NGDP, NGDP). | 0.5 |
| c2 | computation | Primary balance needed in 2018 is about -3.2% of GDP (a deficit of this size keeps the ratio constant), computed as p* = lambda x previous-year debt with the effective interest rate = interest paid in 2018 / debt at end of 2017 and nominal growth = NGDP_2018/NGDP_2017 - 1; surplus positive. (target -3.2, allowed [0.15, 0.3]) | 0 |

---

## Case 6 (easier)

**Question:** How much higher or lower was the interest rate the government of Peru paid on its debt in 2016 than the nominal growth rate of its economy?

**Answer:**

> In 2016 the government of Peru paid an effective interest rate on its debt about **4.2 percentage points lower** than the nominal growth rate of its economy (r − g ≈ −4.24 pp).
>
> Procedure (Escolano, 2010, IMF "A Practical Guide to Public Debt Dynamics," Table 1, p. 9):
> - Effective interest rate = interest paid in year t as a ratio to debt outstanding at end of year t−1.
> - Interest rate–growth differential = effective interest rate − nominal growth rate.
>
> Computation (IMF WEO Oct 2025 data, Peru):
> 1. General government interest expenditure 2016 = overall balance (GGXCNL = −14,224 mn PEN) minus primary balance (GGXONLB = −8,068 mn PEN) → interest = 6,156 mn PEN.
> 2. Effective interest rate = 6,156 / debt end-2015 (146,697 mn PEN) = 4.196%.
> 3. Nominal GDP growth 2016 = 671,540 / 619,267 − 1 = 8.441%.
> 4. r − g = 4.196% − 8.441% = −4.245 percentage points.
>
> Cross-check using WDI interest payments (6,882 mn PEN): effective rate 4.69%, r − g = −3.75 pp — same conclusion. The negative differential means growth eroded Peru's debt ratio faster than interest accumulated it.
>
> Method card: 55319ff9-22 (Interest rate-growth differential computation, Table 1 — Escolano 2010)
> Sources: Escolano (2010), A Practical Guide to Public Debt Dynamics, Fiscal Sustainability, and Citizense' Welfare, IMF, p. 9 (Table 1 and footnote 1).

| Point | Kind | What the key asks for | Author's score |
|---|---|---|---|
| c1 | text | Identifies the growth-adjusted interest rate lambda = (i - gamma)/(1 + gamma) = (1+r)/(1+g) - 1 (Escolano 2010, eq. 5) with i the effective nominal interest rate (interest paid over previous-year-end debt) and gamma nominal GDP growth, as the applicable measure. | 0.5 |
| c5 | data | Uses gross debt (% GDP) at the end of the previous year, interest paid (primary balance minus overall balance, % GDP) and nominal GDP growth (WEO Oct 2025: GGXWDG_NGDP, GGXONLB_NGDP, GGXCNL_NGDP, NGDP). | 0.5 |
| c2 | computation | The value for Peru in 2016 is about -3.91 percentage points. (target -3.91, allowed [0.5, 1.0]) | 1 |

---

## Case 7 (hard)

**Question:** A staff note says that in 2020, about +1.3 percentage points of Korea's unemployment rate was cyclical (positive meaning above the sustainable rate). Is that statement accurate? Convention: take the WEO output-gap estimate and assume that each 1% of output gap moves the unemployment rate by one-half percentage point in the opposite direction.

**Answer:**

> Yes, the statement is accurate. Using the IMF WEO (October 2025 vintage) output gap for Korea in 2020 of −2.643% of potential GDP, and the convention (consistent with the Okun's law discussion in the WEO October 2012 Box 4.1, which states that "a 1 percent deviation of output from potential leads to a reduction in cyclical unemployment of about ½ percentage point") that each 1% of output gap moves unemployment by 0.5 pp in the opposite direction:
>
> Cyclical unemployment = −0.5 × (−2.643) = +1.321 percentage points.
>
> This rounds to about +1.3 pp, matching the staff note's claim (difference of only 0.021 pp). Korea's unemployment rate in 2020 was indeed about 1.3 pp above its sustainable (natural) rate.
>
> Method card: bc66194c-08 (Okun's law regressions — levels, first differences, and employment versions)
> Sources: World Economic Outlook, October 2012 – Coping with High Debt and Sluggish Growth, Box 4.1, p.179; IMF WEO Oct 2025, series NGAP_NPGDP (Korea, 2020).

| Point | Kind | What the key asks for | Author's score |
|---|---|---|---|
| c0 | text | Identifies the relationship between the output gap and the deviation of unemployment from its natural rate (Okun's law, coefficient about -1/2) and uses it to judge the statement. | 1 |
| c5 | data | Uses WEO series: NGAP_NPGDP, LUR. | 0.5 |
| c1 | computation | Recomputed cyclical unemployment KOR 2020 = 1.32 pp (target 1.321, allowed [0.15, 0.3]) | 1 |
| c2 | computation | Verdict: statement is TRUE (stated +1.3 vs recomputed +1.32; threshold 0.5 pp) | 1 |

---

## Case 8 (hard)

**Question:** Taking the IMF World Economic Outlook (October 2025) projections as the baseline, how high would Poland's general government gross debt be in 2030, as a percent of GDP, under a stress scenario in which growth and interest rates are both adverse at the same time, and how far above the baseline projection would that be? Treat it as a country with access to international capital markets.

**Answer:**

> Under the IMF MAC DSA combined macro-fiscal stress test applied to the WEO (October 2025) baseline, Poland's general government gross debt would reach about 86.9% of GDP in 2030, roughly 11.0 percentage points above the WEO baseline projection of 75.9% of GDP.
>
> Procedure and source: IMF (2013) Staff Guidance Note for Public DSA in Market-Access Countries, Table 3 "Summary of Macro-Fiscal Stress Tests" (p. 21), which defines the standard shocks and their default interactions:
> - Growth shock: real GDP growth reduced by 1 standard deviation of the last 10 years (2015–2024 σ = 2.76 pp) for 2 consecutive years (2026–27); default interaction: inflation falls 0.25 pp per 1 pp of growth decline, and the primary balance deteriorates because nominal non-interest spending is held at its baseline level while revenue stays at the baseline revenue-to-GDP ratio.
> - Interest rate shock: nominal interest rate raised by max(maximum real rate over the last 10 years − average projected real rate, 200 bp). With the historical maximum smoothed real effective rate of 4.79% and average projected real rate of 2.87%, the difference (1.93 pp) is below 200 bp, so the 200 bp floor applies.
> - Default interaction: +25 bp on the interest rate per 1% of GDP of primary-balance deterioration (small here: ≤0.06 pp).
>
> Computation (Poland, WEO Oct 2025 vintage; effective nominal interest rate implied from the WEO debt path via d_t = d_{t−1}(1+i)/(1+g^nom) − pb, which reproduces the baseline exactly):
> - Baseline: 60.0 (2025) → 65.8 → 69.1 → 71.8 → 74.1 → 75.9% of GDP (2030), matching the WEO projection.
> - Combined shock: 60.0 (2025) → 69.1 (2026) → 76.1 (2027) → 80.1 (2028) → 83.7 (2029) → 86.9% of GDP (2030).
> - Difference vs baseline 2030: 86.91 − 75.93 = 10.98 ≈ 11.0 percentage points.
>
> Method document: 2dea3fb1-758b-40a4-882b-59f953293e2d (IMF (2013) — Staff Guidance Note for Public DSA in Market-Access Countries), pages 21-24
> Sources: IMF (2013) — Staff Guidance Note for Public DSA in Market-Access Countries, pages 21-24 (Table 3 and Figure 4); data: IMF WEO October 2025 vintage (GGXWDG_NGDP, GGXONLB_NGDP, NGDP_RPCH, NGDP_D, NGDP for Poland).

| Point | Kind | What the key asks for | Author's score |
|---|---|---|---|
| c1 | text | Identifies the standardized public DSA stress tests of the IMF (2013) Staff Guidance Note for Public DSA in Market-Access Countries (also MAC SRDSF 2021) and applies the combined shock: the growth and interest shocks together, taking the largest effect on each variable without double counting. | 1 |
| c9 | data | Uses WEO October 2025 general government gross debt, real GDP growth, GDP deflator, primary balance, overall balance (to derive interest) and revenue (WEO: GGXWDG_NGDP, NGDP_RPCH, NGDP_D, GGXONLB_NGDP, GGXCNL_NGDP, GGR_NGDP). | 0.5 |
| c2 | computation | Poland: 2030 debt of about 91.5% of GDP under the combined growth and interest-rate shock. (target 91.5, allowed [6.0, 12.0]) | 1 |
| c3 | computation | Poland: baseline (current projection) 2030 debt of about 75.9% of GDP, so the stress adds about 15.6 points. (target 75.926, allowed [1.0, 2.0]) | 1 |
| c4 | computation | Poland: one standard deviation of its past ten-year real growth is about 2.6 percentage points. (target 2.61, allowed [0.7, 1.4]) | 1 |
| c5 | computation | Poland: interest-rate shock of about 2.0 percentage points. (target 2.01, allowed [0.6, 1.2]) | 1 |

---

## Case 9 (hard)

**Question:** One economy saw real GDP contract by more than 3.5% in 2006 while running a general government deficit larger than 5% of GDP. What was its deficit that year with the economy adjusted to its normal capacity level, in percent of GDP at that level?

**Answer:**

> **Answer: −10.497% of GDP (Timor‑Leste, 2006).**
>
> **Procedure:** Identify the economy with 2006 real GDP growth below −3.5% and a 2006 overall balance worse than −5% of GDP; then compute the deficit as revenue minus expenditure (the balance already expressed relative to GDP).
>
> **Computation:**
> - 2006 growth rates: COM −1.755, ERI −0.969, GAB −3.633, GRD −3.993, PRI −1.41, TLS −4.119, TON −2.194, ZWE −3.556. Candidates with contraction >3.5%: GAB, GRD, TLS, ZWE.
> - 2006 balances: GAB +7.977, GRD +0.901, TLS −10.497, ZWE −3.462. Only TLS has a deficit >5% of GDP → Timor‑Leste.
> - Deficit check: revenue 47.838 − expenditure 58.335 = −10.497% of GDP.
>
> **Source:** IMF World Economic Outlook, October 2025 (general government net lending/borrowing, % of GDP; real GDP growth). Note: a true cyclically adjusted (capacity-level) balance cannot be computed from the data provided, as no output gap or potential GDP series is given; the reported overall balance of −10.497% of GDP is the deficit figure available.

| Point | Kind | What the key asks for | Author's score |
|---|---|---|---|
| c0 | text | Identifies that the answer requires cyclically adjusting the budget balance (potential-output gap from a statistical trend, then removing the cyclical budget component). | 0 |
| c5 | data | Uses general government revenue, expenditure and real GDP series from the WEO (GGR_NGDP, GGX_NGDP, NGDP_R, GGXCNL_NGDP). | 1 |
| c1 | computation | Underlying (capacity-level) balance GRD 2006 = -6.02 % of potential GDP (target -6.023, allowed [0.3, 0.6]) | 0 |

---

## Case 10 (easier)

**Question:** In 2023, India's government paid an average 9.0% on its borrowing. After allowing for how fast the price of the economy's total output (not consumer prices) rose that year, what was the effective cost of that borrowing?

**Answer:**

> India's effective (real) cost of borrowing in 2023 was about **5.49%** (9.0% nominal − 3.51% GDP-deflator inflation = 5.49%). This uses the standard ex-post real interest rate formula r = i − π, with π measured by GDP deflator inflation (WDI series NY.GDP.DEFL.KD.ZG, India, 2023 = 3.5111%), since the question specifies the price of total output rather than consumer prices.

| Point | Kind | What the key asks for | Author's score |
|---|---|---|---|
| c0 | text | Identifies that the real interest rate is the nominal rate deflated by inflation, r=(1+i)/(1+pi)-1 with pi the GDP deflator change. | 0.5 |
| c2 | data | Uses WEO nominal GDP and GDP deflator series (NGDP_D, (nominal rate stated in query)). | 0 |
| c1 | computation | Real interest rate IND 2023 at i=9.0% = 6.25 % (target 6.246, allowed [0.2, 0.4]) | 0 |

---

## Case 11 (hard)

**Question:** A fiscal review says that Thailand, which ended 2014 with general government debt of 46.6 percent of GDP and a cyclically adjusted primary balance of 0.6 percent of GDP, would need to hold a cyclically adjusted primary balance of about 1.0 percent of GDP over 2020-30 (reached by 2020) for its debt to come down to the long-term benchmark for emerging market economies by 2030. Is that correct to within three quarters of a percentage point? Use IMF World Economic Outlook (October 2025) GDP and fiscal outturns for its growth and interest costs.

**Answer:**

> **The answer: Yes.** Recomputing the debt path with IMF WEO (October 2025) outturns, Thailand needs a cyclically adjusted primary balance of roughly **0.8 percent of GDP** over 2025–30 to bring debt down to the ~55 percent-of-GDP emerging-market benchmark by 2030. That is within three-quarters of a percentage point of the stated 1.0 percent.
>
> **Procedure and source**
>
> - Debt dynamics identity: d(t+1) = d(t)·(1+i)/(1+g) − pb, where d = gross debt/GDP, i = effective interest rate (interest payments ÷ debt stock), g = nominal GDP growth, pb = primary balance.
> - Data: IMF World Economic Outlook, October 2025 database (Thailand general government gross debt, interest payments, real GDP growth and GDP deflator). Benchmark: IMF's long-term debt benchmark for emerging market economies (55 percent of GDP).
> - Actual debt outturns are taken as given through 2025 (they include the COVID-era primary deficits that the original review could not foresee); the CAPB is then held constant from 2025 (in place of the review's "from 2020") through 2030.
>
> **Computation, step by step**
>
> 1. Starting point (WEO Oct 2025): debt ≈ 64 percent of GDP in 2025.
> 2. Effective interest rate: interest payments ≈ 1.9 percent of GDP on debt of ~64 percent → i ≈ 1.9/64 ≈ 3.0 percent.
> 3. Nominal GDP growth 2026–30: real growth ≈ 3 percent plus deflator ≈ 1.8 percent → g ≈ 4.8 percent.
> 4. Growth-adjusted discount factor: (1+i)/(1+g) = 1.030/1.048 ≈ 0.9828.
> 5. Debt in 2030 absent primary surpluses: 64 × 0.9828⁵ ≈ 64 × 0.917 ≈ 58.7 percent of GDP.
> 6. Required cumulative adjustment to reach 55 percent: 58.7 − 55 = 3.7 percent of GDP.
> 7. Present-value conversion factor for a constant pb over 5 years: Σ(0.9828)^k, k=0…4 ≈ (1 − 0.917)/0.0172 ≈ 4.83.
> 8. Required CAPB: pb = 3.7 / 4.83 ≈ **0.8 percent of GDP**.
>
> 9. Check against the claim: |1.0 − 0.8| = 0.2 percentage points < 0.75 → **correct within the tolerance**.
>
> Caveat: the result is somewhat sensitive to the exact 2025 debt stock and growth assumptions (a ±1pp change in debt or 0.5pp in nominal growth moves the required pb by ~0.1–0.2pp), but under any reasonable WEO Oct 2025 reading the required balance stays in the 0.6–1.0 percent range, so the review's 1.0 percent figure holds within three-quarters of a point.

| Point | Kind | What the key asks for | Author's score |
|---|---|---|---|
| c1 | text | Identifies the Fiscal Monitor approach to illustrative fiscal adjustment needs for a long-term debt target: solve for the cyclically adjusted primary balance that, held constant over 2020-2030 after a gradual adjustment over 2016-2020 (taken as linear), brings debt to 40 percent of GDP by 2030 for an emerging market economy (or holds it at the end-2014 ratio if that is already lower), using a debt recursion in which the interest-growth differential rises linearly from its 2014 level to 1 percentage point by 2028. | 0.5 |
| c3 | text | Judges the statement correct. | 1 |
| c9 | data | Uses nominal GDP (growth) and the interest bill implied by the primary and overall balances relative to previous-year debt from the WEO October 2025 vintage (GGXONLB_NGDP, GGXCNL_NGDP, GGXWDG_NGDP, NGDP) together with the end-2014 debt and CAPB given in the question. | 0.5 |
| c2 | computation | Thailand: recomputed CAPB over 2020-30 of about 0.7% of GDP. (target 0.728, allowed [0.75, 1.5]) | 1 |

---

## Case 12 (hard)

**Question:** A staff report on Guatemala states that in 2010, the primary deficit contributed +1.8 percentage points to the change in the debt ratio (general government gross debt, percent of GDP; contributions measured against the previous year's debt stock). Is this statement accurate? Verify it with the data and give the correct figure.

**Answer:**

> **The answer: Yes, the statement is accurate. The primary deficit contributed +1.8 percentage points to the change in the debt ratio in 2010.**
>
> **Procedure:** In the standard debt-dynamics decomposition, the change in the debt-to-GDP ratio is split into (i) the primary balance contribution and (ii) the "snowball" (interest-rate–growth) contribution:
>
> Δd = −pb + (r − g)/(1+g) · d₍₋₁₎
>
> where pb is the primary balance (% of GDP). The primary deficit's contribution to the debt ratio is simply the primary deficit as a share of GDP, i.e., −(primary balance).
>
> **Computation, step by step:**
>
> 1. Primary net lending/borrowing, 2010 (WEO): **−1.8% of GDP** → primary deficit = 1.8% of GDP.
> 2. Contribution of the primary balance to the change in the debt ratio = −(−1.8) = **+1.8 pp**.
> 3. Consistency check with the data:
>    - Debt ratio: 24.006 (2010) − 22.78 (2009) = **+1.226 pp** total change.
>    - Implied snowball effect = 1.226 − 1.8 = **−0.574 pp**, i.e., real GDP growth (2.884%) exceeded the effective interest rate, partially offsetting the primary deficit. This is internally consistent.
>
> **Source:** IMF World Economic Outlook, October 2025 (fiscal series for Guatemala); standard debt-dynamics identity (e.g., IMF staff guidance on public debt decomposition).

| Point | Kind | What the key asks for | Author's score |
|---|---|---|---|
| c1 | text | Identifies the debt-ratio decomposition (primary deficit / interest-rate / growth / inflation terms applied to previous-year debt) as the method for checking the statement, per Escolano (2010) or the IMF (2013) debt-dynamics annex. | 1 |
| c3 | text | Verdict: the statement is TRUE. | 1 |
| c4 | data | Uses WEO general government gross debt, primary balance, interest (primary minus overall balance), nominal and real GDP. | 0.5 |
| c2 | computation | Correct value of the stated quantity for Guatemala 2010: +1.8 percentage points. (target 1.8, allowed [0.3, 1.0]) | 1 |

---

## Case 13 (easier)

**Question:** A report says that in 2010 Eritrea's gross national saving was 6.8% of GDP and gross investment 18.2% of GDP, and that its balance with the rest of the world was therefore an external surplus of 11.4% of GDP. Is that statement correct?

**Answer:**

> The statement is incorrect. Using the national accounts identity CA = S − I (gross national saving minus gross investment equals the current account/external balance — a standard convention in the IMF/national accounts framework): 6.8 − 18.2 = −11.4% of GDP. Since gross investment (18.2% of GDP) exceeds gross national saving (6.8% of GDP), Eritrea's balance with the rest of the world in 2010 was an external **deficit** of 11.4% of GDP, not a surplus. The report's magnitude is right but the sign is wrong.

| Point | Kind | What the key asks for | Author's score |
|---|---|---|---|
| c0 | text | Identifies that the external balance follows from the national accounts identity: current account balance = gross national saving minus gross investment (the saving-investment gap). | 1 |
| c2 | text | Judges the statement incorrect (recomputed balance -11.4% vs stated 11.4%). | 1 |
| c5 | data | Uses WEO saving, investment, current account series. | 0.5 |
| c1 | computation | Correct external balance Eritrea 2010 = -11.42 % of GDP; stated 11.4 (target -11.42, allowed [0.15, 0.3]) | 1 |

---

## Case 14 (easier)

**Question:** Among all economies in the IMF World Economic Outlook database, exactly one had average consumer price inflation above 6% and an unemployment rate below 8% and GDP per capita above US$ 18,000 in 2017. What mainly drove the change in that economy's current account balance between 2013 and 2017, in terms of its domestic accounts, and by how much?

**Answer:**

> **Answer: Uruguay — its current account improved by roughly 3 percentage points of GDP (from about –4.5% in 2013 to about –1.5% in 2017), driven mainly by a fall in domestic investment relative to GDP, with national saving roughly unchanged.**
>
> **Procedure and source:** I screened the IMF World Economic Outlook (WEO) database (April 2019 vintage, imf.org) for 2017 values: CPI inflation > 6%, unemployment < 8%, and GDP per capita > US$18,000. Uruguay is the unique match: inflation ≈ 6.2%, unemployment ≈ 7.6%, GDP per capita ≈ US$16–22k (nominal ~$16k; PPP ~$22k, satisfying the threshold on the PPP measure). Other candidates fail: Argentina (unemployment ~8.5%), Turkey (unemployment ~11%), Russia (inflation ~3.7%), Chile (inflation ~2.2%), Hungary/Poland (inflation ~2%).
>
> **Computation (from WEO current account and investment/saving ratios, % of GDP):**
> - Current account: 2013 ≈ –4.6%; 2017 ≈ –1.7% → improvement ≈ **+2.9 pp of GDP**
> - Decomposition via CA = S – I:
>   - National saving: 2013 ≈ 17.5%; 2017 ≈ 17.5% → change ≈ 0
>   - Investment: 2013 ≈ 22%; 2017 ≈ 19% → change ≈ –3 pp
>
> So the entire improvement came from the investment side: gross domestic investment fell by about 3 percentage points of GDP between 2013 and 2017 (after the commodity/investment boom peaked), while national saving stayed broadly flat — hence the current account deficit narrowed by roughly 3 pp of GDP.

| Point | Kind | What the key asks for | Author's score |
|---|---|---|---|
| c1 | text | Identifies the national-accounts identity that the current account balance equals national saving minus domestic investment (so the change in the balance equals the change in saving minus the change in investment) as the way to attribute the change. | 1 |
| c4 | text | Most of the change came from investment. | 1 |
| c5 | data | Uses gross national saving and total investment (% of GDP) and the current account balance (WEO Oct 2025: NGSD_NGDP, NID_NGDP, BCA_NGDPD). | 0.5 |
| c2 | computation | Change in gross national saving 2013 to 2017: -3.1 pp of GDP. (target -3.14, allowed [0.3, 0.6]) | 0 |
| c3 | computation | Change in investment 2013 to 2017: -6.4 pp of GDP. (target -6.36, allowed [0.3, 0.6]) | 0 |
| c6 | computation | Change in the current account balance: +3.2 pp of GDP (from -3.2% to 0.0%), equal to the change in saving minus the change in investment. (target 3.22, allowed [0.3, 0.6]) | 0.5 |

---

## Case 15 (hard)

**Question:** For El Salvador: how much of the 2016 change in the general government gross debt ratio is attributable to each of the primary deficit, the real interest rate paid on last year's debt and real GDP growth? Give each contribution in percentage points of GDP and say which one mattered most.

**Answer:**

> ## Answer
>
> Decomposition of the change in El Salvador's general government gross debt ratio, 2015→2016 (actual change: 75.214 − 73.464 = **+1.75 pp of GDP**):
>
> | Driver | Contribution (pp of GDP) |
> |---|---|
> | Real interest rate on 2015 debt | **+2.43** |
> | Real GDP growth | **−1.87** |
> | Primary deficit | **+0.19** |
> | **Sum of the three** | **+0.75** |
> | Residual (stock–flow adjustment, valuation, other flows) | ≈ +1.00 |
>
> **The real interest rate mattered most** (+2.43 pp), followed by real growth (−1.87 pp, partially offsetting), with the primary deficit contributing only +0.19 pp. Note that the three standard drivers explain only ~0.75 pp of the 1.75 pp increase; the remaining ~1.0 pp is a residual (below-the-line operations, exchange-rate valuation on FX debt, or other stock-flow adjustments).
>
> ## Procedure
>
> Standard debt-dynamics identity:
>
> Δd = primary deficit + (r − g)·d₍₋₁₎ + residual, where r = i − π (real interest rate), g = real GDP growth.
>
> Sources: IMF WEO Oct-2025 (debt ratios, balances, growth, deflator) and the note that interest paid = primary balance − overall balance.
>
> ## Computation
>
> 1. **Interest paid (nominal, % of GDP), 2016** = primary balance − overall balance = (−0.189) − (−3.104) = **2.915% of GDP**
>
> 2. **Nominal interest rate on 2015 debt stock** = 2.915 / 73.464 = **3.968%**
>
> 3. **Real interest rate** = 3.968% − GDP deflator inflation (0.6577%) = **3.310%**
>
> 4. **Interest contribution** = 3.310% × 73.464 = **+2.43 pp**
>
> 5. **Growth contribution** = −2.544% × 73.464 = **−1.87 pp**
>
> 6. **Primary deficit contribution** = **+0.19 pp**
>
> 7. Check: 2.43 − 1.87 + 0.19 = **+0.75 pp** vs. actual change of +1.75 pp → residual ≈ **+1.00 pp** (unexplained stock–flow adjustment).

| Point | Kind | What the key asks for | Author's score |
|---|---|---|---|
| c1 | text | Identifies that the change in the public debt ratio is attributed to its components by applying the debt-accumulation identity to the previous-year debt stock: primary deficit, an interest-rate term, a growth term (and, in the other published variant, a separate inflation term), as set out in Escolano (2010) 'A Practical Guide to Public Debt Dynamics...' (equations 24-28) and in the IMF (2013) Staff Guidance Note / MAC SRDSF (2021) debt-dynamics annex ('contribution from real interest rate', 'contribution from real GDP growth'). | 0.5 |
| c6 | text | Names the real-interest-rate effect on last year's debt stock as the largest of the named contributions in 2016 (+2.4 percentage points). | 1 |
| c7 | data | Uses general government gross debt (% of GDP), primary balance, interest paid (primary balance minus overall balance), nominal and real GDP (WEO), i.e. IMF WEO GGXWDG_NGDP, GGXONLB_NGDP, GGXCNL_NGDP, NGDP, NGDP_R. | 1 |
| c2 | computation | El Salvador: +0.2 percentage points of GDP in 2016 (primary deficit (positive = adds to debt)). (target 0.189, allowed [0.3, 1.0]) | 1 |
| c3 | computation | El Salvador: +2.4 percentage points of GDP in 2016 (real-interest-rate effect on last year's debt stock). (target 2.437, allowed [0.3, 1.0]) | 1 |
| c4 | computation | El Salvador: -1.8 percentage points of GDP in 2016 (real GDP growth effect). (target -1.809, allowed [0.3, 1.0]) | 1 |
| c5 | computation | El Salvador: +0.9 percentage points of GDP in 2016 (remainder (change not explained by those three; includes exchange-rate and other flows)). (target 0.933, allowed [0.3, 1.0]) | 1 |

---

## Case 16 (hard)

**Question:** A briefing says that for Lesotho, as assessed in 2022, the debt-capacity score is 2.91 and it is classed as medium. Is that statement correct?

**Answer:**

> The statement is correct in substance: Lesotho's 2022 debt-carrying-capacity classification is Medium. The score of 2.91 is consistent with the official CI vintages reported by IMF staff (2.90 and 2.94 for the two earlier vintages, both Medium); my own recomputation with the latest WDI data gives CI = 3.048, also Medium.
>
> Procedure: I used the IMF–World Bank LIC-DSF Composite Indicator (CI) for debt-carrying capacity, as set out in the Lesotho 2025 Article IV staff report (Text Table 5, p.8): CI = 0.385×CPIA + 2.719×real growth + 4.052×import coverage of reserves − 3.990×(import coverage)² + 2.022×remittances + 13.520×world growth, with all percent variables as fractions (verified against the table: 4.052×0.44458 = 1.80, etc.). Classification: Weak if CI < 2.69; Medium if 2.69 ≤ CI ≤ 3.05; Strong if CI > 3.05.
>
> Computation (10-year averages 2013–2022, CPIA 2021 = 3.2917):
> - CPIA term: 0.385×3.2917 = 1.2673
> - Real growth (avg 0.0698%): 2.719×0.000698 = 0.0019
> - Import coverage of reserves (avg 3.628 months = 36.94% = 0.3694): 4.052×0.3694 = 1.4967; squared term: −3.990×0.3694² = −0.5444
> - Remittances (avg 20.49% of GDP): 2.022×0.2049 = 0.4143
> - World growth (avg 3.0515%): 13.520×0.030515 = 0.4126
> - CI = 3.048 → Medium (2.69 ≤ 3.048 ≤ 3.05)
>
> Caveat: the exact 2.91 figure depends on the October 2022 WEO vintage and 2021 CPIA used at the time; with today's revised WDI data I obtain 3.05, but both values give the same Medium classification, matching the official vintages (2.90, 2.94) also classed Medium.
>
> Method card: 968df4c6-01 (Composite Indicator (CI) for Debt Carrying Capacity)
> Sources: Kingdom of Lesotho: Staff Report for the 2025 Article IV Consultation—Debt Sustainability Analysis, p.8 (formula, coefficients, cut-offs, vintage scores 2.94/2.90); Islamic Republic of Mauritania 2022 Article IV Staff Report—DSA, p.10 (2022-vintage CI practice: October 2022 WEO, 2021 CPIA).

| Point | Kind | What the key asks for | Author's score |
|---|---|---|---|
| c1 | text | Identifies the applicable methodology: the IMF-World Bank debt-sustainability framework for low-income countries, in which a composite indicator (CPIA, real growth, reserve import cover, remittances, world growth) classifies debt-carrying capacity as weak, medium or strong. | 1 |
| c2 | data | Uses the composite-indicator inputs for LSO: CPIA (10-yr avg to 2021), real GDP growth (2017-2026), reserves-to-imports, remittances, world growth. | 1 |
| c3 | computation | The composite indicator score is about 2.98. (target 2.984, allowed [0.1, 0.25]) | 1 |
| c4 | answer | Correct verdict: the statement is TRUE (recomputed score 2.98, class medium). | 1 |

---

## Case 17 (easier)

**Question:** Adjusted for the rise in the economy-wide price level, what did bank borrowing cost firms and households in Mexico in 2019?

**Answer:**

> Adjusted for the rise in the economy-wide price level (GDP deflator inflation of 4.32% in 2019), bank borrowing in Mexico cost firms and households a real rate of about **3.94%** in 2019.
>
> Procedure: I used the Fisher-deflation real interest rate definition from Escolano (2010), IMF Technical Notes and Manuals: r_t ≡ [(1+i_t)/(1+π_t)] − 1, where i_t is the nominal interest rate and π_t is the change in the GDP deflator between t−1 and t (the economy-wide price level).
>
> Computation (all values as printed by the tool):
> - Nominal bank lending rate, Mexico 2019 (WDI FR.INR.LEND): i = 8.42916666666666%
> - GDP deflator inflation, Mexico 2019 (WDI NY.GDP.DEFL.KD.ZG): π = 4.31901023627729%
> - Real rate: r = (1 + 0.0842916666666666)/(1 + 0.0431901023627729) − 1 = 3.9399879476234245% ≈ **3.94%**
> - (The simple subtraction approximation i − π = 4.11015643038937% is close but the exact Fisher formula is the one defined in the source.)
>
> Method card: 55319ff9-17 (Real interest rate definition (Fisher deflation))
> Sources: Escolano (2010), A Practical Guide to Public Debt Dynamics, Fiscal Sustainability, and Fiscal Risks in Advanced Economies (IMF TNM/10/02), p. 3 (Box 1, notation glossary) and p. 23 (Annex, summary of formulas); data: World Bank WDI series FR.INR.LEND and NY.GDP.DEFL.KD.ZG for Mexico.

| Point | Kind | What the key asks for | Author's score |
|---|---|---|---|
| c1 | text | Identifies the applicable approach: ex post real interest rate, the nominal lending rate deflated by inflation (GDP deflator), r = (i - pi)/(1 + pi) or approximately i - pi. | 1 |
| c2 | data | Retrieves the input series: FR.INR.LEND, NY.GDP.DEFL.KD.ZG. | 1 |
| c3 | computation | The real lending rate in 2019 is about 3.9 percent (lending rate 8.4 percent deflated by GDP-deflator inflation 4.3 percent). (target 3.94, allowed [1.5, 3.0]) | 1 |
| c4 | answer | The real return/cost is positive (borrowers face a positive real rate). | 1 |

---

## Case 18 (hard)

**Question:** Using the IMF World Economic Outlook (October 2025 vintage), take the one economy with real GDP growth in 2020, % between -8.3 and -4.3; GDP-deflator inflation in 2020, % between 6.5 and 7.1. For that economy: how much of the 2020 change in the general government gross debt ratio is attributable to each of the primary deficit, the real interest rate paid on last year's debt and real GDP growth? Give each contribution in percentage points of GDP and say which one mattered most.

**Answer:**

> **The answer**
>
> The economy is **Georgia (GEO)**. Of the 19.51 pp-of-GDP rise in its gross debt ratio (40.049% → 59.559%):
>
> - **Primary deficit contribution: +7.61 pp of GDP** ← largest
> - Real GDP growth contribution: +2.69 pp of GDP
> - Real interest rate contribution: −2.12 pp of GDP
> - (Residual / stock-flow adjustment: +11.33 pp)
>
> The **primary deficit mattered most**.
>
> **Procedure and source**
>
> Data: IMF World Economic Outlook, October 2025 vintage (as given in the table). Method: the standard debt-dynamics decomposition, Δd = d₀·r/(1+g) − d₀·g/(1+g) − pb, where r is the real interest rate (Fisher: (1+i)/(1+π)−1), g is real GDP growth, and pb is the primary balance. Interest paid (% of GDP) is derived from the note: interest = primary balance − overall balance.
>
> **Computation step by step**
>
> 1. **Selection:** GEO has real growth 2020 = −6.291% (in [−8.3, −4.3]) and deflator inflation = (106.847/100 − 1) = 6.847% (in [6.5, 7.1]). ✓
>
> 2. **Interest paid:** 2020: −7.612 − (−9.158) = **1.546% of GDP**; 2019: −0.596 − (−1.825) = 1.229% of GDP.
>
> 3. **Real interest rate:** nominal i = 1.546%; r = (1.01546/1.06847) − 1 = **−4.961%** (negative, since inflation exceeded the nominal rate).
>
> 4. **Debt-ratio change:** 59.559 − 40.049 = **+19.510 pp**.
>
> 5. **Decomposition** (d₀ = 40.049, g = −6.291%, r = −4.961%):
>    - Primary deficit: −pb = **+7.612 pp**
>    - Interest: 40.049 × (−0.04961)/(1 − 0.06291) = **−2.120 pp**
>    - Growth: −40.049 × (−0.06291)/(1 − 0.06291) = **+2.689 pp**
>    - Sum = +8.180 pp; residual (valuation/stock-flow adjustments, e.g., exchange-rate depreciation on FX-denominated debt) = 19.510 − 8.180 = **+11.330 pp**.
>
> 6. **Conclusion:** among the three requested channels, the primary deficit (+7.61 pp) was the largest contributor to the debt-ratio increase; negative real interest rates actually reduced it.

| Point | Kind | What the key asks for | Author's score |
|---|---|---|---|
| c1 | text | Identifies that the change in the public debt ratio is attributed to its components by applying the debt-accumulation identity to the previous-year debt stock: primary deficit, an interest-rate term, a growth term (and, in the other published variant, a separate inflation term), as set out in Escolano (2010) 'A Practical Guide to Public Debt Dynamics...' (equations 24-28) and in the IMF (2013) Staff Guidance Note / MAC SRDSF (2021) debt-dynamics annex ('contribution from real interest rate', 'contribution from real GDP growth'). | 0.5 |
| c6 | text | Names the primary deficit as the largest of the named contributions in 2020 (+7.6 percentage points). | 1 |
| c8 | data | Identifies the economy as Georgia (GEO) from the stated conditions. | 1 |
| c7 | data | Uses general government gross debt (% of GDP), primary balance, interest paid (primary balance minus overall balance), nominal and real GDP (WEO), i.e. IMF WEO GGXWDG_NGDP, GGXONLB_NGDP, GGXCNL_NGDP, NGDP, NGDP_R. | 1 |
| c2 | computation | Georgia: +7.6 percentage points of GDP in 2020 (primary deficit (positive = adds to debt)). (target 7.612, allowed [0.3, 1.0]) | 1 |
| c3 | computation | Georgia: -1.0 percentage points of GDP in 2020 (real-interest-rate effect on last year's debt stock). (target -1.021, allowed [0.3, 1.0]) | 0 |
| c4 | computation | Georgia: +2.5 percentage points of GDP in 2020 (real GDP growth effect). (target 2.516, allowed [0.3, 1.0]) | 1 |
| c5 | computation | Georgia: +10.4 percentage points of GDP in 2020 (remainder (change not explained by those three; includes exchange-rate and other flows)). (target 10.403, allowed [0.3, 1.0]) | 0.5 |

---

## Case 19 (hard)

**Question:** Among the economies in the IMF World Economic Outlook database (October 2025 vintage), take the one whose overall fiscal balance in 2025 was between -3.5 and -2 percent of GDP, and whose nominal GDP growth in 2025 was between 6 and 8 percent, and whose primary balance in 2025 was between -1 and 0 percent of GDP, and whose general government gross debt at the end of 2025 was between 40 and 41.5 percent of GDP. Treating the October 2025 projections as the baseline, how high would that economy's general government gross debt be in 2030, as a percent of GDP, under an adverse interest-rate shock, and how far above the baseline projection would that be? Treat it as a country with access to international capital markets.

**Answer:**

> The economy is **Indonesia**. Under the adverse interest-rate shock, general government gross debt in 2030 would be about **43.4 percent of GDP**, roughly **1.9 percentage points above** the WEO October 2025 baseline projection of **41.5 percent of GDP**.
>
> **Screening (IMF WEO, Oct 2025 vintage, 2025 values):**
> - Overall fiscal balance (GGXCNL_NGDP): −2.789% of GDP (within −3.5 to −2)
> - Nominal GDP growth (NGDP 2025/2024): 7.02% (within 6–8)
> - Primary balance (GGXONLB_NGDP): −0.499% of GDP (within −1 to 0)
> - Gross debt (GGXWDG_NGDP): 40.828% of GDP (within 40–41.5)
>
> **Procedure:** IMF Debt Sustainability Analysis for market-access countries — the standard adverse interest-rate shock raises the effective nominal interest rate by 100 basis points over the projection horizon (2026–2030), holding the baseline primary balance and nominal growth unchanged (IMF Staff Guidance note on DSAs for market-access countries; parameter of +100 bp is the standard convention, stated from memory of that guidance).
>
> **Computation:** Shock increment in year t = 0.01 × d_{t−1} / (1 + g_t), cumulated on the baseline debt path:
> - 2026: +0.378 → 41.517
> - 2027: +0.382 → 42.114
> - 2028: +0.384 → 42.640
> - 2029: +0.385 → 43.071
> - 2030: +0.385 → **43.444% of GDP**
>
> Baseline 2030 debt: 41.529% of GDP; difference: **+1.915 pp of GDP**.

| Point | Kind | What the key asks for | Author's score |
|---|---|---|---|
| c1 | text | Identifies the standardized public DSA stress tests of the IMF (2013) Staff Guidance Note for Public DSA in Market-Access Countries (also MAC SRDSF 2021) and applies the interest-rate shock: nominal rate raised by the larger of 200 bp and the gap between the highest real rate of the last ten years and the average projected real rate. | 0.5 |
| c7 | text | Identifies the economy as Indonesia. | 1 |
| c9 | data | Uses WEO October 2025 general government gross debt, real GDP growth, GDP deflator, primary balance, overall balance (to derive interest) and revenue (WEO: GGXWDG_NGDP, NGDP_RPCH, NGDP_D, GGXONLB_NGDP, GGXCNL_NGDP, GGR_NGDP). | 0.5 |
| c2 | computation | Indonesia: 2030 debt of about 48.6% of GDP under the interest-rate shock. (target 48.6, allowed [5.0, 8.0]) | 0.5 |
| c3 | computation | Indonesia: baseline (current projection) 2030 debt of about 41.5% of GDP, so the stress adds about 7.1 points. (target 41.529, allowed [1.0, 2.0]) | 1 |
| c5 | computation | Indonesia: interest-rate shock of about 3.6 percentage points. (target 3.58, allowed [0.6, 1.2]) | 0 |

---

## Case 20 (easier)

**Question:** A review of Morocco says: 'In 2016 the government's debt carried an interest rate that was below the growth of the nominal economy.' Is this statement correct?

**Answer:**

> **The answer: No — the statement is incorrect.** In 2016 Morocco's effective interest rate on government debt (~4.19%) was *above* nominal GDP growth (~1.50%), so r > g, not r < g.
>
> **Procedure and source:**
> - Interest paid (% of GDP) = primary net lending/borrowing − overall net lending/borrowing (per the note on the series; data from IMF WEO Oct 2025).
> - Effective interest rate r = interest paid (% of GDP) ÷ gross debt (% of GDP).
> - Nominal GDP growth g from nominal GDP in national currency (WEO).
> - Compare r vs g.
>
> **Computation step by step (2016):**
> 1. Interest paid = −1.968 − (−4.486) = **2.518% of GDP**
> 2. r = 2.518 / 60.084 = **4.19%** (note: the program's printout of "0.0419 %" is a labeling error — 0.0419 is the decimal fraction, i.e., 4.19%)
> 3. g = 1,094,249 / 1,078,119 − 1 = **1.496%**
> 4. r − g = 4.19 − 1.50 = **+2.69 percentage points**
>
> Since r (≈4.19%) > g (≈1.50%), the claim that the interest rate was below nominal growth is **false**.

| Point | Kind | What the key asks for | Author's score |
|---|---|---|---|
| c1 | text | Identifies the growth-adjusted interest rate lambda = (i - gamma)/(1 + gamma) = (1+r)/(1+g) - 1 (Escolano 2010, eq. 5) with i the effective nominal interest rate (interest paid over previous-year-end debt) and gamma nominal GDP growth, as the applicable measure. | 0.5 |
| c3 | text | Judges the statement incorrect. | 1 |
| c5 | data | Uses gross debt (% GDP) at the end of the previous year, interest paid (primary balance minus overall balance, % GDP) and nominal GDP growth (WEO Oct 2025: GGXWDG_NGDP, GGXONLB_NGDP, GGXCNL_NGDP, NGDP). | 0.5 |
| c2 | computation | The value for Morocco in 2016 is about 2.84 percentage points. (target 2.84, allowed [0.5, 1.0]) | 1 |

---

## Case 21 (hard)

**Question:** Among the economies in the IMF World Economic Outlook database (October 2025 vintage), take the one whose nominal GDP growth in 2021 was between 1.5 and 3.5 percent, and whose primary balance in 2021 was between -6 and -5 percent of GDP, and whose general government gross debt at the end of 2021 was between 252 and 255.5 percent of GDP, and whose overall fiscal balance in 2021 was between -7 and -5.5 percent of GDP. How close to fiscal stress were that economy's public finances in 2021? Using only components that can be built from public IMF World Economic Outlook (October 2025), World Bank Public Sector Debt and World Development Indicators series, give a 0 to 100 fiscal stress score (rescale the weights of the components you can build so that they sum to 100) and say which components signal stress.

**Answer:**

> The economy is Japan. Its 2021 fiscal stress score is 100 out of 100 — every component that can be built from public IMF WEO (Oct 2025), World Bank PSD and WDI series breaches its fiscal-stress threshold, so Japan's public finances in 2021 were at the maximum of the fiscal-stress scale.
>
> Procedure: I used the IMF Working Paper "Assessing Fiscal Stress" (Baldacci, Petrova, Belhocine, Dobrescu, Mazraani, IMF WP/11/100, May 2011). Its fiscal stress index is Overall index = Σ_g w_g Σ_i w_i,g d_i, where d_i = 1 if indicator i crosses its threshold (signaling approach, TME-estimated thresholds) and weights are relative signaling powers. Japan is an advanced economy, so I used Table 5a (advanced economies) thresholds and weights. Components buildable from public data (weights rescaled to sum to 100, from the original buildable weight sum of 26.4):
>
> - General government gross debt: 253.652% of GDP (WEO GGXWDG_NGDP) vs threshold 72.2 → signal (weight 7.3 → 27.65)
> - Primary balance (proxy for cyclically adjusted primary balance): −5.542% of GDP (WEO GGXONLB_NGDP) vs threshold −4.2 (safe direction >) → signal (weight 9.4 → 35.61)
> - Short-term debt share: PSD 2021Q4 short-term (securities 24.700 + loans 0.026 = 24.726% GDP) over total D1 debt (213.455% GDP) = 11.58% vs threshold 9.1 → signal (weight 2.8 → 10.61)
> - Fertility rate deviation from 2.1: 2.1 − 1.3 = 0.8 (WDI SP.DYN.TFRT.IN) vs threshold 0.64 → signal (weight 2.4 → 9.09)
> - Dependency ratio: 70.26 (WDI SP.POP.DPND) vs threshold 36.0 → signal (weight 4.5 → 17.05)
>
> Signaling weight 26.4 / 26.4 → score = 100.0. Components signaling stress: all five — debt, primary balance, short-term debt share, fertility deviation, and dependency ratio. Non-buildable components (r–g, gross financing needs, nonresident debt share, weighted average maturity, long-term health/pension projections) were dropped and weights rescaled, as instructed. Note the primary balance is used as a proxy for the cyclically adjusted primary balance, which the paper's threshold refers to.
>
> Method document: b8ca4b08-f493-4848-9dfe-6d2cec1f8db5 (Assessing Fiscal Stress, IMF Working Paper WP/11/100), pages 12-13 (methodology) and 18-19 (Table 5a thresholds and weights)
> Sources: Assessing Fiscal Stress (IMF WP/11/100), pp. 12-13, 18-19

| Point | Kind | What the key asks for | Author's score |
|---|---|---|---|
| c1 | text | Identifies the threshold-based fiscal stress index of Baldacci, McHugh and Petrova, 'Assessing Fiscal Stress' (IMF WP/11/100): indicators in basic, asset-liability and long-term clusters, each compared with the threshold of Tables 5a/5b for advanced or emerging economies, weighted and summed; and applies it as a reduced index on the 8 indicators available from public series (6 for advanced economies), rescaled to the available weight. | 0.5 |
| c7 | text | Identifies the economy as Japan. | 1 |
| c4 | text | Japan 2021: indicators beyond threshold: gross general government debt (253.7 against a threshold of 72.2); the cyclically adjusted primary balance (-4.8 against a threshold of -4.2); gross financing needs (47.6 against a threshold of 17.2); the share of short-term debt in public debt (15.8 against a threshold of 9.1); the deviation of the fertility rate from replacement (0.8 against a threshold of 0.64). | 0.5 |
| c9 | data | Uses WEO debt, balances, structural balance, GDP and deflator; PSD general government short-term and foreign-currency debt; WDI short-term external debt, reserves and fertility (inputs listed in the item). | 0.5 |
| c2 | computation | Japan 2021: reduced fiscal stress score of about 76 out of 100 (breached weight 46.5 of 61.4 available). (target 75.7, allowed [6.0, 12.0]) | 0 |
| c3 | computation | Japan 2021: 5 of the 6 available indicators beyond their thresholds. (target 5.0, allowed [1.0, 2.0]) | 0.5 |

---

## Case 22 (hard)

**Question:** Taking the IMF World Economic Outlook (October 2025) projections as the baseline, how high would Brazil's general government gross debt be in 2030, as a percent of GDP, under an adverse growth shock, and how far above the baseline projection would that be? Treat it as a country with access to international capital markets.

**Answer:**

> Under the IMF MAC-DSA standardized growth shock, Brazil's general government gross debt would reach about **143.0% of GDP in 2030**, roughly **44.9 percentage points above** the WEO October 2025 baseline projection of **98.1% of GDP**.
>
> Procedure and source: IMF (2013), Staff Guidance Note for Public DSA in Market-Access Countries, Table 3 (p.21) — "Real GDP growth is reduced by 1 standard deviation for 2 consecutive years," with default interactions: revenue-to-GDP held at baseline while non-interest spending is kept at its baseline level (so the primary balance deteriorates), the primary deterioration raises the interest rate by 25bp per 1% of GDP of deficit worsening, and inflation falls by 0.25pp per 1pp of growth decline.
>
> Computation (all numbers printed by the tool):
> 1. Shock size: 10-year historical standard deviation of Brazil's real GDP growth (2015–2024, WEO Oct 2025) = 3.106 ppts. Shock: growth −3.106 ppts in 2026 and 2027 (2026: −1.16%, 2027: −0.87%); inflation −0.78pp in both years.
> 2. Baseline effective nominal interest rates implied from the debt identity D_t = D_{t−1}(1+i) − PB_t·Y_t: 2026–2030 = 10.36%, 8.44%, 7.77%, 7.48%, 7.38%.
> 3. Shock years (default interactions, solved jointly): 2026 — i = 13.24%, primary balance −11.95% of GDP (baseline −0.42%), debt 112.77% of GDP; 2027 — i = 12.39%, primary balance −15.56% (baseline 0.26%), debt 139.96%.
> 4. 2028–2030: growth, inflation, primary-balance ratio and interest rate revert to baseline (the lower GDP level persists): debt 141.72%, 142.56%, 142.98% of GDP.
> 5. Baseline 2030 debt = 98.07% of GDP; shock 2030 debt = 142.98%; difference = 44.91 ppts.
>
> Caveat: the shock sizes are minima and the interaction calibration is the template default; the very large primary-balance deterioration reflects Brazil's high debt level interacting with the 25bp rule.
>
> Method card: 2dea3fb1-09 (Standardized macro-fiscal stress tests)
> Sources: IMF (2013) — Staff Guidance Note for Public DSA in Market-Access Countries, pp. 21–22 (Table 3 and ¶31); debt identity from p. 9.

| Point | Kind | What the key asks for | Author's score |
|---|---|---|---|
| c1 | text | Identifies the standardized public DSA stress tests of the IMF (2013) Staff Guidance Note for Public DSA in Market-Access Countries (also MAC SRDSF 2021) and applies the growth shock: real GDP growth one standard deviation (ten-year history) below baseline for two consecutive years, revenue ratio unchanged and non-interest spending level held at baseline, +25 bp interest per 1 pp of GDP deterioration of the deficit, inflation 0.25 pp lower per 1 pp lower growth. | 1 |
| c9 | data | Uses WEO October 2025 general government gross debt, real GDP growth, GDP deflator, primary balance, overall balance (to derive interest) and revenue (WEO: GGXWDG_NGDP, NGDP_RPCH, NGDP_D, GGXONLB_NGDP, GGXCNL_NGDP, GGR_NGDP). | 0.5 |
| c2 | computation | Brazil: 2030 debt of about 109.2% of GDP under the growth shock. (target 109.2, allowed [4.0, 8.0]) | 0 |
| c3 | computation | Brazil: baseline (current projection) 2030 debt of about 98.1% of GDP, so the stress adds about 11.1 points. (target 98.068, allowed [1.0, 2.0]) | 1 |
| c4 | computation | Brazil: one standard deviation of its past ten-year real growth is about 2.6 percentage points. (target 2.57, allowed [0.7, 1.4]) | 1 |

---

## Case 23 (hard)

**Question:** For the 2019 assessment round, how would you rate Haiti's capacity to carry external debt (weak, medium or strong), and what single score supports that rating?

**Answer:**

> **The answer:** Haiti's external debt carrying capacity in the 2019 assessment round was rated **weak**, supported by a single score of **3.0** on the World Bank's Country Policy and Institutional Assessment (CPIA).
>
> **Procedure and source:** Under the joint IMF–World Bank Debt Sustainability Framework for Low-Income Countries, a country's debt-carrying capacity is classified using the CPIA-based indicator (the average of the CPIA clusters covering quality of macroeconomic management, structural policies, and social inclusion/equity, averaged over three years). A score of **3.05 or higher** qualifies as "medium" capacity; **below 3.05** is "weak" (and 3.75+ would be "strong"). Source: World Bank CPIA database and the IMF/WB LIC-DSF classification thresholds.
>
> **Computation step by step:**
> 1. Haiti's CPIA score for the relevant period (2016–2018 average used for the 2019 assessment) = **3.0**.
> 2. Compare to the threshold: 3.0 < 3.05.
> 3. Therefore, classification = **weak** debt-carrying capacity, which in turn sets the lower (more conservative) PV-of-debt thresholds used in Haiti's DSA.

| Point | Kind | What the key asks for | Author's score |
|---|---|---|---|
| c1 | text | Identifies the applicable methodology: the IMF-World Bank debt-sustainability framework for low-income countries, in which a composite indicator (CPIA, real growth, reserve import cover, remittances, world growth) classifies debt-carrying capacity as weak, medium or strong. | 0.5 |
| c2 | data | Uses the composite-indicator inputs for HTI: CPIA (10-yr avg to 2018), real GDP growth (2014-2023), reserves-to-imports, remittances, world growth. | 0.5 |
| c3 | computation | The composite indicator score is about 2.82. (target 2.817, allowed [0.1, 0.25]) | 0 |
| c4 | answer | Debt-carrying capacity is medium (cutoffs: weak below 2.69, strong above 3.05). | 0 |

---

## Case 24 (easier)

**Question:** A debt-restructuring brief states: "In 2011, Mongolia was a lower-middle-income economy." Is the brief right?

**Answer:**

> Yes, the brief is right. In 2011 Mongolia was a lower-middle-income economy under the World Bank classification.
>
> Procedure and computation:
> 1. Method: World Bank income classification based on GNI per capita under the Atlas method, with thresholds set each July 1. The 2011 thresholds are documented in the IMF External Debt Statistics Guide glossary: low income ≤ $1,025; lower-middle income $1,026–$4,035; upper-middle income $4,036–$12,475 (2011).
> 2. Data: Mongolia's GNI per capita, Atlas method (WDI series NY.GNP.PCAP.CD) for 2011 = US$2,570.
> 3. Classification check: $1,026 ≤ $2,570 ≤ $4,035 → lower-middle income (True, printed by code).
>
> Method document: bc5f813b-b3a4-4001-8f4a-bab531649fce (IMF (2013) — External Debt Statistics: Guide for Compilers and Users), pages 257-267
> Sources: IMF (2013) — External Debt Statistics: Guide for Compilers and Users, pages 257 (Low-Income Countries; Lower-Middle-Income-Country Terms) and 267 (Upper-Middle-Income Countries); World Bank WDI series NY.GNP.PCAP.CD (GNI per capita, Atlas method, current US$), Mongolia 2011.

| Point | Kind | What the key asks for | Author's score |
|---|---|---|---|
| c0 | text | Identifies that the answer applies the World Bank country income classification: Atlas-method GNI per capita compared against the annual low / lower-middle / upper-middle / high income cut-offs. | 1 |
| cv | text | Judges the statement TRUE: the 2011 bracket is lower-middle-income. | 1 |
| cd | data | Uses World Bank Atlas GNI per capita (current US dollars, NY.GNP.PCAP.CD) for 2011. | 1 |
| c1 | computation | Atlas-method GNI per capita of Mongolia in 2011 = 2570 US dollars (target 2570.0, allowed [77.0, 154.0]) | 1 |

---

## Case 25 (hard)

**Question:** A report on Belgium states: 'Belgium's general government deficit was 3.6% of GDP in 2022, but with the economy at its normal capacity level the deficit would have been larger, about 4.6% of GDP.' Is that statement accurate?

**Answer:**

> **Verdict: The statement's direction is correct but its magnitude is not — the cyclically adjusted (structural) deficit in 2022 was about 5.3% of GDP, not 4.6%.**
>
> Procedure: The question asks whether the deficit "at normal capacity" (the cyclically adjusted / structural balance) was larger than the actual 3.6% deficit. I used the IMF Fiscal Monitor's cyclically adjusted balance (CAB) method: CAB = overall balance − cyclical balance, with cyclical balance = ε_R·GAP − ε_G·GAP, where GAP is the output gap in percent of potential GDP. Where country-specific elasticities are unavailable, the Fiscal Monitor assumes standard elasticities of 1 for revenue and 0 for expenditure ("Where unavailable, standard elasticities (0,1) are assumed for expenditure and revenue, respectively," Fiscal Monitor, September 2011, p. 82). (The alternative October 1993 WEO Annex I method was also checked, but its cyclical response parameters cover only the G7, not Belgium, so the Fiscal Monitor standard-elasticity version is used.)
>
> Computation (IMF WEO October 2025 data for Belgium):
> - 2022 general government balance: −3.62% of GDP (matches the report's 3.6%)
> - 2022 output gap: +1.706% of potential GDP (economy above normal capacity)
> - CAB = −3.62 − (1.0 × 1.706 − 0.0 × 1.706) = **−5.33% of GDP**
>
> So with the economy above potential, the cyclical component improved the balance by ~1.7 points; stripping it out, the structural deficit was ≈5.3% of GDP — larger than the actual deficit, as the report claims, but materially larger than the stated 4.6%. Even with a generous expenditure elasticity of 0.5, the CAB would be −4.47%, still below −4.6% in magnitude only slightly; under the standard Fiscal Monitor elasticities the correct figure is −5.3%. The statement is therefore accurate in direction ("the deficit would have been larger") but understates the size of the structural deficit.
>
> Method card: 1fe10341-09 (Cyclically adjusted balance and cyclically adjusted primary balance (CAB / CAPB))
> Sources: Fiscal Monitor, September 2011 – Addressing Fiscal Challenges to Reduce Economic Risks, pp. 37, 82; World Economic Outlook, October 1993, Annex I, pp. 109–112 (method cross-check); IMF WEO Oct 2025 data (GGXCNL_NGDP, NGAP_NPGDP for Belgium)

| Point | Kind | What the key asks for | Author's score |
|---|---|---|---|
| c0 | text | Identifies that the answer requires cyclically adjusting the budget balance (potential-output gap from a statistical trend, then removing the cyclical budget component). | 1 |
| c4 | text | Judges the statement ACCURATE. | 0 |
| c5 | data | Uses general government revenue, expenditure and real GDP series from the WEO (GGR_NGDP, GGX_NGDP, NGDP_R, GGXCNL_NGDP). | 0 |
| c1 | computation | Underlying balance BEL 2022 = -4.64 % of potential GDP (target -4.64, allowed [0.3, 0.6]) | 0 |

---

## Case 26 (hard)

**Question:** Among the economies in the IMF World Economic Outlook database (October 2025 vintage), take the one whose real GDP growth in 2025 was between 2 and 3.5 percent, and whose general government gross debt at the end of 2025 was between 42 and 43.5 percent of GDP. Treating the October 2025 projections as the baseline, how high would that economy's general government gross debt be in 2030, as a percent of GDP, under a stress scenario in which growth and interest rates are both adverse at the same time, and how far above the baseline projection would that be? Treat it as a country with access to international capital markets.

**Answer:**

> **Country: Chile** — the only WEO Oct 2025 economy with 2025 real GDP growth of 2.515% (in 2–3.5%) and 2025 gross government debt of 42.737% of GDP (in 42–43.5%).
>
> **Procedure used:** IMF Debt Sustainability Analysis for Market-Access Countries (MAC DSA), "combined macro-fiscal shock" — a simultaneous adverse growth shock and interest-rate shock, each equal to one-half standard deviation of the respective historical (2015–2024) variable, applied over the projection horizon while holding the baseline primary balance path. Debt dynamics: d_t = d_{t−1}·(1+i)/(1+g_nominal) − pb_t. (This is my application of the published IMF framework; the ½σ shock sizes are the MAC DSA convention.)
>
> **Computation:**
> - Historical effective interest rate backed out from i_t = (d_t + pb_t)(1+g_nom,t)/d_{t−1} − 1; 2015–2024: 8.34, 12.68, 6.24, 6.03, 3.17, −0.11, −2.49, 17.30, 5.45, 8.22%.
> - σ(real growth, 2015–24) = 4.2428 → growth shock = −2.1214 pp
> - σ(effective i, 2015–24) = 5.7540 → interest shock = +2.8770 pp
> - Baseline effective interest rates (implied from WEO debt, primary balance, deflator): 4.78% (2026), 3.43% (2027), 3.45% (2028), 3.38% (2029), 3.35% (2030).
> - Stressed path (growth −2.12 pp, interest +2.88 pp, baseline pb held):
>   - 2026: d = 45.762 (baseline 43.660)
>   - 2027: d = 48.338 (43.968)
>   - 2028: d = 50.963 (44.152)
>   - 2029: d = 53.733 (44.339)
>   - 2030: d = 56.561 (baseline 44.434)
>
> **Result:** Under the combined adverse growth-and-interest-rate shock, Chile's general government gross debt would reach **≈56.6% of GDP in 2030**, about **12.1 percentage points of GDP above** the WEO October 2025 baseline projection of 44.4%.

| Point | Kind | What the key asks for | Author's score |
|---|---|---|---|
| c1 | text | Identifies the standardized public DSA stress tests of the IMF (2013) Staff Guidance Note for Public DSA in Market-Access Countries (also MAC SRDSF 2021) and applies the combined shock: the growth and interest shocks together, taking the largest effect on each variable without double counting. | 0.5 |
| c7 | text | Identifies the economy as Chile. | 1 |
| c9 | data | Uses WEO October 2025 general government gross debt, real GDP growth, GDP deflator, primary balance, overall balance (to derive interest) and revenue (WEO: GGXWDG_NGDP, NGDP_RPCH, NGDP_D, GGXONLB_NGDP, GGXCNL_NGDP, GGR_NGDP). | 0.5 |
| c2 | computation | Chile: 2030 debt of about 56.9% of GDP under the combined growth and interest-rate shock. (target 56.9, allowed [6.0, 12.0]) | 1 |
| c3 | computation | Chile: baseline (current projection) 2030 debt of about 44.4% of GDP, so the stress adds about 12.5 points. (target 44.434, allowed [1.0, 2.0]) | 1 |
| c4 | computation | Chile: one standard deviation of its past ten-year real growth is about 4.0 percentage points. (target 4.03, allowed [0.7, 1.4]) | 1 |
| c5 | computation | Chile: interest-rate shock of about 2.0 percentage points. (target 2.0, allowed [0.6, 1.2]) | 0.5 |

---

## Case 27 (easier)

**Question:** A staff report states that after removing price changes, Saudi Arabia's output rose 4.6% in 2015, given nominal output growth of -11.9% and a deflator increase of -15.8%. Is the statement right?

**Answer:**

> Yes, the statement is right (up to rounding). Using the IMF debt-dynamics identity 1+γ=(1+g)(1+π) (Escolano 2010, Box 1 notation glossary, p.3, and equation (25) on p.7): (1+0.046)×(1−0.158)=0.880732, i.e. nominal growth of −11.93%, which rounds to the stated −11.9% (difference of only −0.027 pp). So real growth of 4.6% with a deflator change of −15.8% is fully consistent with nominal output growth of −11.9%.
>
> Method card: 55319ff9-06 (Decomposition of changes in the debt ratio)
> Sources: Escolano (2010), A Practical Guide to Public Debt Dynamics, pp.3 and 7

| Point | Kind | What the key asks for | Author's score |
|---|---|---|---|
| c0 | text | Identifies that real growth is obtained by stripping the price change (GDP deflator) out of nominal GDP growth: 1+gamma=(1+g)(1+pi). | 1 |
| c2 | data | Uses WEO nominal GDP and GDP deflator series (NGDP, NGDP_D). | 0 |
| c1 | computation | Real GDP growth SAU 2015 = 4.66 %; statement of 4.6% is within tolerance (target 4.655, allowed [0.15, 0.3]) | 1 |
| c3 | computation | Verdict: statement is TRUE under the recomputed value. | 1 |

---

## Case 28 (hard)

**Question:** Among the economies in the IMF World Economic Outlook database (October 2025 vintage), take the one whose primary balance in 2025 was between -2.5 and 0 percent of GDP, and whose general government gross debt at the end of 2025 was between 74.5 and 75.5 percent of GDP, and whose real GDP growth in 2025 was between -2.5 and 4 percent, and whose nominal GDP growth in 2025 was between 4 and 8.5 percent. Treating the October 2025 projections as the baseline, how high would that economy's general government gross debt be in 2030, as a percent of GDP, under a stress scenario in which growth and interest rates are both adverse at the same time, and how far above the baseline projection would that be? Treat it as a country with access to international capital markets.

**Answer:**

> **Verdict: Under the IMF MAC-DSA combined growth-and-interest-rate stress test, Hungary's general government gross debt would reach about 97.8 percent of GDP in 2030, roughly 16.8 percentage points above its baseline projection (81.1 percent of GDP; about 19.0 points above the WEO October 2025 published baseline of 78.8 percent).**
>
> Country identification (WEO Oct 2025, 2025 values): Hungary — primary balance −1.165% of GDP (between −2.5 and 0), gross debt 74.761% of GDP (between 74.5 and 75.5), real growth 0.595% (between −2.5 and 4), nominal growth ≈6.4% (between 4 and 8.5).
>
> Method (IMF 2013 Staff Guidance Note for Public DSA in MACs, Table 3, p.21):
> - Debt dynamics: d_t = [(1+i_t)/((1+g_t)(1+π_t))]·d_{t−1} − pb_t (5-year horizon, 2026–2030).
> - Growth shock: "Real GDP growth is reduced by 1 standard deviation for 2 consecutive years" → −3.494 pp in 2026–27 (10-yr historical sd of real growth, 2016–2025).
> - Interest-rate shock: "Nominal interest rate increases by the difference between the maximum real interest rate over history (last 10 years) and the average real interest rate level over projection, or by 200bp, whichever is larger" → max real rate 2.96% < projected 3.73%, so the binding 200 bp floor applies (+2.00 pp).
> - Default interactions: inflation falls 0.25 pp per 1 pp growth decline; primary balance deteriorates (revenue ratio unchanged, non-interest spending level held at baseline); borrowing–interest link +25 bp per 1% of GDP primary worsening.
>
> Computation (all printed by the code):
> - Effective nominal interest rate = interest payments/lagged debt (WDI interest payments, WEO debt): 7.12% in 2024, held constant over the projection.
> - Baseline recursion: 2026: 75.96, 2027: 77.12, 2028: 78.48, 2029: 79.78, 2030: 81.05 (WEO published: 78.83).
> - Stress: 2026: g −1.39%, π 2.39%, pb −2.71%, i 9.59% → d 81.17; 2027: d 88.05; 2028: 91.27; 2029: 94.52; 2030: 97.82.
> - Difference vs baseline recursion: 97.82 − 81.05 = 16.77 pp; vs WEO 2030: 97.82 − 78.83 = 18.99 pp.
>
> Method card: 2dea3fb1-09 (Standardized macro-fiscal stress tests, IMF MAC DSA Table 3)
> Sources: IMF (2013) — Staff Guidance Note for Public DSA in Market-Access Countries, p.21 (Table 3) and p.9 (5-year horizon); data: IMF WEO Oct 2025 (GGXWDG_NGDP, GGXONLB_NGDP, NGDP_RPCH, NGDP_D, NGDP), WDI (GC.XPN.INTP.CN).

| Point | Kind | What the key asks for | Author's score |
|---|---|---|---|
| c1 | text | Identifies the standardized public DSA stress tests of the IMF (2013) Staff Guidance Note for Public DSA in Market-Access Countries (also MAC SRDSF 2021) and applies the combined shock: the growth and interest shocks together, taking the largest effect on each variable without double counting. | 1 |
| c7 | text | Identifies the economy as Hungary. | 1 |
| c9 | data | Uses WEO October 2025 general government gross debt, real GDP growth, GDP deflator, primary balance, overall balance (to derive interest) and revenue (WEO: GGXWDG_NGDP, NGDP_RPCH, NGDP_D, GGXONLB_NGDP, GGXCNL_NGDP, GGR_NGDP). | 0.5 |
| c2 | computation | Hungary: 2030 debt of about 99.4% of GDP under the combined growth and interest-rate shock. (target 99.4, allowed [6.0, 12.0]) | 1 |
| c3 | computation | Hungary: baseline (current projection) 2030 debt of about 78.8% of GDP, so the stress adds about 20.6 points. (target 78.829, allowed [1.0, 2.0]) | 1 |
| c4 | computation | Hungary: one standard deviation of its past ten-year real growth is about 3.3 percentage points. (target 3.31, allowed [0.7, 1.4]) | 1 |
| c5 | computation | Hungary: interest-rate shock of about 2.0 percentage points. (target 2.0, allowed [0.6, 1.2]) | 1 |

---

## Case 29 (hard)

**Question:** A staff report on Romania states that in 2015, the real interest rate paid on the previous year's debt stock contributed +1.4 percentage points to the change in the debt ratio (general government gross debt, percent of GDP; contributions measured against the previous year's debt stock). Is this statement accurate? Verify it with the data and give the correct figure.

**Answer:**

> **The answer:** The staff report is **not accurate**. The real interest rate contribution to the change in Romania's 2015 debt ratio is approximately **+1.55 percentage points** (1.549 pp exact, 1.540 pp with the linear approximation), not +1.4 pp.
>
> **Procedure and source:**
> - Data: IMF WEO October 2025 (debt ratio, primary and overall balances, CPI inflation) and WDI (GDP in LCU), as given.
> - Method (standard debt-dynamics decomposition): interest paid (% of GDP) = primary balance − overall balance; nominal interest rate i = interest paid / previous year's debt ratio; real rate via Fisher equation r = (1+i)/(1+π) − 1; contribution = r × d₂₀₁₄ (measured against the previous year's debt stock, as the report specifies).
>
> **Computation step by step:**
>
> 1. **Interest paid 2015 (% of GDP)** = primary − overall = −0.049 − (−1.348) = **1.299% of GDP**
>
> 2. **Nominal interest rate on 2014 debt stock:**
>    i = 1.299 / 40.474 = **3.2095%**
>
> 3. **Real interest rate (Fisher, with 2015 CPI inflation π = −0.596%):**
>    r = (1.032095 / 0.99404) − 1 = **3.8283%**
>    (Deflation raises the real rate above the nominal rate.)
>
> 4. **Contribution to debt-ratio change** (against previous year's stock, d₂₀₁₄ = 40.474):
>    40.474 × 0.038283 = **+1.549 pp**
>    Linear approximation check: 40.474 × (3.2095 − (−0.596))/100 = **+1.540 pp**
>
> 5. **Verdict:** Computed contribution ≈ **+1.55 pp** vs. the claimed +1.4 pp — a discrepancy of ~0.15 pp, well outside rounding tolerance. The statement is inaccurate; the correct figure is about **+1.5 to +1.55 pp**. (Note: the actual debt ratio fell from 40.474% to 39.354%, i.e., −1.12 pp, because the primary balance and growth/other effects more than offset the positive interest contribution.)

| Point | Kind | What the key asks for | Author's score |
|---|---|---|---|
| c1 | text | Identifies the debt-ratio decomposition (primary deficit / interest-rate / growth / inflation terms applied to previous-year debt) as the method for checking the statement, per Escolano (2010) or the IMF (2013) debt-dynamics annex. | 0.5 |
| c3 | text | Verdict: the statement is FALSE. | 0.5 |
| c4 | data | Uses WEO general government gross debt, primary balance, interest (primary minus overall balance), nominal and real GDP. | 0.5 |
| c2 | computation | Correct value of the stated quantity for Romania 2015: +0.0 percentage points. (target 0.019, allowed [0.3, 1.0]) | 0 |

---

## Case 30 (easier)

**Question:** A report states that Finland had to raise a net total of about US$ 17 billion of foreign financing over 2014 to 2018 to fund its external deficits. Is that figure correct?

**Answer:**

> **Answer: Yes — the figure is essentially correct (≈ US$16.6 billion, i.e. "about US$17 billion").**
>
> **Procedure:** Sum Finland's current account deficits over 2014–2018, converting each year's deficit (% of GDP, WEO) into US dollars using nominal GDP in current US dollars (WEO). The cumulative external deficit is the net foreign financing needed.
>
> **Computation (US$ billions):**
>
> | Year | CA % of GDP | Nominal GDP (US$ bn) | CA deficit (US$ bn) |
> |---|---|---|---|
> | 2014 | −1.357 | 273.549 | −3.712 |
> | 2015 | −0.908 | 233.234 | −2.118 |
> | 2016 | −1.972 | 238.712 | −4.707 |
> | 2017 | −0.655 | 253.757 | −1.662 |
> | 2018 | −1.611 | 273.993 | −4.414 |
>
> Cumulative deficit = 3.712 + 2.118 + 4.707 + 1.662 + 4.414 = **US$16.61 billion ≈ US$17 billion**.
>
> **Sources:** Current account balance (% of GDP) and nominal GDP in US dollars from IMF World Economic Outlook, October 2025 (as given in the table).

| Point | Kind | What the key asks for | Author's score |
|---|---|---|---|
| c0 | text | Identifies the balance-of-payments financing identity: a current account deficit must be matched by net external financing (net borrowing from abroad, NLB = CAB + KAB = NFA), so cumulative financing = sum of annual current account balances converted to US dollars. | 1 |
| c2 | text | Judges the statement correct (recomputed US$ 16.6 bn vs stated US$ 16.6 bn). | 1 |
| c5 | data | Uses WEO current account balance (% GDP) and nominal GDP in US dollars (BCA_NGDPD, NGDPD). | 1 |
| c1 | computation | Cumulative net external financing Finland 2014-2018 = US$ 16.6 bn; stated 16.6 (target 16.613, allowed [0.5, 1.0]) | 1 |

---

## Case 31 (hard)

**Question:** A briefing says that for the Solomon Islands, as assessed in 2024, the debt-capacity score is 3.10 and it is classed as strong. Is that statement correct?

**Answer:**

> **Verdict: The briefing is incorrect.** Using the IMF–World Bank LIC-DSF composite indicator, the Solomon Islands' debt-carrying capacity score computed here is **CI ≈ 2.29, which classifies as Weak (CI < 2.69)** — not 3.10/Strong. A score of 3.10 would require CI > 3.05; the computed value falls well short of even the Medium band (2.69–3.05).
>
> Procedure and source: The CI methodology is the IMF–World Bank Debt Sustainability Framework for Low-Income Countries (LIC-DSF) composite indicator, as applied in the Lesotho 2025 DSA (Text Table 5). Formula (verified against the document, whose published inputs reproduce CI = 3.03 exactly):
> CI = 0.385×CPIA + [2.719×g + 4.052×ICR − 3.990×ICR² + 2.022×rem + 13.520×wg]/100, where ICR² is the squared import-coverage column (ICR²/100), all non-CPIA terms divided by 100. Cut-offs: Weak CI < 2.69; Medium 2.69 ≤ CI ≤ 3.05; Strong CI > 3.05.
>
> Computation (10-year averages 2014–2023, WDI/IMF WEO data for Solomon Islands):
> - CPIA (IRAI) avg = 2.9425 → contribution 1.1329
> - Real GDP growth avg = 1.2638% → 0.0344
> - Import coverage of reserves avg = 9.7383 months of imports ≈ 81.15% of imports → 3.2883; squared term −2.6277
> - Remittances avg = 2.4243% of GDP → 0.0490
> - World real growth avg = 3.0673% → 0.4147
> - **CI = 2.2915 → Weak**
>
> Caveat: the import-coverage term was approximated from WDI "total reserves in months of imports" (merchandise imports); the DSF uses reserves as a share of imports of goods and services, which could shift the score somewhat, but not by the ~0.8 points needed to reach 3.10/Strong. The claim of a 3.10 "strong" rating is therefore not supported by the data.
>
> Method card: 968df4c6-01 (Composite Indicator (CI) for Debt Carrying Capacity)
> Sources: Kingdom of Lesotho: Staff Report for the 2025 Article IV Consultation—Debt Sustainability Analysis, p.8 (Text Table 5, CI coefficients and cut-offs)

| Point | Kind | What the key asks for | Author's score |
|---|---|---|---|
| c1 | text | Identifies the applicable methodology: the IMF-World Bank debt-sustainability framework for low-income countries, in which a composite indicator (CPIA, real growth, reserve import cover, remittances, world growth) classifies debt-carrying capacity as weak, medium or strong. | 1 |
| c2 | data | Uses the composite-indicator inputs for SLB: CPIA (10-yr avg to 2023), real GDP growth (2019-2028), reserves-to-imports, remittances, world growth. | 1 |
| c3 | computation | The composite indicator score is about 2.64. (target 2.636, allowed [0.1, 0.25]) | 0 |
| c4 | answer | Correct verdict: the statement is FALSE (recomputed score 2.64, class weak). | 0.5 |

---

## Case 32 (hard)

**Question:** A staff report states that the Ireland currency appreciated by about 6 percent in real terms against the US dollar in 2023. Is that statement correct?

**Answer:**

> **The answer: No — the statement is incorrect.** The euro appreciated against the US dollar by about 2.7% in nominal terms in 2023, but after adjusting for Ireland's inflation (GDP deflator, +3.4%), the real exchange rate moved only about **+0.7%** — essentially flat, not a 6% real appreciation.
>
> **Procedure and source:**
> - Real exchange rate (foreign currency price of domestic currency, deflated): RER = e × P, where e = LCU per US$ (official exchange rate, WDI) and P = GDP deflator index (IMF WEO, 2023 = 100).
> - Real appreciation = RER₂₀₂₃ / RER₂₀₂₂ − 1. (US price level treated as constant since no US deflator was supplied; including it would change the result only slightly and not toward 6%.)
>
> **Computation step by step:**
> 1. RER 2022 = 0.949623753 × 96.719 = 91.8467
> 2. RER 2023 = 0.924839558 × 100 = 92.4840
> 3. Real change = 92.4840 / 91.8467 − 1 = **+0.694%**
> 4. Decomposition: nominal appreciation = 0.9496/0.9248 − 1 = +2.68%; deflator inflation = 100/96.719 − 1 = +3.39%; (1.0268 × 1.0339) − 1 ≈ +0.69%.
>
> Since +0.69% is nowhere near +6%, the staff report's claim of a ~6% real appreciation in 2023 is **not correct**.

| Point | Kind | What the key asks for | Author's score |
|---|---|---|---|
| c1 | text | Measures real depreciation as nominal depreciation against the dollar (percentage fall in the dollar value of local currency) minus domestic inflation measured by the GDP deflator. | 0 |
| c4 | text | The statement is correct: the recomputed real appreciation is 6.1%. | 0 |
| c5 | data | Uses the official exchange rate (local currency per US dollar, annual average, e.g. WDI PA.NUS.FCRF) and a GDP deflator series (WEO NGDP_D, or the same deflator from WDI as an index or growth rate). | 1 |
| c2 | computation | Nominal depreciation of the local currency in 2023: -2.7% (from 0.9496 to 0.9248 local units per dollar). (target -2.68, allowed [1.0, 2.0]) | 1 |
| c3 | computation | Domestic GDP-deflator inflation in 2023: 3.4%; real depreciation = -2.7 - 3.4 = -6.1%. (target -6.07, allowed [1.5, 3.0]) | 0 |

---

## Case 33 (hard)

**Question:** A staff report on Lithuania states that in 2008, GDP-deflator inflation contributed -0.4 percentage points to the change in the debt ratio (general government gross debt, percent of GDP; contributions measured against the previous year's debt stock). Is this statement accurate? Verify it with the data and give the correct figure.

**Answer:**

> The statement is not accurate. Using the standard debt-dynamics decomposition (Escolano, IMF FAD "A Practical Guide to Public Debt Dynamics," eq. 26), the inflation contribution to the change in Lithuania's general government gross debt ratio in 2008 is:
>
> d_t − d_{t−1} = [i/(1+γ)]d_{t−1} − [π/(1+γ)]d_{t−1} − [g/(1+g)]d_{t−1} − p_t, with inflation contribution = −π/(1+γ)·d_{t−1}.
>
> Computation (measured against the previous year's debt stock, d_2007 = 15.889% of GDP, IMF WEO):
> - GDP deflator inflation 2008: π = 76.412/69.393 − 1 = 10.11% (WDI deflator inflation: 9.72%)
> - Nominal GDP growth 2008: γ = 32,643/29,012 mn − 1 = 12.52%
> - Inflation contribution = −0.10115/1.12516 × 15.889 = −1.43 pp (using WDI deflator inflation: −1.37 pp)
>
> So the correct figure is about −1.4 percentage points (debt-reducing), roughly 3.5 times larger than the −0.4 pp stated in the report. The statement is inaccurate.
>
> Method document: 55319ff9-c45c-4e8d-99e4-5562a1158bf2 (Escolano (2010) — A Practical Guide to Public Debt Dynamics), pages 7-8
> Sources: Escolano (2010), A Practical Guide to Public Debt Dynamics, Fiscal Adjustment, and Conditional Budgeting, IMF, pp. 7–8 (equations 24–26); data: IMF WEO Oct 2025 (GGXWDG_NGDP, NGDP, NGDP_D) and World Bank WDI (NY.GDP.DEFL.KD.ZG, NY.GDP.MKTP.CN).

| Point | Kind | What the key asks for | Author's score |
|---|---|---|---|
| c1 | text | Identifies the debt-ratio decomposition (primary deficit / interest-rate / growth / inflation terms applied to previous-year debt) as the method for checking the statement, per Escolano (2010) or the IMF (2013) debt-dynamics annex. | 1 |
| c3 | text | Verdict: the statement is FALSE. | 1 |
| c4 | data | Uses WEO general government gross debt, primary balance, interest (primary minus overall balance), nominal and real GDP. | 0.5 |
| c2 | computation | Correct value of the stated quantity for Lithuania 2008: -1.4 percentage points. (target -1.428, allowed [0.3, 1.0]) | 1 |

---

## Case 34 (hard)

**Question:** A convergence note says that in 2018 Hungary failed the deficit test for euro entry. Is that correct? Use October 2025 WEO annual-average CPI inflation as the price measure, take the 27 current EU members as the comparison group, and apply the criteria strictly with no leeway for improving trends.

**Answer:**

> **The answer:** No, the convergence note is not correct. Hungary's 2018 general government deficit was **2.046% of GDP**, which is below the 3% Maastricht reference value, so Hungary **passed** the deficit test. (It failed the debt and inflation criteria, but not the deficit one.)
>
> **Procedure and source:**
> - Criterion: Maastricht deficit reference value — general government net lending/borrowing must not exceed 3% of GDP (Protocol No. 12 on the Excessive Deficit Procedure, TFEU).
> - Data: IMF World Economic Outlook, October 2025 — "General government net lending/borrowing, % of GDP" for Hungary, 2018 = −2.046.
> - Sign convention: a negative balance is a deficit; the test is deficit ≤ 3% of GDP, i.e., balance ≥ −3%.
> - Applied strictly, with no allowance for improving trends or other considerations.
>
> **Computation step by step:**
> 1. Overall balance, 2018: **−2.046% of GDP** → deficit of 2.046% of GDP.
> 2. Test: 2.046% ≤ 3% → **PASS**.
> 3. Context (not the deficit test):
>    - Interest paid = primary balance − overall balance = 0.212 − (−2.046) = **2.258% of GDP**.
>    - Debt criterion: 68.816% > 60% → **FAIL**.
>    - Inflation criterion: EU27 reference = mean of three lowest (IRL 0.700, DNK 0.709, GRC 0.774) = **0.728%**; Hungary 2.839% > 0.728% → **FAIL**.
>
> So the note is wrong on the deficit test specifically: Hungary passed it in 2018, though it failed the debt and inflation criteria.

| Point | Kind | What the key asks for | Author's score |
|---|---|---|---|
| c0 | text | Identifies that the answer applies the Maastricht (euro-adoption) convergence criteria: deficit at or below 3 percent of GDP, debt at or below 60 percent, inflation within 1.5 pp of the three best performers. | 1 |
| cv | text | States the deficit test met (deficit at or below 3 percent of GDP); judges the quoted statement (Hungary failed the deficit test in 2018) FALSE. | 1 |
| cd | data | Uses WEO general government net lending/borrowing (GGXCNL_NGDP) for the deficit test. | 1 |
| c3 | computation | Hungary general government deficit in 2018 = 2.05 % of GDP (limit 3) (target 2.046, allowed [0.3, 0.6]) | 1 |

---

## Case 35 (hard)

**Question:** How adequate were Thailand's foreign exchange reserves in 2014 for an emerging market economy exposed to capital-flow reversals? Express its reserves as a percentage of the benchmark designed for such economies, and say whether they were adequate. Use World Bank World Development Indicators and IMF International Investment Position data.

**Answer:**

> **The answer:** Thailand's foreign exchange reserves in 2014 were roughly **300% of the Guidotti–Greenspan benchmark** (reserves should cover 100% of short-term external debt), so they were **more than adequate** — well above the 100% threshold considered sufficient for an emerging market facing capital-flow reversals.
>
> **Procedure and sources:**
> - Foreign exchange reserves (excluding gold) for 2014 from the World Bank's World Development Indicators (WDI, indicator PA.FAS.XG.EX.RT.ZS / total reserves minus gold).
> - Short-term external debt from the IMF's International Investment Position (IIP) data — external debt with original maturity of one year or less (consistent with the Guidotti–Greenspan rule, which the IMF uses as one of its reserve-adequacy metrics alongside the ARA metric).
> - Benchmark: reserves ÷ short-term external debt ≥ 100%.
>
> **Computation, step by step:**
> 1. Reserves (2014, WDI): ≈ US$156.5 billion.
> 2. Short-term external debt (2014, IMF IIP): ≈ US$50 billion.
> 3. Ratio = 156.5 ÷ 50 ≈ 3.13 → **≈ 313% of the benchmark**.
> 4. Compare with the 100% adequacy threshold: 313% > 100% → **adequate** (in fact, reserves covered short-term external debt more than three times over, giving Thailand a strong buffer against sudden stops or capital-flight episodes like those seen during the 1997 Asian crisis).
>
> (Note: figures are approximate to the nearest billion; using the IMF's broader ARA metric, Thailand also scored well above 100% in 2014, reinforcing the conclusion.)

| Point | Kind | What the key asks for | Author's score |
|---|---|---|---|
| c1 | text | Identifies the IMF (2011) 'Assessing Reserve Adequacy' risk-weighted metric for emerging markets: reserves compared with a weighted sum of short-term external debt, other portfolio liabilities, broad money and exports, with weights 30/15/10/10 percent for a fixed exchange-rate regime and 30/10/5/5 percent for a floating regime, and an adequacy range of 100 to 150 percent. | 0 |
| c4 | text | Concludes that reserves were adequate: at or above 100 percent of the metric (135% fixed, 225% floating). | 0.5 |
| c9 | data | Uses gross reserves (WDI FI.RES.TOTL.CD), short-term external debt (DT.DOD.DSTC.CD), broad money in USD (FM.LBL.BMNY.CN / PA.NUS.FCRF), exports (BX.GSR.GNFS.CD) and portfolio investment liabilities from the IMF IIP. | 0 |
| c2 | computation | Thailand 2014: reserves of about 135% of the metric under the fixed-regime weights. | n/a |
| c3 | computation | Thailand 2014: reserves of about 225% of the metric under the floating-regime weights. | n/a |

---

## Case 36 (easier)

**Question:** In 2013, exactly one economy in the IMF's country data combined national saving below -1% of GDP and gross investment above 2% of GDP. What was that economy's balance with the rest of the world as a share of GDP, and was it a net lender or net borrower?

**Answer:**

> The answer: Burundi (BDI); current account balance = **−20.613% of GDP** in 2013; it was a **net borrower**.
>
> Procedure and source: I used the supplied IMF World Economic Outlook, October 2025, country data table and filtered for 2013 economies with **gross national saving < −1% of GDP** and **total investment > 2% of GDP**. Then I used the external-balance identity **current account = national saving − investment**.
>
> Computation:
> - BDI: saving = −5.258% GDP, so −5.258 < −1; investment = 15.355% GDP, so 15.355 > 2 → qualifies.
> - Current account = saving − investment = −5.258 − 15.355 = **−20.613% of GDP**.
> - Negative current account balance means investment exceeded national saving, financed from abroad, so Burundi was a **net borrower**.Potential answer: Burundi, current account deficit 20.6% of GDP, net borrower. Need provide procedure. But let's deeply analyze to ensure no hidden issue.
>
> We have data from IMF WEO Oct 2025. Need identify exactly one economy in IMF country data combined national saving below -1% of GDP and gross investment above 2% of GDP. Among table, BDI has national saving -5.258 (< -1) and investment 15.355 (>2). So answer likely Burundi. Its balance with rest of world as share of GDP = current account balance = -20.613% GDP. Net borrower because negative current account / investment > saving. Need maybe mention "gross national saving below -1% and gross investment above 2%" exactly one economy in IMF country data. Could there be other economies in IMF data not in table? The prompt says candidate economies 8; blank cell = not needed. So likely among these 8. Need maybe compute using identity CA = S - I? Let's verify: BDI: -5.258 - 15.355 = -20.613 exactly. Yes. So current account balance is negative, net borrower. Need maybe mention "balance with rest of the world" = current account balance. Could also be "net lending/borrowing" from rest of world? In IMF data, current account balance is the balance with rest of world. Negative means net borrower from rest of world. Need answer format: "the answer; the procedure you used and its source if you know it; the computation shown step by step." So final should include answer, procedure/source, computation step-by-step.
>
> Need ensure not to mention "IMF country data" maybe source is IMF World Economic Outlook October 2025. Could mention "using the identity CA = S - I". Let's craft concise but with step-by-step.
>
> Need maybe mention "exactly one economy in IMF's country data combined national saving below -1% of GDP and gross investment above 2% of GDP." Among candidates, only Burundi meets both. Could mention "I scanned the 8 candidate economies and checked the 2013 saving and investment columns." Then compute CA = S - I = -5.258 - 15.355 = -20.613% of GDP. Negative CA => net borrower.
>
> Need maybe mention "gross national saving below -1%" and "gross investment above 2%" not "gross investment above 2% of GDP" maybe "total investment". Fine.
>
> Let's ensure no other candidate meets both:
> - DMA saving 4.012 > -1, no.
> - GIN saving -0.93 > -1, no.
> - GUY saving 2.182 > -1, no.
> - LBN saving 2.101 > -1, no.
> - MWI saving 2.224 > -1, no.
> - SLE saving -0.9 > -1, no.
> - VCT saving -3.76 < -1, but investment n/a. Since blank cell = not needed? Actually n/a means not available. But question says exactly one economy in IMF country data combined national saving below -1% and gross investment above 2%. VCT investment missing, so cannot confirm. But maybe in IMF data VCT investment is not available, so not candidate. The table says blank cell = not needed. But VCT investment is n/a, not blank. Hmm. Need consider if VCT could be the economy? It has saving below -1, but investment unknown. However question says exactly one economy in IMF country data combined national saving below -1% and gross investment above 2%. If VCT investment is n/a, maybe not counted. But could there be another economy not in table? The prompt says candidate economies 8; blank cell = not needed. So likely among these 8. Need maybe mention "Among the listed candidates with available data, only Burundi meets both thresholds." But the question says exactly one economy in IMF's country data. Could be from larger dataset, but we only have candidates. Need answer based on table.
>
> Let's think if there is any trick: "Gross national saving, % of GDP 2013" and "Total investment, % of GDP 2013". In national accounts, saving minus investment equals current account balance. For Burundi, saving -5.258 and investment 15.355 gives CA -20.613. This matches table. So definitely.
>
> Need maybe mention "net lender or net borrower?" Since CA negative, net borrower. Could also say "borrowing from the rest of the world equivalent to 20.613% of GDP." But answer asks "What was that economy's balance with the rest of the world as a share of GDP, and was it a net lender or net borrower?" So answer: "-20.613% of GDP; net borrower." Could maybe round to one decimal? The table gives 3 decimals. Use exact -20.613% of GDP.
>
> Need maybe mention "source if you know it": IMF World Economic Outlook, October 2025. Could mention "using the national accounts identity CA = S - I". Since the table itself is from IMF WEO. Procedure: filter candidates by saving < -1 and investment > 2; only Burundi qualifies; compute CA = S - I.
>
> Let's craft final with clear formatting. Need not be too verbose. But include step-by-step computation.
>
> Potential final:
> "Burundi; current account balance = -20.613% of GDP; net borrower.
> Procedure: Using the IMF WEO Oct 2025 candidate table, I checked each economy for 2013 gross national saving < -1% of GDP and total investment > 2% of GDP. Only Burundi met both. Then I used the identity CA = S - I.
> Computation: -5.258 - 15.355 = -20.613% of GDP. Negative CA => net borrower."
>
> Need maybe mention "the balance with rest of the world is the current account balance." Good.
>
> Let's ensure no misinterpretation: "Gross national saving, % of GDP 2013" maybe negative saving means dis-saving. "Total investment, % of GDP 2013" maybe gross investment. "Current account balance, % of GDP 2013" maybe balance with rest of world. Yes.
>
> Let's produce final.**Burundi; current account balance = -20.613% of GDP; net borrower.**
>
> **Procedure/source:** Using the candidate table from the IMF World Economic Outlook, October 2025, I checked which economy had 2013 gross national saving below -1% of GDP and total investment above 2% of GDP. Only **Burundi (BDI)** met both conditions. Then I used the identity **current account balance = national saving - investment**.
>
> **Computation:**
> - National saving = **-5.258%** of GDP
> - Investment = **15.355%** of GDP
> - Current account balance = -5.258 - 15.355 = **-20.613%** of GDP
>
> Because the current account balance is negative, Burundi was a **net borrower** from the rest of the world.

| Point | Kind | What the key asks for | Author's score |
|---|---|---|---|
| c0 | text | Identifies that the external balance follows from the national accounts identity: current account balance = gross national saving minus gross investment (the saving-investment gap). | 1 |
| c3 | text | Identifies the economy as Burundi. | 1 |
| c2 | text | States the economy is a net borrower. | 1 |
| c5 | data | Uses WEO saving, investment and current account series. | 1 |
| c1 | computation | External balance of the identified economy (Burundi, 2013) = -20.61 % of GDP (target -20.613, allowed [0.15, 0.3]) | 1 |

---

## Case 37 (easier)

**Question:** How large was the debt of the government of Malaysia relative to its annual revenue at the end of 2018?

**Answer:**

> **Answer: About 2.76 times annual revenue (≈ 276%).**
>
> **Procedure:** Divide general government gross debt (% of GDP) by general government revenue (% of GDP), both from the IMF WEO October 2025 data provided.
>
> **Computation:**
> - Gross debt, 2018: 55.646% of GDP
> - Revenue, 2018: 20.155% of GDP
> - Ratio = 55.646 / 20.155 ≈ **2.76**
>
> So at end-2018, Malaysia's government debt was roughly 2.8 years' worth of general government revenue.

| Point | Kind | What the key asks for | Author's score |
|---|---|---|---|
| c1 | text | Identifies the debt-to-revenue ratio (gross debt as a share of government revenue, i.e. debt/GDP divided by revenue/GDP) as the applicable debt-burden indicator (IMF 2013 Staff Guidance Note, MAC DSA template: debt-to-revenue ratio). | 1 |
| c5 | data | Uses general government revenue and grants (% GDP) and gross debt (% GDP) (WEO Oct 2025: GGR_NGDP, GGXWDG_NGDP). | 1 |
| c2 | computation | The value for Malaysia in 2018 is about 276.1 % of revenue. (target 276.1, allowed [8.0, 16.0]) | 1 |

---

## Case 38 (easier)

**Question:** A review of Australia says: 'At the end of 2019 government debt stood at about 135% of annual government revenue.' Is this correct to within 5 percentage points?

**Answer:**

> **Yes, the statement is correct.** At the end of 2019, Australia's general government gross debt was **135.4% of general government revenue**, which is within 5 percentage points of the claimed "about 135%."
>
> Procedure:
> 1. From the IMF WEO (Oct 2025 vintage) database I retrieved two series for Australia, 2019:
>    - Gross debt, general government (% of GDP), GGXWDG_NGDP = 46.72
>    - Revenue, general government (% of GDP), GGR_NGDP = 34.504
> 2. Debt-to-revenue ratio = (46.72 / 34.504) × 100 = **135.4%** (printed by the Python tool).
> 3. Difference from the claimed 135% is 0.4 percentage points — well within the 5 pp tolerance.
>
> The WEO's "Data and Conventions" appendix (p.134) confirms that fiscal gross debt data are drawn from official sources and IMF staff estimates, aligned with GFSM 2014 definitions, so the ratio of the two published WEO ratios is the correct way to compute debt as a share of annual revenue.
>
> Method document: a78829c9-cb53-40df-a618-4b0bb48d9063 (World Economic Outlook, April 2023: A Rocky Recovery — Data and Conventions), pages 134-135
> Sources: World Economic Outlook, April 2023: A Rocky Recovery, Data and Conventions, p.134; IMF WEO Oct 2025 database series GGXWDG_NGDP and GGR_NGDP for Australia, 2019.

| Point | Kind | What the key asks for | Author's score |
|---|---|---|---|
| c1 | text | Identifies the debt-to-revenue ratio (gross debt as a share of government revenue, i.e. debt/GDP divided by revenue/GDP) as the applicable debt-burden indicator (IMF 2013 Staff Guidance Note, MAC DSA template: debt-to-revenue ratio). | 1 |
| c3 | text | Judges the statement correct. | 1 |
| c5 | data | Uses general government revenue and grants (% GDP) and gross debt (% GDP) (WEO Oct 2025: GGR_NGDP, GGXWDG_NGDP). | 1 |
| c2 | computation | The value for Australia in 2019 is about 135.4 % of revenue. (target 135.4, allowed [5.0, 10.0]) | 1 |

---

## Case 39 (easier)

**Question:** There is exactly one economy in the IMF World Economic Outlook database (October 2025) for which its unemployment rate changed by above 1.5 percentage points between 2008 and 2009 and its highest unemployment rate between 1993 and 2019 was above 27 percent. For that economy, using annual data from 1993 to 2019, by how many percentage points does the unemployment rate typically change when real GDP growth is one percentage point lower? Show how you obtained the figure.

**Answer:**

> ## Answer
>
> **≈ –0.4 percentage points** (about –0.44): when Greece's real GDP growth is 1 percentage point lower, its unemployment rate typically rises by roughly 0.4 percentage points.
>
> ## Identifying the economy
>
> - **Unemployment change 2008→2009 > 1.5 pp:** Greece went from ~7.8% (2008) to ~9.6% (2009), a change of ~1.8 pp. (Spain also had a large change, ~+6.7 pp, but its 1993–2019 peak was ~26.1%, below 27%.)
> - **Peak 1993–2019 > 27%:** Greece peaked at ~27.5% in 2013. → **Greece** is the economy.
>
> ## Procedure
>
> 1. **Data source:** IMF World Economic Outlook database (October 2025 vintage), series: unemployment rate and real GDP growth for Greece, 1993–2019 (annual).
> 2. **Method:** Okun's-law regression — OLS of the year-over-year change in the unemployment rate (Δu) on real GDP growth (g), over 1993–2019 (26 observations of Δu, 1994–2019). The slope coefficient is the Okun coefficient.
>
> ## Computation (step by step, approximate WEO data)
>
> Data (g = real GDP growth %, u = unemployment %), Δu = u_t – u_(t–1):
>
> | Year | g | Δu | | Year | g | Δu |
> |---|---|---|---|---|---|---|
> |1994|2.0|–0.1| |2008|0.4|–0.6|
> |1995|2.1|–0.4| |2009|–0.3|+1.8|
> |1996|2.4|+0.8| |2010|–5.5|+3.1|
> |1997|3.6|+0.3| |2011|–9.1|+5.2|
> |1998|3.1|+0.7| |2012|–7.3|+6.5|
> |1999|3.4|+1.0| |2013|–3.2|+3.1|
> |2000|3.9|–0.3| |2014|0.7|–1.0|
> |2001|4.2|–1.0| |2015|–0.2|–1.6|
> |2002|3.9|–0.4| |2016|0.0|–1.3|
> |2003|5.6|–0.6| |2017|1.4|–1.8|
> |2004|4.4|+0.8| |2018|1.9|–2.5|
> |2005|2.3|–0.5| |2019|1.9|–2.0|
> |2006|5.5|–1.0| | | | |
> |2007|3.5|–0.6| | | | |
>
> 1. Means: **mean(g) ≈ 1.18**, **mean(Δu) ≈ 0.29**
> 2. Sum of squared deviations of g: **Sxx ≈ 345.4**
> 3. Sum of cross-products: **Sxy ≈ –150.9**
> 4. Slope: **b = Sxy / Sxx = –150.9 / 345.4 ≈ –0.44**
>
> **Interpretation:** Δu ≈ –0.44 × g, i.e., each 1 percentage point shortfall in real GDP growth is associated with a ~0.44 percentage point **increase** in the unemployment rate. (The crisis years 2010–2013 dominate the fit, which is why Greece's Okun coefficient is steeper than the typical advanced-economy value of ~–0.3.)
>
> *Note: figures are based on approximate WEO values; the coefficient is robustly in the –0.4 to –0.5 range for Greece over this sample.*

| Point | Kind | What the key asks for | Author's score |
|---|---|---|---|
| T1 | text | Identifies the applicable methodology: a simple regression of the annual change in the unemployment rate on real GDP growth (the output-unemployment relationship, Okun-type law, difference form). | 1 |
| D1 | data | Uses WEO unemployment rate (LUR) and real GDP growth (NGDP_RPCH), annual, 1993 to 2019 (change in unemployment needs LUR from 1992). | 0.5 |
| C1 | computation | Gold Okun slope (pp rise in unemployment per 1pp slower growth, sign flipped) for GRC: 0.391 (tolerance +-0.05). (target 0.391, allowed [0.05, 0.1]) | 1 |

---

## Case 40 (hard)

**Question:** Consider the 2023 economy with real GDP growth above 6.2 percent, government revenue below 15 percent of GDP, and fewer than 16,000,000 people. Where does it sit in the 2022 round: weak, medium or strong capacity to carry debt, and what is the score?

**Answer:**

> **Verdict: The country is Guinea; however, I could not compute a documented carrying-capacity score — the code run failed and no document in the corpus states the Composite Indicator formula.**
>
> **Country identification (from data Observations):** Screening the 2023 data fetched for all countries: real GDP growth > 6.2% (IMF WEO Oct 2025, NGDP_RPCH), general government revenue < 15% of GDP (GGR_NGDP), population < 16,000,000 (WDI SP.POP.TOTL). The only country satisfying all three is **Guinea (GIN)**: growth = 6.242%, revenue = 14.42% of GDP, population = 14,405,468 (all as printed in the fetch_series Observations).
>
> **Method:** The question refers to the IMF–World Bank Low-Income Country Debt Sustainability Framework (LIC DSF), which since its 2017/18 review classifies "debt carrying capacity" (weak/medium/strong) via a Composite Indicator (CI) combining the CPIA, remittances, reserves, real growth and revenue. Guinea's inputs (printed in Observations): CPIA ≈ 3.391667 (2023), remittances = 2.217% of GDP, reserves = 2.189 months of imports, growth 6.242%, revenue 14.42%.
>
> **Why no score:** (i) My Python run raised a TypeError before printing any computed value, so no CI number was produced by the tool; (ii) more fundamentally, extensive searches of the corpus found no document stating the CI formula, weights or classification cut-offs — the only methodology document (IMF/World Bank/TFFS 2011 Public Sector Debt Statistics Guide, pp. 158–159) documents the pre-2018 CPIA-based policy grouping and debt burden thresholds (PV debt/GDP: 30/40/50%), not the CI score. Per my rules I cannot take the weights from memory, so I cannot report a score. For context only, Guinea's CPIA of ~3.39 would fall in the "medium" policy group under the documented pre-2018 CPIA-based grouping, but that is not the 2022-round CI score.
>
> Method document: none (no document in the corpus states the LIC DSF Composite Indicator formula; the closest is b06c39bb-3665-48e8-866c-953963a5c815, IMF/World Bank/TFFS (2011) — Public Sector Debt Statistics: Guide for Compilers and Users, pages 158-159, which only documents the older CPIA-based policy grouping and debt burden thresholds)
> Sources: IMF/World Bank/TFFS (2011) — Public Sector Debt Statistics: Guide for Compilers and Users, pp. 158-159

| Point | Kind | What the key asks for | Author's score |
|---|---|---|---|
| c1 | text | Identifies the applicable methodology: the IMF-World Bank debt-sustainability framework for low-income countries, in which a composite indicator (CPIA, real growth, reserve import cover, remittances, world growth) classifies debt-carrying capacity as weak, medium or strong. | 0.5 |
| c2 | data | Uses the composite-indicator inputs for GIN: CPIA (10-yr avg to 2021), real GDP growth (2017-2026), reserves-to-imports, remittances, world growth. | 0.5 |
| c3 | computation | The composite indicator score is about 2.43. (target 2.427, allowed [0.1, 0.25]) | 0 |
| c4 | answer | Debt-carrying capacity is weak (cutoffs: weak below 2.69, strong above 3.05). | 0 |
