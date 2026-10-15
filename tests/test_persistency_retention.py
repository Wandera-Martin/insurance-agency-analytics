"""Adversarial PostgreSQL cases for Phase 4 historical persistency metrics."""

from decimal import Decimal

import pytest
from psycopg.rows import dict_row

from dataset import ROOT
from load_postgres import load
from persistency_retention import read_analysis


def add_policy(conn, policy_id, issue_date, premium=1000, status="Active", agent="A1"):
    conn.execute(
        """
        INSERT INTO policies (policy_id, customer_id, agent_id, product_name, issue_date,
            policy_term_years, payment_frequency, premium_amount, annualized_premium,
            sum_assured, maturity_date, policy_status)
        VALUES (%s, 'C1', %s, 'Protection Plus', %s, 10, 'Annual', %s, %s,
                100000, %s::date + INTERVAL '10 years', %s)
        """,
        (policy_id, agent, issue_date, premium, premium, issue_date, status),
    )
    add_event(conn, f"H-{policy_id}-0", policy_id, "Active", issue_date)


def add_event(conn, event_id, policy_id, status, status_date):
    conn.execute(
        "INSERT INTO policy_status_history VALUES (%s, %s, %s, %s, NULL)",
        (event_id, policy_id, status, status_date),
    )


def milestone(conn, policy_id, months):
    return conn.execute(
        "SELECT * FROM persistency_analytics.policy_persistency "
        "WHERE policy_id=%s AND milestone_months=%s",
        (policy_id, months),
    ).fetchone()


