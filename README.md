# Life Insurance Agency Performance & Persistency Analytics

> A business-focused analytics project exploring how a life insurer can use agency sales, policy, premium-payment and customer data to improve **agent productivity, policy persistency and customer retention**.

---

## Project Overview

Life insurers do not only need agents who sell more policies. They need agents who produce **sustainable business** — policies that remain active, generate premium income and continue delivering value over time.

This project simulates the analytical environment of a life-insurance Agency distribution function and answers one central question:

> **How can a life insurer use agency sales, policy and premium data to improve agent productivity, policy persistency and customer retention?**

The project combines relational data modelling, synthetic insurance data generation, PostgreSQL and SQL, Python/Pandas, data-quality validation, Agency KPI analysis, policy lapse and persistency analysis, retention analytics, incentive-effectiveness analysis, Power BI reporting, and predictive lapse-risk modelling.

All data in this repository is **synthetic** and created for learning and portfolio purposes.

---

## Business Context

An Agency distribution model relies on insurance agents to acquire customers and generate new business.

However, evaluating agents only by the number of policies sold can be misleading.

An agent may sell many policies while also producing business that lapses quickly. Another agent may sell fewer policies but retain a much larger proportion of those customers.

This creates two equally important dimensions of Agency performance:

### 1. Production

How much new business is being generated?

- Policies issued
- Annualized premium
- Target achievement
- Lead conversion
- Active-agent productivity

### 2. Business Quality

How sustainable is the business after it is sold?

- Policy persistency
- Lapse rate
- Premium-payment behaviour
- Customer retention
- Reinstatements
- Early-warning payment patterns

A strong Agency analytics function should evaluate **both**.

---

## Core Business Questions

The project is designed to answer questions such as:

1. Which agents and agency units produce the most new business?
2. Which agents consistently achieve their sales targets?
3. Which agency units are driving or dragging overall performance?
4. Are high-selling agents also producing persistent business?
5. Which products and customer segments experience higher lapse rates?
6. Which premium-payment behaviours appear before a policy lapses?
7. Which active policies appear most at risk of future lapse?
8. Do incentive campaigns improve sustainable business or only short-term sales volume?
9. Are newly recruited agents becoming productive?
10. Where should Agency management intervene?

---

## Insurance Concepts Used

### Policy

The insurance contract between the insurer and the policyholder.

### Premium

The amount paid by the policyholder to maintain insurance coverage.

### Annualized Premium

A standardized annual premium value that makes policies with different payment frequencies easier to compare.

```text
UGX 100,000 monthly
× 12 months
= UGX 1,200,000 annualized premium
```

### Policy Lapse

A policy that is no longer in force, commonly because required premiums were not maintained, subject to the policy terms.

### Persistency

A measure of how much previously written insurance business remains in force after a defined period.

```text
100 eligible policies
82 remain in force

Persistency = 82 / 100 × 100
            = 82%
```

Persistency helps measure the **quality and sustainability** of new business.

---

## Synthetic Dataset

The project generates a realistic synthetic life-insurance portfolio.

| Dataset | Approx. Records |
|---|---:|
| Agency Units | 12 |
| Agents | 400 |
| Customers | 25,000 |
| Leads | 70,000 |
| Policies | 35,000 |
| Premium Payments | 400,000+ |
| Policy Status Events | 39,000+ |
| Sales Targets | 6,000+ |
| Incentive Records | 750 |

The synthetic data contains structured business behaviour rather than purely random records.

### Agent Performance Profiles

- **Star** — high conversion, strong production and stronger persistency
- **High-volume risk** — strong production but weaker persistency
- **Steady** — moderate production and healthy persistency
- **Developing** — lower conversion and lower production
- **Inactive-risk** — low current activity and higher inactivity risk

These profiles create realistic analytical differences across Agency performance.

---

## Data Model

```text
agency_units
     │
     └── agents
           │
           ├── leads
           │
           ├── policies ───── customers
           │      │
           │      ├── premium_payments
           │      │
           │      └── policy_status_history
           │
           ├── sales_targets
           │
           └── incentives
```

### Core Tables

