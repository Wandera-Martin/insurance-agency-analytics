# Phase 4 — Persistency and Retention Findings

## Executive summary

The executed SQL layer evaluated the fixed synthetic snapshot at 1 September
2026. Of 35,000 issued policies, 29,492 were mature for 3M, 24,980 for 6M and
17,206 for 13M. Count persistency was 99.89% at 3M, 97.40% at 6M and 92.36% at
13M. Premium persistency was slightly lower at 99.88%, 97.30% and 92.12%.

No policy was Matured or Cancelled at an eligible anniversary in this generated
snapshot, so those disclosed counts are zero. This does not change their metric
treatment: a future Matured anniversary would be reported separately and
excluded from the denominator. Results are descriptive portfolio analytics, not
an insurer standard, causal study or prediction.

## 1. Portfolio scorecard

| Milestone | Eligible policies | Persistent policies | Count persistency | Eligible annualized premium | Persistent annualized premium | Premium persistency | Lapsed | Surrendered |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 3M | 29,492 | 29,461 | 99.89% | UGX 89.283bn | UGX 89.176bn | 99.88% | 31 | 0 |
| 6M | 24,980 | 24,330 | 97.40% | UGX 75.469bn | UGX 73.431bn | 97.30% | 644 | 6 |
| 13M | 17,206 | 15,891 | 92.36% | UGX 52.050bn | UGX 47.946bn | 92.12% | 1,121 | 194 |

**Observation →** Both measures decline as the observation point lengthens, and
premium persistency is below count persistency at every milestone.

**Diagnosis →** More policy exits have accumulated by 13M, while the premium gap
shows that the non-persistent group carries slightly more annualized premium per
policy than the persistent group.

**Business implication →** A count-only scorecard would modestly overstate the
retained premium weight of the portfolio.

**Possible management action →** Monitor count and premium persistency together,
always with eligible counts and annualized-premium denominators.

## 2. Issue cohorts

The lowest mature 13M count result was the July 2025 cohort: 844 of 989 eligible
policies persisted (85.34%), with 85.46% premium persistency. June 2025 recorded
87.47% count persistency and May 2025 recorded 89.35%. In comparison, January
2023 recorded 97.67% across 257 eligible policies. Cohort denominators differ and
only cohorts that actually reached 13M are included.

**Observation →** The latest 13M-mature cohorts in this snapshot have lower
observed retention than several earlier cohorts.

**Diagnosis →** The cohort view localizes the portfolio decline in issue time but
does not show whether product, agent, unit, customer or synthetic generation mix
accounts for it.

**Business implication →** A portfolio average can conceal recent cohort
deterioration.

**Possible management action →** Review the May–July 2025 cohorts by unit,
product and selling agent before choosing an intervention.

## 3. Region and agency unit

| Region | Eligible policies at 13M | Count persistency | Premium persistency |
|---|---:|---:|---:|
| Eastern | 2,553 | 93.07% | 92.94% |
| Western | 2,974 | 92.60% | 92.36% |
| Central | 8,427 | 92.42% | 92.18% |
| Northern | 3,252 | 91.42% | 91.08% |

Mbarara had the highest unit-level 13M count persistency (95.27% across 1,204
eligible policies). Kampala East followed at 93.74%. Lira recorded the lowest
(90.30% across 1,619), followed by Fort Portal (90.79%). The gap between Mbarara
and Lira was 4.96 percentage points.

**Observation →** Northern was the lowest observed region, while unit results
varied inside regions.

**Diagnosis →** Lira contributed a weaker unit result within Northern, but the
available data cannot establish the operational cause. Unit and region are the
selling agent's currently recorded assignment, not historical assignment.

**Business implication →** Region-level action alone may be too broad.

**Possible management action →** Begin with unit and agent drill-down in Lira and
Fort Portal, preserving denominator context and comparing both premium and count
measures.

## 4. Products

| Product | Eligible policies at 13M | Count persistency | Premium persistency |
|---|---:|---:|---:|
| Savings Growth | 3,524 | 92.76% | 92.51% |
| Protection Plus | 3,391 | 92.69% | 92.58% |
| Education Builder | 3,490 | 92.44% | 92.21% |
| Family Income Plan | 3,409 | 92.29% | 92.21% |
| Retirement Secure | 3,392 | 91.60% | 91.53% |

