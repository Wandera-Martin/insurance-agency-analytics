# Phase 5 — Agent Segmentation and Incentive Analysis Findings

## Executive summary

The executed SQL layer evaluated the fixed synthetic snapshot at 1 September
2026. Of 400 agents, 308 (77.0%) met the locked minimum of 20 eligible 13M
policies. The recent-production median among those agents was UGX 21.15 million;
the Agency 13M premium-persistency benchmark inherited from Phase 4 was 92.12%.

The primary management view placed 85 agents in Sustainable Leaders, 69 in
Volume Risk, 95 in Quality Builders, 59 in Development Priority and 92 in
Insufficient Mature History. The latter group produced UGX 8.469 billion of the
UGX 15.523 billion recent AP, making maturity context essential before quality
judgements.

Each campaign roster contained 250 agents. Recorded qualified counts were 105
for Q4 Growth Sprint, 113 for Protection Push and 118 for Mid-Year Agency
Challenge. Production was higher during than before each campaign on the
agent-month measures, but these are descriptive coincidences, not causal uplift.
Only Q4 has complete 3M and 6M retention follow-up; Protection Push has complete
3M follow-up, and Mid-Year has no fully mature milestone at this snapshot.

## 1. Mature-history threshold and benchmarks

| Statistic | Eligible 13M policies per agent |
|---|---:|
| Minimum | 0 |
| First quartile | 23 |
| Median | 48 |
| Third quartile | 62 |
| Maximum | 130 |

**Observation →** The threshold retained 308 of 400 agents, while 92 remained
below it. **Diagnosis →** A material majority can support the 2×2, and the
excluded group remains large enough to require explicit management visibility.
**Business implication →** Lowering the threshold is unnecessary and would trade
away denominator credibility. **Possible management action →** Keep the
20-policy rule and review the insufficient-history group on production and
coaching indicators until its cohorts mature.

## 2. Segment scorecard

| Segment | Agents | Share | Recent policies | Recent AP | 13M eligible | 13M count persistency | 13M premium persistency |
|---|---:|---:|---:|---:|---:|---:|---:|
| Sustainable Leaders | 85 | 21.25% | 893 | UGX 2.822bn | 4,398 | 95.70% | 95.91% |
| Volume Risk | 69 | 17.25% | 745 | UGX 2.360bn | 3,513 | 87.36% | 86.40% |
| Quality Builders | 95 | 23.75% | 402 | UGX 1.133bn | 5,693 | 95.20% | 95.65% |
| Development Priority | 59 | 14.75% | 254 | UGX 0.738bn | 3,333 | 88.57% | 87.37% |
| Insufficient Mature History | 92 | 23.00% | 2,792 | UGX 8.469bn | 269 | 89.59%* | 89.47%* |

\*Shown only as an aggregate with its small mature denominator; these agents are
not quality-classified individually.

**Observation →** Sustainable Leaders and Volume Risk both clear the production
median, but their aggregate 13M premium persistency differs by 9.51 percentage
points. **Diagnosis →** High recent output does not imply the same demonstrated
retention quality. **Business implication →** A volume-only recognition scheme
would combine materially different business-quality histories. **Possible
management action →** Preserve recognition and practice-sharing for Sustainable
Leaders while reviewing Volume Risk agents' mature policy outcomes and customer
follow-up without using stigmatizing labels.

**Observation →** Quality Builders have 95.65% premium persistency but average
UGX 11.93 million recent AP per agent, below the UGX 21.15 million production
benchmark. **Diagnosis →** Their demonstrated quality is strong while current
production is lower. **Business implication →** They are candidates for
production coaching rather than quality remediation. **Possible management
action →** Review pipeline, activity and target context, then pair suitable
agents with Sustainable Leaders for practice-sharing.

**Observation →** Insufficient-history agents contributed 54.6% of recent AP.
**Diagnosis →** Recent production is concentrated among agents whose business
has not yet accumulated a reliable 13M denominator. **Business implication →**
Treating missing maturity as weak quality would misclassify an important source
of current production. **Possible management action →** Monitor their emerging
3M and 6M cohorts and defer 13M quality classification.

