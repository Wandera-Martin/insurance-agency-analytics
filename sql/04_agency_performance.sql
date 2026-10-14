-- Phase 3 metric layer. Install atomically with psql --single-transaction.
-- A separate schema preserves the Phase 2 nine-table loader contract.
CREATE SCHEMA IF NOT EXISTS agency_performance;

CREATE OR REPLACE VIEW agency_performance.snapshot AS
SELECT DATE '2026-09-01' AS as_of, DATE '2023-01-01' AS observation_start;

CREATE OR REPLACE VIEW agency_performance.periods AS
SELECT month::date AS period_start, (month + INTERVAL '1 month')::date AS period_end
FROM agency_performance.snapshot,
LATERAL generate_series(observation_start,
    date_trunc('month', as_of)::date - INTERVAL '1 month', INTERVAL '1 month') AS month;

-- Exactly one row per eligible agent/month. Aggregate independent facts BEFORE joins.
CREATE OR REPLACE VIEW agency_performance.agent_month AS
WITH production AS (
    SELECT date_trunc('month', p.issue_date)::date AS period_start, p.agent_id,
           COUNT(*) AS new_policies, SUM(p.annualized_premium) AS new_business_annualized_premium
    FROM insurance_analytics.policies p CROSS JOIN agency_performance.snapshot s
    WHERE p.issue_date >= s.observation_start AND p.issue_date < date_trunc('month', s.as_of)
    GROUP BY 1, 2
), leads AS (
    SELECT date_trunc('month', l.lead_date)::date AS period_start, l.agent_id,
           COUNT(*) AS leads_created,
           COUNT(*) FILTER (WHERE l.converted AND l.conversion_date <= s.as_of) AS converted_leads
    FROM insurance_analytics.leads l CROSS JOIN agency_performance.snapshot s
    WHERE l.lead_date >= s.observation_start AND l.lead_date < date_trunc('month', s.as_of)
    GROUP BY 1, 2
), base AS (
    SELECT m.period_start, m.period_end, u.region, u.agency_unit_id, u.agency_name,
           a.agent_id, a.agent_grade, a.join_date, a.exit_date,
           CASE WHEN a.join_date > m.period_start - INTERVAL '6 months' THEN '0-<6 months'
                WHEN a.join_date > m.period_start - INTERVAL '12 months' THEN '6-<12 months'
                WHEN a.join_date > m.period_start - INTERVAL '24 months' THEN '12-<24 months'
                ELSE '24+ months' END AS tenure_band,
           COALESCE(p.new_policies, 0) AS new_policies,
           COALESCE(p.new_business_annualized_premium, 0) AS new_business_annualized_premium,
           t.policy_target, t.premium_target,
           COALESCE(l.leads_created, 0) AS leads_created,
           COALESCE(l.converted_leads, 0) AS converted_leads
    FROM agency_performance.periods m
    JOIN insurance_analytics.agents a ON a.join_date < m.period_end
        AND (a.exit_date IS NULL OR a.exit_date >= m.period_start)
    JOIN insurance_analytics.agency_units u USING (agency_unit_id)
    LEFT JOIN production p ON p.agent_id = a.agent_id AND p.period_start = m.period_start
    LEFT JOIN leads l ON l.agent_id = a.agent_id AND l.period_start = m.period_start
    LEFT JOIN insurance_analytics.sales_targets t
        ON t.agent_id = a.agent_id AND t.target_month = m.period_start
), ratios AS (
    SELECT *, new_policies::numeric / NULLIF(policy_target, 0) AS policy_target_achievement,
           new_business_annualized_premium / NULLIF(premium_target, 0) AS premium_target_achievement
    FROM base
)
SELECT *, 1 AS eligible_agents, (new_policies > 0)::int AS producing_agents,
       (new_policies > 0)::int AS producing_agent_ratio,
       new_policies::numeric / NULLIF((new_policies > 0)::int, 0) AS policies_per_producing_agent,
       new_business_annualized_premium / NULLIF(new_policies, 0) AS avg_annualized_premium_per_policy,
       converted_leads::numeric / NULLIF(leads_created, 0) AS lead_conversion,
       CASE WHEN policy_target IS NULL OR policy_target <= 0 THEN 'Missing/Invalid Target'
            WHEN new_policies = 0 THEN 'Non-Producing'
            WHEN policy_target_achievement < 0.8 THEN 'Under Target'
            WHEN policy_target_achievement < 1 THEN 'Near Target'
            WHEN policy_target_achievement < 1.2 THEN 'Target Achiever'
            ELSE 'High Achiever' END AS policy_target_band,
       CASE WHEN premium_target IS NULL OR premium_target <= 0 THEN 'Missing/Invalid Target'
            WHEN new_policies = 0 THEN 'Non-Producing'
            WHEN premium_target_achievement < 0.8 THEN 'Under Target'
            WHEN premium_target_achievement < 1 THEN 'Near Target'
            WHEN premium_target_achievement < 1.2 THEN 'Target Achiever'
            ELSE 'High Achiever' END AS premium_target_band
