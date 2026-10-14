"""Small, internally consistent synthetic portfolio for adversarial checks."""

import json
import os

import pandas as pd
import psycopg
import pytest

from dataset import CONTRACT, SCHEMA, manifest


@pytest.fixture
def connection():
    """Rollback-only integration connection to an explicitly disposable database."""
    dsn = os.environ.get("TEST_DATABASE_URL")
    if not dsn:
        pytest.skip("TEST_DATABASE_URL is required for PostgreSQL integration tests")
    with psycopg.connect(dsn) as conn:
        assert not conn.execute(
            "SELECT 1 FROM pg_namespace WHERE nspname IN (%s, %s)",
            (SCHEMA, "agency_performance"),
        ).fetchone(), "Use a disposable database with no analytics schemas"
        try:
            yield conn
        finally:
            conn.rollback()


@pytest.fixture
def frames():
    rows = {
        "agency_units": dict(
            agency_unit_id="U1",
            agency_name="Synthetic unit",
            branch="Test",
            launch_date="2020-01-01",
            status="Active",
        ),
        "customers": dict(customer_id="C1", date_of_birth="1990-01-01", created_date="2023-01-01"),
        "agents": dict(
            agent_id="A1",
            agency_unit_id="U1",
            join_date="2022-01-01",
            status="Active",
            experience_years="4",
        ),
        "leads": dict(
            lead_id="L1",
            agent_id="A1",
            customer_id="C1",
            lead_date="2024-01-01",
            contact_status="Contacted",
            appointment_status="Completed",
            application_status="Approved",
            converted="True",
            conversion_date="2024-01-03",
        ),
        "policies": dict(
            policy_id="P1",
            customer_id="C1",
            agent_id="A1",
            product_name="Test",
            distribution_channel="Agency",
            issue_date="2024-01-03",
            policy_term_years="10",
            payment_frequency="Monthly",
            premium_amount="100",
            annualized_premium="1200",
            sum_assured="10000",
            maturity_date="2034-01-03",
            policy_status="Active",
        ),
        "premium_payments": dict(
            payment_id="PM1",
            policy_id="P1",
            due_date="2024-01-03",
            payment_date="2024-01-03",
            amount_due="100",
            amount_paid="100",
            payment_status="Paid",
        ),
        "policy_status_history": dict(
            status_history_id="H1", policy_id="P1", status="Active", status_date="2024-01-03"
        ),
        "sales_targets": dict(
            target_id="T1",
            agent_id="A1",
            target_month="2024-01-01",
            policy_target="1",
            premium_target="1200",
            new_customer_target="1",
        ),
        "incentives": dict(
            incentive_id="I1",
            agent_id="A1",
            campaign_name="Synthetic campaign",
            start_date="2024-01-01",
            end_date="2024-03-31",
            threshold="1000",
            incentive_amount="500",
            qualified="True",
        ),
    }
    return {
        table: pd.DataFrame(
            [{field: rows[table].get(field, pd.NA) for field in fields}], dtype="string"
        )
        for table, fields in CONTRACT.items()
    }


@pytest.fixture
def csv_directory(tmp_path, frames):
    for table, frame in frames.items():
        frame.to_csv(tmp_path / f"{table}.csv", index=False)
    (tmp_path / "manifest.json").write_text(json.dumps(manifest(tmp_path)), encoding="utf-8")
    return tmp_path