## 3. Campaign production

| Campaign | Roster | Qualified | Before AP / agent-month | During AP / agent-month | During policies / agent-month |
|---|---:|---:|---:|---:|---:|
| Q4 Growth Sprint | 250 | 105 | UGX 9.230m | UGX 9.957m | 3.273 |
| Protection Push | 250 | 113 | UGX 10.468m | UGX 12.231m | 4.020 |
| Mid-Year Agency Challenge | 250 | 118 | UGX 13.405m | UGX 14.047m | 4.594 |

Q4's complete post-period is January–March 2026 and Protection Push's is
May–June 2026. Mid-Year's August–September post-period is unavailable because
September is incomplete. August alone is retained as a partial observation and
excluded from the primary comparison.

**Observation →** Campaign-roster AP per service-eligible agent-month was higher
during than before all three campaigns. **Diagnosis →** Campaign timing coincides
with higher recorded production, but roster selection, seasonality, changing
service exposure and synthetic generation can also contribute. **Business
implication →** The differences are unsuitable as causal uplift or financial
return estimates. **Possible management action →** Use the patterns to form
hypotheses for a future prospectively designed evaluation, not to calculate ROI.

During each campaign, recorded qualified agents also had higher AP per
agent-month than recorded non-qualified agents: UGX 10.690m versus 9.425m for
Q4, UGX 12.863m versus 11.714m for Protection Push, and UGX 14.586m versus
13.561m for Mid-Year.

**Observation →** Qualified agents recorded higher production during each
campaign. **Diagnosis →** Qualification is a stored probabilistic synthetic flag,
not a recomputed consequence of observed threshold attainment. **Business
implication →** The qualified/not-qualified gap cannot establish that
qualification or the incentive caused performance. **Possible management action
→** Treat the split as descriptive roster context and retain source-system
qualification rules in any operational implementation.

## 4. Campaign retention maturity

| Campaign | Milestone | Campaign policies | Mature policies | Coverage | Count persistency | Premium persistency | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| Q4 Growth Sprint | 3M | 2,412 | 2,412 | 100.00% | 99.92% | 99.89% | Complete |
| Q4 Growth Sprint | 6M | 2,412 | 2,412 | 100.00% | 96.56% | 96.92% | Complete |
| Q4 Growth Sprint | 13M | 2,412 | 0 | 0.00% | — | — | Not mature |
| Protection Push | 3M | 1,982 | 1,982 | 100.00% | 99.90% | 99.90% | Complete |
| Protection Push | 6M | 1,982 | 41 | 2.07% | 95.12% | 93.90% | Partial |
| Protection Push | 13M | 1,982 | 0 | 0.00% | — | — | Not mature |
| Mid-Year Agency Challenge | 3M | 2,288 | 36 | 1.57% | 100.00% | 100.00% | Partial |
| Mid-Year Agency Challenge | 6M | 2,288 | 0 | 0.00% | — | — | Not mature |
| Mid-Year Agency Challenge | 13M | 2,288 | 0 | 0.00% | — | — | Not mature |

**Observation →** Only Q4 3M/6M and Protection Push 3M have complete campaign
cohort maturity. **Diagnosis →** The apparently strong partial cells represent
only 41 or 36 early policies and are not full campaign outcomes. **Business
implication →** Cross-campaign comparison at 6M or 13M would mix incompatible
follow-up coverage. **Possible management action →** Report only complete cells
as primary findings and refresh Protection Push and Mid-Year after their full
cohorts mature.

## 5. Limitations

- All records and behavioural relationships are synthetic.
- The snapshot is fixed at 2026-09-01; September is incomplete.
- The segmentation combines recent production with older mature quality cohorts.
- Current unit and region are used because transfer history is unavailable.
- Qualification is recorded simulation output and is not reconstructed from
  production or threshold.
- Campaign-roster versus other-agent and qualified versus not-qualified results
  are descriptive comparisons, not experiments.
- Annualized premium is contract value, not collected cash, revenue or profit.
- No ROI, cost-effectiveness, treatment-effect, clustering or predictive
  lapse-risk model is included.
