# Phase 5 — Agent segmentation and incentive analysis metric contract

## Scope and reproducibility

Phase 5 answers: **Which agents combine strong production with strong business
quality, which agents need intervention, and what do incentive campaigns appear
to do to production and subsequent retention?**

`sql/06_agent_segmentation_incentives.sql` is the metric authority. Python
validates and exports its results; it does not reproduce segmentation, campaign,
or persistency formulas. The fixed observation date is **2026-09-01**. September
2026 is incomplete and is excluded from complete-month comparisons. SQL never
uses the system date.

All results use synthetic data. Annualized premium (AP) is normalized contract
value, not cash, revenue, profit, or a basis for incentive ROI.

## Primary management segmentation

The primary view intentionally combines **current production × historical
demonstrated business quality**. It is a management segmentation, not a
time-aligned causal comparison.

Every agent in the validated snapshot receives one row. A complete agent spine
means an agent with no June–August production has measurable zero production,
not missing production. Current unit, region, grade, and status are used because
assignment history does not exist. The source includes Active, Inactive, and
Exited agents; status is exposed rather than used as an undisclosed exclusion.

### Production

The recent window is the three complete months from **2026-06-01 through
2026-08-31**, implemented as `[2026-06-01, 2026-09-01)`. Recent policies count
issued policy rows once. Recent AP sums policy annualized premium once, without
joining payments. Producing months count months with at least one issued policy.
Average policies and AP per month divide by all three complete months, including
zero months.

Policy and premium targets are summed across the same three months. Positive
targets are valid; missing or zero totals yield NULL achievement. Actual
production is never discarded because a target is unavailable.

The high-production cutoff is the SQL median recent AP among agents with at least
20 eligible 13M policies. Exact equality is **High production**; values below the
median are **Lower production**.

### Quality and mature-history gate

Quality reuses `persistency_analytics.persistency_facts` and the Phase 4
historical anniversary-status logic. Primary quality is 13M premium persistency;
13M count persistency is secondary. The benchmark is the Agency 13M premium
persistency read from `persistency_analytics.overall_persistency`, never a
documented constant.

Agents need at least **20 eligible 13M policies** for the 2×2. The executed
pre-build profile found 400 candidate agents, minimum 0, Q1 23, median 48, Q3 62,
maximum 130; 308 agents (77.0%) meet the threshold. The threshold is therefore
retained unchanged. Agents below it are `Insufficient Mature History` regardless
of production.

For sufficient-history agents, premium persistency exactly equal to the Agency
benchmark is **Strong quality**; a value below it is **Weaker quality**.

| Segment | Rule |
|---|---|
| Sustainable Leaders | High production + Strong quality |
| Volume Risk | High production + Weaker quality |
| Quality Builders | Lower production + Strong quality |
| Development Priority | Lower production + Weaker quality |
| Insufficient Mature History | Fewer than 20 eligible 13M policies |

Segment summaries calculate persistency from summed persistent and eligible
components, never an average of agent percentages. Segment share uses all agents
in the displayed Agency, region, or unit as its denominator, including the
insufficient-history segment.

`cohort_aligned_agent_quality` is secondary analytical support. It reports
production volume and retention for the same 13M-mature policy cohort. It does
not replace the primary management segmentation.

## Campaign roster and qualification

The incentives table is the campaign roster at one agent–campaign record. The
exporter rejects duplicate agent/campaign/date records. It uses the three
recorded campaigns and their stored dates:

| Campaign | Start | End |
|---|---|---|
| Q4 Growth Sprint | 2025-10-01 | 2025-12-31 |
| Protection Push | 2026-03-01 | 2026-04-30 |
| Mid-Year Agency Challenge | 2026-06-01 | 2026-07-31 |

`qualified` is recorded synthetic status. It is not recomputed from `threshold`,
and roster membership does not imply qualification. The generator assigned it
probabilistically, so qualified/not-qualified comparisons are descriptive. The
incentive amount is not a valid financial-return measure; Phase 5 calculates no
ROI or cost-effectiveness result.

## Campaign production windows

All complete comparisons use equal-duration calendar windows:

| Campaign | Before | During | After |
|---|---|---|---|
| Q4 Growth Sprint | Jul–Sep 2025 | Oct–Dec 2025 | Jan–Mar 2026 |
| Protection Push | Jan–Feb 2026 | Mar–Apr 2026 | May–Jun 2026 |
| Mid-Year Agency Challenge | Apr–May 2026 | Jun–Jul 2026 | Unavailable: Aug–Sep 2026 is not complete |

An August-only Mid-Year observation is exposed as `Partial post (August only)`,
marked partial and excluded from primary equal-window comparisons. The full
Mid-Year After row remains visible as unavailable with NULL metrics; it is not
silently truncated.

Campaign production is aggregated at agent-month before campaign summaries.
Agent-month service eligibility follows Phase 3: `join_date < month_end` and no
exit before month start. Policies, AP, producing months, service-eligible agent
months, targets, and target numerators/denominators remain additive. Policies
and AP per agent-month divide by summed service-eligible agent-months.

Campaign-roster agents are compared with other service-eligible agents labelled
`Descriptive comparison group`. This is not an experimental design. No treatment
effects or difference-in-differences estimates are produced.

## Campaign retention follow-up

A campaign policy must satisfy both conditions: its selling agent is on that
campaign roster and its issue date falls inside the recorded campaign dates.
Each such policy is joined to the existing Phase 4 3M, 6M, and 13M facts.

Maturity coverage is:

`milestone-mature campaign policies / all campaign policies`.

The policy count, mature count, Phase 4 eligible denominator, persistent count,
eligible AP, and persistent AP are all shown. Count and premium persistency use
the Phase 4 eligible denominators. Full-cohort comparability is determined from
the campaign end plus the milestone, not from a fortuitously early subset of
actual sales.

At the snapshot, Q4 Growth Sprint is fully mature at 3M and 6M but not 13M;
Protection Push is fully mature only at 3M; and Mid-Year Agency Challenge is not
fully mature at any milestone. Partial results expose coverage and are excluded
from primary campaign-to-campaign comparisons. Campaigns are not compared on
13M persistency at this snapshot.

## Interpretation and limitations

- Campaign patterns are associations in synthetic data, not causal effects.
- Qualification is recorded simulation output, not observed threshold attainment.
- Current unit attribution is not historical organization reconstruction.
- Agent status does not reconstruct service history; join and exit dates define
  service-eligible agent-months.
- Annualized premium is not cash collection, revenue, or profitability.
- Incomplete follow-up is never presented as fully comparable.
- No clustering, predictive model, lapse-risk score, ROI, or cost-effectiveness
  calculation belongs to Phase 5.