FROM ratios;

-- Zero-agent units remain visible. Ratios always use summed numerators/denominators.
CREATE OR REPLACE VIEW agency_performance.performance AS
WITH totals AS (
    SELECT m.period_start, u.region, u.agency_unit_id, u.agency_name,
           a.agent_grade, a.tenure_band,
           CASE WHEN GROUPING(u.region, u.agency_unit_id, a.agent_grade, a.tenure_band) = 15
                    THEN 'Agency'
                WHEN GROUPING(u.agency_unit_id, a.agent_grade, a.tenure_band) = 7 THEN 'Region'
                WHEN GROUPING(a.agent_grade) = 0 THEN 'Grade'
                WHEN GROUPING(a.tenure_band) = 0 THEN 'Tenure'
                ELSE 'Unit' END AS grain,
           COUNT(DISTINCT a.agent_id) AS eligible_agents,
           COUNT(DISTINCT a.agent_id) FILTER (WHERE a.new_policies > 0) AS producing_agents,
           COALESCE(SUM(a.new_policies), 0) AS new_policies,
           COALESCE(SUM(a.new_business_annualized_premium), 0) AS new_business_annualized_premium,
           SUM(a.policy_target) FILTER (WHERE a.policy_target > 0) AS policy_target,
           SUM(a.premium_target) FILTER (WHERE a.premium_target > 0) AS premium_target,
           COUNT(a.agent_id) FILTER (WHERE a.policy_target > 0) AS agents_with_policy_target,
           COUNT(a.agent_id) FILTER (WHERE a.premium_target > 0) AS agents_with_premium_target,
           COUNT(a.agent_id) FILTER (WHERE a.policy_target_achievement >= 1) AS policy_target_achievers,
           COUNT(a.agent_id) FILTER (WHERE a.premium_target_achievement >= 1) AS premium_target_achievers,
           COALESCE(SUM(a.leads_created), 0) AS leads_created,
           COALESCE(SUM(a.converted_leads), 0) AS converted_leads
    FROM agency_performance.periods m CROSS JOIN insurance_analytics.agency_units u
    LEFT JOIN agency_performance.agent_month a
        ON a.period_start = m.period_start AND a.agency_unit_id = u.agency_unit_id
    GROUP BY GROUPING SETS ((m.period_start), (m.period_start, u.region),
        (m.period_start, u.region, u.agency_unit_id, u.agency_name),
        (m.period_start, a.agent_grade), (m.period_start, a.tenure_band))
)
SELECT *, producing_agents::numeric / NULLIF(eligible_agents, 0) AS producing_agent_ratio,
       new_policies / NULLIF(producing_agents, 0) AS policies_per_producing_agent,
       new_business_annualized_premium / NULLIF(new_policies, 0) AS avg_annualized_premium_per_policy,
       new_policies / NULLIF(policy_target, 0) AS policy_target_achievement,
       new_business_annualized_premium / NULLIF(premium_target, 0) AS premium_target_achievement,
       converted_leads::numeric / NULLIF(leads_created, 0) AS lead_conversion
