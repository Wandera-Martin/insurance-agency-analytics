-- Life Insurance Agency Performance & Persistency Analytics
-- PostgreSQL schema

CREATE SCHEMA IF NOT EXISTS insurance_analytics;
SET search_path TO insurance_analytics;

DROP TABLE IF EXISTS incentives CASCADE;
DROP TABLE IF EXISTS sales_targets CASCADE;
DROP TABLE IF EXISTS policy_status_history CASCADE;
DROP TABLE IF EXISTS premium_payments CASCADE;
DROP TABLE IF EXISTS policies CASCADE;
DROP TABLE IF EXISTS leads CASCADE;
DROP TABLE IF EXISTS agents CASCADE;
DROP TABLE IF EXISTS agency_units CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

CREATE TABLE customers (
    customer_id VARCHAR(20) PRIMARY KEY,
    gender VARCHAR(10) CHECK (gender IN ('Male','Female')),
    date_of_birth DATE NOT NULL,
    marital_status VARCHAR(20),
    occupation VARCHAR(80),
    district VARCHAR(80),
    region VARCHAR(30),
    income_band VARCHAR(30),
    acquisition_channel VARCHAR(30),
    created_date DATE NOT NULL
);

CREATE TABLE agency_units (
    agency_unit_id VARCHAR(20) PRIMARY KEY,
    agency_name VARCHAR(120) NOT NULL,
    branch VARCHAR(120) NOT NULL,
    district VARCHAR(80),
    region VARCHAR(30),
    manager_id VARCHAR(20),
    launch_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('Active','Inactive'))
);

CREATE TABLE agents (
    agent_id VARCHAR(20) PRIMARY KEY,
    agency_unit_id VARCHAR(20) NOT NULL REFERENCES agency_units(agency_unit_id),
    gender VARCHAR(10) CHECK (gender IN ('Male','Female')),
    join_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('Active','Inactive','Exited')),
    experience_years NUMERIC(5,2) DEFAULT 0,
    agent_grade VARCHAR(20) CHECK (agent_grade IN ('Trainee','Junior','Standard','Senior','Elite')),
    supervisor_id VARCHAR(20),
    exit_date DATE,
    CHECK ((status <> 'Exited') OR exit_date IS NOT NULL)
);

CREATE TABLE leads (
    lead_id VARCHAR(20) PRIMARY KEY,
    agent_id VARCHAR(20) NOT NULL REFERENCES agents(agent_id),
    customer_id VARCHAR(20) REFERENCES customers(customer_id),
    lead_date DATE NOT NULL,
    source VARCHAR(30),
    contact_status VARCHAR(20) CHECK (contact_status IN ('Uncontacted','Contacted')),
    appointment_status VARCHAR(20) CHECK (appointment_status IN ('None','Booked','Completed','No Show')),
    application_status VARCHAR(20) CHECK (application_status IN ('None','Submitted','Approved','Declined','Withdrawn')),
    converted BOOLEAN NOT NULL DEFAULT FALSE,
    conversion_date DATE
);

CREATE TABLE policies (
    policy_id VARCHAR(20) PRIMARY KEY,
    customer_id VARCHAR(20) NOT NULL REFERENCES customers(customer_id),
    agent_id VARCHAR(20) NOT NULL REFERENCES agents(agent_id),
    product_name VARCHAR(60) NOT NULL,
    distribution_channel VARCHAR(20) NOT NULL DEFAULT 'Agency',
    issue_date DATE NOT NULL,
    policy_term_years INTEGER NOT NULL CHECK (policy_term_years > 0),
    payment_frequency VARCHAR(20) NOT NULL CHECK (payment_frequency IN ('Monthly','Quarterly','Semi-Annual','Annual')),
    premium_amount NUMERIC(14,2) NOT NULL CHECK (premium_amount > 0),
    annualized_premium NUMERIC(14,2) NOT NULL CHECK (annualized_premium > 0),
    sum_assured NUMERIC(16,2) NOT NULL CHECK (sum_assured > 0),
    maturity_date DATE NOT NULL,
    policy_status VARCHAR(20) NOT NULL CHECK (policy_status IN ('Active','Grace','Lapsed','Surrendered','Matured','Cancelled')),
    lapse_date DATE,
    surrender_date DATE
);

CREATE TABLE premium_payments (
    payment_id VARCHAR(24) PRIMARY KEY,
    policy_id VARCHAR(20) NOT NULL REFERENCES policies(policy_id),
    due_date DATE NOT NULL,
    payment_date DATE,
    amount_due NUMERIC(14,2) NOT NULL CHECK (amount_due > 0),
    amount_paid NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (amount_paid >= 0),
    payment_status VARCHAR(20) NOT NULL CHECK (payment_status IN ('Paid','Late','Missed','Partial')),
    payment_method VARCHAR(30)
);

CREATE TABLE policy_status_history (
    status_history_id VARCHAR(24) PRIMARY KEY,
    policy_id VARCHAR(20) NOT NULL REFERENCES policies(policy_id),
    status VARCHAR(20) NOT NULL CHECK (status IN ('Active','Grace','Lapsed','Reinstated','Surrendered','Matured','Cancelled')),
    status_date DATE NOT NULL,
    reason VARCHAR(120)
);

CREATE TABLE sales_targets (
    target_id VARCHAR(24) PRIMARY KEY,
    agent_id VARCHAR(20) NOT NULL REFERENCES agents(agent_id),
    target_month DATE NOT NULL,
    policy_target INTEGER NOT NULL CHECK (policy_target >= 0),
    premium_target NUMERIC(14,2) NOT NULL CHECK (premium_target >= 0),
    new_customer_target INTEGER NOT NULL CHECK (new_customer_target >= 0),
    UNIQUE (agent_id, target_month)
);

CREATE TABLE incentives (
    incentive_id VARCHAR(24) PRIMARY KEY,
    agent_id VARCHAR(20) NOT NULL REFERENCES agents(agent_id),
    campaign_name VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    threshold NUMERIC(14,2),
    incentive_amount NUMERIC(14,2) NOT NULL DEFAULT 0,
    qualified BOOLEAN NOT NULL DEFAULT FALSE,
    CHECK (end_date >= start_date)
);

CREATE INDEX idx_agents_unit ON agents(agency_unit_id);
CREATE INDEX idx_leads_agent_date ON leads(agent_id, lead_date);
CREATE INDEX idx_policies_agent_issue ON policies(agent_id, issue_date);
CREATE INDEX idx_policies_status ON policies(policy_status);
CREATE INDEX idx_payments_policy_due ON premium_payments(policy_id, due_date);
CREATE INDEX idx_status_policy_date ON policy_status_history(policy_id, status_date);
CREATE INDEX idx_targets_agent_month ON sales_targets(agent_id, target_month);
