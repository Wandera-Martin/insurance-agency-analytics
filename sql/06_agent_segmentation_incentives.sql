-- Phase 5 agent segmentation and incentive analysis metric layer.
-- Requires the validated Phase 3 and Phase 4 views. Install atomically.
CREATE SCHEMA IF NOT EXISTS agent_intelligence;

CREATE OR REPLACE VIEW agent_intelligence.snapshot AS
SELECT DATE '2026-09-01' AS as_of,
       DATE '2026-06-01' AS recent_window_start,
       DATE '2026-09-01' AS recent_window_end,
       20::bigint AS minimum_eligible_13m_policies;

-- One row per snapshot agent. Policies and targets aggregate independently.
CREATE OR REPLACE VIEW agent_intelligence.recent_agent_production AS
WITH production AS (
    SELECT p.agent_id, COUNT(*)::bigint AS recent_policies,
           SUM(p.annualized_premium) AS recent_annualized_premium,
           COUNT(DISTINCT date_trunc('month', p.issue_date))::bigint AS recent_producing_months
    FROM insurance_analytics.policies p
    CROSS JOIN agent_intelligence.snapshot s
    WHERE p.issue_date >= s.recent_window_start
      AND p.issue_date < s.recent_window_end
    GROUP BY p.agent_id
), targets AS (
    SELECT t.agent_id,
           SUM(t.policy_target) FILTER (WHERE t.policy_target > 0) AS recent_policy_target,
           SUM(t.premium_target) FILTER (WHERE t.premium_target > 0) AS recent_premium_target,
           COUNT(*) FILTER (WHERE t.policy_target > 0)::bigint AS policy_target_months,
           COUNT(*) FILTER (WHERE t.premium_target > 0)::bigint AS premium_target_months
    FROM insurance_analytics.sales_targets t
    CROSS JOIN agent_intelligence.snapshot s
    WHERE t.target_month >= s.recent_window_start
      AND t.target_month < s.recent_window_end
    GROUP BY t.agent_id
)
SELECT a.agent_id, a.agency_unit_id, u.agency_name, u.region, a.agent_grade,
       a.join_date, a.status, a.exit_date,
       s.recent_window_start, (s.recent_window_end - 1) AS recent_window_end,
       COALESCE(p.recent_policies, 0)::bigint AS recent_policies,
       COALESCE(p.recent_annualized_premium, 0) AS recent_annualized_premium,
       COALESCE(p.recent_producing_months, 0)::bigint AS recent_producing_months,
       COALESCE(p.recent_policies, 0)::numeric / 3 AS avg_policies_per_month,
       COALESCE(p.recent_annualized_premium, 0) / 3 AS avg_annualized_premium_per_month,
       t.recent_policy_target, t.recent_premium_target,
       COALESCE(t.policy_target_months, 0)::bigint AS policy_target_months,
       COALESCE(t.premium_target_months, 0)::bigint AS premium_target_months,
       COALESCE(p.recent_policies, 0)::numeric / NULLIF(t.recent_policy_target, 0)
           AS recent_policy_target_achievement,
       COALESCE(p.recent_annualized_premium, 0) / NULLIF(t.recent_premium_target, 0)
           AS recent_premium_target_achievement
FROM insurance_analytics.agents a
JOIN insurance_analytics.agency_units u USING (agency_unit_id)
CROSS JOIN agent_intelligence.snapshot s
LEFT JOIN production p USING (agent_id)
LEFT JOIN targets t USING (agent_id)
WHERE a.join_date <= s.as_of;

-- Phase 4 supplies every persistency numerator, denominator, and ratio.
CREATE OR REPLACE VIEW agent_intelligence.agent_quality AS
SELECT a.agent_id,
       COALESCE(p.eligible_policies, 0)::bigint AS eligible_13m_policies,
       COALESCE(p.persistent_policies, 0)::bigint AS persistent_13m_policies,
       COALESCE(p.eligible_annualized_premium, 0) AS eligible_13m_annualized_premium,
       COALESCE(p.persistent_annualized_premium, 0) AS persistent_13m_annualized_premium,
       p.count_persistency AS count_persistency_13m,
       p.premium_persistency AS premium_persistency_13m
FROM insurance_analytics.agents a
CROSS JOIN agent_intelligence.snapshot s
LEFT JOIN persistency_analytics.agent_persistency p
  ON p.agent_id = a.agent_id AND p.milestone_months = 13
WHERE a.join_date <= s.as_of;

