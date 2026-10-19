-- Phase 6 leakage-safe historical lapse-risk feature layer.
-- This file builds the historical panel only; it does not train or score a model.
-- The schema contains generated analytical objects only and is rebuilt atomically.
DROP SCHEMA IF EXISTS lapse_risk CASCADE;
CREATE SCHEMA lapse_risk;

CREATE OR REPLACE VIEW lapse_risk.snapshot AS
SELECT DATE '2026-09-01' AS as_of;

-- Calendar month-ends from the first analytically useful portfolio month through
-- the final complete month before the fixed snapshot.
CREATE OR REPLACE VIEW lapse_risk.observation_dates AS
SELECT (month_start + INTERVAL '1 month - 1 day')::date AS observation_date
FROM lapse_risk.snapshot s
CROSS JOIN LATERAL generate_series(
    DATE '2023-02-01',
    date_trunc('month', s.as_of)::date - INTERVAL '1 month',
    INTERVAL '1 month'
) AS month_start;

-- One row per issued policy/month. Historical status comes only from event history.
CREATE MATERIALIZED VIEW lapse_risk.policy_status_asof AS
SELECT p.policy_id, d.observation_date, p.issue_date,
       d.observation_date - p.issue_date AS policy_age_days,
       h.status AS status_at_observation,
       h.status_date AS status_event_date,
       h.status_history_id AS status_history_id
FROM insurance_analytics.policies p
JOIN lapse_risk.observation_dates d ON d.observation_date >= p.issue_date
LEFT JOIN LATERAL (
    SELECT e.status, e.status_date, e.status_history_id
    FROM insurance_analytics.policy_status_history e
    WHERE e.policy_id = p.policy_id
      AND e.status_date <= d.observation_date
    ORDER BY e.status_date DESC, e.status_history_id DESC
    LIMIT 1
) h ON TRUE;

CREATE UNIQUE INDEX policy_status_asof_policy_observation_idx
    ON lapse_risk.policy_status_asof (policy_id, observation_date);
CREATE INDEX policy_status_asof_observation_idx
    ON lapse_risk.policy_status_asof (observation_date);

-- Keep immature rows visible with a NULL target so right-censoring is auditable.
CREATE MATERIALIZED VIEW lapse_risk.policy_observations AS
SELECT s.policy_id, s.observation_date, s.issue_date, s.policy_age_days,
       s.status_at_observation, s.status_event_date,
       s.policy_age_days >= 30
           AND s.status_at_observation IN ('Active', 'Grace', 'Reinstated')
           AS risk_set_eligible,
       s.observation_date + 90 <= snap.as_of AS label_eligible,
       next_lapse.first_lapse_date,
       CASE
           WHEN s.policy_age_days < 30
             OR s.status_at_observation NOT IN ('Active', 'Grace', 'Reinstated')
             OR s.status_at_observation IS NULL THEN NULL
           WHEN s.observation_date + 90 > snap.as_of THEN NULL
           ELSE COALESCE(
               next_lapse.first_lapse_date <= s.observation_date + 90,
               FALSE
           )::int
       END AS lapse_next_90d
FROM lapse_risk.policy_status_asof s
CROSS JOIN lapse_risk.snapshot snap
LEFT JOIN LATERAL (
    SELECT MIN(e.status_date) AS first_lapse_date
    FROM insurance_analytics.policy_status_history e
    WHERE e.policy_id = s.policy_id
      AND e.status = 'Lapsed'
      AND e.status_date > s.observation_date
) next_lapse ON TRUE;

CREATE UNIQUE INDEX policy_observations_policy_observation_idx
    ON lapse_risk.policy_observations (policy_id, observation_date);
CREATE INDEX policy_observations_observation_target_idx
    ON lapse_risk.policy_observations (observation_date, lapse_next_90d)
    WHERE risk_set_eligible AND label_eligible;

