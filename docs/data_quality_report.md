# Phase 2 data quality report

**Result: PASS — PostgreSQL validated**

- Run (UTC): 2026-09-05T22:47:04.698319+00:00
- Scope: PostgreSQL + CSV reconciliation
- Synthetic snapshot: 2026-09-01; seed: 42
- All records are synthetic.
- Rules evaluated: 542; failing rules: 0.

## Dataset coverage

| Table | Rows |
|---|---:|
| agency_units | 12 |
| customers | 25,000 |
| agents | 400 |
| leads | 70,000 |
| policies | 35,000 |
| premium_payments | 410,316 |
| policy_status_history | 39,452 |
| sales_targets | 7,044 |
| incentives | 750 |

## Validation results

Affected counts are per rule and can overlap. Zero means the rule passed; sample IDs identify synthetic records for investigation.

| Scope | Table | Rule | Failure severity | Affected | Sample IDs |
|---|---|---|---|---:|---|
| CSV | agency_units | nonempty dataset | ERROR | 0 |  |
| CSV | agency_units | duplicate complete rows | ERROR | 0 |  |
| CSV | agency_units | agency_unit_id: required | ERROR | 0 |  |
| CSV | agency_units | agency_unit_id: unique | ERROR | 0 |  |
| CSV | agency_units | agency_unit_id: text length | ERROR | 0 |  |
| CSV | agency_units | agency_name: required | ERROR | 0 |  |
| CSV | agency_units | agency_name: text length | ERROR | 0 |  |
| CSV | agency_units | branch: required | ERROR | 0 |  |
| CSV | agency_units | branch: text length | ERROR | 0 |  |
| CSV | agency_units | district: text length | ERROR | 0 |  |
| CSV | agency_units | region: text length | ERROR | 0 |  |
| CSV | agency_units | manager_id: text length | ERROR | 0 |  |
| CSV | agency_units | launch_date: required | ERROR | 0 |  |
| CSV | agency_units | launch_date: valid date | ERROR | 0 |  |
| CSV | agency_units | launch_date: within snapshot | ERROR | 0 |  |
| CSV | agency_units | status: required | ERROR | 0 |  |
| CSV | agency_units | status: allowed category | ERROR | 0 |  |
| CSV | agency_units | status: text length | ERROR | 0 |  |
| CSV | customers | nonempty dataset | ERROR | 0 |  |
| CSV | customers | duplicate complete rows | ERROR | 0 |  |
| CSV | customers | customer_id: required | ERROR | 0 |  |
| CSV | customers | customer_id: unique | ERROR | 0 |  |
| CSV | customers | customer_id: text length | ERROR | 0 |  |
| CSV | customers | gender: allowed category | ERROR | 0 |  |
| CSV | customers | gender: text length | ERROR | 0 |  |
| CSV | customers | date_of_birth: required | ERROR | 0 |  |
| CSV | customers | date_of_birth: valid date | ERROR | 0 |  |
| CSV | customers | date_of_birth: within snapshot | ERROR | 0 |  |
| CSV | customers | marital_status: text length | ERROR | 0 |  |
| CSV | customers | occupation: text length | ERROR | 0 |  |
| CSV | customers | district: text length | ERROR | 0 |  |
| CSV | customers | region: text length | ERROR | 0 |  |
| CSV | customers | income_band: text length | ERROR | 0 |  |
| CSV | customers | acquisition_channel: text length | ERROR | 0 |  |
| CSV | customers | created_date: required | ERROR | 0 |  |
| CSV | customers | created_date: valid date | ERROR | 0 |  |
| CSV | customers | created_date: within snapshot | ERROR | 0 |  |
| CSV | agents | nonempty dataset | ERROR | 0 |  |
| CSV | agents | duplicate complete rows | ERROR | 0 |  |
| CSV | agents | agent_id: required | ERROR | 0 |  |
| CSV | agents | agent_id: unique | ERROR | 0 |  |
| CSV | agents | agent_id: text length | ERROR | 0 |  |
| CSV | agents | agency_unit_id: required | ERROR | 0 |  |
| CSV | agents | agency_unit_id: references agency_units | ERROR | 0 |  |
| CSV | agents | agency_unit_id: text length | ERROR | 0 |  |
| CSV | agents | gender: allowed category | ERROR | 0 |  |
| CSV | agents | gender: text length | ERROR | 0 |  |
| CSV | agents | join_date: required | ERROR | 0 |  |
| CSV | agents | join_date: valid date | ERROR | 0 |  |
| CSV | agents | join_date: within snapshot | ERROR | 0 |  |
| CSV | agents | status: required | ERROR | 0 |  |
| CSV | agents | status: allowed category | ERROR | 0 |  |
| CSV | agents | status: text length | ERROR | 0 |  |
| CSV | agents | experience_years: finite number | ERROR | 0 |  |
| CSV | agents | experience_years: at most two decimals | ERROR | 0 |  |
| CSV | agents | agent_grade: allowed category | ERROR | 0 |  |
| CSV | agents | agent_grade: text length | ERROR | 0 |  |
| CSV | agents | supervisor_id: text length | ERROR | 0 |  |
| CSV | agents | exit_date: valid date | ERROR | 0 |  |
| CSV | agents | exit_date: within snapshot | ERROR | 0 |  |
| CSV | leads | nonempty dataset | ERROR | 0 |  |
| CSV | leads | duplicate complete rows | ERROR | 0 |  |
| CSV | leads | lead_id: required | ERROR | 0 |  |
| CSV | leads | lead_id: unique | ERROR | 0 |  |
| CSV | leads | lead_id: text length | ERROR | 0 |  |
| CSV | leads | agent_id: required | ERROR | 0 |  |
| CSV | leads | agent_id: references agents | ERROR | 0 |  |
| CSV | leads | agent_id: text length | ERROR | 0 |  |
| CSV | leads | customer_id: references customers | ERROR | 0 |  |
| CSV | leads | customer_id: text length | ERROR | 0 |  |
| CSV | leads | lead_date: required | ERROR | 0 |  |
| CSV | leads | lead_date: valid date | ERROR | 0 |  |
| CSV | leads | lead_date: within snapshot | ERROR | 0 |  |
| CSV | leads | source: text length | ERROR | 0 |  |
| CSV | leads | contact_status: allowed category | ERROR | 0 |  |
| CSV | leads | contact_status: text length | ERROR | 0 |  |
| CSV | leads | appointment_status: allowed category | ERROR | 0 |  |
| CSV | leads | appointment_status: text length | ERROR | 0 |  |
| CSV | leads | application_status: allowed category | ERROR | 0 |  |
| CSV | leads | application_status: text length | ERROR | 0 |  |
| CSV | leads | converted: required | ERROR | 0 |  |
| CSV | leads | converted: valid boolean | ERROR | 0 |  |
| CSV | leads | conversion_date: valid date | ERROR | 0 |  |
| CSV | leads | conversion_date: within snapshot | ERROR | 0 |  |
| CSV | policies | nonempty dataset | ERROR | 0 |  |
| CSV | policies | duplicate complete rows | ERROR | 0 |  |
| CSV | policies | policy_id: required | ERROR | 0 |  |
| CSV | policies | policy_id: unique | ERROR | 0 |  |
| CSV | policies | policy_id: text length | ERROR | 0 |  |
| CSV | policies | customer_id: required | ERROR | 0 |  |
| CSV | policies | customer_id: references customers | ERROR | 0 |  |
| CSV | policies | customer_id: text length | ERROR | 0 |  |
| CSV | policies | agent_id: required | ERROR | 0 |  |
| CSV | policies | agent_id: references agents | ERROR | 0 |  |
| CSV | policies | agent_id: text length | ERROR | 0 |  |
| CSV | policies | product_name: required | ERROR | 0 |  |
| CSV | policies | product_name: text length | ERROR | 0 |  |
| CSV | policies | distribution_channel: required | ERROR | 0 |  |
| CSV | policies | distribution_channel: text length | ERROR | 0 |  |
| CSV | policies | issue_date: required | ERROR | 0 |  |
| CSV | policies | issue_date: valid date | ERROR | 0 |  |
| CSV | policies | issue_date: within snapshot | ERROR | 0 |  |
| CSV | policies | policy_term_years: required | ERROR | 0 |  |
| CSV | policies | policy_term_years: finite number | ERROR | 0 |  |
| CSV | policies | policy_term_years: whole number | ERROR | 0 |  |
| CSV | policies | payment_frequency: required | ERROR | 0 |  |
| CSV | policies | payment_frequency: allowed category | ERROR | 0 |  |
| CSV | policies | payment_frequency: text length | ERROR | 0 |  |
| CSV | policies | premium_amount: required | ERROR | 0 |  |
| CSV | policies | premium_amount: finite number | ERROR | 0 |  |
| CSV | policies | premium_amount: at most two decimals | ERROR | 0 |  |
| CSV | policies | annualized_premium: required | ERROR | 0 |  |
| CSV | policies | annualized_premium: finite number | ERROR | 0 |  |
| CSV | policies | annualized_premium: at most two decimals | ERROR | 0 |  |
| CSV | policies | sum_assured: required | ERROR | 0 |  |
| CSV | policies | sum_assured: finite number | ERROR | 0 |  |
| CSV | policies | sum_assured: at most two decimals | ERROR | 0 |  |
| CSV | policies | maturity_date: required | ERROR | 0 |  |
| CSV | policies | maturity_date: valid date | ERROR | 0 |  |
| CSV | policies | policy_status: required | ERROR | 0 |  |
| CSV | policies | policy_status: allowed category | ERROR | 0 |  |
| CSV | policies | policy_status: text length | ERROR | 0 |  |
| CSV | policies | lapse_date: valid date | ERROR | 0 |  |
| CSV | policies | lapse_date: within snapshot | ERROR | 0 |  |
| CSV | policies | surrender_date: valid date | ERROR | 0 |  |
| CSV | policies | surrender_date: within snapshot | ERROR | 0 |  |
| CSV | premium_payments | nonempty dataset | ERROR | 0 |  |
| CSV | premium_payments | duplicate complete rows | ERROR | 0 |  |
| CSV | premium_payments | payment_id: required | ERROR | 0 |  |
| CSV | premium_payments | payment_id: unique | ERROR | 0 |  |
| CSV | premium_payments | payment_id: text length | ERROR | 0 |  |
| CSV | premium_payments | policy_id: required | ERROR | 0 |  |
| CSV | premium_payments | policy_id: references policies | ERROR | 0 |  |
| CSV | premium_payments | policy_id: text length | ERROR | 0 |  |
| CSV | premium_payments | due_date: required | ERROR | 0 |  |
| CSV | premium_payments | due_date: valid date | ERROR | 0 |  |
| CSV | premium_payments | due_date: within snapshot | ERROR | 0 |  |
| CSV | premium_payments | payment_date: valid date | ERROR | 0 |  |
| CSV | premium_payments | payment_date: within snapshot | ERROR | 0 |  |
| CSV | premium_payments | amount_due: required | ERROR | 0 |  |
| CSV | premium_payments | amount_due: finite number | ERROR | 0 |  |
| CSV | premium_payments | amount_due: at most two decimals | ERROR | 0 |  |
| CSV | premium_payments | amount_paid: required | ERROR | 0 |  |
| CSV | premium_payments | amount_paid: finite number | ERROR | 0 |  |
| CSV | premium_payments | amount_paid: at most two decimals | ERROR | 0 |  |
| CSV | premium_payments | payment_status: required | ERROR | 0 |  |
| CSV | premium_payments | payment_status: allowed category | ERROR | 0 |  |
| CSV | premium_payments | payment_status: text length | ERROR | 0 |  |
| CSV | premium_payments | payment_method: text length | ERROR | 0 |  |
| CSV | policy_status_history | nonempty dataset | ERROR | 0 |  |
| CSV | policy_status_history | duplicate complete rows | ERROR | 0 |  |
| CSV | policy_status_history | status_history_id: required | ERROR | 0 |  |
| CSV | policy_status_history | status_history_id: unique | ERROR | 0 |  |
| CSV | policy_status_history | status_history_id: text length | ERROR | 0 |  |
| CSV | policy_status_history | policy_id: required | ERROR | 0 |  |
| CSV | policy_status_history | policy_id: references policies | ERROR | 0 |  |
| CSV | policy_status_history | policy_id: text length | ERROR | 0 |  |
| CSV | policy_status_history | status: required | ERROR | 0 |  |
| CSV | policy_status_history | status: allowed category | ERROR | 0 |  |
| CSV | policy_status_history | status: text length | ERROR | 0 |  |
| CSV | policy_status_history | status_date: required | ERROR | 0 |  |
| CSV | policy_status_history | status_date: valid date | ERROR | 0 |  |
| CSV | policy_status_history | status_date: within snapshot | ERROR | 0 |  |
| CSV | policy_status_history | reason: text length | ERROR | 0 |  |
| CSV | sales_targets | nonempty dataset | ERROR | 0 |  |
| CSV | sales_targets | duplicate complete rows | ERROR | 0 |  |
| CSV | sales_targets | target_id: required | ERROR | 0 |  |
| CSV | sales_targets | target_id: unique | ERROR | 0 |  |
| CSV | sales_targets | target_id: text length | ERROR | 0 |  |
| CSV | sales_targets | agent_id: required | ERROR | 0 |  |
| CSV | sales_targets | agent_id: references agents | ERROR | 0 |  |
| CSV | sales_targets | agent_id: text length | ERROR | 0 |  |
| CSV | sales_targets | target_month: required | ERROR | 0 |  |
| CSV | sales_targets | target_month: valid date | ERROR | 0 |  |
| CSV | sales_targets | target_month: within snapshot | ERROR | 0 |  |
| CSV | sales_targets | policy_target: required | ERROR | 0 |  |
| CSV | sales_targets | policy_target: finite number | ERROR | 0 |  |
| CSV | sales_targets | policy_target: whole number | ERROR | 0 |  |
| CSV | sales_targets | premium_target: required | ERROR | 0 |  |
| CSV | sales_targets | premium_target: finite number | ERROR | 0 |  |
| CSV | sales_targets | premium_target: at most two decimals | ERROR | 0 |  |
| CSV | sales_targets | new_customer_target: required | ERROR | 0 |  |
| CSV | sales_targets | new_customer_target: finite number | ERROR | 0 |  |
| CSV | sales_targets | new_customer_target: whole number | ERROR | 0 |  |
| CSV | incentives | nonempty dataset | ERROR | 0 |  |
| CSV | incentives | duplicate complete rows | ERROR | 0 |  |
| CSV | incentives | incentive_id: required | ERROR | 0 |  |
| CSV | incentives | incentive_id: unique | ERROR | 0 |  |
| CSV | incentives | incentive_id: text length | ERROR | 0 |  |
| CSV | incentives | agent_id: required | ERROR | 0 |  |
| CSV | incentives | agent_id: references agents | ERROR | 0 |  |
| CSV | incentives | agent_id: text length | ERROR | 0 |  |
| CSV | incentives | campaign_name: required | ERROR | 0 |  |
| CSV | incentives | campaign_name: text length | ERROR | 0 |  |
| CSV | incentives | start_date: required | ERROR | 0 |  |
| CSV | incentives | start_date: valid date | ERROR | 0 |  |
| CSV | incentives | start_date: within snapshot | ERROR | 0 |  |
| CSV | incentives | end_date: required | ERROR | 0 |  |
| CSV | incentives | end_date: valid date | ERROR | 0 |  |
| CSV | incentives | end_date: within snapshot | ERROR | 0 |  |
| CSV | incentives | threshold: finite number | ERROR | 0 |  |
| CSV | incentives | threshold: at most two decimals | ERROR | 0 |  |
| CSV | incentives | incentive_amount: required | ERROR | 0 |  |
| CSV | incentives | incentive_amount: finite number | ERROR | 0 |  |
| CSV | incentives | incentive_amount: at most two decimals | ERROR | 0 |  |
| CSV | incentives | qualified: required | ERROR | 0 |  |
| CSV | incentives | qualified: valid boolean | ERROR | 0 |  |
| CSV | customers | birth before onboarding | ERROR | 0 |  |
| CSV | agents | nonnegative experience | ERROR | 0 |  |
| CSV | agents | exit date agrees with status | ERROR | 0 |  |
| CSV | agents | exit after join | ERROR | 0 |  |
| CSV | agents | join on/after unit launch | ERROR | 0 |  |
| CSV | policies | issue_date: within agent service | ERROR | 0 |  |
| CSV | leads | lead_date: within agent service | ERROR | 0 |  |
| CSV | leads | conversion_date: within agent service | ERROR | 0 |  |
| CSV | sales_targets | target_month: within agent service | ERROR | 0 |  |
| CSV | policies | issue on/after customer onboarding | ERROR | 0 |  |
| CSV | leads | conversion on/after customer onboarding | ERROR | 0 |  |
| CSV | leads | conversion flag agrees with date | ERROR | 0 |  |
| CSV | leads | conversion after lead | ERROR | 0 |  |
| CSV | leads | converted lead has customer and approved application | ERROR | 0 |  |
| CSV | leads | converted lead contacted | ERROR | 0 |  |
| CSV | policies | premium_amount: positive | ERROR | 0 |  |
| CSV | policies | annualized_premium: positive | ERROR | 0 |  |
| CSV | policies | sum_assured: positive | ERROR | 0 |  |
| CSV | policies | policy_term_years: positive | ERROR | 0 |  |
| CSV | policies | annualization within UGX 0.01 | ERROR | 0 |  |
| CSV | policies | Agency distribution only | ERROR | 0 |  |
| CSV | policies | maturity after issue | ERROR | 0 |  |
| CSV | policies | Lapsed: status/date consistency | ERROR | 0 |  |
| CSV | policies | lapse_date: after issue | ERROR | 0 |  |
| CSV | policies | Surrendered: status/date consistency | ERROR | 0 |  |
| CSV | policies | surrender_date: after issue | ERROR | 0 |  |
| CSV | premium_payments | unique installment | ERROR | 0 |  |
| CSV | premium_payments | positive due and nonnegative paid | ERROR | 0 |  |
| CSV | premium_payments | installment agrees with policy | ERROR | 0 |  |
| CSV | premium_payments | due on/after issue | ERROR | 0 |  |
| CSV | premium_payments | due before lapse_date | ERROR | 0 |  |
| CSV | premium_payments | due before surrender_date | ERROR | 0 |  |
| CSV | premium_payments | payment date agrees with amount | ERROR | 0 |  |
| CSV | premium_payments | missed means zero paid and no date | ERROR | 0 |  |
| CSV | premium_payments | partial amount between zero and due | ERROR | 0 |  |
| CSV | premium_payments | Paid/Late settled in full | ERROR | 0 |  |
| CSV | premium_payments | Paid within synthetic two-day tolerance | ERROR | 0 |  |
| CSV | premium_payments | Late exceeds two-day tolerance | ERROR | 0 |  |
| CSV | policy_status_history | event on/after issue | ERROR | 0 |  |
| CSV | policy_status_history | unique policy event date | ERROR | 0 |  |
| CSV | policies | current status agrees with latest history | ERROR | 0 |  |
| CSV | policies | Lapsed: history date agrees with policy | ERROR | 0 |  |
| CSV | policies | Surrendered: history date agrees with policy | ERROR | 0 |  |
| CSV | policies | initial Active event on issue date | ERROR | 0 |  |
| CSV | policies | at least one installment | ERROR | 0 |  |
| CSV | sales_targets | unique agent/month | ERROR | 0 |  |
| CSV | sales_targets | month begins on day one | ERROR | 0 |  |
| CSV | sales_targets | policy_target: nonnegative | ERROR | 0 |  |
| CSV | sales_targets | premium_target: nonnegative | ERROR | 0 |  |
| CSV | sales_targets | new_customer_target: nonnegative | ERROR | 0 |  |
| CSV | incentives | campaign end on/after start | ERROR | 0 |  |
| CSV | incentives | unique agent/campaign | ERROR | 0 |  |
| CSV | incentives | nonnegative threshold and award | ERROR | 0 |  |
| CSV | incentives | qualification agrees with award | ERROR | 0 |  |
| CSV | incentives | campaign overlaps agent service | ERROR | 0 |  |
| PostgreSQL | agency_units | nonempty dataset | ERROR | 0 |  |
| PostgreSQL | agency_units | duplicate complete rows | ERROR | 0 |  |
| PostgreSQL | agency_units | agency_unit_id: required | ERROR | 0 |  |
| PostgreSQL | agency_units | agency_unit_id: unique | ERROR | 0 |  |
| PostgreSQL | agency_units | agency_unit_id: text length | ERROR | 0 |  |
| PostgreSQL | agency_units | agency_name: required | ERROR | 0 |  |
| PostgreSQL | agency_units | agency_name: text length | ERROR | 0 |  |
| PostgreSQL | agency_units | branch: required | ERROR | 0 |  |
| PostgreSQL | agency_units | branch: text length | ERROR | 0 |  |
| PostgreSQL | agency_units | district: text length | ERROR | 0 |  |
| PostgreSQL | agency_units | region: text length | ERROR | 0 |  |
| PostgreSQL | agency_units | manager_id: text length | ERROR | 0 |  |
| PostgreSQL | agency_units | launch_date: required | ERROR | 0 |  |
| PostgreSQL | agency_units | launch_date: valid date | ERROR | 0 |  |
| PostgreSQL | agency_units | launch_date: within snapshot | ERROR | 0 |  |
| PostgreSQL | agency_units | status: required | ERROR | 0 |  |
| PostgreSQL | agency_units | status: allowed category | ERROR | 0 |  |
| PostgreSQL | agency_units | status: text length | ERROR | 0 |  |
| PostgreSQL | customers | nonempty dataset | ERROR | 0 |  |
| PostgreSQL | customers | duplicate complete rows | ERROR | 0 |  |
| PostgreSQL | customers | customer_id: required | ERROR | 0 |  |
| PostgreSQL | customers | customer_id: unique | ERROR | 0 |  |
| PostgreSQL | customers | customer_id: text length | ERROR | 0 |  |
| PostgreSQL | customers | gender: allowed category | ERROR | 0 |  |
| PostgreSQL | customers | gender: text length | ERROR | 0 |  |
| PostgreSQL | customers | date_of_birth: required | ERROR | 0 |  |
| PostgreSQL | customers | date_of_birth: valid date | ERROR | 0 |  |
| PostgreSQL | customers | date_of_birth: within snapshot | ERROR | 0 |  |
| PostgreSQL | customers | marital_status: text length | ERROR | 0 |  |
| PostgreSQL | customers | occupation: text length | ERROR | 0 |  |
| PostgreSQL | customers | district: text length | ERROR | 0 |  |
| PostgreSQL | customers | region: text length | ERROR | 0 |  |
| PostgreSQL | customers | income_band: text length | ERROR | 0 |  |
| PostgreSQL | customers | acquisition_channel: text length | ERROR | 0 |  |
| PostgreSQL | customers | created_date: required | ERROR | 0 |  |
| PostgreSQL | customers | created_date: valid date | ERROR | 0 |  |
| PostgreSQL | customers | created_date: within snapshot | ERROR | 0 |  |
| PostgreSQL | agents | nonempty dataset | ERROR | 0 |  |
| PostgreSQL | agents | duplicate complete rows | ERROR | 0 |  |
| PostgreSQL | agents | agent_id: required | ERROR | 0 |  |
| PostgreSQL | agents | agent_id: unique | ERROR | 0 |  |
| PostgreSQL | agents | agent_id: text length | ERROR | 0 |  |
| PostgreSQL | agents | agency_unit_id: required | ERROR | 0 |  |
| PostgreSQL | agents | agency_unit_id: references agency_units | ERROR | 0 |  |
| PostgreSQL | agents | agency_unit_id: text length | ERROR | 0 |  |
| PostgreSQL | agents | gender: allowed category | ERROR | 0 |  |
| PostgreSQL | agents | gender: text length | ERROR | 0 |  |
| PostgreSQL | agents | join_date: required | ERROR | 0 |  |
| PostgreSQL | agents | join_date: valid date | ERROR | 0 |  |
| PostgreSQL | agents | join_date: within snapshot | ERROR | 0 |  |
| PostgreSQL | agents | status: required | ERROR | 0 |  |
| PostgreSQL | agents | status: allowed category | ERROR | 0 |  |
| PostgreSQL | agents | status: text length | ERROR | 0 |  |
| PostgreSQL | agents | experience_years: finite number | ERROR | 0 |  |
| PostgreSQL | agents | experience_years: at most two decimals | ERROR | 0 |  |
| PostgreSQL | agents | agent_grade: allowed category | ERROR | 0 |  |
| PostgreSQL | agents | agent_grade: text length | ERROR | 0 |  |
| PostgreSQL | agents | supervisor_id: text length | ERROR | 0 |  |
| PostgreSQL | agents | exit_date: valid date | ERROR | 0 |  |
| PostgreSQL | agents | exit_date: within snapshot | ERROR | 0 |  |
| PostgreSQL | leads | nonempty dataset | ERROR | 0 |  |
| PostgreSQL | leads | duplicate complete rows | ERROR | 0 |  |
| PostgreSQL | leads | lead_id: required | ERROR | 0 |  |
| PostgreSQL | leads | lead_id: unique | ERROR | 0 |  |
| PostgreSQL | leads | lead_id: text length | ERROR | 0 |  |
| PostgreSQL | leads | agent_id: required | ERROR | 0 |  |
| PostgreSQL | leads | agent_id: references agents | ERROR | 0 |  |
| PostgreSQL | leads | agent_id: text length | ERROR | 0 |  |
| PostgreSQL | leads | customer_id: references customers | ERROR | 0 |  |
| PostgreSQL | leads | customer_id: text length | ERROR | 0 |  |
| PostgreSQL | leads | lead_date: required | ERROR | 0 |  |
| PostgreSQL | leads | lead_date: valid date | ERROR | 0 |  |
| PostgreSQL | leads | lead_date: within snapshot | ERROR | 0 |  |
| PostgreSQL | leads | source: text length | ERROR | 0 |  |
| PostgreSQL | leads | contact_status: allowed category | ERROR | 0 |  |
| PostgreSQL | leads | contact_status: text length | ERROR | 0 |  |
| PostgreSQL | leads | appointment_status: allowed category | ERROR | 0 |  |
| PostgreSQL | leads | appointment_status: text length | ERROR | 0 |  |
| PostgreSQL | leads | application_status: allowed category | ERROR | 0 |  |
| PostgreSQL | leads | application_status: text length | ERROR | 0 |  |
| PostgreSQL | leads | converted: required | ERROR | 0 |  |
| PostgreSQL | leads | converted: valid boolean | ERROR | 0 |  |
| PostgreSQL | leads | conversion_date: valid date | ERROR | 0 |  |
| PostgreSQL | leads | conversion_date: within snapshot | ERROR | 0 |  |
| PostgreSQL | policies | nonempty dataset | ERROR | 0 |  |
| PostgreSQL | policies | duplicate complete rows | ERROR | 0 |  |
| PostgreSQL | policies | policy_id: required | ERROR | 0 |  |
| PostgreSQL | policies | policy_id: unique | ERROR | 0 |  |
| PostgreSQL | policies | policy_id: text length | ERROR | 0 |  |
| PostgreSQL | policies | customer_id: required | ERROR | 0 |  |
| PostgreSQL | policies | customer_id: references customers | ERROR | 0 |  |
| PostgreSQL | policies | customer_id: text length | ERROR | 0 |  |
| PostgreSQL | policies | agent_id: required | ERROR | 0 |  |
| PostgreSQL | policies | agent_id: references agents | ERROR | 0 |  |
| PostgreSQL | policies | agent_id: text length | ERROR | 0 |  |
| PostgreSQL | policies | product_name: required | ERROR | 0 |  |
| PostgreSQL | policies | product_name: text length | ERROR | 0 |  |
| PostgreSQL | policies | distribution_channel: required | ERROR | 0 |  |
| PostgreSQL | policies | distribution_channel: text length | ERROR | 0 |  |
| PostgreSQL | policies | issue_date: required | ERROR | 0 |  |
| PostgreSQL | policies | issue_date: valid date | ERROR | 0 |  |
| PostgreSQL | policies | issue_date: within snapshot | ERROR | 0 |  |
| PostgreSQL | policies | policy_term_years: required | ERROR | 0 |  |
| PostgreSQL | policies | policy_term_years: finite number | ERROR | 0 |  |
| PostgreSQL | policies | policy_term_years: whole number | ERROR | 0 |  |
| PostgreSQL | policies | payment_frequency: required | ERROR | 0 |  |
| PostgreSQL | policies | payment_frequency: allowed category | ERROR | 0 |  |
| PostgreSQL | policies | payment_frequency: text length | ERROR | 0 |  |
| PostgreSQL | policies | premium_amount: required | ERROR | 0 |  |
| PostgreSQL | policies | premium_amount: finite number | ERROR | 0 |  |
| PostgreSQL | policies | premium_amount: at most two decimals | ERROR | 0 |  |
| PostgreSQL | policies | annualized_premium: required | ERROR | 0 |  |
| PostgreSQL | policies | annualized_premium: finite number | ERROR | 0 |  |
| PostgreSQL | policies | annualized_premium: at most two decimals | ERROR | 0 |  |
| PostgreSQL | policies | sum_assured: required | ERROR | 0 |  |
| PostgreSQL | policies | sum_assured: finite number | ERROR | 0 |  |
| PostgreSQL | policies | sum_assured: at most two decimals | ERROR | 0 |  |
| PostgreSQL | policies | maturity_date: required | ERROR | 0 |  |
| PostgreSQL | policies | maturity_date: valid date | ERROR | 0 |  |
| PostgreSQL | policies | policy_status: required | ERROR | 0 |  |
| PostgreSQL | policies | policy_status: allowed category | ERROR | 0 |  |
| PostgreSQL | policies | policy_status: text length | ERROR | 0 |  |
| PostgreSQL | policies | lapse_date: valid date | ERROR | 0 |  |
| PostgreSQL | policies | lapse_date: within snapshot | ERROR | 0 |  |
| PostgreSQL | policies | surrender_date: valid date | ERROR | 0 |  |
| PostgreSQL | policies | surrender_date: within snapshot | ERROR | 0 |  |
| PostgreSQL | premium_payments | nonempty dataset | ERROR | 0 |  |
| PostgreSQL | premium_payments | duplicate complete rows | ERROR | 0 |  |
| PostgreSQL | premium_payments | payment_id: required | ERROR | 0 |  |
| PostgreSQL | premium_payments | payment_id: unique | ERROR | 0 |  |
| PostgreSQL | premium_payments | payment_id: text length | ERROR | 0 |  |
| PostgreSQL | premium_payments | policy_id: required | ERROR | 0 |  |
| PostgreSQL | premium_payments | policy_id: references policies | ERROR | 0 |  |
| PostgreSQL | premium_payments | policy_id: text length | ERROR | 0 |  |
| PostgreSQL | premium_payments | due_date: required | ERROR | 0 |  |
| PostgreSQL | premium_payments | due_date: valid date | ERROR | 0 |  |
| PostgreSQL | premium_payments | due_date: within snapshot | ERROR | 0 |  |
| PostgreSQL | premium_payments | payment_date: valid date | ERROR | 0 |  |
| PostgreSQL | premium_payments | payment_date: within snapshot | ERROR | 0 |  |
| PostgreSQL | premium_payments | amount_due: required | ERROR | 0 |  |
| PostgreSQL | premium_payments | amount_due: finite number | ERROR | 0 |  |
| PostgreSQL | premium_payments | amount_due: at most two decimals | ERROR | 0 |  |
| PostgreSQL | premium_payments | amount_paid: required | ERROR | 0 |  |
| PostgreSQL | premium_payments | amount_paid: finite number | ERROR | 0 |  |
| PostgreSQL | premium_payments | amount_paid: at most two decimals | ERROR | 0 |  |
| PostgreSQL | premium_payments | payment_status: required | ERROR | 0 |  |
| PostgreSQL | premium_payments | payment_status: allowed category | ERROR | 0 |  |
| PostgreSQL | premium_payments | payment_status: text length | ERROR | 0 |  |
| PostgreSQL | premium_payments | payment_method: text length | ERROR | 0 |  |
| PostgreSQL | policy_status_history | nonempty dataset | ERROR | 0 |  |
| PostgreSQL | policy_status_history | duplicate complete rows | ERROR | 0 |  |
| PostgreSQL | policy_status_history | status_history_id: required | ERROR | 0 |  |
| PostgreSQL | policy_status_history | status_history_id: unique | ERROR | 0 |  |
| PostgreSQL | policy_status_history | status_history_id: text length | ERROR | 0 |  |
| PostgreSQL | policy_status_history | policy_id: required | ERROR | 0 |  |
| PostgreSQL | policy_status_history | policy_id: references policies | ERROR | 0 |  |
| PostgreSQL | policy_status_history | policy_id: text length | ERROR | 0 |  |
| PostgreSQL | policy_status_history | status: required | ERROR | 0 |  |
| PostgreSQL | policy_status_history | status: allowed category | ERROR | 0 |  |
| PostgreSQL | policy_status_history | status: text length | ERROR | 0 |  |
| PostgreSQL | policy_status_history | status_date: required | ERROR | 0 |  |
| PostgreSQL | policy_status_history | status_date: valid date | ERROR | 0 |  |
| PostgreSQL | policy_status_history | status_date: within snapshot | ERROR | 0 |  |
| PostgreSQL | policy_status_history | reason: text length | ERROR | 0 |  |
| PostgreSQL | sales_targets | nonempty dataset | ERROR | 0 |  |
| PostgreSQL | sales_targets | duplicate complete rows | ERROR | 0 |  |
| PostgreSQL | sales_targets | target_id: required | ERROR | 0 |  |
| PostgreSQL | sales_targets | target_id: unique | ERROR | 0 |  |
| PostgreSQL | sales_targets | target_id: text length | ERROR | 0 |  |
| PostgreSQL | sales_targets | agent_id: required | ERROR | 0 |  |
| PostgreSQL | sales_targets | agent_id: references agents | ERROR | 0 |  |
| PostgreSQL | sales_targets | agent_id: text length | ERROR | 0 |  |
| PostgreSQL | sales_targets | target_month: required | ERROR | 0 |  |
| PostgreSQL | sales_targets | target_month: valid date | ERROR | 0 |  |
| PostgreSQL | sales_targets | target_month: within snapshot | ERROR | 0 |  |
| PostgreSQL | sales_targets | policy_target: required | ERROR | 0 |  |
| PostgreSQL | sales_targets | policy_target: finite number | ERROR | 0 |  |
| PostgreSQL | sales_targets | policy_target: whole number | ERROR | 0 |  |
| PostgreSQL | sales_targets | premium_target: required | ERROR | 0 |  |
| PostgreSQL | sales_targets | premium_target: finite number | ERROR | 0 |  |
| PostgreSQL | sales_targets | premium_target: at most two decimals | ERROR | 0 |  |
| PostgreSQL | sales_targets | new_customer_target: required | ERROR | 0 |  |
| PostgreSQL | sales_targets | new_customer_target: finite number | ERROR | 0 |  |
| PostgreSQL | sales_targets | new_customer_target: whole number | ERROR | 0 |  |
| PostgreSQL | incentives | nonempty dataset | ERROR | 0 |  |
| PostgreSQL | incentives | duplicate complete rows | ERROR | 0 |  |
| PostgreSQL | incentives | incentive_id: required | ERROR | 0 |  |
| PostgreSQL | incentives | incentive_id: unique | ERROR | 0 |  |
| PostgreSQL | incentives | incentive_id: text length | ERROR | 0 |  |
| PostgreSQL | incentives | agent_id: required | ERROR | 0 |  |
| PostgreSQL | incentives | agent_id: references agents | ERROR | 0 |  |
| PostgreSQL | incentives | agent_id: text length | ERROR | 0 |  |
| PostgreSQL | incentives | campaign_name: required | ERROR | 0 |  |
| PostgreSQL | incentives | campaign_name: text length | ERROR | 0 |  |
| PostgreSQL | incentives | start_date: required | ERROR | 0 |  |
| PostgreSQL | incentives | start_date: valid date | ERROR | 0 |  |
| PostgreSQL | incentives | start_date: within snapshot | ERROR | 0 |  |
| PostgreSQL | incentives | end_date: required | ERROR | 0 |  |
| PostgreSQL | incentives | end_date: valid date | ERROR | 0 |  |
| PostgreSQL | incentives | end_date: within snapshot | ERROR | 0 |  |
| PostgreSQL | incentives | threshold: finite number | ERROR | 0 |  |
| PostgreSQL | incentives | threshold: at most two decimals | ERROR | 0 |  |
| PostgreSQL | incentives | incentive_amount: required | ERROR | 0 |  |
| PostgreSQL | incentives | incentive_amount: finite number | ERROR | 0 |  |
| PostgreSQL | incentives | incentive_amount: at most two decimals | ERROR | 0 |  |
| PostgreSQL | incentives | qualified: required | ERROR | 0 |  |
| PostgreSQL | incentives | qualified: valid boolean | ERROR | 0 |  |
| PostgreSQL | customers | birth before onboarding | ERROR | 0 |  |
| PostgreSQL | agents | nonnegative experience | ERROR | 0 |  |
| PostgreSQL | agents | exit date agrees with status | ERROR | 0 |  |
| PostgreSQL | agents | exit after join | ERROR | 0 |  |
| PostgreSQL | agents | join on/after unit launch | ERROR | 0 |  |
| PostgreSQL | policies | issue_date: within agent service | ERROR | 0 |  |
| PostgreSQL | leads | lead_date: within agent service | ERROR | 0 |  |
| PostgreSQL | leads | conversion_date: within agent service | ERROR | 0 |  |
| PostgreSQL | sales_targets | target_month: within agent service | ERROR | 0 |  |
| PostgreSQL | policies | issue on/after customer onboarding | ERROR | 0 |  |
| PostgreSQL | leads | conversion on/after customer onboarding | ERROR | 0 |  |
| PostgreSQL | leads | conversion flag agrees with date | ERROR | 0 |  |
| PostgreSQL | leads | conversion after lead | ERROR | 0 |  |
| PostgreSQL | leads | converted lead has customer and approved application | ERROR | 0 |  |
| PostgreSQL | leads | converted lead contacted | ERROR | 0 |  |
| PostgreSQL | policies | premium_amount: positive | ERROR | 0 |  |
| PostgreSQL | policies | annualized_premium: positive | ERROR | 0 |  |
| PostgreSQL | policies | sum_assured: positive | ERROR | 0 |  |
| PostgreSQL | policies | policy_term_years: positive | ERROR | 0 |  |
| PostgreSQL | policies | annualization within UGX 0.01 | ERROR | 0 |  |
| PostgreSQL | policies | Agency distribution only | ERROR | 0 |  |
| PostgreSQL | policies | maturity after issue | ERROR | 0 |  |
| PostgreSQL | policies | Lapsed: status/date consistency | ERROR | 0 |  |
| PostgreSQL | policies | lapse_date: after issue | ERROR | 0 |  |
| PostgreSQL | policies | Surrendered: status/date consistency | ERROR | 0 |  |
| PostgreSQL | policies | surrender_date: after issue | ERROR | 0 |  |
| PostgreSQL | premium_payments | unique installment | ERROR | 0 |  |
| PostgreSQL | premium_payments | positive due and nonnegative paid | ERROR | 0 |  |
| PostgreSQL | premium_payments | installment agrees with policy | ERROR | 0 |  |
| PostgreSQL | premium_payments | due on/after issue | ERROR | 0 |  |
| PostgreSQL | premium_payments | due before lapse_date | ERROR | 0 |  |
| PostgreSQL | premium_payments | due before surrender_date | ERROR | 0 |  |
| PostgreSQL | premium_payments | payment date agrees with amount | ERROR | 0 |  |
| PostgreSQL | premium_payments | missed means zero paid and no date | ERROR | 0 |  |
| PostgreSQL | premium_payments | partial amount between zero and due | ERROR | 0 |  |
| PostgreSQL | premium_payments | Paid/Late settled in full | ERROR | 0 |  |
| PostgreSQL | premium_payments | Paid within synthetic two-day tolerance | ERROR | 0 |  |
| PostgreSQL | premium_payments | Late exceeds two-day tolerance | ERROR | 0 |  |
| PostgreSQL | policy_status_history | event on/after issue | ERROR | 0 |  |
| PostgreSQL | policy_status_history | unique policy event date | ERROR | 0 |  |
| PostgreSQL | policies | current status agrees with latest history | ERROR | 0 |  |
| PostgreSQL | policies | Lapsed: history date agrees with policy | ERROR | 0 |  |
| PostgreSQL | policies | Surrendered: history date agrees with policy | ERROR | 0 |  |
| PostgreSQL | policies | initial Active event on issue date | ERROR | 0 |  |
| PostgreSQL | policies | at least one installment | ERROR | 0 |  |
| PostgreSQL | sales_targets | unique agent/month | ERROR | 0 |  |
| PostgreSQL | sales_targets | month begins on day one | ERROR | 0 |  |
| PostgreSQL | sales_targets | policy_target: nonnegative | ERROR | 0 |  |
| PostgreSQL | sales_targets | premium_target: nonnegative | ERROR | 0 |  |
| PostgreSQL | sales_targets | new_customer_target: nonnegative | ERROR | 0 |  |
| PostgreSQL | incentives | campaign end on/after start | ERROR | 0 |  |
| PostgreSQL | incentives | unique agent/campaign | ERROR | 0 |  |
| PostgreSQL | incentives | nonnegative threshold and award | ERROR | 0 |  |
| PostgreSQL | incentives | qualification agrees with award | ERROR | 0 |  |
| PostgreSQL | incentives | campaign overlaps agent service | ERROR | 0 |  |
| Reconciliation | agency_units | PostgreSQL row count matches CSV | ERROR | 0 |  |
| Reconciliation | agency_units | PostgreSQL values match CSV | ERROR | 0 |  |
| Reconciliation | customers | PostgreSQL row count matches CSV | ERROR | 0 |  |
| Reconciliation | customers | PostgreSQL values match CSV | ERROR | 0 |  |
| Reconciliation | agents | PostgreSQL row count matches CSV | ERROR | 0 |  |
| Reconciliation | agents | PostgreSQL values match CSV | ERROR | 0 |  |
| Reconciliation | leads | PostgreSQL row count matches CSV | ERROR | 0 |  |
| Reconciliation | leads | PostgreSQL values match CSV | ERROR | 0 |  |
| Reconciliation | policies | PostgreSQL row count matches CSV | ERROR | 0 |  |
| Reconciliation | policies | PostgreSQL values match CSV | ERROR | 0 |  |
| Reconciliation | premium_payments | PostgreSQL row count matches CSV | ERROR | 0 |  |
| Reconciliation | premium_payments | PostgreSQL values match CSV | ERROR | 0 |  |
| Reconciliation | policy_status_history | PostgreSQL row count matches CSV | ERROR | 0 |  |
| Reconciliation | policy_status_history | PostgreSQL values match CSV | ERROR | 0 |  |
| Reconciliation | sales_targets | PostgreSQL row count matches CSV | ERROR | 0 |  |
| Reconciliation | sales_targets | PostgreSQL values match CSV | ERROR | 0 |  |
| Reconciliation | incentives | PostgreSQL row count matches CSV | ERROR | 0 |  |
| Reconciliation | incentives | PostgreSQL values match CSV | ERROR | 0 |  |

