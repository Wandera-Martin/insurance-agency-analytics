# Phase 4 — Persistency and retention metric contract

## Scope and reproducibility

Phase 4 answers: **How persistent is new business after 3, 6 and 13 months,
where are policies being lost, and which agents, units, products, customer
segments and payment behaviours are associated with stronger or weaker
retention?**

`sql/05_persistency_retention.sql` is the metric authority. Its ordinary views
live in `persistency_analytics`, separate from the nine-table source contract and
the Phase 3 layer. Python validates the snapshot, reconciles SQL results and
exports them; it does not calculate persistency.

The fixed observation date is **2026-09-01**. SQL must not use the system clock.
These are portfolio analytical definitions for this synthetic dataset and may
differ from an insurer's actuarial, regulatory or product-specific definitions.
All amounts are UGX. Annualized premium is contract value normalized to one year,
not collected cash or revenue.

## Policy × milestone base grain

`policy_milestones` contains exactly one row for every policy and each milestone
(3, 6 and 13 months). The anniversary is `issue_date + milestone_months`.
A row is milestone-eligible when its anniversary is on or before AS_OF. Immature
rows remain visible for auditability but never enter a denominator.

`policy_persistency` enriches that grain with the selling agent, the agent's
currently recorded unit and region, product, payment frequency and customer
attributes. Selling-agent attribution is fixed by `policies.agent_id`.
Historical unit, region and agent-grade transfers do not exist, so hierarchy
reporting uses the selling agent's currently recorded unit and region and must
not be described as a historical organization reconstruction.

## Historical status reconstruction

For each eligible anniversary, status is the most recent
`policy_status_history` event whose `status_date <= anniversary_date`. Events
after the anniversary cannot affect that milestone. If no event is found, the
policy is treated as Active: issuance establishes initial Active coverage and it
remains effective until a later event. Source validation separately requires an
initial Active event on issue date and unique policy/event dates; SQL also uses
`status_history_id` as a deterministic secondary ordering key.

Status treatment at the anniversary:

| Status | Treatment |
|---|---|
| Active | In force / persistent |
| Grace | In force / persistent |
| Reinstated | In force / persistent |
| Lapsed | Not persistent; separate outcome count |
| Surrendered | Not persistent; separate outcome count |
| Cancelled | Not persistent; separate outcome count |
| Matured | Report separately; not a retention failure and excluded from denominator |

Reinstatement is chronological. A lapse before an anniversary followed by a
reinstatement on or before that anniversary is persistent; a reinstatement after
the anniversary cannot revise the earlier result. Current `policies.policy_status`
is never used to reconstruct a milestone.

## Numerators, denominators and exposed components

`denominator_eligible` means the milestone is mature and status at the
anniversary is not Matured. A policy that matured by the anniversary is excluded
from both policy-count and premium denominators while remaining visible in the
matured count. An immature policy is neither persistent nor non-persistent.

| Metric | Definition |
|---|---|
| Eligible policy count | Count of denominator-eligible policies |
| Persistent policy count | Eligible policies with Active, Grace or Reinstated status |
| Count persistency | Persistent policy count / eligible policy count |
| Eligible annualized premium | One policy-level annualized premium per denominator-eligible policy |
| Persistent annualized premium | Annualized premium on persistent policies |
| Premium persistency | Persistent annualized premium / eligible annualized premium |
| Lapsed / surrendered / cancelled count | Mature milestone rows with that exact status |
| Matured count | Mature milestone rows with Matured status; excluded from denominator |

Zero denominators return SQL NULL, never an invented zero or infinity. Counts and
premium sums are exposed beside every ratio. Premium is aggregated only from the
one-row-per-policy/milestone layer, never after a one-to-many payment join.

## Cohorts and analytical cuts

The primary cohort is calendar issue month. Each cohort/milestone combination
shows policies issued, milestone-eligible policies, denominator-eligible
policies, persistent policies, eligible and persistent annualized premium, both
persistency ratios and separate outcomes. Immature cohorts therefore have zero
eligible counts and NULL ratios rather than being compared with mature cohorts.

The same additive components and ratios are provided for Agency, Region, Agency
Unit, Agent, product, payment frequency and customer segments. Customer segments
are income band, age at issue, acquisition channel and customer region. Age at
issue is completed years on `issue_date`, not age at AS_OF, and uses these bands:
`<25`, `25-34`, `35-44`, `45-54`, `55+`.

Product, customer, hierarchy and payment-frequency comparisons are descriptive.
They show association, not causation, and no external persistency benchmark is
implied.

## Outcome timing

`lapse_timing` uses the first recorded Lapsed, Surrendered or Cancelled event for
each policy/outcome. It keeps the three outcomes distinct and exposes event date,
days from issue, completed elapsed months and these timing bands:
`0-<3 months`, `3-<6 months`, `6-<13 months`, `13-<24 months`, `24+ months`.
“Non-persistent” must not be relabelled “lapsed”.

## Payment behaviour at the observation point

For a policy/milestone, `payment_behavior` includes only installments whose
`due_date <= anniversary_date`; future installments cannot explain an earlier
milestone. It exposes installments due, Paid/Late/Missed/Partial counts, amount
due, amount paid, payment completion, missed, late, partial and paid rates.
The policy annualized premium is not summed from this payment join.

Payment completion is `SUM(amount_paid) / SUM(amount_due)`. Status rates are
status counts / installments due. A milestone with no due installments has zero
counts and amounts and NULL rates. `payment_behavior_summary` compares
persistent, non-persistent and matured outcomes using summed numerators and
denominators; it does not average policy percentages. Immature milestones are
excluded from this comparison.

Payment behaviour is diagnostic and descriptive. Approved language includes
“associated with”, “observed alongside” and “descriptively linked”; it must not
be presented as causing lapse.

## Known limitations

- The snapshot is synthetic and fixed at 2026-09-01.
- Unit and region use the selling agent's current recorded assignment because
  transfer history is unavailable.
- Status is observed at discrete recorded events; no daily coverage ledger or
  product-specific grace-period rules exist.
- Maturity is excluded based on recorded status at the anniversary, not inferred
  from a product-specific contractual convention.
- Payment status is taken from the synthetic installment record; partial and late
  definitions are not insurer-specific accounting rules.
- Annualized-premium persistency is premium-weighted contract retention, not cash
  collection, profitability or revenue.
- Results describe associations in this portfolio and do not establish causes or
  predict future lapse.