-- Reconstruct each installment exactly as it was observable at the observation date.
-- Stored final-snapshot payment_status is deliberately never referenced.
CREATE MATERIALIZED VIEW lapse_risk.payment_features AS
WITH classified AS (
    SELECT o.policy_id, o.observation_date, pm.payment_id, pm.due_date,
           CASE
               WHEN pm.payment_date <= o.observation_date THEN pm.payment_date
           END AS observable_payment_date,
           pm.amount_due,
           CASE
               WHEN pm.payment_date <= o.observation_date THEN pm.amount_paid
               ELSE 0::numeric
           END AS observable_amount_paid,
           CASE
               WHEN pm.payment_date IS NULL OR pm.payment_date > o.observation_date
                   THEN 'Missed'
               WHEN pm.amount_paid < pm.amount_due THEN 'Partial'
               WHEN pm.payment_date <= pm.due_date + 2 THEN 'Paid'
               ELSE 'Late'
           END AS observable_payment_state
    FROM lapse_risk.policy_observations o
    JOIN insurance_analytics.premium_payments pm
      ON pm.policy_id = o.policy_id
     AND pm.due_date <= o.observation_date
    WHERE o.risk_set_eligible
), aggregated AS (
    SELECT o.policy_id, o.observation_date,
           COUNT(c.payment_id)::bigint AS installments_due_to_date,
           COUNT(c.payment_id) FILTER (WHERE c.observable_payment_state = 'Paid')::bigint
               AS paid_count_to_date,
           COUNT(c.payment_id) FILTER (WHERE c.observable_payment_state = 'Late')::bigint
               AS late_count_to_date,
           COUNT(c.payment_id) FILTER (WHERE c.observable_payment_state = 'Missed')::bigint
               AS missed_count_to_date,
           COUNT(c.payment_id) FILTER (WHERE c.observable_payment_state = 'Partial')::bigint
               AS partial_count_to_date,
           COALESCE(SUM(c.amount_due), 0) AS amount_due_to_date,
           COALESCE(SUM(c.observable_amount_paid), 0) AS amount_paid_to_date,
           COUNT(c.payment_id) FILTER (
               WHERE c.due_date > o.observation_date - 90
           )::bigint AS installments_due_last_90d,
           COUNT(c.payment_id) FILTER (
               WHERE c.due_date > o.observation_date - 90
                 AND c.observable_payment_state = 'Paid'
           )::bigint AS paid_count_last_90d,
           COUNT(c.payment_id) FILTER (
               WHERE c.due_date > o.observation_date - 90
                 AND c.observable_payment_state = 'Late'
           )::bigint AS late_count_last_90d,
           COUNT(c.payment_id) FILTER (
               WHERE c.due_date > o.observation_date - 90
                 AND c.observable_payment_state = 'Missed'
           )::bigint AS missed_count_last_90d,
           COUNT(c.payment_id) FILTER (
               WHERE c.due_date > o.observation_date - 90
                 AND c.observable_payment_state = 'Partial'
           )::bigint AS partial_count_last_90d,
           COALESCE(SUM(c.amount_due) FILTER (
               WHERE c.due_date > o.observation_date - 90
           ), 0) AS amount_due_last_90d,
           COALESCE(SUM(c.observable_amount_paid) FILTER (
               WHERE c.due_date > o.observation_date - 90
           ), 0) AS amount_paid_last_90d,
           o.observation_date - MAX(c.observable_payment_date) AS days_since_last_payment,
           o.observation_date - MAX(c.observable_payment_date) FILTER (
               WHERE c.observable_payment_state = 'Late'
           ) AS days_since_last_late_payment,
           o.observation_date - MAX(c.due_date) FILTER (
               WHERE c.observable_payment_state = 'Missed'
           ) AS days_since_last_missed_installment
    FROM lapse_risk.policy_observations o
    LEFT JOIN classified c USING (policy_id, observation_date)
    WHERE o.risk_set_eligible
    GROUP BY o.policy_id, o.observation_date
)
SELECT a.*,
       a.paid_count_to_date::numeric / NULLIF(a.installments_due_to_date, 0)
           AS paid_rate_to_date,
       a.late_count_to_date::numeric / NULLIF(a.installments_due_to_date, 0)
           AS late_rate_to_date,
       a.missed_count_to_date::numeric / NULLIF(a.installments_due_to_date, 0)
           AS missed_rate_to_date,
       a.partial_count_to_date::numeric / NULLIF(a.installments_due_to_date, 0)
           AS partial_rate_to_date,
       a.amount_paid_to_date / NULLIF(a.amount_due_to_date, 0)
           AS payment_completion_rate_to_date,
       a.paid_count_last_90d::numeric / NULLIF(a.installments_due_last_90d, 0)
           AS paid_rate_last_90d,
       a.late_count_last_90d::numeric / NULLIF(a.installments_due_last_90d, 0)
           AS late_rate_last_90d,
       a.missed_count_last_90d::numeric / NULLIF(a.installments_due_last_90d, 0)
           AS missed_rate_last_90d,
       a.partial_count_last_90d::numeric / NULLIF(a.installments_due_last_90d, 0)
           AS partial_rate_last_90d,
       a.amount_paid_last_90d / NULLIF(a.amount_due_last_90d, 0)
           AS payment_completion_rate_last_90d