def payment(conn, payment_id, policy_id, due_date, amount, status="Paid"):
    paid = 0 if status == "Missed" else amount
    payment_date = None if status == "Missed" else due_date
    conn.execute(
        """
        INSERT INTO premium_payments (payment_id, policy_id, due_date, payment_date,
            amount_due, amount_paid, payment_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (payment_id, policy_id, due_date, payment_date, amount, paid, status),
    )


def _install(conn):
    conn.execute((ROOT / "sql/05_persistency_retention.sql").read_text())
    conn.row_factory = dict_row
    return conn


def _base(connection):
    connection.execute((ROOT / "sql/01_schema.sql").read_text())
    connection.execute("""
        INSERT INTO agency_units VALUES
            ('U1','One','Test','D1','Central',NULL,'2020-01-01','Active'),
            ('U2','Two','Test','D2','Eastern',NULL,'2020-01-01','Active');
        INSERT INTO customers (customer_id,date_of_birth,region,income_band,
            acquisition_channel,created_date)
        VALUES ('C1','1990-06-15','Central','Middle','Referral','2020-01-01');
        INSERT INTO agents (agent_id,agency_unit_id,join_date,status,agent_grade)
        VALUES ('A1','U1','2020-01-01','Active','Senior'),
               ('A2','U2','2020-01-01','Active','Junior');
    """)
    return connection


def test_historical_status_chronology_and_reinstatement(connection):
    conn = _base(connection)
    add_policy(conn, "P1", "2025-09-01")
    add_event(conn, "H-P1-1", "P1", "Lapsed", "2026-02-01")  # month 5
    add_policy(conn, "P2", "2025-09-01")
    add_event(conn, "H-P2-1", "P2", "Lapsed", "2026-01-01")
    add_event(conn, "H-P2-2", "P2", "Reinstated", "2026-02-01")
    add_policy(conn, "P3", "2025-09-01", status="Lapsed")
    add_event(conn, "H-P3-1", "P3", "Lapsed", "2025-11-30")
    conn = _install(conn)

    assert milestone(conn, "P1", 3)["persistent_flag"] is True
    assert milestone(conn, "P1", 6)["persistent_flag"] is False
    assert milestone(conn, "P2", 3)["persistent_flag"] is True
    assert milestone(conn, "P2", 6)["persistent_flag"] is True
    assert milestone(conn, "P2", 6)["status_at_anniversary"] == "Reinstated"
    assert milestone(conn, "P3", 3)["persistent_flag"] is False


def test_grace_future_events_latest_event_and_current_status_are_safe(connection):
    conn = _base(connection)
    add_policy(conn, "P4", "2025-09-01", status="Lapsed")
    add_event(conn, "H-P4-1", "P4", "Grace", "2025-11-01")
    add_event(conn, "H-P4-2", "P4", "Lapsed", "2026-01-01")
    add_policy(conn, "P5", "2025-09-01", status="Lapsed")
    add_event(conn, "H-P5-1", "P5", "Grace", "2025-10-01")
    add_event(conn, "H-P5-2", "P5", "Active", "2025-11-01")
    add_event(conn, "H-P5-3", "P5", "Lapsed", "2026-01-01")
    conn = _install(conn)

    row = milestone(conn, "P4", 3)
    assert row["status_at_anniversary"] == "Grace"
    assert row["persistent_flag"] is True
    row = milestone(conn, "P5", 3)
    assert row["status_at_anniversary"] == "Active"
    assert row["persistent_flag"] is True


def test_immaturity_exact_boundaries_and_maturity_exclusion(connection):
    conn = _base(connection)
    add_policy(conn, "Young", "2026-07-01")
    add_policy(conn, "B3", "2026-06-01")
    add_policy(conn, "B6", "2026-03-01")
    add_policy(conn, "B13", "2025-08-01")
    add_policy(conn, "Mature", "2025-09-01", status="Matured")
    add_event(conn, "H-Mature-1", "Mature", "Matured", "2025-11-01")
    conn = _install(conn)

    young = milestone(conn, "Young", 3)
    assert young["milestone_eligible"] is False
    assert young["denominator_eligible"] is False
    assert young["persistent_flag"] is None
    assert milestone(conn, "B3", 3)["milestone_eligible"] is True
    assert milestone(conn, "B6", 6)["milestone_eligible"] is True
    assert milestone(conn, "B13", 13)["milestone_eligible"] is True
    mature = milestone(conn, "Mature", 3)
    assert mature["status_at_anniversary"] == "Matured"
    assert mature["denominator_eligible"] is False
    assert mature["persistent_flag"] is None
    summary = conn.execute(
        "SELECT * FROM persistency_analytics.overall_persistency WHERE milestone_months=3"
    ).fetchone()
    assert summary["matured_count"] == 1
    assert summary["eligible_policies"] == 3


def test_premium_and_count_persistency_diverge_without_payment_inflation(connection):
    conn = _base(connection)
    add_policy(conn, "Small1", "2025-09-01", 1000)
    add_policy(conn, "Small2", "2025-09-01", 1000)
    add_policy(conn, "Large", "2025-09-01", 8000, status="Lapsed")
    add_event(conn, "H-Large-1", "Large", "Lapsed", "2025-11-01")
    for number, due in enumerate(("2025-09-01", "2025-10-01", "2025-11-01"), 1):
        payment(conn, f"PM-{number}", "Small1", due, 1000)
    conn = _install(conn)

    row = conn.execute(
        "SELECT * FROM persistency_analytics.overall_persistency WHERE milestone_months=3"
    ).fetchone()
    assert row["eligible_policies"] == 3
    assert row["eligible_annualized_premium"] == 10000
    assert float(row["count_persistency"]) == pytest.approx(2 / 3)
    assert row["premium_persistency"] == Decimal("0.2")


def test_payment_cutoff_and_status_rates(connection):
    conn = _base(connection)
    add_policy(conn, "Pay", "2025-09-01", 1200)
    payment(conn, "PM1", "Pay", "2025-10-01", 100, "Paid")
    payment(conn, "PM2", "Pay", "2025-11-01", 100, "Missed")
    payment(conn, "PM3", "Pay", "2026-01-01", 100, "Missed")  # after 3M
    conn = _install(conn)

    row = conn.execute(
        "SELECT * FROM persistency_analytics.payment_behavior "
        "WHERE policy_id='Pay' AND milestone_months=3"
    ).fetchone()
    assert row["installments_due"] == 2
    assert row["paid_count"] == row["missed_count"] == 1
    assert row["amount_due"] == 200
    assert row["payment_completion_rate"] == Decimal("0.5")


def test_lapse_timing_keeps_outcomes_separate(connection):
    conn = _base(connection)
    add_policy(conn, "Outcome", "2025-01-01", status="Surrendered")
    add_event(conn, "H-Outcome-1", "Outcome", "Lapsed", "2025-03-15")
    add_event(conn, "H-Outcome-2", "Outcome", "Reinstated", "2025-04-01")
    add_event(conn, "H-Outcome-3", "Outcome", "Surrendered", "2025-08-01")
    conn = _install(conn)

    rows = conn.execute(
        "SELECT outcome_status, timing_band FROM persistency_analytics.lapse_timing "
        "WHERE policy_id='Outcome' ORDER BY outcome_status"
    ).fetchall()
    assert [(r["outcome_status"], r["timing_band"]) for r in rows] == [
        ("Lapsed", "0-<3 months"),
        ("Surrendered", "6-<13 months"),
    ]


def test_hierarchy_and_cohort_reconcile_to_agency(connection):
    conn = _base(connection)
    add_policy(conn, "East", "2025-08-01", 2000, agent="A2")
    add_policy(conn, "Central", "2025-08-01", 1000, agent="A1")
    conn = _install(conn)

    assert (
        conn.execute("""
        WITH levels AS (
            SELECT milestone_months, grain, SUM(eligible_policies) AS eligible,
                   SUM(persistent_policies) AS persistent,
                   SUM(eligible_annualized_premium) AS premium
            FROM persistency_analytics.hierarchy_persistency
            GROUP BY milestone_months, grain
        )
        SELECT milestone_months FROM levels GROUP BY milestone_months
        HAVING COUNT(DISTINCT (eligible, persistent, premium)) > 1
    """).fetchall()
        == []
    )
    assert (
        conn.execute("""
        SELECT milestone_months
        FROM persistency_analytics.cohort_persistency
        GROUP BY milestone_months
        HAVING SUM(eligible_policies) <> (
            SELECT eligible_policies FROM persistency_analytics.overall_persistency o
            WHERE o.milestone_months = cohort_persistency.milestone_months)
    """).fetchall()
        == []
    )


def test_sql_has_fixed_clock_and_no_current_status_dependency():
    text = (ROOT / "sql/05_persistency_retention.sql").read_text().lower()
    assert "current_date" not in text
    assert "p.policy_status" not in text
    assert "2026-09-01" in text


def test_validated_phase4_export_and_snapshot_rejection(connection, csv_directory):
    load(connection, csv_directory)
    connection.execute((ROOT / "sql/05_persistency_retention.sql").read_text())
    outputs, provenance = read_analysis(connection, csv_directory)
    assert provenance["validation_failures"] == 0
    assert provenance["phase4_reconciliation"].startswith("PASS")
    assert len(outputs["policy_persistency"]) == 3
    connection.execute(
        "CREATE OR REPLACE VIEW persistency_analytics.snapshot AS SELECT DATE '2026-08-31' AS as_of"
    )
    with pytest.raises(ValueError, match="snapshot differs"):
        read_analysis(connection, csv_directory)
