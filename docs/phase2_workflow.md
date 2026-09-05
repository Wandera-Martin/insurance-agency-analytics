# Phase 2 — PostgreSQL loading and validation

## Why this phase exists

Agency analysis joins production (policies), collections (installments), people
(agents/customers) and objectives (targets). A missing parent can lose policies in
a join; duplicate installments can inflate collections. Validate these foundations
before interpreting productivity, persistency or incentive outcomes.

All inputs come from the seeded synthetic generator. No customer exports or real
insurance records are used. The manifest records the snapshot, seed, generator
hash and nine CSV hashes; it is a reproducibility check, not a cryptographic proof
of origin for arbitrary user-provided data.

## Reproduce from a clean clone

Use Python 3.11 and PostgreSQL 17. Run commands from the repository root.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-phase2.txt
python src/generate_synthetic_data.py
python src/data_quality.py --report data/processed/source_quality_report.md
```

Start a dedicated PostgreSQL database using the provided Compose file:

```powershell
$env:POSTGRES_PASSWORD = Read-Host 'Choose a local synthetic database password'
docker compose up -d --wait
$env:PGPASSWORD = $env:POSTGRES_PASSWORD
$env:DATABASE_URL = 'host=127.0.0.1 port=55432 dbname=insurance_agency_analytics user=agency'
python src/load_postgres.py
python src/data_quality.py --database
psql -X -v ON_ERROR_STOP=1 -f sql/02_quality_checks.sql $env:DATABASE_URL
psql -X -v ON_ERROR_STOP=1 -f sql/03_data_understanding.sql $env:DATABASE_URL
```

On Bash, use `python3 -m venv .venv`, `source .venv/bin/activate`, `export` for
the same environment variables, and pass `"$DATABASE_URL"` to psql. `psql` must
be installed locally for the SQL commands. With an existing PostgreSQL installation,
create a dedicated empty database and set DATABASE_URL/PGPASSWORD to that database;
Compose is optional. Passwords stay outside tracked files and reports.

The loader creates the schema when all nine tables are absent. Do not manually
run schema SQL on a populated database. An incomplete or extra-table schema is
rejected. `01_schema.sql` now creates objects without dropping existing tables.

For an intentional replacement of an already loaded synthetic snapshot:

```powershell
python src/load_postgres.py --replace
```

This explicitly replaces rows in the nine named tables in one transaction. It
does not drop tables or cascade into unrelated objects. Plain reruns refuse to
append. A constraint, validation, reconciliation or commit failure rolls back the
load, including replacement. Reports represent a particular run; a failed later
command never establishes readiness even if an older PASS report remains.

## Loading: business reason and technical behaviour

The dependency order is `agency_units → customers → agents → leads → policies →
premium_payments → policy_status_history → sales_targets → incentives`. The first
two are independent. Customers must precede leads/policies; agents must precede
sales records, targets and incentives; policies must precede installments/events.
`manager_id` and `supervisor_id` are external synthetic labels with no parent table.

`load_postgres.py` validates the CSVs and their hashes, obtains a transaction lock,
uses client-side COPY with explicit column names, validates the database snapshot,
and compares every value by primary key. CSV blanks become SQL NULL; booleans and
dates are interpreted by PostgreSQL's typed columns. The loader then commits and
writes the report. A PASS establishes a complete, reconciled snapshot, not good
commercial performance. Access-exclusive table locks block concurrent readers
during replacement, appropriate for this local learning dataset.

The executable Python contract in `src/dataset_contract.json` mirrors the SQL
columns, nullability, categories and foreign keys. PostgreSQL remains the authority
for its CHECK constraints and numeric precision. Changes to the data model should
update both; integration tests compare the contract to the created database.

## Validation: fields and interpretation

`data_quality.py` checks every dataset for nonempty input, duplicate rows/keys,
required fields, types, permitted categories and all defined foreign keys. It also
checks agent recruitment/exit, customer onboarding, lead conversion, policy dates,
premium annualization, installment settlement, status history, monthly target
grain and campaign participation dates. See the generated report for each rule,
affected count and up to five synthetic IDs. A record may fail multiple rules.

Financial checks prevent annualized premium being confused with cash received.
Chronology checks prevent sales being attributed to an agent before recruitment
or after exit. Status checks support later cohort analysis without calculating
persistency prematurely. Zero affected rows means that specific rule passed.
Documented modelling limitations remain even when every implemented check passes.

The CLI exits 0 on success, 1 for quality/load failure, and 2 when standalone
validation cannot run (or a committed load cannot write its report). The standalone
database validator uses a read-only repeatable snapshot. CSV-only success explicitly
does not claim PostgreSQL readiness. Reports include hashes and PostgreSQL version.

## SQL understanding and next-phase boundary

`02_quality_checks.sql` extends diagnostics to all keys and relationships; empty anomaly
result sets mean no exceptions to those queries. Python provides the broader
blocking gate. `03_data_understanding.sql` describes grains, observed dates,
category distributions, premium ranges and incomplete reporting periods. Read
each result at its stated grain; do not add policy and installment row counts or
sum policy premiums after a one-to-many payment join.

These are executed data profiles, not inferred agent rankings or causal findings.
Phase 3 must define eligible cohorts, complete months and metric denominators
before calculating Agency performance. Power BI and machine learning remain later
phases.

## Engineering checks

```powershell
python -m ruff check .
python -m ruff format --check .
python -m pytest -q
```

Integration tests require `TEST_DATABASE_URL` pointing to a dedicated disposable
database with no `insurance_analytics` schema. They do not use DATABASE_URL and
roll their changes back. Without TEST_DATABASE_URL those tests are explicitly
skipped; this is not evidence of a PostgreSQL test pass.

COPY and transaction behaviour follow the official
[Psycopg COPY documentation](https://www.psycopg.org/psycopg3/docs/basic/copy.html)
and [transaction documentation](https://www.psycopg.org/psycopg3/docs/basic/transactions.html).

See [local execution evidence](phase2_verification.md) and the saved
[data understanding output](data_understanding_output.txt) for the completed run.
