# Phase 3 — Agency performance metric contract

## Scope and reproducibility

The business question is: **How is the Agency business performing overall, where
is performance coming from, and where should management intervene?**

`sql/04_agency_performance.sql` is the primary metric layer. Its ordinary views
live in `agency_performance`, separate from the Phase 2 nine-table contract in
`insurance_analytics`. No materialized views or payment joins are used. Python
validates the existing snapshot and reads SQL results; Pandas only presents them.

AS_OF is **2026-09-01**, inclusive for observed events. Complete monthly production
uses half-open `[period_start, period_end)` intervals, from January 2023 through
August 2026. The generator's policy and lead observation window starts January 1,
2023; the calendar does not infer coverage from the first observed sale. Latest
complete month is August, previous complete month July. September is excluded
from production trends, targets, and MoM. The SQL never uses the system date.

All amounts are UGX. Annualized premium is normalized new business contract value,
**not collected cash or revenue**. All issued policies count, including policies
that subsequently lapse, surrender or cancel. Current status counts are not
persistency. This phase does not calculate persistency.

## Metrics and denominators

| Metric | Definition |
|---|---|
| New policies | Count policy rows with issue_date in the period; one row per policy_id. |
| New business annualized premium | Sum annualized_premium of those policies. |
| Eligible agents | join_date < period_end AND (exit_date IS NULL OR exit_date >= period_start). Current status is not an eligibility filter. |
| Producing agents | Distinct eligible agent_id with at least one policy issued in the period. |
| Producing agent ratio / monthly activation | Producing agents / eligible agents. |
| Policies per producing agent | New policies / producing agents. |
| Average annualized premium per new policy | New business annualized premium / new policies. |
| Policy target achievement | SUM(actual new policies) / SUM(valid policy targets). |
| Premium target achievement | SUM(actual annualized premium) / SUM(valid premium targets). |
| Policy / premium target achievers | Separate counts of eligible agents with the respective valid target and achievement >=100%. |
| Lead cohort conversion | Leads created in the period marked converted with conversion_date <= AS_OF / all leads created in the period. |
| Policy MoM | (Current complete-month new policies - immediately previous complete-month new policies) / previous complete-month new policies. |
| Premium MoM | Same method using new business annualized premium. |

Zero denominators produce SQL NULL (unavailable), never infinity or an invented
zero. Zero production with a positive target is 0% achievement. Eligible agents
without production remain in the denominator. Distinct counts apply within each
period: adding monthly headcounts gives agent-months, not unique annual agents.

Targets are unique by agent/month in the existing contract. A positive target is
valid; zero, missing or nonpositive targets cannot establish achievement. Coverage
counts are returned separately for policy and premium targets. Aggregate ratios
retain **all actual production** over the sum of available positive targets, as
specified; when coverage is incomplete they describe partial target coverage and
must not be presented as fully comparable performance. No targets are imputed or
prorated. Targets begin January 2025 and the generator skips midmonth recruits;
earlier months have NULL achievement. Never average agent achievement percentages.

## Grains and reconciliation

`agent_month`: one eligible agent per complete month, with production, targets,
leads, activation, tenure and grade. Policies and leads are independently
aggregated before either is joined to this spine. Targets join at their unique
agent/month grain. Premium installments and status-history rows never enter it.

`performance`: Agency → Region → Agency Unit; `agent_month` supplies the final
Agent level. `performance` also provides Grade and Tenure cuts. Units with no
eligible agents remain visible, with zero counts and NULL ratios. Each grain's
additive totals reconcile to Agency, including eligible non-producers. NULL region
or grade is an unknown category, not discarded. Current unit assignment, region
and grade are used retrospectively because transfer and grade history do not
exist; these views are not reconstructions of historical reporting lines.

`monthly_trends`: complete-month Agency metrics and lagged MoM. The full calendar
retains zero-production months, so lag never jumps across a missing month.
The first month and any zero prior denominator have NULL growth.