CREATE OR REPLACE VIEW agent_intelligence.mature_history_distribution AS
SELECT COUNT(*)::bigint AS candidate_agents,
       MIN(eligible_13m_policies)::bigint AS minimum_eligible_13m_policies,
       percentile_cont(0.25) WITHIN GROUP (ORDER BY eligible_13m_policies) AS q1_eligible_13m_policies,
       percentile_cont(0.50) WITHIN GROUP (ORDER BY eligible_13m_policies) AS median_eligible_13m_policies,
       percentile_cont(0.75) WITHIN GROUP (ORDER BY eligible_13m_policies) AS q3_eligible_13m_policies,
       MAX(eligible_13m_policies)::bigint AS maximum_eligible_13m_policies,
       COUNT(*) FILTER (WHERE eligible_13m_policies >= s.minimum_eligible_13m_policies)::bigint
           AS agents_meeting_threshold,
       COUNT(*) FILTER (WHERE eligible_13m_policies >= s.minimum_eligible_13m_policies)::numeric
           / NULLIF(COUNT(*), 0) AS threshold_retained_share,
       s.minimum_eligible_13m_policies AS locked_threshold
FROM agent_intelligence.agent_quality q
CROSS JOIN agent_intelligence.snapshot s
GROUP BY s.minimum_eligible_13m_policies;

CREATE OR REPLACE VIEW agent_intelligence.segmentation_thresholds AS
SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY p.recent_annualized_premium)
           AS production_benchmark,
       o.premium_persistency AS quality_benchmark,
       s.minimum_eligible_13m_policies
FROM agent_intelligence.recent_agent_production p
JOIN agent_intelligence.agent_quality q USING (agent_id)
CROSS JOIN agent_intelligence.snapshot s
CROSS JOIN persistency_analytics.overall_persistency o
WHERE q.eligible_13m_policies >= s.minimum_eligible_13m_policies
  AND o.milestone_months = 13
GROUP BY o.premium_persistency, s.minimum_eligible_13m_policies;

CREATE OR REPLACE VIEW agent_intelligence.agent_segmentation AS
WITH classified AS (
    SELECT p.*, q.eligible_13m_policies, q.persistent_13m_policies,
           q.eligible_13m_annualized_premium, q.persistent_13m_annualized_premium,
           q.count_persistency_13m, q.premium_persistency_13m,
           t.production_benchmark, t.quality_benchmark,
           q.eligible_13m_policies >= t.minimum_eligible_13m_policies AS sufficient_history,
           CASE
               WHEN q.eligible_13m_policies < t.minimum_eligible_13m_policies THEN 'Not assessed'
               WHEN p.recent_annualized_premium >= t.production_benchmark THEN 'High production'
               ELSE 'Lower production'
           END AS production_band,
           CASE
               WHEN q.eligible_13m_policies < t.minimum_eligible_13m_policies THEN 'Not assessed'
               WHEN q.premium_persistency_13m >= t.quality_benchmark THEN 'Strong quality'
               ELSE 'Weaker quality'
           END AS quality_band
    FROM agent_intelligence.recent_agent_production p
    JOIN agent_intelligence.agent_quality q USING (agent_id)
    CROSS JOIN agent_intelligence.segmentation_thresholds t
)
SELECT *, CASE
    WHEN NOT sufficient_history THEN 'Insufficient Mature History'
    WHEN production_band = 'High production' AND quality_band = 'Strong quality'
        THEN 'Sustainable Leaders'
    WHEN production_band = 'High production' AND quality_band = 'Weaker quality'
        THEN 'Volume Risk'
    WHEN production_band = 'Lower production' AND quality_band = 'Strong quality'
        THEN 'Quality Builders'
    ELSE 'Development Priority'
END AS segment
FROM classified;

