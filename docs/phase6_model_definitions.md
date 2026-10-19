# Phase 6 Lapse-Risk Model Definitions

## Status and checkpoint discipline

Phase 6 estimates which currently in-force policies are at elevated risk of entering
`Lapsed` status within the next 90 days. The first delivery checkpoint is the validated
historical panel and its monthly target profile. No model may be trained until the panel,
monthly observation counts, monthly positive counts, monthly positive rates, and proposed
temporal split counts have been executed and reviewed. If validation or test positives are
too sparse for meaningful evaluation, implementation stops without silently changing dates.

## Fixed analytical clock

The source snapshot is fixed at **2026-09-01**. SQL uses this literal through
`lapse_risk.snapshot`; it never uses `CURRENT_DATE`. A labelled observation is mature only
when `observation_date + 90 days <= 2026-09-01`.

## Observation grain and risk set

The historical grain is one row per policy and calendar month-end observation date, beginning
2023-02-28. An executed pre-model profile found only one eligible row at 2023-01-31, so that
analytically meaningless early snapshot was excluded before the temporal split was locked. A
policy is eligible at an observation date only when:

- the policy has been issued;
- `observation_date - issue_date >= 30` calendar days; and
- its latest status-history event on or before the observation date is `Active`, `Grace`, or
  `Reinstated`.

The exact age boundary is intentional: day 29 is excluded and day 30 is included. `Grace` is
an in-force risk state, not a lapse. A chronologically later `Reinstated` event can return a
policy to the risk set. `Lapsed`, `Surrendered`, `Cancelled`, and `Matured` are excluded.
Historical status is reconstructed only from `insurance_analytics.policy_status_history`;
the final `policies.policy_status` and outcome date columns are not used.

Repeated monthly rows are repeated risk assessments, not independent policy entities. Random
row splitting and random cross-validation are prohibited.

## Target definition and label maturity

`lapse_next_90d = 1` when the first `Lapsed` status event strictly after the observation date
falls on or before `observation_date + 90 days`. A lapse exactly on day 90 is positive; a lapse
on day 91 is negative. A lapse on the observation date makes the policy already lapsed and
therefore outside the risk set. Only mature risk-set observations enter `model_dataset`.
Immature risk-set rows remain visible in `policy_observations` with a null target and must not
be coerced to zero.

## Historical status reconstruction

For every policy/observation pair, SQL selects the latest event whose `status_date` is on or
before the observation date, ordered by event date and then stable history identifier. The
first event after the observation date is never allowed to affect the reconstructed status.
The same chronology applies at the current scoring date.

## Payment-history reconstruction

Only installments with `due_date <= observation_date` are present in historical features.
Stored `payment_status` is not used because it represents the final synthetic snapshot and can
encode later resolution. SQL reconstructs the observable state from `due_date`, `payment_date`,
`amount_due`, and `amount_paid`:

- a payment received by the observation date for the full amount is `Paid` when received no
  more than two days after its due date, otherwise `Late`;
- a payment received by the observation date for less than the amount due is `Partial`;
- an installment with no payment received by the observation date is `Missed as of
  observation`, including one eventually resolved after the observation date.

For a future payment resolution, the historical observable amount paid is zero. This convention
describes snapshot delinquency, not a contractual lapse or grace determination. Lifetime and
trailing-90-day counts, rates, amounts, completion ratios, and event recencies are calculated
after reducing payments to one aggregate row per policy/observation.

## Eligible feature families

Policy features are product, payment frequency, premium amount, annualized premium, sum assured,
term, age in days/months, reconstructed status, and premium-to-sum-assured ratio. Customer
features are income band, acquisition channel, customer region, and age at issue. Region is the
main organizational feature. Current unit identifiers are retained only for operational
traceability because historical assignment changes are unavailable.

Gender is excluded from predictors and retained separately only for descriptive model-risk
diagnostics. Optional occupation and marital status are not included in the first implementation.

## Prohibited predictors and leakage audit

The training feature matrix must exclude all identifiers, outcome dates, final policy status,
future events and payments, future campaign or target results, hidden generator profiles, and
Phase 5 segmentation or current persistency classifications. In particular it may not contain
`policy_id`, `customer_id`, `agent_id`, `agency_unit_id`, `payment_id`, `status_history_id`,
`target_id`, `incentive_id`, `lapse_date`, `surrender_date`, gender, or any column whose name
indicates a future target or outcome. Identifiers may remain in panel and scoring exports for
traceability but must be removed before preprocessing.

## Proposed temporal split

The split is subject to the first checkpoint profile:

- Train: all mature observations through 2025-12-31.
- Validation: 2026-01-31 through 2026-03-31.
- Test: 2026-04-30 through 2026-05-31.

The maximum train date must precede the minimum validation date, and the maximum validation date
must precede the minimum test date. The test set remains untouched during selection. Split dates
will not change unless the monthly distribution demonstrates inadequate positives and the change
is explicitly documented before modelling.

## Model candidates and selection contract

After the checkpoint passes, candidates will be a constant base-rate benchmark, Logistic
Regression in an sklearn preprocessing pipeline, and exactly one simple nonlinear challenger.
Selection uses validation PR-AUC, ROC-AUC, top-5/10/20% recall and lift, Brier score, calibration,
stability, and interpretability. Accuracy is not a primary metric. If Logistic Regression is
close to the challenger, the simpler model is preferred. The selected model is evaluated once
on the held-out test set.

## Operational use, tiers, and explanation

Current scoring uses the same reconstructed risk-set and 30-day age rules at 2026-09-01 but has
no fabricated future target. Capacity-based tiers are Priority (top 10%), Watch (next 20%), and
Routine (remaining 70%), subject to deterministic tie handling. Observable reason flags describe
known signals such as recent missed premiums, repeated lateness, low payment completion, Grace
status, or short tenure. They are not causal explanations or SHAP values.

The output supports human retention review, customer outreach, and service or payment support.
It must not drive cancellation, adverse pricing, benefit reduction, underwriting denial, or
discriminatory treatment.

## Fairness and model-risk diagnostics

Post-model diagnostics will report sample size, prevalence, average score, precision, and recall
where meaningful across gender, age-at-issue band, customer region, and income band. PR-AUC is
reported only where group sample sizes and both target classes support it. These are descriptive
diagnostics, not legal fairness certification.

## Limitations

The data is synthetic. Lapse and payment behaviour partly inherit hidden generator structure,
including agent-profile risk, so measured performance may be cleaner than real insurer data.
There is no historical agent-transfer data, intervention outcome data, contractual arrears
engine, or basis for causal interpretation. Results must not be presented as expected production
performance on real insurance business.
