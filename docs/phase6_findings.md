# Phase 6 Executed Findings

All results below were executed on the deterministic synthetic snapshot dated 2026-09-01.
They demonstrate a historical modelling workflow, not expected performance on real insurance
business. The model is intended only for human-reviewed retention prioritization.

## 1. Historical panel and temporal change

**Observation.** The mature panel contains 403,549 monthly observations for 27,837 policies from
2023-02-28 through 2026-05-31. It contains 7,703 positive observations, an overall 1.9088% positive
rate. Train contains 288,768 rows and 4,683 positives (1.6217%); validation contains 65,482 rows
and 1,606 positives (2.4526%); test contains 49,299 rows and 1,414 positives (2.8682%).

**Diagnosis.** Lapse prevalence rises materially through time. The validation and test periods
are not sparse, but their base rates differ substantially from train.

**Business implication.** Later portfolios face a higher synthetic lapse rate, so discrimination
and calibration must be interpreted separately. Historical probability levels cannot be assumed
to remain accurate merely because ranking remains useful.

**Possible management action.** Monitor both capture/lift and observed-versus-predicted risk by
scoring period. Recalibration would require a new, prospectively governed model cycle; it must not
be performed after inspecting this frozen test result.

## 2. Validation comparison and frozen selection

**Observation.** The train-prevalence benchmark achieved validation PR-AUC 0.02453, ROC-AUC 0.5000,
and Brier score 0.02399. Logistic Regression achieved PR-AUC 0.03149, ROC-AUC 0.57552, Brier score
0.02398, Recall@10% 15.26%, and Lift@10% 1.53. Random Forest achieved PR-AUC 0.03420, ROC-AUC
0.59268, Brier score 0.02395, Recall@10% 16.31%, and Lift@10% 1.63.

**Diagnosis.** Random Forest produced a relative validation PR-AUC improvement of about 8.6% over
Logistic Regression and stronger capture at 5%, 10%, and 20%. Logistic Regression therefore did
not satisfy the predeclared “within 5%” simplicity preference.

**Business implication.** The nonlinear challenger offered a small but material validation ranking
advantage. The gain is not evidence of causality or production readiness.

**Possible management action.** Random Forest was frozen before test evaluation. Its validation
top-10% score cutoff was also frozen at 0.022013; it is an operational review threshold, not a
universal actuarial boundary.

## 3. Held-out test discrimination

**Observation.** The frozen Random Forest achieved test PR-AUC 0.03421 and ROC-AUC 0.56063. At the
validation-frozen cutoff, precision was 3.59%, recall 12.66%, and F1 0.0559. The confusion matrix
was 43,072 true negatives, 4,813 false positives, 1,235 false negatives, and 179 true positives.

Test operational capture was:

| Capacity | Recall | Lift |
|---:|---:|---:|
| Top 5% | 5.94% | 1.19 |
| Top 10% | 12.38% | 1.24 |
| Top 20% | 25.18% | 1.26 |

**Diagnosis.** Ranking remained above random but weakened versus validation. The model captures
approximately one quarter of positive observations in the highest-scored fifth of the test panel.

**Business implication.** The score may help order a constrained review queue, but it is not strong
enough to replace human judgment or broad servicing controls. Most later lapses are not captured
in the top tiers.

**Possible management action.** Use the score as one input to retention outreach, track contacted
and uncontacted outcomes, and compare it with simple payment-rule queues before production use.

## 4. Calibration is weaker than ranking

**Observation.** On validation, the selected model predicted 1.5710% mean risk against 2.4526%
observed, with calibration slope 0.841 and Brier score 0.02395. On test it predicted 1.5763% against
2.8682% observed, with calibration slope 0.803, calibration-in-the-large -1.2919 percentage points,
expected calibration error 0.01292, and Brier score 0.02799.

**Diagnosis.** The model systematically underpredicts absolute risk in later periods even while
retaining modest ranking ability. Its scores are not reliable literal probabilities on the test
period.

**Business implication.** Management capacity tiers are more defensible than statements such as
“this policy has an exact X% chance of lapse.” The temporal base-rate shift is operationally more
important than the small differences in Brier score between validation candidates.

**Possible management action.** Present risk scores as prioritization indices, monitor calibration
prospectively, and only recalibrate with new governance and a new untouched evaluation period.

## 5. Observable associations and explanations

**Observation.** Validation permutation importance ranked days since last payment, age at issue,
paid installment count, premium amount, annualized premium, paid amount, installment count, and
missed installment count among the more informative raw features. Several importances were small
or unstable across the two repeats.

**Diagnosis.** Payment history contributes to ranking, but no single feature dominates. Negative
permutation values and small magnitudes are sampling/interaction signals, not protective causal
effects.

**Business implication.** The model should not be explained with causal language. Deterministic
observable flags are more suitable for an outreach queue than claiming an exact mathematical
reason for each score.

**Possible management action.** Show servicing staff observable signals such as recent missed
premiums, repeated late payments, low recent completion, Grace status, high missed/late rates, and
short tenure. Treat them as review prompts rather than automated decisions.

## 6. Descriptive model-risk diagnostics

**Observation.** Gender was excluded from training. On test, female rows had 2.75% prevalence,
3.25% PR-AUC, and 10.96% recall at the frozen cutoff; male rows had 2.98% prevalence, 3.63% PR-AUC,
and 14.17% recall. Age-band recall ranged from 6.79% to 17.72%. Customer-region recall ranged from
11.57% to 13.56%. Income-band recall ranged from 10.14% to 15.50%.

**Diagnosis.** Descriptive performance differences exist, particularly across age bands, but the
model and data do not establish discrimination, causation, or legal fairness certification.
Synthetic group construction and differing prevalence affect these comparisons.

**Business implication.** A retention workflow requires ongoing group-level monitoring and human
oversight even though gender is not a predictor.

**Possible management action.** Review outreach rates, service offers, and eventual outcomes by
group. Do not use the score for cancellation, pricing, benefit reduction, or underwriting denial.

## 7. Current scoring population

**Observation.** After the frozen test evaluation, the selected train-only model scored 29,360
eligible policies as of 2026-09-01. Capacity tiers contain 2,936 Priority policies (10%), 5,872
Watch policies (20%), and 20,552 Routine policies (70%). Common configured signals include repeated
late payments, short tenure, high late-payment rates, recent missed premiums, and low recent payment
completion. Some policies have no configured observable flag despite receiving a model score.

**Diagnosis.** Percentile tiers reliably match management capacity, whereas absolute scores inherit
the documented underprediction. Flags describe observed conditions but are not SHAP explanations.

**Business implication.** The output can prioritize review and customer support without presenting
uncalibrated scores as exact probabilities.

**Possible management action.** Route Priority policies to prompt human review, use Watch for lower-
intensity monitoring, preserve service for Routine policies, and record outreach outcomes for future
prospective validation.

## Major limitations

- Data and outcomes are synthetic and partly driven by hidden generator profile structure.
- Historical rows for the same policy are repeated risk assessments, not independent entities.
- Current organizational assignment is used because transfer history is unavailable.
- No real intervention, contact, affordability, or causal outcome data exists.
- Test discrimination is modest and later-period absolute risk is materially underpredicted.
- The interrupted first execution was invalidated because test results were not persisted before
  cancellation. No result from that attempt was used. The corrected replacement run persisted its
  frozen test evaluation immediately and is the sole source of findings above.
- Nothing in this work authorizes automatic adverse action.