| Table | Purpose |
|---|---|
| `customers` | Customer demographics and segmentation attributes |
| `agency_units` | Agency structure, location and management units |
| `agents` | Agent profile, tenure, grade and status |
| `leads` | Sales-funnel activity from lead creation to conversion |
| `policies` | Core insurance contract and premium information |
| `premium_payments` | Premium due dates, payments and payment behaviour |
| `policy_status_history` | Policy lifecycle changes over time |
| `sales_targets` | Monthly policy and premium targets |
| `incentives` | Agent incentive campaigns and qualification |

---

## Technology Stack

### Database & Querying
- PostgreSQL
- SQL

### Data Analysis
- Python
- Pandas
- NumPy
- Jupyter Notebook

### Data Quality
- SQL validation queries
- Python-based validation

### Visualization
- Power BI
- Matplotlib

### Predictive Analytics
- Scikit-learn

### Version Control
- Git
- GitHub

---

## Core KPIs

### Agency Performance
- New Policies
- Annualized Premium
- Active Agents
- Policies per Active Agent
- Target Achievement %
- Lead Conversion %
- Month-on-Month Growth

### Policy Quality
- Active Policies
- Lapsed Policies
- Lapse Rate
- 3-Month Persistency
- 6-Month Persistency
- 13-Month Persistency

### Agent Quality
- Policies Sold
- Annualized Premium
- Target Achievement
- Lead Conversion
- Persistency
- Lapse Rate

---

## KPI Definitions

### Target Achievement %

```text
Actual Production
----------------- × 100
Sales Target
```

### Lead Conversion %

```text
Converted Leads
--------------- × 100
Eligible Leads
```

### Active Agent Ratio

```text
Active Producing Agents
----------------------- × 100
Registered Agents
```

### Lapse Rate

```text
Lapsed Eligible Policies
------------------------ × 100
Eligible Policies
```

### Persistency

```text
Eligible Policies Remaining In Force
------------------------------------ × 100
Eligible Policies
```

> Persistency methodology can vary between insurers. This project explicitly documents its eligibility rules, observation periods and treatment of policy statuses during analysis.

---

## Analytical Workflow

```text
Business Question
        ↓
Data Requirements
        ↓
Data Validation
        ↓
SQL / Python Analysis
        ↓
Business Diagnosis
        ↓
Visualization
        ↓
Management Recommendation
```

The goal is not simply to create charts.

The goal is to convert insurance data into **management decisions**.

---

## Planned Analysis

### 1. Agency Performance Analysis
Measure:
- Policies issued
- Annualized premium
- Active agents
- Policies per agent
- Target achievement
- Performance by region and Agency unit

### 2. Agent Sales Funnel

```text
Lead
  ↓
Contact
  ↓
Appointment
  ↓
Application
  ↓
Policy Issued
```

Measure conversion at every stage.

### 3. Persistency Analysis
Compare policy retention by:
- Agent
- Agency unit
- Product
- Customer segment
- Payment frequency
- Policy cohort

with emphasis on:
- 3-month persistency
- 6-month persistency
- 13-month persistency

### 4. Agent Quality vs Volume

| | High Persistency | Low Persistency |
|---|---|---|
| **High Sales** | Star Agents | High-Volume Risk |
| **Low Sales** | Development Opportunity | Intervention Required |

### 5. Incentive Effectiveness

```text
Before Incentive
      ↓
During Incentive
      ↓
After Incentive
```

Evaluate both sales uplift and subsequent persistency.

### 6. Lapse-Risk Analysis

Potential risk signals include:
- Missed premiums
- Late payments
- Policy tenure
- Payment frequency
- Product type
- Agent historical persistency

A simple predictive model will be developed to support retention prioritization.

---

## Planned Power BI Dashboard

### 1. Executive Overview
- New Policies
- Annualized Premium
- Active Agents
- Target Achievement
- Persistency
- Lapse Rate
- Monthly Trends

### 2. Agency Performance
- Agency-unit performance
- Agent ranking
- Target vs Actual
- Sales funnel
- Productivity trends
- Quality vs Volume segmentation

