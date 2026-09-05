-- Diagnostic queries: every anomaly query should return zero rows.
SET search_path TO insurance_analytics;

-- 1. All nine primary keys (PostgreSQL also enforces these).
SELECT agency_unit_id, COUNT(*) FROM agency_units GROUP BY agency_unit_id HAVING COUNT(*) > 1;
SELECT customer_id, COUNT(*) FROM customers GROUP BY customer_id HAVING COUNT(*) > 1;
SELECT agent_id, COUNT(*) FROM agents GROUP BY agent_id HAVING COUNT(*) > 1;
SELECT lead_id, COUNT(*) FROM leads GROUP BY lead_id HAVING COUNT(*) > 1;
SELECT policy_id, COUNT(*) FROM policies GROUP BY policy_id HAVING COUNT(*) > 1;
SELECT payment_id, COUNT(*) FROM premium_payments GROUP BY payment_id HAVING COUNT(*) > 1;
SELECT status_history_id, COUNT(*) FROM policy_status_history GROUP BY status_history_id HAVING COUNT(*) > 1;
SELECT target_id, COUNT(*) FROM sales_targets GROUP BY target_id HAVING COUNT(*) > 1;
SELECT incentive_id, COUNT(*) FROM incentives GROUP BY incentive_id HAVING COUNT(*) > 1;

-- 2. Every declared foreign key; nullable lead customer references are allowed.
SELECT child.agent_id
FROM agents child LEFT JOIN agency_units parent ON child.agency_unit_id = parent.agency_unit_id
WHERE child.agency_unit_id IS NOT NULL AND parent.agency_unit_id IS NULL;
SELECT child.lead_id
FROM leads child LEFT JOIN agents parent ON child.agent_id = parent.agent_id
WHERE child.agent_id IS NOT NULL AND parent.agent_id IS NULL;
SELECT child.lead_id
FROM leads child LEFT JOIN customers parent ON child.customer_id = parent.customer_id
WHERE child.customer_id IS NOT NULL AND parent.customer_id IS NULL;
SELECT child.policy_id
FROM policies child LEFT JOIN customers parent ON child.customer_id = parent.customer_id
WHERE child.customer_id IS NOT NULL AND parent.customer_id IS NULL;
SELECT child.policy_id
FROM policies child LEFT JOIN agents parent ON child.agent_id = parent.agent_id
WHERE child.agent_id IS NOT NULL AND parent.agent_id IS NULL;
SELECT child.payment_id
FROM premium_payments child LEFT JOIN policies parent ON child.policy_id = parent.policy_id
WHERE child.policy_id IS NOT NULL AND parent.policy_id IS NULL;
SELECT child.status_history_id
FROM policy_status_history child LEFT JOIN policies parent ON child.policy_id = parent.policy_id
WHERE child.policy_id IS NOT NULL AND parent.policy_id IS NULL;
SELECT child.target_id
FROM sales_targets child LEFT JOIN agents parent ON child.agent_id = parent.agent_id
WHERE child.agent_id IS NOT NULL AND parent.agent_id IS NULL;
SELECT child.incentive_id
FROM incentives child LEFT JOIN agents parent ON child.agent_id = parent.agent_id
WHERE child.agent_id IS NOT NULL AND parent.agent_id IS NULL;

-- 3. Impossible policy dates
SELECT *
FROM policies
WHERE maturity_date <= issue_date
   OR (lapse_date IS NOT NULL AND lapse_date < issue_date)
   OR (surrender_date IS NOT NULL AND surrender_date < issue_date);

-- 4. Premium checks
SELECT *
FROM policies
WHERE premium_amount <= 0
   OR annualized_premium <= 0
   OR sum_assured <= 0;

-- 5. Annualization consistency
SELECT *
FROM policies
WHERE ABS(
   annualized_premium -
      premium_amount * CASE payment_frequency
         WHEN 'Monthly' THEN 12
         WHEN 'Quarterly' THEN 4
         WHEN 'Semi-Annual' THEN 2
         WHEN 'Annual' THEN 1
      END
) > 0.01;

-- 6. Payment anomalies
SELECT *
FROM premium_payments
WHERE payment_date IS NOT NULL AND payment_date < due_date - INTERVAL '60 days';

SELECT *
FROM premium_payments
WHERE payment_status = 'Missed' AND amount_paid > 0;

-- 7. Policy status/date consistency
SELECT *
FROM policies
WHERE (policy_status = 'Lapsed' AND lapse_date IS NULL)
   OR (policy_status = 'Surrendered' AND surrender_date IS NULL);

-- 8. Lead conversion consistency
SELECT *
FROM leads
WHERE converted = TRUE AND conversion_date IS NULL;

-- 9. Agent exit consistency
SELECT *
FROM agents
WHERE status = 'Exited' AND exit_date IS NULL;

-- 10. Summary row counts
SELECT 'customers' AS table_name, COUNT(*) FROM customers
UNION ALL SELECT 'agency_units', COUNT(*) FROM agency_units
UNION ALL SELECT 'agents', COUNT(*) FROM agents
UNION ALL SELECT 'leads', COUNT(*) FROM leads
UNION ALL SELECT 'policies', COUNT(*) FROM policies
UNION ALL SELECT 'premium_payments', COUNT(*) FROM premium_payments
UNION ALL SELECT 'policy_status_history', COUNT(*) FROM policy_status_history
UNION ALL SELECT 'sales_targets', COUNT(*) FROM sales_targets
UNION ALL SELECT 'incentives', COUNT(*) FROM incentives;
