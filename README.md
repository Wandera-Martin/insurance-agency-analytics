# Life Insurance Agency Performance & Persistency Analytics

## Project question
**How can a life insurer use agency sales, policy and premium data to improve agent productivity, policy persistency and customer retention?**

This portfolio project simulates the analytical environment of a life-insurance Agency distribution function. It combines relational data modelling, synthetic data generation, SQL, Python/Pandas, data-quality checks, KPI design, persistency analysis, retention analytics and Power BI reporting.

## Business areas covered
- Agency sales performance
- Agent productivity and activation
- Lead conversion funnels
- Premium production and collections
- Policy lapse and persistency
- Incentive effectiveness
- Customer retention and lapse-risk analysis

## Repository structure
```text
insurance-agency-analytics/
├── data/
│   ├── raw/                 # generated source datasets
│   └── processed/           # analysis-ready outputs
├── docs/
│   ├── data_dictionary.md
│   └── synthetic_data_rules.md
├── sql/
│   ├── 01_schema.sql
│   └── 02_quality_checks.sql
├── src/
│   └── generate_synthetic_data.py
├── notebooks/
│   └── 01_agency_overview.ipynb
├── powerbi/
│   └── README.md
├── requirements.txt
└── README.md
```

## Core KPIs
- New Policies
- Annualized Premium
- Active Agents
- Policies per Agent
- Target Achievement %
- Lead Conversion %
- Lapse Rate
- 3-, 6- and 13-Month Persistency
- Agent Quality vs Volume

## Important note
All data in this repository is synthetic and created for learning and portfolio purposes. It does not contain real customer, agent or proprietary company information.

## Current build status
- [x] Business framing
- [x] Relational data model
- [x] PostgreSQL schema
- [x] Data dictionary
- [x] Synthetic data rules
- [x] Synthetic data generator
- [x] Initial dataset
- [x] Data-quality checks
- [x] Starter agency overview notebook
- [ ] Persistency cohort analysis
- [ ] Incentive effectiveness analysis
- [ ] Lapse-risk model
- [ ] Power BI dashboard