FROM totals WHERE grain IN ('Agency', 'Region', 'Unit') OR eligible_agents > 0;

CREATE OR REPLACE VIEW agency_performance.monthly_trends AS
WITH previous AS (
    SELECT *, LAG(new_policies) OVER (ORDER BY period_start) AS previous_new_policies,
           LAG(new_business_annualized_premium) OVER (ORDER BY period_start) AS previous_premium
    FROM agency_performance.performance WHERE grain = 'Agency'
)
SELECT *, (new_policies - previous_new_policies) / NULLIF(previous_new_policies, 0) AS policy_mom_growth,
       (new_business_annualized_premium - previous_premium) / NULLIF(previous_premium, 0) AS premium_mom_growth
FROM previous;

CREATE OR REPLACE VIEW agency_performance.target_distribution AS
SELECT period_start, 'Policy' AS target_type, policy_target_band AS target_band, COUNT(*) AS agents
FROM agency_performance.agent_month GROUP BY 1, 3
UNION ALL
SELECT period_start, 'Premium', premium_target_band, COUNT(*)
FROM agency_performance.agent_month GROUP BY 1, 3;

-- Recorded stage evidence, not fabricated transition history. Counts need not nest.
CREATE OR REPLACE VIEW agency_performance.lead_funnel AS
WITH cohorts AS (
    SELECT m.period_start, COUNT(l.lead_id) AS leads_created,
           COUNT(l.lead_id) FILTER (WHERE l.contact_status = 'Contacted') AS contacted,
           COUNT(l.lead_id) FILTER (WHERE l.appointment_status IN ('Booked', 'Completed', 'No Show')) AS booked,
           COUNT(l.lead_id) FILTER (WHERE l.appointment_status = 'Completed') AS completed,
           COUNT(l.lead_id) FILTER (WHERE l.application_status IN ('Submitted', 'Approved', 'Declined', 'Withdrawn')) AS submitted,
           COUNT(l.lead_id) FILTER (WHERE l.application_status = 'Approved') AS approved,
           COUNT(l.lead_id) FILTER (WHERE l.converted AND l.conversion_date <= s.as_of) AS converted
    FROM agency_performance.periods m CROSS JOIN agency_performance.snapshot s
    LEFT JOIN insurance_analytics.leads l ON l.lead_date >= m.period_start AND l.lead_date < m.period_end
    GROUP BY 1
)
SELECT period_start, stage_order, stage, leads, leads_created,
       leads::numeric / NULLIF(leads_created, 0) AS share_of_cohort
FROM cohorts CROSS JOIN LATERAL (VALUES
    (1, 'Lead', leads_created), (2, 'Contacted', contacted),
    (3, 'Appointment Booked', booked), (4, 'Appointment Completed', completed),
    (5, 'Application Submitted', submitted), (6, 'Application Approved', approved),
    (7, 'Converted', converted)) AS stages(stage_order, stage, leads);

CREATE OR REPLACE VIEW agency_performance.agent_activation AS
WITH first_policy AS (
    SELECT p.agent_id, MIN(p.issue_date) AS first_observed_policy_date
    FROM insurance_analytics.policies p CROSS JOIN agency_performance.snapshot s
    WHERE p.issue_date >= s.observation_start AND p.issue_date <= s.as_of GROUP BY p.agent_id
), base AS (
    SELECT a.agent_id, a.agency_unit_id, u.region, a.join_date, a.exit_date,
           date_trunc('month', a.join_date)::date AS recruitment_month,
           f.first_observed_policy_date, a.join_date >= s.observation_start AS history_observed,
           a.join_date + 30 <= s.as_of + 1 AS window_mature,
           a.exit_date IS NULL OR a.exit_date >= a.join_date + 29 AS full_service_window
    FROM insurance_analytics.agents a JOIN insurance_analytics.agency_units u USING (agency_unit_id)
    CROSS JOIN agency_performance.snapshot s LEFT JOIN first_policy f USING (agent_id)
    WHERE a.join_date <= s.as_of
)
SELECT *, CASE WHEN history_observed THEN first_observed_policy_date - join_date END AS days_to_first_policy,
       history_observed AND window_mature AND full_service_window AS first_30_day_eligible,
       CASE WHEN history_observed AND window_mature AND full_service_window
            THEN COALESCE(first_observed_policy_date < join_date + 30, FALSE)
       END AS activated_first_30_days