FROM aggregated a;

CREATE UNIQUE INDEX payment_features_policy_observation_idx
    ON lapse_risk.payment_features (policy_id, observation_date);

-- Trusted mature historical panel. Identity and diagnostic fields are carried for
-- traceability but are not authorized model predictors.
CREATE MATERIALIZED VIEW lapse_risk.model_dataset AS
SELECT o.policy_id, o.observation_date, o.lapse_next_90d,
       p.customer_id, p.agent_id, a.agency_unit_id,
       u.region, c.gender,
       p.product_name, p.payment_frequency, p.premium_amount,
       p.annualized_premium, p.sum_assured, p.policy_term_years,
       o.policy_age_days,
       (EXTRACT(YEAR FROM age(o.observation_date, p.issue_date)) * 12
        + EXTRACT(MONTH FROM age(o.observation_date, p.issue_date)))::int
           AS policy_age_months,
       o.status_at_observation,
       p.premium_amount / NULLIF(p.sum_assured, 0) AS premium_to_sum_assured,
       c.income_band, c.acquisition_channel, c.region AS customer_region,
       EXTRACT(YEAR FROM age(p.issue_date, c.date_of_birth))::int AS age_at_issue,
       CASE
           WHEN EXTRACT(YEAR FROM age(p.issue_date, c.date_of_birth)) < 25 THEN '<25'
           WHEN EXTRACT(YEAR FROM age(p.issue_date, c.date_of_birth)) < 35 THEN '25-34'
           WHEN EXTRACT(YEAR FROM age(p.issue_date, c.date_of_birth)) < 45 THEN '35-44'
           WHEN EXTRACT(YEAR FROM age(p.issue_date, c.date_of_birth)) < 55 THEN '45-54'
           ELSE '55+'
       END AS age_at_issue_band,
       pf.installments_due_to_date, pf.paid_count_to_date,
       pf.late_count_to_date, pf.missed_count_to_date, pf.partial_count_to_date,
       pf.paid_rate_to_date, pf.late_rate_to_date, pf.missed_rate_to_date,
       pf.partial_rate_to_date, pf.amount_due_to_date, pf.amount_paid_to_date,
       pf.payment_completion_rate_to_date,
       pf.installments_due_last_90d, pf.paid_count_last_90d,
       pf.late_count_last_90d, pf.missed_count_last_90d, pf.partial_count_last_90d,
       pf.paid_rate_last_90d, pf.late_rate_last_90d, pf.missed_rate_last_90d,
       pf.partial_rate_last_90d, pf.amount_due_last_90d, pf.amount_paid_last_90d,
       pf.payment_completion_rate_last_90d,
       pf.days_since_last_payment, pf.days_since_last_late_payment,
       pf.days_since_last_missed_installment