## Target bands

Missing/Invalid Target takes precedence even for zero production. For valid
policy targets the exact bands are:

| Band | Rule |
|---|---|
| Non-Producing | Zero policies |
| Under Target | Positive production and policy achievement <80% |
| Near Target | 80% to <100% |
| Target Achiever | 100% to <120% |
| High Achiever | >=120% |

The premium distribution uses the same disclosed 80/100/120% cutoffs applied to
premium achievement, with zero-policy agents Non-Producing. Policy and premium
bands and achiever counts are separate. `target_distribution` includes all eligible
agents, including missing targets; omitted combinations have zero observations.

## Lead funnel and maturity

`lead_funnel` counts **recorded stage evidence in the creation cohort**, observed
at AS_OF. It is not timestamped transition tracking:

| Display stage | Evidence |
|---|---|
| Lead | Every lead created in the month |
| Contacted | contact_status = Contacted |
| Appointment Booked | appointment_status in Booked, Completed, No Show |
| Appointment Completed | appointment_status = Completed |
| Application Submitted | application_status in Submitted, Approved, Declined, Withdrawn |
| Application Approved | application_status = Approved |
| Converted | converted and conversion_date <= AS_OF |

Completed appointments and no-shows establish booking evidence; decided
applications establish submission evidence. We do not infer an appointment from
an approved application. The synthetic generator allows approval without recorded
appointment completion, so stage counts can rise. Do not interpret such increases
as negative drop-off, or claim sequential stage conversion rates. Each stage share
uses all leads in that creation cohort as denominator.

Recent cohorts have less time to convert: **cohort maturity bias** makes their
snapshot conversion rates non-equivalent to older cohorts. Conversion observed
after the creation month but on/before AS_OF still counts. The generator clips
conversion dates to service end/AS_OF, so it also simplifies realistic delays.
There is no lead_id on policies; matching customer/agent/date does not establish
direct lead-to-policy attribution. Policy counts and converted leads are separate.

## Recruitment activation, tenure and concentration

`agent_activation` records each recruited agent's first **observed** policy through
AS_OF. Days to first policy is issue_date - join_date only when join_date is on or
after January 1, 2023; earlier recruits are left-censored and return NULL. Agents
with no observed policy also return NULL, not zero days. Summaries of observed
days describe agents who sold, not the waiting time of every recruit.

First-30-day activation uses `[join_date, join_date + 30 days)` (day 0 through
day 29). A valid denominator requires observable recruitment history, a fully
elapsed 30-day window through AS_OF inclusive, and no exit before day 29. An
eligible recruit activates if its first policy falls in that interval. A mature
eligible recruit with no policy is False; left-censored, immature and early-exit
recruits are NULL/excluded. These flags and excluded counts are exposed, not
silently pooled. Early-exit exclusion avoids comparing unequal exposure and
conditions the rate on full service; it must not hide onboarding attrition.
Exclusion counts may overlap. `activation_cohorts` groups by recruitment month.

Tenure at reporting-month start uses disclosed bands 0–<6, 6–<12, 12–<24 and 24+
calendar months; agents joining within the month enter the first band. These are
descriptive cuts, not performance thresholds. Grade uses the recorded current
agent_grade, including unknown values.

`concentration`: take CEIL(10% × distinct producing agents) each month. Rank
independently by policies and annualized premium, descending, with agent_id as
deterministic tie-breaker. Each share divides top-group production by all producing
agents' production. Small cohorts can yield a group larger than exactly 10%; the
selected count is exposed. No producers yields zero selected and NULL shares.

## Interpretation

Findings follow Observation → Diagnosis → Business implication → Possible
management action. Descriptive associations do not establish causes. Target bands,
tenure bands, activation eligibility and concentration rounding above are the only
analytical thresholds; no hidden red/amber/green cutoffs are introduced.
