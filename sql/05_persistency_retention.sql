-- Phase 4 persistency and retention metric layer.
-- Install atomically with psql --single-transaction after the nine source tables.
CREATE SCHEMA IF NOT EXISTS persistency_analytics;

CREATE OR REPLACE VIEW persistency_analytics.snapshot AS
SELECT DATE '2026-09-01' AS as_of;

-- Exactly one row per policy and required milestone, including immature rows.
CREATE OR REPLACE VIEW persistency_analytics.policy_milestones AS
SELECT p.policy_id, m.milestone_months,
       (p.issue_date + make_interval(months => m.milestone_months))::date AS anniversary_date,
       (p.issue_date + make_interval(months => m.milestone_months))::date <= s.as_of
           AS milestone_eligible,
       CASE
           WHEN (p.issue_date + make_interval(months => m.milestone_months))::date <= s.as_of
           THEN COALESCE(h.status, 'Active')
       END AS status_at_anniversary
FROM insurance_analytics.policies p
CROSS JOIN persistency_analytics.snapshot s
CROSS JOIN (VALUES (3), (6), (13)) AS m(milestone_months)
LEFT JOIN LATERAL (
    SELECT e.status
    FROM insurance_analytics.policy_status_history e
    WHERE e.policy_id = p.policy_id
      AND e.status_date <=
          (p.issue_date + make_interval(months => m.milestone_months))::date
    ORDER BY e.status_date DESC, e.status_history_id DESC
    LIMIT 1
) h ON TRUE;

-- Trusted analytical base: one row per policy/milestone, never joined to payments.
CREATE OR REPLACE VIEW persistency_analytics.policy_persistency AS
SELECT pm.policy_id, pm.milestone_months, pm.anniversary_date,
       pm.milestone_eligible, pm.status_at_anniversary,
       pm.milestone_eligible AND pm.status_at_anniversary <> 'Matured'
           AS denominator_eligible,
       CASE
           WHEN NOT pm.milestone_eligible OR pm.status_at_anniversary = 'Matured' THEN NULL
           ELSE pm.status_at_anniversary IN ('Active', 'Grace', 'Reinstated')
       END AS persistent_flag,
       p.issue_date, date_trunc('month', p.issue_date)::date AS issue_month,
       p.annualized_premium, p.product_name, p.payment_frequency,
       p.agent_id, a.agency_unit_id, u.agency_name, u.region,
       p.customer_id, c.income_band, c.acquisition_channel,
       c.region AS customer_region,
       EXTRACT(YEAR FROM age(p.issue_date, c.date_of_birth))::int AS age_at_issue,
       CASE
           WHEN EXTRACT(YEAR FROM age(p.issue_date, c.date_of_birth)) < 25 THEN '<25'
           WHEN EXTRACT(YEAR FROM age(p.issue_date, c.date_of_birth)) < 35 THEN '25-34'
           WHEN EXTRACT(YEAR FROM age(p.issue_date, c.date_of_birth)) < 45 THEN '35-44'
           WHEN EXTRACT(YEAR FROM age(p.issue_date, c.date_of_birth)) < 55 THEN '45-54'
           ELSE '55+'
       END AS age_at_issue_band
FROM persistency_analytics.policy_milestones pm
JOIN insurance_analytics.policies p USING (policy_id)
JOIN insurance_analytics.agents a USING (agent_id)
JOIN insurance_analytics.agency_units u USING (agency_unit_id)
JOIN insurance_analytics.customers c USING (customer_id);

-- Additive facts provide a single safe source for every summary ratio.
CREATE OR REPLACE VIEW persistency_analytics.persistency_facts AS
SELECT pp.*,
       1::bigint AS policies_issued,
       pp.milestone_eligible::int::bigint AS milestone_eligible_policies,
       pp.denominator_eligible::int::bigint AS eligible_policies,
       COALESCE(pp.persistent_flag, FALSE)::int::bigint AS persistent_policies,
       CASE WHEN pp.denominator_eligible THEN pp.annualized_premium ELSE 0 END
           AS eligible_annualized_premium,
       CASE WHEN pp.persistent_flag THEN pp.annualized_premium ELSE 0 END
           AS persistent_annualized_premium,
       (pp.milestone_eligible AND pp.status_at_anniversary = 'Lapsed')::int::bigint
           AS lapsed_count,
       (pp.milestone_eligible AND pp.status_at_anniversary = 'Surrendered')::int::bigint
           AS surrendered_count,
       (pp.milestone_eligible AND pp.status_at_anniversary = 'Cancelled')::int::bigint
           AS cancelled_count,
       (pp.milestone_eligible AND pp.status_at_anniversary = 'Matured')::int::bigint
           AS matured_count
