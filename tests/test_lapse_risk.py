"""Adversarial PostgreSQL checks for the Phase 6 historical-panel checkpoint."""

from decimal import Decimal

from psycopg.rows import dict_row

from dataset import ROOT


def _base(connection):
    connection.execute((ROOT / "sql/01_schema.sql").read_text())
    connection.execute("""
        INSERT INTO agency_units VALUES
            ('U1','One','Test','D1','Central',NULL,'2020-01-01','Active');
        INSERT INTO customers (
            customer_id, gender, date_of_birth, region, income_band,
            acquisition_channel, created_date
        ) VALUES ('C1','Female','1990-06-15','Central','Middle','Referral','2020-01-01');
        INSERT INTO agents (agent_id,agency_unit_id,join_date,status,agent_grade)
        VALUES ('A1','U1','2020-01-01','Active','Senior');
    """)
    return connection


def _policy(conn, policy_id, issue_date, final_status="Active"):
    conn.execute(
        """
        INSERT INTO policies (
            policy_id, customer_id, agent_id, product_name, issue_date,
            policy_term_years, payment_frequency, premium_amount,
            annualized_premium, sum_assured, maturity_date, policy_status
        ) VALUES (%s, 'C1', 'A1', 'Protection Plus', %s, 10, 'Monthly',
                  100, 1200, 10000, %s::date + INTERVAL '10 years', %s)
        """,
        (policy_id, issue_date, issue_date, final_status),
    )
    _event(conn, f"H-{policy_id}-0", policy_id, "Active", issue_date)


def _event(conn, event_id, policy_id, status, status_date):
    conn.execute(
        "INSERT INTO policy_status_history VALUES (%s, %s, %s, %s, NULL)",
        (event_id, policy_id, status, status_date),
    )


def _payment(
    conn,
    payment_id,
    policy_id,
    due_date,
    payment_date=None,
    amount_paid=0,
    final_status="Missed",
):
    conn.execute(
        """
        INSERT INTO premium_payments (
            payment_id, policy_id, due_date, payment_date,
            amount_due, amount_paid, payment_status
        ) VALUES (%s, %s, %s, %s, 100, %s, %s)
        """,
        (payment_id, policy_id, due_date, payment_date, amount_paid, final_status),
    )


def _install(conn):
    conn.execute((ROOT / "sql/07_lapse_risk_features.sql").read_text())
    conn.row_factory = dict_row
    return conn


def _observation(conn, policy_id, observation_date="2026-01-31"):
    return conn.execute(
        """
        SELECT * FROM lapse_risk.policy_observations
        WHERE policy_id = %s AND observation_date = %s
        """,
        (policy_id, observation_date),
    ).fetchone()


def test_historical_status_risk_set_and_future_event_isolation(connection):
    conn = _base(connection)
    cases = {
        "Lapsed": "Lapsed",
        "Surrendered": "Surrendered",
        "Cancelled": "Cancelled",
        "Matured": "Matured",
        "Grace": "Grace",
    }
    for policy_id, status in cases.items():
        _policy(conn, policy_id, "2025-01-01")
        _event(conn, f"H-{policy_id}-1", policy_id, status, "2026-01-15")

    _policy(conn, "Reinstated", "2025-01-01", final_status="Lapsed")
    _event(conn, "H-Reinstated-1", "Reinstated", "Lapsed", "2026-01-10")
    _event(conn, "H-Reinstated-2", "Reinstated", "Reinstated", "2026-01-20")

    _policy(conn, "Future", "2025-01-01", final_status="Lapsed")
    _event(conn, "H-Future-1", "Future", "Grace", "2026-02-01")
    _event(conn, "H-Future-2", "Future", "Lapsed", "2026-02-10")
    conn = _install(conn)

    for policy_id in ("Lapsed", "Surrendered", "Cancelled", "Matured"):
        assert _observation(conn, policy_id)["risk_set_eligible"] is False
    assert _observation(conn, "Grace")["risk_set_eligible"] is True
    reinstated = _observation(conn, "Reinstated")
    assert reinstated["status_at_observation"] == "Reinstated"
    assert reinstated["risk_set_eligible"] is True
    future = _observation(conn, "Future")
    assert future["status_at_observation"] == "Active"
    assert future["risk_set_eligible"] is True


def test_exact_policy_age_boundary(connection):
    conn = _base(connection)
    _policy(conn, "Age29", "2026-03-02")
    _policy(conn, "Age30", "2026-03-01")
    conn = _install(conn)

    age29 = _observation(conn, "Age29", "2026-03-31")
    age30 = _observation(conn, "Age30", "2026-03-31")
    assert age29["policy_age_days"] == 29
    assert age29["risk_set_eligible"] is False
    assert age30["policy_age_days"] == 30
    assert age30["risk_set_eligible"] is True


