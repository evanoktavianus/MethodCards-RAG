# Grading rubric for methodology-grounded questions (proposal, 30 Oct 2026)

Each question is graded by the LLM judge in four parts. For each part the judge gives full (1), partial (0.5) or none (0) against claims and gold values injected into its prompt. The judge never computes.

| Part | Weight | Credit when |
|---|---|---|
| Methodology | 0.40 | The answer identifies and follows the correct procedure with the right specification and steps (acceptable alternatives listed per item) |
| Inputs | 0.20 | The series, window and vintage used are those the method calls for (read from the tool trace) |
| Result | 0.25 | The stated number or verdict lies inside the gold band or tolerance |
| Interpretation | 0.15 | The conclusion follows from the stated result |

Rules:
- A correct result reached by an inappropriate method earns at most partial credit on Result and none on Methodology.
- Report primary score = weighted sum. Also report, per question, the four part scores and the counts "method right, result wrong" and "result right, method wrong".
- Regression-type items: gold is a band over defensible specifications (windows, vintages); the judge is given the band, sign and significance.
- Weights are a design choice; state them and the reason in the paper.

Human check: eval/human_check/ holds the sheet for the human-checked sample and the agreement results.

## Parameter rule (added 30 Oct 2026)
Methodology correctness (the right procedure) carries the weight. A parameter value differing from the gold is a small deduction under Inputs/Result, not under Methodology, unless the supplied methodology document fixes that value and the answer contradicts it.
- Version-dependent numbers (e.g. income cut-offs): state the version in the question; another official set is a minor deduction.
- Rules of thumb (e.g. Okun coefficient 0.4-0.7): accept the range; record the value used.
- Conventions (e.g. whether interest is discounted): graded against the convention the document states.
Observed failure modes: methodology is recognised in nearly every cell; failures are in execution (convention, table column, sign, arithmetic).