FROM persistency_analytics.policy_persistency pp;

CREATE OR REPLACE VIEW persistency_analytics.overall_persistency AS
SELECT milestone_months,
       SUM(policies_issued)::bigint AS policies_issued,
       SUM(milestone_eligible_policies)::bigint AS milestone_eligible_policies,
       SUM(eligible_policies)::bigint AS eligible_policies,
       SUM(persistent_policies)::bigint AS persistent_policies,
       SUM(eligible_annualized_premium) AS eligible_annualized_premium,
       SUM(persistent_annualized_premium) AS persistent_annualized_premium,
       SUM(persistent_policies)::numeric / NULLIF(SUM(eligible_policies), 0)
           AS count_persistency,
       SUM(persistent_annualized_premium) / NULLIF(SUM(eligible_annualized_premium), 0)
           AS premium_persistency,
       SUM(lapsed_count)::bigint AS lapsed_count,
       SUM(surrendered_count)::bigint AS surrendered_count,
       SUM(cancelled_count)::bigint AS cancelled_count,
       SUM(matured_count)::bigint AS matured_count
FROM persistency_analytics.persistency_facts
GROUP BY milestone_months;

CREATE OR REPLACE VIEW persistency_analytics.cohort_persistency AS
SELECT issue_month, milestone_months,
       SUM(policies_issued)::bigint AS policies_issued,
       SUM(milestone_eligible_policies)::bigint AS milestone_eligible_policies,
       SUM(eligible_policies)::bigint AS eligible_policies,
       SUM(persistent_policies)::bigint AS persistent_policies,
       SUM(eligible_annualized_premium) AS eligible_annualized_premium,
       SUM(persistent_annualized_premium) AS persistent_annualized_premium,
       SUM(persistent_policies)::numeric / NULLIF(SUM(eligible_policies), 0)
           AS count_persistency,
       SUM(persistent_annualized_premium) / NULLIF(SUM(eligible_annualized_premium), 0)
           AS premium_persistency,
       SUM(lapsed_count)::bigint AS lapsed_count,
       SUM(surrendered_count)::bigint AS surrendered_count,
       SUM(cancelled_count)::bigint AS cancelled_count,
       SUM(matured_count)::bigint AS matured_count
FROM persistency_analytics.persistency_facts
GROUP BY issue_month, milestone_months;

-- Agency, Region, Unit and Agent share identical components and definitions.
CREATE OR REPLACE VIEW persistency_analytics.hierarchy_persistency AS
WITH totals AS (
    SELECT CASE
               WHEN GROUPING(agent_id) = 0 THEN 'Agent'
               WHEN GROUPING(agency_unit_id) = 0 THEN 'Unit'
               WHEN GROUPING(region) = 0 THEN 'Region'
               ELSE 'Agency'
           END AS grain,
           region, agency_unit_id, agency_name, agent_id, milestone_months,
           SUM(eligible_policies)::bigint AS eligible_policies,
           SUM(persistent_policies)::bigint AS persistent_policies,
           SUM(eligible_annualized_premium) AS eligible_annualized_premium,
           SUM(persistent_annualized_premium) AS persistent_annualized_premium,
           SUM(lapsed_count)::bigint AS lapsed_count,
           SUM(surrendered_count)::bigint AS surrendered_count,
           SUM(cancelled_count)::bigint AS cancelled_count,
           SUM(matured_count)::bigint AS matured_count
    FROM persistency_analytics.persistency_facts
    GROUP BY GROUPING SETS (
        (milestone_months),
        (region, milestone_months),
        (region, agency_unit_id, agency_name, milestone_months),
        (region, agency_unit_id, agency_name, agent_id, milestone_months)
    )
)
SELECT *, persistent_policies::numeric / NULLIF(eligible_policies, 0) AS count_persistency,
       persistent_annualized_premium / NULLIF(eligible_annualized_premium, 0)
           AS premium_persistency
FROM totals;

CREATE OR REPLACE VIEW persistency_analytics.agent_persistency AS
SELECT * FROM persistency_analytics.hierarchy_persistency WHERE grain = 'Agent';

CREATE OR REPLACE VIEW persistency_analytics.unit_persistency AS
SELECT * FROM persistency_analytics.hierarchy_persistency WHERE grain = 'Unit';