FROM lapse_risk.policy_observations o
JOIN insurance_analytics.policies p USING (policy_id)
JOIN insurance_analytics.customers c USING (customer_id)
JOIN insurance_analytics.agents a USING (agent_id)
JOIN insurance_analytics.agency_units u USING (agency_unit_id)
JOIN lapse_risk.payment_features pf USING (policy_id, observation_date)
WHERE o.risk_set_eligible AND o.label_eligible;

CREATE UNIQUE INDEX model_dataset_policy_observation_idx
    ON lapse_risk.model_dataset (policy_id, observation_date);
CREATE INDEX model_dataset_observation_target_idx
    ON lapse_risk.model_dataset (observation_date, lapse_next_90d);

-- Current operational population at the fixed snapshot. It deliberately has no target.
CREATE MATERIALIZED VIEW lapse_risk.current_policy_status AS
SELECT p.policy_id, s.as_of AS observation_date, p.issue_date,
       s.as_of - p.issue_date AS policy_age_days,
       h.status AS status_at_observation
FROM insurance_analytics.policies p
CROSS JOIN lapse_risk.snapshot s
LEFT JOIN LATERAL (
    SELECT e.status
    FROM insurance_analytics.policy_status_history e
    WHERE e.policy_id = p.policy_id
      AND e.status_date <= s.as_of
    ORDER BY e.status_date DESC, e.status_history_id DESC
    LIMIT 1
) h ON TRUE
WHERE s.as_of >= p.issue_date;

CREATE UNIQUE INDEX current_policy_status_policy_idx
    ON lapse_risk.current_policy_status (policy_id);

