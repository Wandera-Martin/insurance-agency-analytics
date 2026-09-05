SET search_path TO insurance_analytics;

-- 1. Duplicate primary-key checks (should return zero rows)
SELECT customer_id, COUNT(*) FROM customers GROUP BY customer_id HAVING COUNT(*) > 1;
SELECT agent_id, COUNT(*) FROM agents GROUP BY agent_id HAVING COUNT(*) > 1;
SELECT policy_id, COUNT(*) FROM policies GROUP BY policy_id HAVING COUNT(*) > 1;

-- 2. Broken foreign-key style checks
SELECT p.policy_id
FROM policies p
LEFT JOIN customers c ON c.customer_id = p.customer_id
WHERE c.customer_id IS NULL;

SELECT p.policy_id
FROM policies p
LEFT JOIN agents a ON a.agent_id = p.agent_id
WHERE a.agent_id IS NULL;

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
) > 1;

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
