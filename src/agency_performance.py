"""Validate the synthetic snapshot and export Phase 3 SQL results without Pandas metrics."""

from __future__ import annotations

import argparse
import json
import platform
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import psycopg
from psycopg import sql

from data_quality import read_database, reconcile, validate
from dataset import AS_OF, ROOT, connection_string, read_csvs, sha256, verify_manifest

VIEWS = (
    "monthly_trends",
    "performance",
    "agent_month",
    "target_distribution",
    "lead_funnel",
    "agent_activation",
    "activation_cohorts",
    "activation_summary",
    "concentration",
)

# Independent raw-fact reconciliation also catches production lost through eligibility joins.
RECONCILIATION_SQL = """
WITH raw AS (
    SELECT m.period_start, COUNT(p.policy_id)::numeric AS new_policies,
           COALESCE(SUM(p.annualized_premium),0) AS premium
    FROM agency_performance.periods m LEFT JOIN insurance_analytics.policies p
      ON p.issue_date >= m.period_start AND p.issue_date < m.period_end GROUP BY 1
), levels AS (
    SELECT period_start, grain, SUM(new_policies) AS new_policies,
           SUM(new_business_annualized_premium) AS premium
    FROM agency_performance.performance GROUP BY 1,2
    UNION ALL
    SELECT period_start, 'Agent', SUM(new_policies), SUM(new_business_annualized_premium)
    FROM agency_performance.agent_month GROUP BY 1
)
SELECT l.period_start, l.grain FROM levels l JOIN raw r USING (period_start)
WHERE l.new_policies <> r.new_policies OR l.premium <> r.premium
"""


def read_analysis(conn, data_dir: Path = ROOT / "data/raw"):
    """Caller owns a repeatable-read transaction; no metric calculations in Python."""
    provenance = verify_manifest(data_dir)
    frames = read_csvs(data_dir)
    loaded = read_database(conn)
    checks = validate(frames) + validate(loaded, scope="PostgreSQL") + reconcile(frames, loaded)
    if any(c.affected and c.severity == "ERROR" for c in checks):
        raise ValueError("Snapshot validation failed; run data_quality.py --database")
    snapshot = conn.execute("SELECT as_of FROM agency_performance.snapshot").fetchone()[0]
    if snapshot.isoformat() != AS_OF:
        raise ValueError("SQL snapshot differs from the dataset contract")
    if conn.execute(RECONCILIATION_SQL).fetchall():
        raise ValueError("Phase 3 production does not reconcile to raw policy facts")
    outputs = {}
    for view in VIEWS:
        cursor = conn.execute(
            sql.SQL("SELECT * FROM agency_performance.{} ORDER BY 1, 2, 3").format(
                sql.Identifier(view)
            )
        )
        outputs[view] = pd.DataFrame.from_records(
            cursor.fetchall(), columns=[column.name for column in cursor.description]
        )
    provenance.update(
        executed_at_utc=datetime.now(UTC).isoformat(),
        python_version=platform.python_version(),
        postgresql_version=conn.info.server_version,
        phase3_sql_sha256=sha256(ROOT / "sql/04_agency_performance.sql"),
        validation_checks=len(checks),
        validation_failures=0,
        production_reconciliation=(
            "PASS: raw policies / Agency / Region / Unit / Agent / Grade / Tenure"
        ),
        result_rows={name: len(frame) for name, frame in outputs.items()},
    )
    return outputs, provenance


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/processed/phase3")
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data/raw")
    args = parser.parse_args()
    try:
        with psycopg.connect(connection_string()) as conn:
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
            outputs, provenance = read_analysis(conn, args.data_dir)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for name, frame in outputs.items():
            frame.to_csv(args.output_dir / f"{name}.csv", index=False)
        provenance["output_sha256"] = {
            name: sha256(args.output_dir / f"{name}.csv") for name in outputs
        }
        (args.output_dir / "execution.json").write_text(
            json.dumps(provenance, indent=2) + "\n", encoding="utf-8"
        )
    except (ValueError, OSError, psycopg.Error) as exc:
        print(f"Analysis failed ({type(exc).__name__}); prior outputs do not establish success.")
        return 1
    print(f"Validated snapshot; exported {len(outputs)} SQL views to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
