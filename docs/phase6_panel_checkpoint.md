# Phase 6 Historical-Panel Checkpoint

## Checkpoint result

**PASS — modelling may begin in a later work stage, but no model was trained at this
checkpoint.**

The leakage-safe historical panel and monthly positive-rate profile were executed against the
validated 35,000-policy synthetic PostgreSQL snapshot dated 2026-09-01. The proposed temporal
split was retained because validation contains 1,606 positive observations and test contains
1,414; neither evaluation period is event-sparse.

SQL source SHA-256:
`3a689e636196e0fa6a4cf3ca8bdba36bb1780a058b83e9475154f279629a7924`

The hash was refreshed after adding the target-free 2026-09-01 scoring population to the same
SQL file. Historical panel definitions and the executed checkpoint counts below were unchanged.

## Historical panel

| Measure | Executed result |
|---|---:|
| Rows | 403,549 |
| Unique policies | 27,837 |
| Observation months | 40 |
| First observation | 2023-02-28 |
| Last mature observation | 2026-05-31 |
| Positive observations | 7,703 |
| Negative observations | 395,846 |
| Overall positive rate | 1.9088% |
| Null targets in mature panel | 0 |
| Duplicate policy/month keys | 0 |
| Immature risk-set rows retained outside model dataset | 83,929 |
| First immature month | 2026-06-30 |

An exploratory installation initially produced one eligible row at 2023-01-31. That isolated
row was excluded before the split was locked because it is not a meaningful monthly portfolio
snapshot. The final panel therefore begins 2023-02-28, consistent with the requirement to avoid
meaningless early observations.

## Monthly target profile

Rates below are `positives / observations` for mature risk-set rows.

| Observation month | Observations | Positives | Positive rate |
|---|---:|---:|---:|
| 2023-02-28 | 236 | 0 | 0.0000% |
| 2023-03-31 | 547 | 1 | 0.1828% |
| 2023-04-30 | 903 | 3 | 0.3322% |
| 2023-05-31 | 1,256 | 9 | 0.7166% |
| 2023-06-30 | 1,618 | 19 | 1.1743% |
| 2023-07-31 | 1,936 | 20 | 1.0331% |
| 2023-08-31 | 2,303 | 23 | 0.9987% |
| 2023-09-30 | 2,686 | 25 | 0.9308% |
| 2023-10-31 | 3,055 | 34 | 1.1129% |
| 2023-11-30 | 3,485 | 43 | 1.2339% |
| 2023-12-31 | 3,904 | 41 | 1.0502% |
| 2024-01-31 | 4,315 | 37 | 0.8575% |
| 2024-02-29 | 4,721 | 39 | 0.8261% |
| 2024-03-31 | 5,235 | 46 | 0.8787% |
| 2024-04-30 | 5,745 | 53 | 0.9225% |
| 2024-05-31 | 6,265 | 60 | 0.9577% |
| 2024-06-30 | 6,811 | 69 | 1.0131% |
| 2024-07-31 | 7,331 | 88 | 1.2004% |
| 2024-08-31 | 7,907 | 100 | 1.2647% |
| 2024-09-30 | 8,480 | 110 | 1.2972% |
| 2024-10-31 | 9,056 | 124 | 1.3693% |
| 2024-11-30 | 9,642 | 133 | 1.3794% |
| 2024-12-31 | 10,283 | 159 | 1.5462% |
| 2025-01-31 | 10,889 | 170 | 1.5612% |
| 2025-02-28 | 11,511 | 193 | 1.6767% |
| 2025-03-31 | 12,188 | 195 | 1.5999% |
| 2025-04-30 | 12,871 | 197 | 1.5306% |
| 2025-05-31 | 13,637 | 209 | 1.5326% |
| 2025-06-30 | 14,439 | 239 | 1.6552% |
| 2025-07-31 | 15,351 | 282 | 1.8370% |
| 2025-08-31 | 16,235 | 316 | 1.9464% |
| 2025-09-30 | 17,169 | 358 | 2.0852% |
| 2025-10-31 | 18,049 | 408 | 2.2605% |
| 2025-11-30 | 18,887 | 434 | 2.2979% |
| 2025-12-31 | 19,822 | 446 | 2.2500% |
| 2026-01-31 | 20,837 | 482 | 2.3132% |
| 2026-02-28 | 21,750 | 535 | 2.4598% |
| 2026-03-31 | 22,895 | 589 | 2.5726% |
| 2026-04-30 | 24,019 | 657 | 2.7353% |
| 2026-05-31 | 25,280 | 757 | 2.9945% |

## Proposed temporal split

| Split | Exact dates | Rows | Positives | Positive rate |
|---|---|---:|---:|---:|
| Train | 2023-02-28–2025-12-31 | 288,768 | 4,683 | 1.6217% |
| Validation | 2026-01-31–2026-03-31 | 65,482 | 1,606 | 2.4526% |
| Test | 2026-04-30–2026-05-31 | 49,299 | 1,414 | 2.8682% |

The dates preserve strict temporal ordering and every labelled date has a complete 90-day future
window at the fixed snapshot. The rising positive rate across periods is material distribution
drift. Later model selection must assess validation/test stability and calibration rather than
assuming a stationary base rate. Because this is generator-driven synthetic data, the trend is
not evidence about a real insurer.

## Leakage and boundary verification

- Historical status is reconstructed from status history; final `policies.policy_status` is not
  referenced.
- Stored final-snapshot `premium_payments.payment_status` is not referenced.
- Payments due after an observation and payment resolutions occurring after it are excluded.
- Active, Grace, adverse-status, reinstatement, and future-status-event cases were tested.
- Exact policy-age days 29/30 and target days 90/91 were tested.
- A lapse on the observation date removes the policy from the risk set.
- Immature labels remain null outside `model_dataset`; mature targets contain no nulls.
- The panel has exactly one row per policy and observation date.
- Train precedes validation, which precedes test; no random split is used.

During the checkpoint, the first executed profile exposed a defect in which policies with no
future lapse had a null target rather than zero. The SQL was corrected with an explicit negative
label, the reconciliation test was strengthened, and the panel was fully rebuilt before these
results were recorded.

## Engineering verification

- Phase 6 PostgreSQL tests: **8 passed**.
- Complete repository PostgreSQL-backed suite: **74 passed**.
- Ruff lint: **PASS**.
- Ruff format check: **PASS** after mechanically formatting the new test file.
- PostgreSQL source tables changed: **none**.
- Model fitting or scoring performed: **none**.

The remaining Phase 6 tasks from the implementation brief—including preprocessing, baselines,
challenger modelling, validation-only selection, held-out testing, calibration, explainability,
fairness diagnostics, current scoring, notebook, final findings, README, inventory, and CI—remain
pending until work resumes after this checkpoint.