CREATE MATERIALIZED VIEW lapse_risk.current_payment_features AS
WITH classified AS (
    SELECT o.policy_id, o.observation_date, pm.payment_id, pm.due_date,
           CASE
               WHEN pm.payment_date <= o.observation_date THEN pm.payment_date
           END AS observable_payment_date,
           pm.amount_due,
           CASE
               WHEN pm.payment_date <= o.observation_date THEN pm.amount_paid
               ELSE 0::numeric
           END AS observable_amount_paid,
           CASE
               WHEN pm.payment_date IS NULL OR pm.payment_date > o.observation_date
                   THEN 'Missed'
               WHEN pm.amount_paid < pm.amount_due THEN 'Partial'
               WHEN pm.payment_date <= pm.due_date + 2 THEN 'Paid'
               ELSE 'Late'
           END AS observable_payment_state
    FROM lapse_risk.current_policy_status o
    JOIN insurance_analytics.premium_payments pm
      ON pm.policy_id = o.policy_id
     AND pm.due_date <= o.observation_date
    WHERE o.policy_age_days >= 30
      AND o.status_at_observation IN ('Active', 'Grace', 'Reinstated')
), aggregated AS (
    SELECT o.policy_id, o.observation_date,
           COUNT(c.payment_id)::bigint AS installments_due_to_date,
           COUNT(c.payment_id) FILTER (WHERE c.observable_payment_state = 'Paid')::bigint
               AS paid_count_to_date,
           COUNT(c.payment_id) FILTER (WHERE c.observable_payment_state = 'Late')::bigint
               AS late_count_to_date,
           COUNT(c.payment_id) FILTER (WHERE c.observable_payment_state = 'Missed')::bigint
               AS missed_count_to_date,
           COUNT(c.payment_id) FILTER (WHERE c.observable_payment_state = 'Partial')::bigint
               AS partial_count_to_date,
           COALESCE(SUM(c.amount_due), 0) AS amount_due_to_date,
           COALESCE(SUM(c.observable_amount_paid), 0) AS amount_paid_to_date,
           COUNT(c.payment_id) FILTER (
               WHERE c.due_date > o.observation_date - 90
           )::bigint AS installments_due_last_90d,
           COUNT(c.payment_id) FILTER (
               WHERE c.due_date > o.observation_date - 90
                 AND c.observable_payment_state = 'Paid'
           )::bigint AS paid_count_last_90d,
           COUNT(c.payment_id) FILTER (
               WHERE c.due_date > o.observation_date - 90
                 AND c.observable_payment_state = 'Late'
           )::bigint AS late_count_last_90d,
           COUNT(c.payment_id) FILTER (
               WHERE c.due_date > o.observation_date - 90
                 AND c.observable_payment_state = 'Missed'
           )::bigint AS missed_count_last_90d,
           COUNT(c.payment_id) FILTER (
               WHERE c.due_date > o.observation_date - 90
                 AND c.observable_payment_state = 'Partial'
           )::bigint AS partial_count_last_90d,
           COALESCE(SUM(c.amount_due) FILTER (
               WHERE c.due_date > o.observation_date - 90
           ), 0) AS amount_due_last_90d,
           COALESCE(SUM(c.observable_amount_paid) FILTER (
               WHERE c.due_date > o.observation_date - 90
           ), 0) AS amount_paid_last_90d,
           o.observation_date - MAX(c.observable_payment_date) AS days_since_last_payment,
           o.observation_date - MAX(c.observable_payment_date) FILTER (
               WHERE c.observable_payment_state = 'Late'
           ) AS days_since_last_late_payment,
           o.observation_date - MAX(c.due_date) FILTER (
               WHERE c.observable_payment_state = 'Missed'
           ) AS days_since_last_missed_installment
    FROM lapse_risk.current_policy_status o
    LEFT JOIN classified c USING (policy_id, observation_date)
    WHERE o.policy_age_days >= 30
      AND o.status_at_observation IN ('Active', 'Grace', 'Reinstated')
    GROUP BY o.policy_id, o.observation_date
)
SELECT a.*,
       a.paid_count_to_date::numeric / NULLIF(a.installments_due_to_date, 0)
           AS paid_rate_to_date,
       a.late_count_to_date::numeric / NULLIF(a.installments_due_to_date, 0)
           AS late_rate_to_date,
       a.missed_count_to_date::numeric / NULLIF(a.installments_due_to_date, 0)
           AS missed_rate_to_date,
       a.partial_count_to_date::numeric / NULLIF(a.installments_due_to_date, 0)
           AS partial_rate_to_date,
       a.amount_paid_to_date / NULLIF(a.amount_due_to_date, 0)
           AS payment_completion_rate_to_date,
       a.paid_count_last_90d::numeric / NULLIF(a.installments_due_last_90d, 0)
           AS paid_rate_last_90d,
       a.late_count_last_90d::numeric / NULLIF(a.installments_due_last_90d, 0)
           AS late_rate_last_90d,
       a.missed_count_last_90d::numeric / NULLIF(a.installments_due_last_90d, 0)
           AS missed_rate_last_90d,
       a.partial_count_last_90d::numeric / NULLIF(a.installments_due_last_90d, 0)
           AS partial_rate_last_90d,
       a.amount_paid_last_90d / NULLIF(a.amount_due_last_90d, 0)
           AS payment_completion_rate_last_90d
FROM aggregated a;

CREATE UNIQUE INDEX current_payment_features_policy_idx
    ON lapse_risk.current_payment_features (policy_id);

