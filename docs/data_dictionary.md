# Data Dictionary

This dictionary defines the first version of the synthetic life-insurance Agency analytics model.

## `customers`
| Field | Type | Nullable | Key | Meaning / analytical use |
|---|---|---:|---|---|
| customer_id | VARCHAR(20) | No | PK | Unique policyholder identifier |
| gender | VARCHAR(10) | Yes | | Customer segmentation |
| date_of_birth | DATE | No | | Age / life-stage analysis |
| marital_status | VARCHAR(20) | Yes | | Household segmentation |
| occupation | VARCHAR(80) | Yes | | Occupation / affordability proxy |
| district | VARCHAR(80) | Yes | | Geographic segmentation |
| region | VARCHAR(30) | Yes | | Regional analysis |
| income_band | VARCHAR(30) | Yes | | Affordability proxy |
| acquisition_channel | VARCHAR(30) | Yes | | Original customer source |
| created_date | DATE | No | | Customer onboarding date |

## `agency_units`
| Field | Type | Nullable | Key | Meaning / analytical use |
|---|---|---:|---|---|
| agency_unit_id | VARCHAR(20) | No | PK | Unique agency/unit |
| agency_name | VARCHAR(120) | No | | Management reporting unit |
| branch | VARCHAR(120) | No | | Branch/location label |
| district | VARCHAR(80) | Yes | | Location |
| region | VARCHAR(30) | Yes | | Region |
| manager_id | VARCHAR(20) | Yes | | Unit manager identifier |
| launch_date | DATE | No | | Unit tenure |
| status | VARCHAR(20) | No | | Active/inactive unit |

## `agents`
| Field | Type | Nullable | Key | Meaning / analytical use |
|---|---|---:|---|---|
| agent_id | VARCHAR(20) | No | PK | Unique agent |
| agency_unit_id | VARCHAR(20) | No | FK | Links agent to agency unit |
| gender | VARCHAR(10) | Yes | | Workforce segmentation |
| join_date | DATE | No | | Recruitment cohort / tenure |
| status | VARCHAR(20) | No | | Active, inactive or exited |
| experience_years | NUMERIC | Yes | | Experience measure |
| agent_grade | VARCHAR(20) | Yes | | Trainee to Elite classification |
| supervisor_id | VARCHAR(20) | Yes | | Reporting relationship |
| exit_date | DATE | Yes | | Attrition analysis |

## `leads`
| Field | Type | Nullable | Key | Meaning / analytical use |
|---|---|---:|---|---|
| lead_id | VARCHAR(20) | No | PK | Unique prospect |
| agent_id | VARCHAR(20) | No | FK | Assigned agent |
| customer_id | VARCHAR(20) | Yes | FK | Populated if linked to known customer |
| lead_date | DATE | No | | Funnel timing |
| source | VARCHAR(30) | Yes | | Referral, digital, event, walk-in etc. |
| contact_status | VARCHAR(20) | Yes | | Contact activity |
| appointment_status | VARCHAR(20) | Yes | | Appointment stage |
| application_status | VARCHAR(20) | Yes | | Application outcome |
| converted | BOOLEAN | No | | Whether lead became issued business |
| conversion_date | DATE | Yes | | Conversion timing |

## `policies`
| Field | Type | Nullable | Key | Meaning / analytical use |
|---|---|---:|---|---|
| policy_id | VARCHAR(20) | No | PK | Unique insurance policy |
| customer_id | VARCHAR(20) | No | FK | Policyholder |
| agent_id | VARCHAR(20) | No | FK | Selling agent |
| product_name | VARCHAR(60) | No | | Product category |
| distribution_channel | VARCHAR(20) | No | | Fixed to Agency for this project |
| issue_date | DATE | No | | New-business timing |
| policy_term_years | INTEGER | No | | Contract duration |
| payment_frequency | VARCHAR(20) | No | | Monthly / quarterly / etc. |
| premium_amount | NUMERIC | No | | Scheduled installment |
| annualized_premium | NUMERIC | No | | Comparable annual premium value |
| sum_assured | NUMERIC | No | | Coverage amount |
| maturity_date | DATE | No | | Contract maturity |
| policy_status | VARCHAR(20) | No | | Current policy state |
| lapse_date | DATE | Yes | | Lapse timing |
| surrender_date | DATE | Yes | | Surrender timing |

## `premium_payments`
| Field | Type | Nullable | Key | Meaning / analytical use |
|---|---|---:|---|---|
| payment_id | VARCHAR(24) | No | PK | Unique premium installment |
| policy_id | VARCHAR(20) | No | FK | Associated policy |
| due_date | DATE | No | | Expected date |
| payment_date | DATE | Yes | | Actual date |
| amount_due | NUMERIC | No | | Expected installment amount |
| amount_paid | NUMERIC | No | | Actual amount received |
| payment_status | VARCHAR(20) | No | | Paid / Late / Missed / Partial |
| payment_method | VARCHAR(30) | Yes | | Mobile Money / Bank / Card / Payroll |

## `policy_status_history`
| Field | Type | Nullable | Key | Meaning / analytical use |
|---|---|---:|---|---|
| status_history_id | VARCHAR(24) | No | PK | Unique status event |
| policy_id | VARCHAR(20) | No | FK | Associated policy |
| status | VARCHAR(20) | No | | Active / Grace / Lapsed / Reinstated / etc. |
| status_date | DATE | No | | Event date |
| reason | VARCHAR(120) | Yes | | Reason / context |

## `sales_targets`
| Field | Type | Nullable | Key | Meaning / analytical use |
|---|---|---:|---|---|
| target_id | VARCHAR(24) | No | PK | Unique monthly target |
| agent_id | VARCHAR(20) | No | FK | Agent |
| target_month | DATE | No | | Month |
| policy_target | INTEGER | No | | Target number of policies |
| premium_target | NUMERIC | No | | Target annualized premium |
| new_customer_target | INTEGER | No | | Target customer acquisition |

## `incentives`
| Field | Type | Nullable | Key | Meaning / analytical use |
|---|---|---:|---|---|
| incentive_id | VARCHAR(24) | No | PK | Unique agent-campaign record |
| agent_id | VARCHAR(20) | No | FK | Agent |
| campaign_name | VARCHAR(100) | No | | Incentive campaign |
| start_date | DATE | No | | Campaign start |
| end_date | DATE | No | | Campaign end |
| threshold | NUMERIC | Yes | | Qualification threshold |
| incentive_amount | NUMERIC | No | | Potential / earned amount |
| qualified | BOOLEAN | No | | Qualification flag |

## KPI definitions used in v1
- **Target Achievement %** = Actual Annualized Premium / Premium Target × 100
- **Lead Conversion %** = Converted Leads / Eligible Leads × 100
- **Active Agent Ratio** = Active Producing Agents / Registered Agents × 100
- **Lapse Rate** = Lapsed Eligible Policies / Eligible Policies × 100
- **Persistency** = Eligible policies remaining in force at the observation point / eligible policies × 100

Persistency definitions will be made explicit in the analysis notebook because real insurers may use policy-count or premium-based methods and different rules for reinstatements, cancellations and observation dates.