-- Segment ratios are always rebuilt from additive components.
CREATE OR REPLACE VIEW agent_intelligence.segment_summary AS
WITH totals AS (
    SELECT CASE
               WHEN GROUPING(s.region) = 1 THEN 'Agency'
               WHEN GROUPING(s.agency_unit_id) = 1 THEN 'Region'
               ELSE 'Unit'
           END AS grain,
           s.region, s.agency_unit_id, s.agency_name, s.segment,
           COUNT(*)::bigint AS agent_count,
           COUNT(*) FILTER (WHERE s.sufficient_history)::bigint AS sufficient_history_agents,
           SUM(s.recent_policies)::bigint AS recent_policies,
           SUM(s.recent_annualized_premium) AS recent_annualized_premium,
           SUM(s.eligible_13m_policies)::bigint AS eligible_13m_policies,
           SUM(s.persistent_13m_policies)::bigint AS persistent_13m_policies,
           SUM(s.eligible_13m_annualized_premium) AS eligible_13m_annualized_premium,
           SUM(s.persistent_13m_annualized_premium) AS persistent_13m_annualized_premium,
           SUM(s.recent_policy_target) AS recent_policy_target,
           SUM(s.recent_premium_target) AS recent_premium_target
    FROM agent_intelligence.agent_segmentation s
    GROUP BY GROUPING SETS (
        (s.segment),
        (s.region, s.segment),
        (s.region, s.agency_unit_id, s.agency_name, s.segment)
    )
), ratios AS (
    SELECT *,
           SUM(agent_count) OVER (PARTITION BY grain, region, agency_unit_id) AS population_agents
    FROM totals
)
SELECT *, agent_count::numeric / NULLIF(population_agents, 0) AS share_of_segmentation_population,
       recent_annualized_premium / NULLIF(agent_count, 0) AS average_recent_ap_per_agent,
       persistent_13m_policies::numeric / NULLIF(eligible_13m_policies, 0)
           AS count_persistency_13m,
       persistent_13m_annualized_premium / NULLIF(eligible_13m_annualized_premium, 0)
           AS premium_persistency_13m,
       recent_policies::numeric / NULLIF(recent_policy_target, 0)
           AS recent_policy_target_achievement,
       recent_annualized_premium / NULLIF(recent_premium_target, 0)
           AS recent_premium_target_achievement
FROM ratios;

-- Same mature policies supply both cohort production and subsequent quality.
CREATE OR REPLACE VIEW agent_intelligence.cohort_aligned_agent_quality AS
SELECT f.agent_id, MIN(f.issue_date) AS cohort_issue_start, MAX(f.issue_date) AS cohort_issue_end,
       SUM(f.eligible_policies)::bigint AS cohort_policies,
       SUM(f.eligible_annualized_premium) AS cohort_annualized_premium,
       SUM(f.persistent_policies)::bigint AS persistent_13m_policies,
       SUM(f.persistent_annualized_premium) AS persistent_13m_annualized_premium,
       SUM(f.persistent_policies)::numeric / NULLIF(SUM(f.eligible_policies), 0)
           AS count_persistency_13m,
       SUM(f.persistent_annualized_premium) / NULLIF(SUM(f.eligible_annualized_premium), 0)
           AS premium_persistency_13m
FROM persistency_analytics.persistency_facts f
WHERE f.milestone_months = 13 AND f.eligible_policies = 1
GROUP BY f.agent_id;

CREATE OR REPLACE VIEW agent_intelligence.campaign_roster AS
SELECT i.incentive_id, i.campaign_name, i.start_date, i.end_date,
       i.agent_id, i.threshold, i.incentive_amount, i.qualified,
       a.agency_unit_id, u.agency_name, u.region, a.agent_grade,
       a.join_date, a.exit_date, a.status AS agent_status
FROM insurance_analytics.incentives i
JOIN insurance_analytics.agents a USING (agent_id)
JOIN insurance_analytics.agency_units u USING (agency_unit_id);

-- End bounds are exclusive. The incomplete Mid-Year After window remains visible.
CREATE OR REPLACE VIEW agent_intelligence.campaign_periods AS
WITH campaigns AS (
    SELECT DISTINCT campaign_name, start_date AS campaign_start, end_date AS campaign_end,
           ((EXTRACT(YEAR FROM end_date)::int - EXTRACT(YEAR FROM start_date)::int) * 12
            + EXTRACT(MONTH FROM end_date)::int - EXTRACT(MONTH FROM start_date)::int + 1)
               AS duration_months
    FROM agent_intelligence.campaign_roster
), equal_windows AS (
    SELECT c.*, w.period_order, w.period_label, w.period_start, w.period_end_exclusive
    FROM campaigns c
    CROSS JOIN LATERAL (VALUES
        (1, 'Before',
            (c.campaign_start - make_interval(months => c.duration_months))::date,
            c.campaign_start),
        (2, 'During', c.campaign_start, c.campaign_end + 1),
        (3, 'After', c.campaign_end + 1,
            (c.campaign_end + 1 + make_interval(months => c.duration_months))::date)
    ) AS w(period_order, period_label, period_start, period_end_exclusive)
), partial_window AS (
    SELECT c.*, 4 AS period_order, 'Partial post (August only)'::text AS period_label,
           DATE '2026-08-01' AS period_start, DATE '2026-09-01' AS period_end_exclusive
    FROM campaigns c
    WHERE c.campaign_name = 'Mid-Year Agency Challenge'
)
SELECT e.campaign_name, e.campaign_start, e.campaign_end, e.period_order, e.period_label,
       e.period_start, e.period_end_exclusive - 1 AS period_end,
       e.period_end_exclusive <= s.as_of AS window_available,
       e.period_label IN ('Before', 'During', 'After')
           AND e.period_end_exclusive <= s.as_of AS primary_comparable,
       CASE WHEN e.period_end_exclusive <= s.as_of THEN 'Complete' ELSE 'Unavailable' END
           AS window_status