CREATE MATERIALIZED VIEW lapse_risk.current_scoring_population AS
SELECT o.policy_id, o.observation_date,
       p.customer_id, p.agent_id, a.agency_unit_id,
       u.region, c.gender,
       p.product_name, p.payment_frequency, p.premium_amount,
       p.annualized_premium, p.sum_assured, p.policy_term_years,
       o.policy_age_days,
       (EXTRACT(YEAR FROM age(o.observation_date, p.issue_date)) * 12
        + EXTRACT(MONTH FROM age(o.observation_date, p.issue_date)))::int
           AS policy_age_months,
       o.status_at_observation,
       p.premium_amount / NULLIF(p.sum_assured, 0) AS premium_to_sum_assured,
       c.income_band, c.acquisition_channel, c.region AS customer_region,
       EXTRACT(YEAR FROM age(p.issue_date, c.date_of_birth))::int AS age_at_issue,
       CASE
           WHEN EXTRACT(YEAR FROM age(p.issue_date, c.date_of_birth)) < 25 THEN '<25'
           WHEN EXTRACT(YEAR FROM age(p.issue_date, c.date_of_birth)) < 35 THEN '25-34'
           WHEN EXTRACT(YEAR FROM age(p.issue_date, c.date_of_birth)) < 45 THEN '35-44'
           WHEN EXTRACT(YEAR FROM age(p.issue_date, c.date_of_birth)) < 55 THEN '45-54'
           ELSE '55+'
       END AS age_at_issue_band,
       pf.installments_due_to_date, pf.paid_count_to_date,
       pf.late_count_to_date, pf.missed_count_to_date, pf.partial_count_to_date,
       pf.paid_rate_to_date, pf.late_rate_to_date, pf.missed_rate_to_date,
       pf.partial_rate_to_date, pf.amount_due_to_date, pf.amount_paid_to_date,
       pf.payment_completion_rate_to_date,
       pf.installments_due_last_90d, pf.paid_count_last_90d,
       pf.late_count_last_90d, pf.missed_count_last_90d, pf.partial_count_last_90d,
       pf.paid_rate_last_90d, pf.late_rate_last_90d, pf.missed_rate_last_90d,
       pf.partial_rate_last_90d, pf.amount_due_last_90d, pf.amount_paid_last_90d,
       pf.payment_completion_rate_last_90d,
       pf.days_since_last_payment, pf.days_since_last_late_payment,
       pf.days_since_last_missed_installment
FROM lapse_risk.current_policy_status o
JOIN insurance_analytics.policies p USING (policy_id)
JOIN insurance_analytics.customers c USING (customer_id)
JOIN insurance_analytics.agents a USING (agent_id)
JOIN insurance_analytics.agency_units u USING (agency_unit_id)
JOIN lapse_risk.current_payment_features pf USING (policy_id, observation_date)
WHERE o.policy_age_days >= 30
  AND o.status_at_observation IN ('Active', 'Grace', 'Reinstated');

CREATE UNIQUE INDEX current_scoring_population_policy_idx
    ON lapse_risk.current_scoring_population (policy_id);

CREATE OR REPLACE VIEW lapse_risk.monthly_target_distribution AS
SELECT observation_date,
       COUNT(*)::bigint AS observations,
       SUM(lapse_next_90d)::bigint AS positives,
       AVG(lapse_next_90d::numeric) AS positive_rate
FROM lapse_risk.model_dataset
GROUP BY observation_date
ORDER BY observation_date;

CREATE OR REPLACE VIEW lapse_risk.proposed_split_profile AS
WITH assigned AS (
    SELECT *, CASE
        WHEN observation_date <= DATE '2025-12-31' THEN 'train'
        WHEN observation_date BETWEEN DATE '2026-01-31' AND DATE '2026-03-31'
            THEN 'validation'
        WHEN observation_date BETWEEN DATE '2026-04-30' AND DATE '2026-05-31'
            THEN 'test'
    END AS split
    FROM lapse_risk.model_dataset
)
SELECT split, MIN(observation_date) AS first_observation_date,
       MAX(observation_date) AS last_observation_date,
       COUNT(*)::bigint AS observations,
       SUM(lapse_next_90d)::bigint AS positives,
       AVG(lapse_next_90d::numeric) AS positive_rate
FROM assigned
WHERE split IS NOT NULL
GROUP BY split;

-- Installation ends with the first-checkpoint evidence, never model training.
SELECT * FROM lapse_risk.monthly_target_distribution;
SELECT * FROM lapse_risk.proposed_split_profile ORDER BY first_observation_date;