### 3. Persistency & Retention
- 3-, 6- and 13-month persistency
- Lapse trends
- Persistency by product
- Persistency by agent
- High-risk policy segments

### 4. Agent Intelligence
- Individual agent scorecard
- Policy production
- Premium production
- Conversion
- Persistency
- Target achievement
- Incentive participation

---

## Repository Structure

```text
insurance-agency-analytics/
│
├── data/
│   ├── raw/
│   └── processed/
│
├── docs/
│   ├── data_dictionary.md
│   └── synthetic_data_rules.md
│
├── sql/
│   ├── 01_schema.sql
│   └── 02_quality_checks.sql
│
├── src/
│   └── generate_synthetic_data.py
│
├── notebooks/
│   └── 01_agency_overview.ipynb
│
├── powerbi/
│   └── README.md
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Wandera-Martin/insurance-agency-analytics.git
cd insurance-agency-analytics
```

### 2. Create a virtual environment

#### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Generate the synthetic dataset

```bash
python src/generate_synthetic_data.py
```

This creates the source CSV datasets inside:

```text
data/raw/
```

### 5. Create the PostgreSQL database

```sql
CREATE DATABASE insurance_agency_analytics;
```

Then run:

```text
sql/01_schema.sql
```

### 6. Load the generated CSV files

Load the nine generated datasets into their corresponding PostgreSQL tables.

### 7. Run data-quality checks

Execute:

```text
sql/02_quality_checks.sql
```

The checks validate:
- Duplicate primary keys
- Broken relationships
- Impossible dates
- Invalid premium values
- Annualized-premium consistency
- Payment anomalies
- Policy-status consistency
- Lead-conversion consistency
- Agent-exit consistency

### 8. Begin analysis

Start with:

```text
notebooks/01_agency_overview.ipynb
```

---

## Current Build Status

### Completed
- [x] Insurance business framing
- [x] Agency analytics problem definition
- [x] Relational insurance data model
- [x] PostgreSQL schema
- [x] Data dictionary
- [x] Synthetic-data rules
- [x] Synthetic dataset generator
- [x] Initial synthetic insurance portfolio
- [x] Data-quality SQL checks
- [x] Starter Agency overview notebook

### In Development
- [ ] PostgreSQL data loading workflow
- [ ] Agency performance analysis
- [ ] Target-performance analysis
- [ ] Persistency cohort analysis
- [ ] Agent quality vs volume segmentation
- [ ] Incentive-effectiveness analysis
- [ ] Lapse-risk modelling
- [ ] Power BI management dashboard

---

## Learning Objective

This project is designed as both a portfolio project and a practical introduction to life-insurance Agency analytics.

Each phase follows this learning process:

```text
Business Question
      ↓
Insurance Concept
      ↓
Required Data
      ↓
Code / SQL
      ↓
Technical Explanation
      ↓
Output
      ↓
Business Interpretation
      ↓
Management Action
```

The purpose is to understand not only **how** the analysis works, but **why the business needs it**.

---

## Data Privacy & Ethics

All data in this repository is synthetic.

The project contains:
- No real customers
- No real insurance agents
- No proprietary insurer information
- No personally identifiable information
- No confidential policy information

The dataset exists solely for learning, analytical experimentation and portfolio demonstration.

---

## Project Roadmap

```text
Phase 1
Business Understanding + Data Model
            ✓

Phase 2
Database Loading + Data Quality
            ↓

Phase 3
Agency Performance Analytics
            ↓

Phase 4
Persistency + Retention Analytics
            ↓

Phase 5
Agent Segmentation + Incentive Analysis
            ↓

Phase 6
Lapse-Risk Modelling
            ↓

Phase 7
Power BI Management Dashboard
            ↓

Phase 8
Final Case Study + Management Recommendations
```

---

## Final Project Goal

By completion, the project should demonstrate an end-to-end analytical workflow capable of answering:

> **Who is producing the strongest insurance business, how sustainable is that business, what is driving policy lapse, and where should Agency management intervene?**

---

## Author

**Martin Wandera**

Data Analytics · Data Quality · Data Engineering · Business Intelligence

GitHub: [Wandera-Martin](https://github.com/Wandera-Martin)