FROM equal_windows e CROSS JOIN agent_intelligence.snapshot s
UNION ALL
SELECT p.campaign_name, p.campaign_start, p.campaign_end, p.period_order, p.period_label,
       p.period_start, p.period_end_exclusive - 1, TRUE, FALSE, 'Partial'
FROM partial_window p;

-- One roster agent per period. Phase 3's agent-month spine supplies service eligibility.
CREATE OR REPLACE VIEW agent_intelligence.campaign_agent_performance AS
SELECT r.campaign_name, r.start_date AS campaign_start, r.end_date AS campaign_end,
       r.agent_id, r.qualified, p.period_order, p.period_label, p.period_start, p.period_end,
       p.window_available, p.primary_comparable, p.window_status,
       CASE WHEN p.window_available THEN COUNT(am.agent_id)::bigint END AS service_agent_months,
       CASE WHEN p.window_available THEN COALESCE(SUM(am.new_policies), 0)::bigint END AS policies,
       CASE WHEN p.window_available THEN COALESCE(SUM(am.new_business_annualized_premium), 0) END
           AS annualized_premium,
       CASE WHEN p.window_available
            THEN COUNT(am.agent_id) FILTER (WHERE am.new_policies > 0)::bigint END
           AS producing_months,
       CASE WHEN p.window_available
            THEN COALESCE(SUM(am.new_policies), 0)::numeric / NULLIF(COUNT(am.agent_id), 0) END
           AS policies_per_agent_month,
       CASE WHEN p.window_available
            THEN COALESCE(SUM(am.new_business_annualized_premium), 0)
                 / NULLIF(COUNT(am.agent_id), 0) END AS annualized_premium_per_agent_month,
       CASE WHEN p.window_available THEN SUM(am.policy_target) FILTER (WHERE am.policy_target > 0) END
           AS policy_target,
       CASE WHEN p.window_available THEN SUM(am.premium_target) FILTER (WHERE am.premium_target > 0) END
           AS premium_target,
       CASE WHEN p.window_available
            THEN COALESCE(SUM(am.new_policies), 0)::numeric
                 / NULLIF(SUM(am.policy_target) FILTER (WHERE am.policy_target > 0), 0) END
           AS policy_target_achievement,
       CASE WHEN p.window_available
            THEN COALESCE(SUM(am.new_business_annualized_premium), 0)
                 / NULLIF(SUM(am.premium_target) FILTER (WHERE am.premium_target > 0), 0) END
           AS premium_target_achievement
FROM agent_intelligence.campaign_roster r
JOIN agent_intelligence.campaign_periods p
  ON p.campaign_name = r.campaign_name
 AND p.campaign_start = r.start_date AND p.campaign_end = r.end_date
LEFT JOIN agency_performance.agent_month am
  ON am.agent_id = r.agent_id AND am.period_start >= p.period_start
 AND am.period_start <= p.period_end
GROUP BY r.campaign_name, r.start_date, r.end_date, r.agent_id, r.qualified,
         p.period_order, p.period_label, p.period_start, p.period_end,
         p.window_available, p.primary_comparable, p.window_status;

