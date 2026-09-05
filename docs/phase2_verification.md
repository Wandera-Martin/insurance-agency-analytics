# Phase 2 execution evidence

Executed locally with Python 3.11.9, the pinned Phase 2 Python requirements and
PostgreSQL 17.4. The supplied Compose/CI configuration targets PostgreSQL 17.6;
Docker was unavailable in this session, so those configurations were not executed.
The GitHub Actions workflow will run when the changes are pushed.

| Verification | Observed result |
|---|---|
| Full generator run | All nine synthetic CSVs created |
| Repeat generation | All nine CSV SHA-256 hashes identical |
| First PostgreSQL load | Nine tables committed |
| Full snapshot replacement | Nine tables replaced and committed |
| Source and PostgreSQL validation | 262 rules per source, zero failures |
| CSV/PostgreSQL reconciliation | Nine row-count and nine value checks passed |
| SQL diagnostics | 26 anomaly queries returned zero rows |
| Data understanding SQL | Executed; saved in `data_understanding_output.txt` |
| Pytest | 29 passed, including two real PostgreSQL integration tests |
| Ruff lint and format | Passed without suppressions |

The integration tests verify dependency ordering, schema-column/nullability
agreement, refusal of ordinary reruns, successful replacement, and preservation
of existing rows when the last table's COPY fails. Other tests inject bad keys,
dates, booleans, premiums, categories, duplicates, empty inputs, stale hashes and
same-count value mismatches. Integration changes are rolled back in a separate
disposable database.

The [generated report](data_quality_report.md) contains the measured counts,
run timestamp, source hashes and database version. It evaluates 542 checks in
total: 262 CSV checks, 262 PostgreSQL checks and 18 reconciliation checks.
Read its limitations before Agency performance analysis. Baseline corrections
are documented separately in [phase2_baseline.md](phase2_baseline.md).
