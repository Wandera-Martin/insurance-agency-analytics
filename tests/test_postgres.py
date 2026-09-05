"""Real PostgreSQL tests; use only a dedicated TEST_DATABASE_URL database."""

import os

import psycopg
import pytest

from data_quality import read_database, reconcile
from dataset import CONTRACT, ROOT, SCHEMA, read_csvs
from load_postgres import load


@pytest.fixture
def connection():
    dsn = os.environ.get("TEST_DATABASE_URL")
    if not dsn:
        pytest.skip("TEST_DATABASE_URL is required for PostgreSQL integration tests")
    with psycopg.connect(dsn) as conn:
        assert not conn.execute(
            "SELECT 1 FROM pg_namespace WHERE nspname = %s", (SCHEMA,)
        ).fetchone(), "Use a disposable database with no insurance_analytics schema"
        try:
            yield conn
        finally:
            conn.rollback()


def test_load_contract_rerun_and_replacement(connection, csv_directory):
    load(connection, csv_directory)
    cursor = connection.execute((ROOT / "sql/02_quality_checks.sql").read_text())
    while True:
        if cursor.description:
            rows = cursor.fetchall()
            if cursor.description[0].name == "table_name":
                assert len(rows) == 9
            else:
                assert rows == [], "Diagnostic SQL must not flag a valid synthetic portfolio"
        if not cursor.nextset():
            break
    columns = connection.execute(
        "SELECT table_name, column_name, is_nullable FROM information_schema.columns "
        "WHERE table_schema = %s ORDER BY table_name, ordinal_position",
        (SCHEMA,),
    ).fetchall()
    for table, fields in CONTRACT.items():
        actual = [(name, nullable) for tab, name, nullable in columns if tab == table]
        assert actual == [
            (name, "NO" if spec["required"] else "YES") for name, spec in fields.items()
        ]
    with pytest.raises(ValueError, match="contain rows"), connection.transaction():
        load(connection, csv_directory)
    load(connection, csv_directory, replace=True)
    assert not any(
        c.affected for c in reconcile(read_csvs(csv_directory), read_database(connection))
    )


def test_late_copy_failure_rolls_back_replacement(connection, csv_directory):
    load(connection, csv_directory)
    before = read_database(connection)
    # Existing rows remain; this constraint fails only when the final table is reloaded.
    connection.execute(
        "ALTER TABLE insurance_analytics.incentives ADD CONSTRAINT injected_failure "
        "CHECK (incentive_amount = 999999) NOT VALID"
    )
    with pytest.raises(psycopg.errors.CheckViolation), connection.transaction():
        load(connection, csv_directory, replace=True)
    assert not any(c.affected for c in reconcile(before, read_database(connection)))
