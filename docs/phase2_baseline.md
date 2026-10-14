# Baseline generator validation

Measured against generator commit `da2d12f`, seed 42, snapshot 2026-09-01,
before Phase 2 chronology corrections. Rule counts overlap; do not sum them
as a distinct-record count. These are data defects, not business findings.

| Table | Rule | Affected |
|---|---|---:|
| premium_payments | payment_date: within snapshot | 2,524 |
| agents | join on/after unit launch | 12 |
| policies | issue_date: within agent service | 1,557 |
| leads | lead_date: within agent service | 2,962 |
| leads | conversion_date: within agent service | 729 |
| policies | issue on/after customer onboarding | 9,719 |
| leads | conversion on/after customer onboarding | 4,315 |
| leads | converted lead contacted | 1,632 |
| incentives | campaign overlaps agent service | 68 |

The final report is generated from the corrected CSVs and PostgreSQL values.
Corrections change the random sequence and portfolio counts; no original rows
were silently dropped by the loader. To reproduce the baseline, generate data
from the stated original commit and run the Phase 2 `validate(read_csvs(path))`
API against it. The original generator did not write a manifest, so the current
manifest-enforcing CLI intentionally rejects that baseline as a load source.