FROM base;

CREATE OR REPLACE VIEW agency_performance.activation_cohorts AS
SELECT recruitment_month, COUNT(*) AS recruits,
       COUNT(*) FILTER (WHERE NOT history_observed) AS left_censored_agents,
       COUNT(*) FILTER (WHERE NOT window_mature) AS immature_agents,
       COUNT(*) FILTER (WHERE NOT full_service_window) AS early_exit_agents,
       COUNT(*) FILTER (WHERE first_30_day_eligible) AS first_30_day_eligible_agents,
       COUNT(*) FILTER (WHERE activated_first_30_days) AS activated_first_30_day_agents,
       COUNT(*) FILTER (WHERE activated_first_30_days)::numeric /
           NULLIF(COUNT(*) FILTER (WHERE first_30_day_eligible), 0) AS first_30_day_activation_ratio,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY days_to_first_policy)
           FILTER (WHERE history_observed) AS median_observed_days_to_first_policy
FROM agency_performance.agent_activation GROUP BY recruitment_month;

CREATE OR REPLACE VIEW agency_performance.activation_summary AS
SELECT COUNT(*) AS recruits,
       COUNT(*) FILTER (WHERE NOT history_observed) AS left_censored_agents,
       COUNT(*) FILTER (WHERE NOT window_mature) AS immature_agents,
       COUNT(*) FILTER (WHERE NOT full_service_window) AS early_exit_agents,
       COUNT(*) FILTER (WHERE first_30_day_eligible) AS first_30_day_eligible_agents,
       COUNT(*) FILTER (WHERE activated_first_30_days) AS activated_first_30_day_agents,
       COUNT(*) FILTER (WHERE activated_first_30_days)::numeric /
           NULLIF(COUNT(*) FILTER (WHERE first_30_day_eligible), 0) AS first_30_day_activation_ratio,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY days_to_first_policy)
           FILTER (WHERE history_observed) AS median_observed_days_to_first_policy
FROM agency_performance.agent_activation;

-- Rank independently by policies and premium; ceil retains at least one producer.
CREATE OR REPLACE VIEW agency_performance.concentration AS
WITH ranks AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY period_start ORDER BY new_policies DESC, agent_id) AS policy_rank,
           ROW_NUMBER() OVER (PARTITION BY period_start ORDER BY new_business_annualized_premium DESC, agent_id) AS premium_rank,
           CEIL(COUNT(*) OVER (PARTITION BY period_start) * 0.1) AS top_agent_count
    FROM agency_performance.agent_month WHERE new_policies > 0
)
SELECT m.period_start, COALESCE(MAX(r.top_agent_count), 0)::int AS top_agent_count,
       COUNT(r.agent_id) AS producing_agents,
       SUM(r.new_policies) FILTER (WHERE policy_rank <= top_agent_count)::numeric /
           NULLIF(SUM(r.new_policies), 0) AS top_policy_share,
       SUM(r.new_business_annualized_premium) FILTER (WHERE premium_rank <= top_agent_count) /
           NULLIF(SUM(r.new_business_annualized_premium), 0) AS top_premium_share
FROM agency_performance.periods m LEFT JOIN ranks r USING (period_start) GROUP BY m.period_start;

-- Executable scorecard; all other outputs are named reusable views above.
SELECT * FROM agency_performance.monthly_trends
WHERE period_start = (SELECT MAX(period_start) FROM agency_performance.periods);