CREATE OR REPLACE VIEW persistency_analytics.region_persistency AS
SELECT * FROM persistency_analytics.hierarchy_persistency WHERE grain = 'Region';

CREATE OR REPLACE VIEW persistency_analytics.product_persistency AS
SELECT product_name, milestone_months,
       SUM(eligible_policies)::bigint AS eligible_policies,
       SUM(persistent_policies)::bigint AS persistent_policies,
       SUM(eligible_annualized_premium) AS eligible_annualized_premium,
       SUM(persistent_annualized_premium) AS persistent_annualized_premium,
       SUM(persistent_policies)::numeric / NULLIF(SUM(eligible_policies), 0)
           AS count_persistency,
       SUM(persistent_annualized_premium) / NULLIF(SUM(eligible_annualized_premium), 0)
           AS premium_persistency,
       SUM(lapsed_count)::bigint AS lapsed_count,
       SUM(surrendered_count)::bigint AS surrendered_count,
       SUM(cancelled_count)::bigint AS cancelled_count,
       SUM(matured_count)::bigint AS matured_count
FROM persistency_analytics.persistency_facts
GROUP BY product_name, milestone_months;

CREATE OR REPLACE VIEW persistency_analytics.payment_frequency_persistency AS
SELECT payment_frequency, milestone_months,
       SUM(eligible_policies)::bigint AS eligible_policies,
       SUM(persistent_policies)::bigint AS persistent_policies,
       SUM(eligible_annualized_premium) AS eligible_annualized_premium,
       SUM(persistent_annualized_premium) AS persistent_annualized_premium,
       SUM(persistent_policies)::numeric / NULLIF(SUM(eligible_policies), 0)
           AS count_persistency,
       SUM(persistent_annualized_premium) / NULLIF(SUM(eligible_annualized_premium), 0)
           AS premium_persistency,
       SUM(lapsed_count)::bigint AS lapsed_count,
       SUM(surrendered_count)::bigint AS surrendered_count,
       SUM(cancelled_count)::bigint AS cancelled_count,
       SUM(matured_count)::bigint AS matured_count
FROM persistency_analytics.persistency_facts
GROUP BY payment_frequency, milestone_months;

CREATE OR REPLACE VIEW persistency_analytics.customer_segment_persistency AS
WITH segments AS (
    SELECT f.*, s.segment_type, s.segment_value
    FROM persistency_analytics.persistency_facts f
    CROSS JOIN LATERAL (VALUES
        ('Income Band', COALESCE(f.income_band, 'Unknown')),
        ('Age at Issue', COALESCE(f.age_at_issue_band, 'Unknown')),
        ('Acquisition Channel', COALESCE(f.acquisition_channel, 'Unknown')),
        ('Customer Region', COALESCE(f.customer_region, 'Unknown'))
    ) AS s(segment_type, segment_value)
)
SELECT segment_type, segment_value, milestone_months,
       SUM(eligible_policies)::bigint AS eligible_policies,
       SUM(persistent_policies)::bigint AS persistent_policies,
       SUM(eligible_annualized_premium) AS eligible_annualized_premium,
       SUM(persistent_annualized_premium) AS persistent_annualized_premium,
       SUM(persistent_policies)::numeric / NULLIF(SUM(eligible_policies), 0)
           AS count_persistency,
       SUM(persistent_annualized_premium) / NULLIF(SUM(eligible_annualized_premium), 0)
           AS premium_persistency,
       SUM(lapsed_count)::bigint AS lapsed_count,
       SUM(surrendered_count)::bigint AS surrendered_count,
       SUM(cancelled_count)::bigint AS cancelled_count,
       SUM(matured_count)::bigint AS matured_count
FROM segments
GROUP BY segment_type, segment_value, milestone_months;

-- First recorded timing of each distinct adverse outcome; outcomes never merge.
CREATE OR REPLACE VIEW persistency_analytics.lapse_timing AS
WITH first_outcome AS (
    SELECT p.policy_id, p.issue_date, e.status AS outcome_status,
           MIN(e.status_date) AS outcome_date
    FROM insurance_analytics.policies p
    JOIN insurance_analytics.policy_status_history e USING (policy_id)
    CROSS JOIN persistency_analytics.snapshot s
    WHERE e.status IN ('Lapsed', 'Surrendered', 'Cancelled')
      AND e.status_date <= s.as_of
    GROUP BY p.policy_id, p.issue_date, e.status
), elapsed AS (
    SELECT *, outcome_date - issue_date AS days_to_outcome,
           (EXTRACT(YEAR FROM age(outcome_date, issue_date)) * 12
            + EXTRACT(MONTH FROM age(outcome_date, issue_date)))::int AS months_to_outcome
    FROM first_outcome
)
SELECT *, CASE
           WHEN outcome_date < issue_date + INTERVAL '3 months' THEN '0-<3 months'
           WHEN outcome_date < issue_date + INTERVAL '6 months' THEN '3-<6 months'
           WHEN outcome_date < issue_date + INTERVAL '13 months' THEN '6-<13 months'
           WHEN outcome_date < issue_date + INTERVAL '24 months' THEN '13-<24 months'
           ELSE '24+ months'
       END AS timing_band