CREATE OR REPLACE VIEW agent_intelligence.campaign_summary AS
WITH classified AS (
    SELECT p.campaign_name, p.campaign_start, p.campaign_end, p.period_order,
           p.period_label, p.period_start, p.period_end, p.window_available,
           p.primary_comparable, p.window_status, am.agent_id, am.new_policies,
           am.new_business_annualized_premium, am.policy_target, am.premium_target,
           CASE WHEN r.agent_id IS NULL THEN 'Descriptive comparison group'
                ELSE 'Campaign roster' END AS comparison_group
    FROM agent_intelligence.campaign_periods p
    JOIN agency_performance.agent_month am
      ON am.period_start >= p.period_start AND am.period_start <= p.period_end
    LEFT JOIN agent_intelligence.campaign_roster r
      ON r.campaign_name = p.campaign_name AND r.start_date = p.campaign_start
     AND r.end_date = p.campaign_end AND r.agent_id = am.agent_id
), totals AS (
    SELECT campaign_name, campaign_start, campaign_end, period_order, period_label,
           period_start, period_end, window_available, primary_comparable, window_status,
           comparison_group, COUNT(DISTINCT agent_id)::bigint AS agents,
           COUNT(*)::bigint AS service_agent_months,
           COUNT(*) FILTER (WHERE new_policies > 0)::bigint AS producing_agent_months,
           SUM(new_policies)::bigint AS policies,
           SUM(new_business_annualized_premium) AS annualized_premium,
           SUM(policy_target) FILTER (WHERE policy_target > 0) AS policy_target,
           SUM(premium_target) FILTER (WHERE premium_target > 0) AS premium_target
    FROM classified
    GROUP BY campaign_name, campaign_start, campaign_end, period_order, period_label,
             period_start, period_end, window_available, primary_comparable, window_status,
             comparison_group
)
SELECT campaign_name, campaign_start, campaign_end, period_order, period_label,
       period_start, period_end, window_available, primary_comparable, window_status,
       comparison_group, agents,
       CASE WHEN window_available THEN service_agent_months END AS service_agent_months,
       CASE WHEN window_available THEN producing_agent_months END AS producing_agent_months,
       CASE WHEN window_available THEN policies END AS policies,
       CASE WHEN window_available THEN annualized_premium END AS annualized_premium,
       CASE WHEN window_available THEN policies::numeric / NULLIF(service_agent_months, 0) END
           AS policies_per_agent_month,
       CASE WHEN window_available THEN annualized_premium / NULLIF(service_agent_months, 0) END
           AS annualized_premium_per_agent_month,
       CASE WHEN window_available THEN policy_target END AS policy_target,
       CASE WHEN window_available THEN premium_target END AS premium_target,
       CASE WHEN window_available THEN policies::numeric / NULLIF(policy_target, 0) END
           AS policy_target_achievement,
       CASE WHEN window_available THEN annualized_premium / NULLIF(premium_target, 0) END
           AS premium_target_achievement
FROM totals;

CREATE OR REPLACE VIEW agent_intelligence.campaign_qualification_comparison AS
SELECT campaign_name, campaign_start, campaign_end, period_order, period_label,
       period_start, period_end, window_available, primary_comparable, window_status,
       CASE WHEN qualified THEN 'Qualified' ELSE 'Not qualified' END AS qualification_group,
       COUNT(*)::bigint AS roster_agents,
       SUM(service_agent_months)::bigint AS service_agent_months,
       SUM(policies)::bigint AS policies, SUM(annualized_premium) AS annualized_premium,
       SUM(producing_months)::bigint AS producing_agent_months,
       SUM(policies)::numeric / NULLIF(SUM(service_agent_months), 0) AS policies_per_agent_month,
       SUM(annualized_premium) / NULLIF(SUM(service_agent_months), 0)
           AS annualized_premium_per_agent_month,
       SUM(policy_target) AS policy_target, SUM(premium_target) AS premium_target,
       SUM(policies)::numeric / NULLIF(SUM(policy_target), 0) AS policy_target_achievement,
       SUM(annualized_premium) / NULLIF(SUM(premium_target), 0) AS premium_target_achievement
FROM agent_intelligence.campaign_agent_performance
GROUP BY campaign_name, campaign_start, campaign_end, period_order, period_label,
         period_start, period_end, window_available, primary_comparable, window_status, qualified;

-- Auditable campaign policy × Phase 4 milestone grain.
CREATE OR REPLACE VIEW agent_intelligence.campaign_policy_followup AS
SELECT r.campaign_name, r.start_date AS campaign_start, r.end_date AS campaign_end,
       r.agent_id, r.qualified, f.policy_id, f.issue_date, f.milestone_months,
       f.anniversary_date, f.milestone_eligible, f.denominator_eligible,
       f.persistent_flag, f.status_at_anniversary, f.annualized_premium,
       f.milestone_eligible_policies, f.eligible_policies, f.persistent_policies,
       f.eligible_annualized_premium, f.persistent_annualized_premium
