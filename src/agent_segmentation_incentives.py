"""Validate prerequisites and export Phase 5 SQL results without Pandas metrics."""

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
    "mature_history_distribution",
    "segmentation_thresholds",
    "agent_segmentation",
    "segment_summary",
    "cohort_aligned_agent_quality",
    "campaign_roster",
    "campaign_periods",
    "campaign_agent_performance",
    "campaign_summary",
    "campaign_qualification_comparison",
    "campaign_maturity",
    "campaign_quality_followup",
    "campaign_policy_followup",
)

REQUIRED_RELATIONS = (
    "agency_performance.snapshot",
    "agency_performance.agent_month",
    "persistency_analytics.snapshot",
    "persistency_analytics.persistency_facts",
    "persistency_analytics.overall_persistency",
    "agent_intelligence.snapshot",
)

EXPECTED_CAMPAIGNS = {
    ("Q4 Growth Sprint", "2025-10-01", "2025-12-31"),
    ("Protection Push", "2026-03-01", "2026-04-30"),
    ("Mid-Year Agency Challenge", "2026-06-01", "2026-07-31"),
}

RECONCILIATION_SQL = """
WITH segment AS (
    SELECT COUNT(*) AS agents, SUM(recent_policies) AS policies,
           SUM(recent_annualized_premium) AS premium,
           SUM(eligible_13m_policies) AS eligible_13m,
           SUM(persistent_13m_policies) AS persistent_13m
    FROM agent_intelligence.agent_segmentation
), summary AS (
    SELECT SUM(agent_count) AS agents, SUM(recent_policies) AS policies,
           SUM(recent_annualized_premium) AS premium,
           SUM(eligible_13m_policies) AS eligible_13m,
           SUM(persistent_13m_policies) AS persistent_13m
    FROM agent_intelligence.segment_summary WHERE grain = 'Agency'
), raw_recent AS (
    SELECT COUNT(*) AS policies, COALESCE(SUM(p.annualized_premium), 0) AS premium
    FROM insurance_analytics.policies p CROSS JOIN agent_intelligence.snapshot s
    WHERE p.issue_date >= s.recent_window_start AND p.issue_date < s.recent_window_end
), campaign_raw AS (
    SELECT r.campaign_name, COUNT(p.policy_id) AS policies,
           COALESCE(SUM(p.annualized_premium), 0) AS premium
    FROM agent_intelligence.campaign_roster r
    LEFT JOIN insurance_analytics.policies p ON p.agent_id = r.agent_id
      AND p.issue_date >= r.start_date AND p.issue_date <= r.end_date
    GROUP BY r.campaign_name
), campaign_view AS (
    SELECT campaign_name, SUM(policies) AS policies, SUM(annualized_premium) AS premium
    FROM agent_intelligence.campaign_agent_performance
    WHERE period_label = 'During' GROUP BY campaign_name
)
SELECT 'segment-summary' AS mismatch
FROM segment s CROSS JOIN summary m
WHERE (s.agents, s.policies, s.premium, s.eligible_13m, s.persistent_13m)
   IS DISTINCT FROM (m.agents, m.policies, m.premium, m.eligible_13m, m.persistent_13m)
UNION ALL
SELECT 'recent-raw' FROM segment s CROSS JOIN raw_recent r
WHERE (s.policies, s.premium) IS DISTINCT FROM (r.policies, r.premium)
UNION ALL
SELECT 'campaign-' || r.campaign_name
FROM campaign_raw r JOIN campaign_view v USING (campaign_name)
WHERE (r.policies, r.premium) IS DISTINCT FROM (v.policies, v.premium)
"""


def _read_view(conn, view: str) -> pd.DataFrame:
    relation = sql.Identifier("agent_intelligence", view)
    with conn.cursor() as cursor:
        cursor.execute(sql.SQL("SELECT * FROM {} LIMIT 0").format(relation))
        columns = [column.name for column in cursor.description]
        ordering = sql.SQL(", ").join(map(sql.Identifier, columns))
        cursor.execute(sql.SQL("SELECT * FROM {} ORDER BY {}").format(relation, ordering))
        return pd.DataFrame.from_records(cursor.fetchall(), columns=columns)


def read_analysis(conn, data_dir: Path = ROOT / "data/raw"):
    """Caller owns a repeatable-read transaction; SQL remains the metric authority."""
    provenance = verify_manifest(data_dir)
    frames = read_csvs(data_dir)
    loaded = read_database(conn)
    checks = validate(frames) + validate(loaded, scope="PostgreSQL") + reconcile(frames, loaded)
    if any(check.affected and check.severity == "ERROR" for check in checks):
        raise ValueError("Snapshot validation failed; run data_quality.py --database")

    missing = [
        relation
        for relation in REQUIRED_RELATIONS
        if conn.execute("SELECT to_regclass(%s)", (relation,)).fetchone()[0] is None
    ]
    if missing:
        raise ValueError(f"Required Phase 3–5 relations are missing: {', '.join(missing)}")

    snapshots = conn.execute("""
        SELECT (SELECT as_of FROM agency_performance.snapshot),
               (SELECT as_of FROM persistency_analytics.snapshot),
               (SELECT as_of FROM agent_intelligence.snapshot)
    """).fetchone()
    if any(value.isoformat() != AS_OF for value in snapshots):
        raise ValueError("Phase 3, Phase 4, Phase 5, and dataset snapshots differ")

    distribution = conn.execute(
        "SELECT * FROM agent_intelligence.mature_history_distribution"
    ).fetchone()
    if distribution is None or distribution[6] == 0 or float(distribution[7]) < 0.5:
        raise ValueError(
            "Locked 20-policy history threshold retains fewer than half of candidate agents; "
            "report the distribution before changing it"
        )

    campaigns = {
        (row[0], row[1].isoformat(), row[2].isoformat())
        for row in conn.execute("""
            SELECT DISTINCT campaign_name, start_date, end_date
            FROM agent_intelligence.campaign_roster
        """)
    }
    if campaigns != EXPECTED_CAMPAIGNS:
        raise ValueError("Campaign roster names or dates differ from the locked Phase 5 design")
    duplicate = conn.execute("""
        SELECT 1 FROM agent_intelligence.campaign_roster
        GROUP BY campaign_name, start_date, end_date, agent_id HAVING COUNT(*) <> 1 LIMIT 1
    """).fetchone()
    if duplicate:
        raise ValueError("Campaign roster is not one row per agent and campaign")
    if conn.execute(RECONCILIATION_SQL).fetchall():
        raise ValueError("Phase 5 segmentation or campaign production does not reconcile")

    outputs = {view: _read_view(conn, view) for view in VIEWS}
    provenance.update(
        executed_at_utc=datetime.now(UTC).isoformat(),
        python_version=platform.python_version(),
        postgresql_version=conn.info.server_version,
        phase5_sql_sha256=sha256(ROOT / "sql/06_agent_segmentation_incentives.sql"),
        validation_checks=len(checks),
        validation_failures=0,
        threshold_validation=(
            f"PASS: {distribution[6]}/{distribution[0]} agents "
            f"({float(distribution[7]):.1%}) meet >= {distribution[8]} eligible 13M policies"
        ),
        phase5_reconciliation=(
            "PASS: agent/segment recent production and 13M components; "
            "campaign roster production to policy facts"
        ),
        result_rows={name: len(frame) for name, frame in outputs.items()},
    )
    return outputs, provenance


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/processed/phase5")
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
        print(f"Analysis failed ({type(exc).__name__}): {exc}")
        return 1
    print(f"Validated snapshot; exported {len(outputs)} SQL views to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
