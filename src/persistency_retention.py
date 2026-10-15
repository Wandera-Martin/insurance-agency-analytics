"""Validate the snapshot and export Phase 4 SQL results without Pandas metrics."""

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
    "overall_persistency",
    "cohort_persistency",
    "hierarchy_persistency",
    "product_persistency",
    "payment_frequency_persistency",
    "customer_segment_persistency",
    "lapse_timing",
    "payment_behavior_summary",
    "policy_persistency",
    "payment_behavior",
)

RECONCILIATION_SQL = """
WITH expected AS (
    SELECT milestone_months, SUM(eligible_policies) AS eligible,
           SUM(persistent_policies) AS persistent,
           SUM(eligible_annualized_premium) AS eligible_premium,
           SUM(persistent_annualized_premium) AS persistent_premium
    FROM persistency_analytics.persistency_facts GROUP BY milestone_months
), comparable AS (
    SELECT milestone_months, 'overall' AS source, eligible_policies AS eligible,
           persistent_policies AS persistent,
           eligible_annualized_premium AS eligible_premium,
           persistent_annualized_premium AS persistent_premium
    FROM persistency_analytics.overall_persistency
    UNION ALL
    SELECT milestone_months, 'cohort', SUM(eligible_policies), SUM(persistent_policies),
           SUM(eligible_annualized_premium), SUM(persistent_annualized_premium)
    FROM persistency_analytics.cohort_persistency GROUP BY milestone_months
    UNION ALL
    SELECT milestone_months, 'product', SUM(eligible_policies), SUM(persistent_policies),
           SUM(eligible_annualized_premium), SUM(persistent_annualized_premium)
    FROM persistency_analytics.product_persistency GROUP BY milestone_months
    UNION ALL
    SELECT milestone_months, 'frequency', SUM(eligible_policies), SUM(persistent_policies),
           SUM(eligible_annualized_premium), SUM(persistent_annualized_premium)
    FROM persistency_analytics.payment_frequency_persistency GROUP BY milestone_months
    UNION ALL
    SELECT milestone_months, 'hierarchy-' || grain, SUM(eligible_policies),
           SUM(persistent_policies), SUM(eligible_annualized_premium),
           SUM(persistent_annualized_premium)
    FROM persistency_analytics.hierarchy_persistency GROUP BY milestone_months, grain
    UNION ALL
    SELECT milestone_months, 'segment-' || segment_type, SUM(eligible_policies),
           SUM(persistent_policies), SUM(eligible_annualized_premium),
           SUM(persistent_annualized_premium)
    FROM persistency_analytics.customer_segment_persistency
    GROUP BY milestone_months, segment_type
)
SELECT c.milestone_months, c.source
FROM comparable c JOIN expected e USING (milestone_months)
WHERE (c.eligible, c.persistent, c.eligible_premium, c.persistent_premium)
   IS DISTINCT FROM (e.eligible, e.persistent, e.eligible_premium, e.persistent_premium)
"""


def read_analysis(conn, data_dir: Path = ROOT / "data/raw"):
    """Caller owns a repeatable-read transaction; SQL remains the metric authority."""
    provenance = verify_manifest(data_dir)
    frames = read_csvs(data_dir)
    loaded = read_database(conn)
    checks = validate(frames) + validate(loaded, scope="PostgreSQL") + reconcile(frames, loaded)
    if any(check.affected and check.severity == "ERROR" for check in checks):
        raise ValueError("Snapshot validation failed; run data_quality.py --database")
    snapshot = conn.execute("SELECT as_of FROM persistency_analytics.snapshot").fetchone()[0]
    if snapshot.isoformat() != AS_OF:
        raise ValueError("Phase 4 SQL snapshot differs from the dataset contract")
    policy_count = conn.execute("SELECT COUNT(*) FROM insurance_analytics.policies").fetchone()[0]
    milestone_count = conn.execute(
        "SELECT COUNT(*) FROM persistency_analytics.policy_milestones"
    ).fetchone()[0]
    if milestone_count != policy_count * 3:
        raise ValueError("Policy/milestone base is not exactly three rows per policy")
    mismatches = conn.execute(RECONCILIATION_SQL).fetchall()
    if mismatches:
        raise ValueError("Phase 4 totals do not reconcile across analytical cuts")

    outputs = {}
    for view in VIEWS:
        relation = sql.Identifier("persistency_analytics", view)
        with conn.cursor() as cursor:
            cursor.execute(sql.SQL("SELECT * FROM {}").format(relation))
            columns = [column.name for column in cursor.description]
            ordering = sql.SQL(", ").join(map(sql.Identifier, columns))
            cursor.execute(sql.SQL("SELECT * FROM {} ORDER BY {}").format(relation, ordering))
            outputs[view] = pd.DataFrame.from_records(cursor.fetchall(), columns=columns)

    provenance.update(
        executed_at_utc=datetime.now(UTC).isoformat(),
        python_version=platform.python_version(),
        postgresql_version=conn.info.server_version,
        phase4_sql_sha256=sha256(ROOT / "sql/05_persistency_retention.sql"),
        validation_checks=len(checks),
        validation_failures=0,
        phase4_reconciliation=(
            "PASS: base grain and Agency / Region / Unit / Agent / cohort / product / "
            "payment frequency / customer segments"
        ),
        result_rows={name: len(frame) for name, frame in outputs.items()},
    )
    return outputs, provenance


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/processed/phase4")
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