## Agency interpretation and limits

Baseline defects and corrections: [phase2_baseline.md](phase2_baseline.md).

Passing checks establishes structural and documented business-rule consistency, not commercial success or predictive validity. No agent rankings, persistency rates or incentive-effectiveness findings are asserted here.

- Installments use fixed 30/91/182/365-day steps, not contract calendar anniversaries.
- Paid permits a synthetic two-day tolerance; Late starts after two days.
- Missed means unpaid at the snapshot, including recently due installments; it does not establish delinquency or a contractual grace-period breach.
- Lead-to-policy linkage has no lead_id on policies. Customer/agent/date matching cannot prove a unique attribution; do not equate policy counts with converted leads.
- Manager and supervisor IDs are external synthetic labels, not agent foreign keys.
- Agent unit/status are current snapshots; transfers and inactivity histories are absent.
- Incentive qualification and lapse are simulated, not derived from threshold achievement or a contractual arrears engine. They cannot support causal conclusions.
- September 2026 is incomplete at the September 1 snapshot; targets cover full months.
- Persistency eligibility, observation windows and reinstatement treatment belong to the next analysis phase.

## Reproduction provenance

```json
{
  "synthetic": true,
  "seed": 42,
  "as_of": "2026-09-01",
  "generator_sha256": "112b17bbb81cc20f20e105a5dd34cb54616afdc3b9b79c93182ba6282d105489",
  "files": {
    "agency_units.csv": "6ddd965bd398edcee1426285d95032b393a0aed5b3c3b115bfc3cb266eb21dd9",
    "customers.csv": "c9918a8eb42d23260d1036c822cd224bc6c69866784fc35f7112a841a1a95dad",
    "agents.csv": "3d13aebfd03e413e3d495547a187a90e555d6fd0b27919fd1a65acd840f66e30",
    "leads.csv": "c56b17571a16e9d1ea2f2b8892d9c50afc70107de9c4ee96c3b2df5179dc38fc",
    "policies.csv": "c51ce3d94081c101bed4432474dd751ca4df79fd41d9f337f7591f4630aa5c30",
    "premium_payments.csv": "8a87f156373e98d70f9e4ee33318773f420b960ca0354229ba2648d7f310930e",
    "policy_status_history.csv": "e442a07f120fe5f437f3c905f819cf5cf44449cf1492c03261bc221cbef98849",
    "sales_targets.csv": "51841b0e94b952eab65f6f194ad27517bdb1180048b4bf95116abb685e743cbf",
    "incentives.csv": "98f5dd465cdfea44dfa23682580a36426cf9f17fa9789867f82846d90c72a73e"
  },
  "postgresql_version": 170004
}
```