FROM elapsed;

-- Aggregate installments before joining them to the policy/milestone grain.
CREATE OR REPLACE VIEW persistency_analytics.payment_behavior AS
WITH payment AS (
    SELECT pp.policy_id, pp.milestone_months,
           COUNT(pm.payment_id)::bigint AS installments_due,
           COUNT(pm.payment_id) FILTER (WHERE pm.payment_status = 'Paid')::bigint AS paid_count,
           COUNT(pm.payment_id) FILTER (WHERE pm.payment_status = 'Late')::bigint AS late_count,
           COUNT(pm.payment_id) FILTER (WHERE pm.payment_status = 'Missed')::bigint AS missed_count,
           COUNT(pm.payment_id) FILTER (WHERE pm.payment_status = 'Partial')::bigint AS partial_count,
           COALESCE(SUM(pm.amount_due), 0) AS amount_due,
           COALESCE(SUM(pm.amount_paid), 0) AS amount_paid
    FROM persistency_analytics.policy_persistency pp
    LEFT JOIN insurance_analytics.premium_payments pm
      ON pm.policy_id = pp.policy_id AND pm.due_date <= pp.anniversary_date
    WHERE pp.milestone_eligible
    GROUP BY pp.policy_id, pp.milestone_months
)
SELECT pp.policy_id, pp.milestone_months, pp.anniversary_date,
       pp.status_at_anniversary, pp.denominator_eligible, pp.persistent_flag,
       pp.annualized_premium, pp.payment_frequency,
       p.installments_due, p.paid_count, p.late_count, p.missed_count, p.partial_count,
       p.amount_due, p.amount_paid,
       p.amount_paid / NULLIF(p.amount_due, 0) AS payment_completion_rate,
       p.missed_count::numeric / NULLIF(p.installments_due, 0) AS missed_rate,
       p.late_count::numeric / NULLIF(p.installments_due, 0) AS late_rate,
       p.partial_count::numeric / NULLIF(p.installments_due, 0) AS partial_rate,
       p.paid_count::numeric / NULLIF(p.installments_due, 0) AS paid_rate
FROM persistency_analytics.policy_persistency pp
JOIN payment p USING (policy_id, milestone_months);

CREATE OR REPLACE VIEW persistency_analytics.payment_behavior_summary AS
WITH outcomes AS (
    SELECT *, CASE
        WHEN persistent_flag THEN 'Persistent'
        WHEN status_at_anniversary = 'Matured' THEN 'Matured'
        ELSE 'Non-persistent'
    END AS outcome_group
    FROM persistency_analytics.payment_behavior
)
SELECT milestone_months, outcome_group,
       COUNT(*)::bigint AS policies,
       SUM(installments_due)::bigint AS installments_due,
       SUM(paid_count)::bigint AS paid_count,
       SUM(late_count)::bigint AS late_count,
       SUM(missed_count)::bigint AS missed_count,
       SUM(partial_count)::bigint AS partial_count,
       SUM(amount_due) AS amount_due, SUM(amount_paid) AS amount_paid,
       SUM(amount_paid) / NULLIF(SUM(amount_due), 0) AS payment_completion_rate,
       SUM(missed_count)::numeric / NULLIF(SUM(installments_due), 0) AS missed_rate,
       SUM(late_count)::numeric / NULLIF(SUM(installments_due), 0) AS late_rate,
       SUM(partial_count)::numeric / NULLIF(SUM(installments_due), 0) AS partial_rate,
       SUM(paid_count)::numeric / NULLIF(SUM(installments_due), 0) AS paid_rate
FROM outcomes
GROUP BY milestone_months, outcome_group;

-- Executable six-KPI scorecard.
SELECT milestone_months, count_persistency, premium_persistency,
       eligible_policies, eligible_annualized_premium
FROM persistency_analytics.overall_persistency
ORDER BY milestone_months;
