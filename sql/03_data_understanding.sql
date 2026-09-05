-- Phase 2: describe the validated synthetic snapshot; do not infer performance.
-- Run with psql -X -v ON_ERROR_STOP=1 -f sql/03_data_understanding.sql.
BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL search_path TO insurance_analytics;

-- Coverage by grain. Counts are not additive business measures across tables.
SELECT 'agency_units' AS dataset, 'one agency unit' AS grain, COUNT(*) AS rows FROM agency_units
UNION ALL SELECT 'customers', 'one customer', COUNT(*) FROM customers
UNION ALL SELECT 'agents', 'one agent', COUNT(*) FROM agents
UNION ALL SELECT 'leads', 'one lead', COUNT(*) FROM leads
UNION ALL SELECT 'policies', 'one policy', COUNT(*) FROM policies
UNION ALL SELECT 'premium_payments', 'one scheduled installment', COUNT(*) FROM premium_payments
UNION ALL SELECT 'policy_status_history', 'one lifecycle event', COUNT(*) FROM policy_status_history
UNION ALL SELECT 'sales_targets', 'one agent/month', COUNT(*) FROM sales_targets
UNION ALL SELECT 'incentives', 'one agent/campaign', COUNT(*) FROM incentives
ORDER BY dataset;

-- Coverage windows determine eligible reporting periods; maturity is contractual/future.
SELECT 'policy issue' AS event, MIN(issue_date) AS first_date, MAX(issue_date) AS last_date FROM policies
UNION ALL SELECT 'lead created', MIN(lead_date), MAX(lead_date) FROM leads
UNION ALL SELECT 'installment due', MIN(due_date), MAX(due_date) FROM premium_payments
UNION ALL SELECT 'cash received', MIN(payment_date), MAX(payment_date) FROM premium_payments
UNION ALL SELECT 'status event', MIN(status_date), MAX(status_date) FROM policy_status_history
UNION ALL SELECT 'target month', MIN(target_month), MAX(target_month) FROM sales_targets;

-- Current status mix is not a cohort persistency calculation.
SELECT policy_status, COUNT(*) AS policies
FROM policies GROUP BY policy_status ORDER BY policy_status;

-- Annualized premium is a normalized contract value, not collected cash or revenue.
SELECT product_name, payment_frequency, COUNT(*) AS policies,
       MIN(premium_amount) AS min_installment_ugx,
       MAX(premium_amount) AS max_installment_ugx,
       SUM(annualized_premium) AS annualized_premium_ugx
FROM policies GROUP BY product_name, payment_frequency ORDER BY product_name, payment_frequency;

-- Profile cash separately to avoid multiplying policy values through installment joins.
SELECT payment_status, COUNT(*) AS installments,
       SUM(amount_due) AS due_ugx, SUM(amount_paid) AS paid_ugx,
       COUNT(*) FILTER (WHERE payment_date IS NULL) AS no_payment_date
FROM premium_payments GROUP BY payment_status ORDER BY payment_status;

-- Nullable fields can have legitimate meanings, not automatic quality failures.
SELECT COUNT(*) FILTER (WHERE customer_id IS NULL) AS leads_without_customer,
       COUNT(*) FILTER (WHERE NOT converted AND conversion_date IS NULL) AS unconverted_without_date,
       COUNT(*) FILTER (WHERE converted AND customer_id IS NULL) AS invalid_converted_customer,
       COUNT(*) FILTER (WHERE converted AND conversion_date IS NULL) AS invalid_converted_date
FROM leads;

-- Unit coverage includes units without agents. Current assignment is not transfer history.
SELECT u.agency_unit_id, u.agency_name, u.region, COUNT(a.agent_id) AS registered_agents
FROM agency_units u LEFT JOIN agents a USING (agency_unit_id)
GROUP BY u.agency_unit_id, u.agency_name, u.region ORDER BY u.agency_unit_id;

-- Snapshot is fixed by the generator, never by CURRENT_DATE.
WITH snapshot AS (SELECT DATE '2026-09-01' AS as_of)
SELECT t.target_month, COUNT(*) AS agent_targets,
       t.target_month + INTERVAL '1 month' - INTERVAL '1 day' <= s.as_of AS complete_month
FROM sales_targets t CROSS JOIN snapshot s
GROUP BY t.target_month, s.as_of ORDER BY t.target_month;

-- Inventory only: qualification is simulated, so this is not incentive effectiveness.
SELECT campaign_name, MIN(start_date) AS starts, MAX(end_date) AS ends,
       COUNT(*) AS participants, COUNT(*) FILTER (WHERE qualified) AS simulated_qualifiers
FROM incentives GROUP BY campaign_name ORDER BY starts, campaign_name;
COMMIT;