**Observation →** The product range is relatively narrow, with a 1.17-point gap
between the highest and lowest count results.

**Diagnosis →** Retirement Secure is associated with the lowest observed 13M
retention in this snapshot; the result does not show that the product caused
policy exits.

**Business implication →** Product comparisons warrant context from customer,
payment-frequency and distribution mix before management acts.

**Possible management action →** Review Retirement Secure's recent mature
cohorts and payment patterns rather than treating the aggregate difference as a
product defect.

## 5. Payment frequency and behaviour

| Frequency | Eligible policies at 13M | Count persistency | Premium persistency |
|---|---:|---:|---:|
| Semi-Annual | 1,080 | 92.87% | 93.49% |
| Annual | 1,681 | 92.50% | 92.74% |
| Monthly | 11,947 | 92.42% | 92.07% |
| Quarterly | 2,498 | 91.71% | 91.29% |

At 13M, non-persistent policies had a 13.61% late-installment rate versus 12.32%
for persistent policies. Their paid-installment rate was 79.43% versus 80.87%,
and payment completion was 94.35% versus 94.69%. Missed rates were 4.40% and
4.27%, respectively. These comparisons use installments due on or before the
anniversary, never future payments, and normalize by installment opportunities.

**Observation →** Quarterly frequency had the lowest observed 13M persistency.
Non-persistent policies also showed a modestly higher late rate and lower paid
rate before the anniversary.

**Diagnosis →** The recorded payment differences are small descriptive
associations and may coexist with product, customer or cohort mix.

**Business implication →** Raw missed-payment counts would be misleading because
frequencies create different numbers of installment opportunities.

**Possible management action →** Monitor opportunity-normalized late and missed
rates within mature cohorts and test operational follow-up separately; do not
treat these findings as causal or predictive.

## 6. Customer segments

At 13M, the 5M+ income band had the highest count persistency (93.32%, 1,152
eligible policies), while the 2M–5M band had the lowest (91.70%, 3,591). The
45–54 age-at-issue band was highest at 93.00%; the 55+ band was lowest at 91.77%.
Digital acquisition was highest at 92.72%, while Event was lowest at 91.81%.
Customer-region count results ranged from 92.04% in Eastern to 92.62% in
Northern.

**Observation →** Segment differences exist but are generally modest in the
executed portfolio.

**Diagnosis →** No single customer cut identifies a dominant retention divide,
and segment composition can overlap across all dimensions.

**Business implication →** Isolated segment rankings are insufficient grounds
for differentiated customer treatment.

**Possible management action →** Use segments to focus descriptive review, then
validate any proposed response with adequately sized cohorts and fair-treatment
controls.

## 7. Outcome timing

The history contained 2,996 policies with a recorded lapse and 603 with a
recorded surrender by AS_OF. Lapse timing was concentrated at 6–<13 months
(1,125 policies), followed by 3–<6 months (789) and 13–<24 months (757). Recorded
surrenders were concentrated at 6–<13 months (345) and 13–<24 months (178).
Only 18 lapses occurred before three months. Lapse and surrender remain distinct;
neither is combined with cancellation under an unlabeled outcome.

**Observation →** The largest recorded lapse and surrender bands occur after the
earliest three-month milestone.

**Diagnosis →** The timing distribution is consistent with the sharpest
scorecard decline appearing between 6M and 13M, but does not identify why those
events occurred.

**Business implication →** Retention monitoring limited to 3M would miss most
recorded exits in this snapshot.

**Possible management action →** Maintain follow-up through the 13M observation
window and distinguish lapse from surrender in operational review.

## 8. Analytical limitations

- All data and behavioural relationships are synthetic.
- The fixed snapshot is 2026-09-01; no system date is used.
- The definition is a portfolio analytical convention, not an insurer-specific
  actuarial or regulatory standard.
- Current agent unit and region are used because historical transfer data does
  not exist.
- No eligible anniversary was Matured or Cancelled in this snapshot, although
  both paths are explicitly implemented and adversarially tested.
- Status events are discrete records rather than a daily coverage ledger.
- Annualized premium is normalized contract value, not cash, revenue or profit.
- Payment-status definitions follow the synthetic source rules.
- All comparisons are descriptive associations; they do not establish causality
  or predict future lapse.