def test_target_boundaries_and_first_future_lapse(connection):
    conn = _base(connection)
    for policy_id in ("Day90", "Day91", "SameDay", "Multiple"):
        _policy(conn, policy_id, "2025-01-01")
    _event(conn, "H-Day90-1", "Day90", "Lapsed", "2026-05-01")
    _event(conn, "H-Day91-1", "Day91", "Lapsed", "2026-05-02")
    _event(conn, "H-SameDay-1", "SameDay", "Lapsed", "2026-01-31")
    _event(conn, "H-Multiple-1", "Multiple", "Lapsed", "2026-03-01")
    _event(conn, "H-Multiple-2", "Multiple", "Reinstated", "2026-03-10")
    _event(conn, "H-Multiple-3", "Multiple", "Lapsed", "2026-04-15")
    conn = _install(conn)

    assert _observation(conn, "Day90")["lapse_next_90d"] == 1
    assert _observation(conn, "Day91")["lapse_next_90d"] == 0
    same_day = _observation(conn, "SameDay")
    assert same_day["risk_set_eligible"] is False
    assert same_day["lapse_next_90d"] is None
    multiple = _observation(conn, "Multiple")
    assert multiple["first_lapse_date"].isoformat() == "2026-03-01"
    assert multiple["lapse_next_90d"] == 1


def test_immature_observation_is_null_and_excluded_from_model_dataset(connection):
    conn = _base(connection)
    _policy(conn, "Immature", "2025-01-01")
    conn = _install(conn)

    row = _observation(conn, "Immature", "2026-06-30")
    assert row["label_eligible"] is False
    assert row["lapse_next_90d"] is None
    assert not conn.execute(
        """
        SELECT EXISTS (
            SELECT 1 FROM lapse_risk.model_dataset
            WHERE policy_id = 'Immature' AND observation_date = DATE '2026-06-30'
        )
        """
    ).fetchone()["exists"]


def test_future_payment_resolution_and_future_due_installment_are_excluded(connection):
    conn = _base(connection)
    _policy(conn, "Pay", "2025-01-01")
    _payment(conn, "PM-Paid", "Pay", "2026-01-01", "2026-01-02", 100, "Paid")
    _payment(conn, "PM-Future", "Pay", "2026-01-10", "2026-02-05", 100, "Late")
    _payment(conn, "PM-NotDue", "Pay", "2026-02-01", None, 0, "Missed")
    conn = _install(conn)

    row = conn.execute(
        """
        SELECT * FROM lapse_risk.payment_features
        WHERE policy_id = 'Pay' AND observation_date = DATE '2026-01-31'
        """
    ).fetchone()
    assert row["installments_due_to_date"] == 2
    assert row["paid_count_to_date"] == 1
    assert row["missed_count_to_date"] == 1
    assert row["amount_due_to_date"] == Decimal("200")
    assert row["amount_paid_to_date"] == Decimal("100")
    assert row["payment_completion_rate_to_date"] == Decimal("0.5")


def test_payment_aggregation_preserves_panel_uniqueness(connection):
    conn = _base(connection)
    _policy(conn, "Unique", "2025-01-01")
    _payment(conn, "PM-U1", "Unique", "2025-12-01", "2025-12-01", 100, "Paid")
    _payment(conn, "PM-U2", "Unique", "2026-01-01", None, 0, "Missed")
    conn = _install(conn)

    duplicates = conn.execute("""
        SELECT policy_id, observation_date, COUNT(*)
        FROM lapse_risk.model_dataset
        GROUP BY policy_id, observation_date
        HAVING COUNT(*) > 1
    """).fetchall()
    assert duplicates == []


def test_monthly_profile_reconciles_and_temporal_split_is_ordered(connection):
    conn = _base(connection)
    _policy(conn, "Positive", "2025-01-01")
    _event(conn, "H-Positive-1", "Positive", "Lapsed", "2026-05-01")
    _policy(conn, "Negative", "2025-01-01")
    conn = _install(conn)

    monthly = conn.execute("SELECT * FROM lapse_risk.monthly_target_distribution").fetchall()
    assert not conn.execute(
        "SELECT EXISTS (SELECT 1 FROM lapse_risk.model_dataset WHERE lapse_next_90d IS NULL)"
    ).fetchone()["exists"]
    assert all(
        row["positive_rate"] == Decimal(row["positives"]) / Decimal(row["observations"])
        for row in monthly
    )
    assert (
        sum(row["observations"] for row in monthly)
        == conn.execute("SELECT COUNT(*) FROM lapse_risk.model_dataset").fetchone()["count"]
    )
    assert (
        sum(row["positives"] for row in monthly)
        == conn.execute("SELECT SUM(lapse_next_90d) FROM lapse_risk.model_dataset").fetchone()[
            "sum"
        ]
    )

    split = {
        row["split"]: row for row in conn.execute("SELECT * FROM lapse_risk.proposed_split_profile")
    }
    assert split["train"]["last_observation_date"] < split["validation"]["first_observation_date"]
    assert split["validation"]["last_observation_date"] < split["test"]["first_observation_date"]


def test_sql_static_leakage_guards_and_fixed_clock():
    text = (ROOT / "sql/07_lapse_risk_features.sql").read_text().lower()
    assert "current_date" not in text
    assert "p.policy_status" not in text
    assert "pm.payment_status" not in text
    assert "2026-09-01" in text
    assert "random" not in text
    for forbidden in (
        "phase5",
        "agent_segment",
        "high-volume risk",
        "inactive-risk",
        "future_lapse_count",
        "days_until_lapse",
    ):
        assert forbidden not in text