FROM agent_intelligence.campaign_roster r
JOIN persistency_analytics.persistency_facts f
  ON f.agent_id = r.agent_id
 AND f.issue_date >= r.start_date AND f.issue_date <= r.end_date;

CREATE OR REPLACE VIEW agent_intelligence.campaign_maturity AS
WITH campaigns AS (
    SELECT DISTINCT campaign_name, start_date AS campaign_start, end_date AS campaign_end
    FROM agent_intelligence.campaign_roster
), milestones AS (
    SELECT c.*, m.milestone_months
    FROM campaigns c CROSS JOIN (VALUES (3), (6), (13)) AS m(milestone_months)
), totals AS (
    SELECT m.campaign_name, m.campaign_start, m.campaign_end, m.milestone_months,
           COUNT(DISTINCT f.policy_id)::bigint AS campaign_policies,
           COALESCE(SUM(f.milestone_eligible_policies), 0)::bigint AS milestone_mature_policies,
           COALESCE(SUM(f.eligible_policies), 0)::bigint AS eligible_policies,
           COALESCE(SUM(f.persistent_policies), 0)::bigint AS persistent_policies,
           COALESCE(SUM(f.eligible_annualized_premium), 0) AS eligible_annualized_premium,
           COALESCE(SUM(f.persistent_annualized_premium), 0) AS persistent_annualized_premium,
           m.campaign_end + make_interval(months => m.milestone_months) <= s.as_of
               AS full_campaign_cohort_mature
    FROM milestones m CROSS JOIN agent_intelligence.snapshot s
    LEFT JOIN agent_intelligence.campaign_policy_followup f
      ON f.campaign_name = m.campaign_name AND f.campaign_start = m.campaign_start
     AND f.campaign_end = m.campaign_end AND f.milestone_months = m.milestone_months
    GROUP BY m.campaign_name, m.campaign_start, m.campaign_end, m.milestone_months,
             s.as_of
)
SELECT *, milestone_mature_policies::numeric / NULLIF(campaign_policies, 0)
           AS maturity_coverage,
       persistent_policies::numeric / NULLIF(eligible_policies, 0) AS count_persistency,
       persistent_annualized_premium / NULLIF(eligible_annualized_premium, 0)
           AS premium_persistency,
       CASE WHEN full_campaign_cohort_mature THEN 'Complete'
            WHEN milestone_mature_policies > 0 THEN 'Partial'
            ELSE 'Not mature' END AS maturity_status,
       full_campaign_cohort_mature AS primary_comparable
FROM totals;

CREATE OR REPLACE VIEW agent_intelligence.campaign_quality_followup AS
WITH grouped AS (
    SELECT campaign_name, campaign_start, campaign_end, milestone_months,
           qualification_group,
           COUNT(DISTINCT policy_id)::bigint AS campaign_policies,
           SUM(milestone_eligible_policies)::bigint AS milestone_mature_policies,
           SUM(eligible_policies)::bigint AS eligible_policies,
           SUM(persistent_policies)::bigint AS persistent_policies,
           SUM(eligible_annualized_premium) AS eligible_annualized_premium,
           SUM(persistent_annualized_premium) AS persistent_annualized_premium
    FROM (
        SELECT f.*, q.qualification_group
        FROM agent_intelligence.campaign_policy_followup f
        CROSS JOIN LATERAL (VALUES
            ('All roster'::text),
            (CASE WHEN f.qualified THEN 'Qualified' ELSE 'Not qualified' END)
        ) AS q(qualification_group)
    ) expanded
    GROUP BY campaign_name, campaign_start, campaign_end, milestone_months,
             qualification_group
)
SELECT g.*, g.milestone_mature_policies::numeric / NULLIF(g.campaign_policies, 0)
           AS maturity_coverage,
       g.persistent_policies::numeric / NULLIF(g.eligible_policies, 0) AS count_persistency,
       g.persistent_annualized_premium / NULLIF(g.eligible_annualized_premium, 0)
           AS premium_persistency,
       m.full_campaign_cohort_mature, m.maturity_status,
       m.full_campaign_cohort_mature AS primary_comparable
FROM grouped g
JOIN agent_intelligence.campaign_maturity m
  USING (campaign_name, campaign_start, campaign_end, milestone_months);

-- Executable Phase 5 scorecard.
SELECT segment, agent_count, recent_annualized_premium, premium_persistency_13m
FROM agent_intelligence.segment_summary
WHERE grain = 'Agency'
ORDER BY segment;
