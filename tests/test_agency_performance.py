"""Adversarial PostgreSQL examples exercise the actual Phase 3 metric views."""

from datetime import date
from decimal import Decimal

import pytest
from psycopg.rows import dict_row

from agency_performance import read_analysis
from dataset import AS_OF, ROOT
from load_postgres import load


@pytest.fixture
def metrics(connection):
    connection.execute((ROOT / "sql/01_schema.sql").read_text())
    connection.execute("""
        INSERT INTO agency_units (agency_unit_id, agency_name, branch, region, launch_date, status)
        VALUES ('U1','One','Test','East','2020-01-01','Active'),
               ('U2','Two','Test','West','2020-01-01','Active'),
               ('U3','Empty','Test','West','2020-01-01','Active');
        INSERT INTO customers (customer_id,date_of_birth,created_date)
        VALUES ('C1','1990-01-01','2023-01-01');
        INSERT INTO agents (agent_id,agency_unit_id,join_date,status,exit_date,agent_grade)
        VALUES ('A1','U1','2023-01-01','Exited','2026-08-01','Senior'),
               ('A2','U1','2026-08-31','Active',NULL,'Junior'),
               ('A3','U1','2026-09-01','Active',NULL,'Junior'),
               ('A4','U2','2023-01-01','Exited','2026-07-31','Senior'),
               ('A5','U2','2024-01-01','Inactive',NULL,'Junior'),
               ('A6','U2','2026-08-01','Active',NULL,'Junior'),
               ('A7','U2','2026-08-02','Active',NULL,'Junior');
        INSERT INTO policies (policy_id,customer_id,agent_id,product_name,issue_date,
            policy_term_years,payment_frequency,premium_amount,annualized_premium,
            sum_assured,maturity_date,policy_status)
        SELECT id,'C1',agent,'Test',issued::date,10,'Monthly',100,1200,10000,
               issued::date + INTERVAL '10 years',status
        FROM (VALUES ('P1','A1','2026-07-31','Lapsed'),
                     ('P2','A1','2026-08-01','Lapsed'),
                     ('P3','A2','2026-08-31','Active'),
                     ('P4','A2','2026-08-31','Active'),
                     ('P5','A3','2026-09-01','Active'),
                     ('P6','A4','2026-07-01','Active'),
                     ('P7','A7','2026-08-31','Active')) AS p(id,agent,issued,status);
        INSERT INTO sales_targets VALUES
            ('T1','A1','2026-08-01',1,2400,1),
            ('T2','A2','2026-08-01',9,1200,1),
            ('T3','A5','2026-08-01',10,1000,1),
            ('T4','A7','2026-08-01',0,0,0);
        INSERT INTO leads (lead_id,agent_id,lead_date,converted,conversion_date,
            contact_status,appointment_status,application_status)
        VALUES ('L1','A2','2026-08-31',TRUE,'2026-09-01','Contacted','Booked','Approved'),
               ('L2','A2','2026-08-31',FALSE,NULL,'Contacted','No Show','None'),
               ('L3','A2','2026-08-31',FALSE,NULL,'Uncontacted','None','None'),
               ('L4','A1','2026-07-01',TRUE,'2026-08-01','Contacted','Completed','Approved'),
               ('L5','A3','2026-09-01',TRUE,'2026-09-01','Contacted','Completed','Approved');
    """)
    connection.execute((ROOT / "sql/04_agency_performance.sql").read_text())
    connection.row_factory = dict_row
    return connection


def august(conn, view="monthly_trends"):
    return conn.execute(
        f"SELECT * FROM agency_performance.{view} WHERE period_start = '2026-08-01'"
    ).fetchone()


def test_reporting_boundaries_eligibility_and_distinct_producers(metrics):
    row = august(metrics)
    assert row["new_policies"] == 4  # Includes historical lapsed production.
    assert row["new_business_annualized_premium"] == 4800
    assert row["eligible_agents"] == 5  # Exit on start, join on last day, inactive included.
    assert row["producing_agents"] == 3  # A2's two policies count as one producer.
    assert row["producing_agent_ratio"] == Decimal("0.6")
    agents = metrics.execute(
        "SELECT agent_id FROM agency_performance.agent_month WHERE period_start = '2026-08-01'"
    ).fetchall()
    assert {r["agent_id"] for r in agents} == {"A1", "A2", "A5", "A6", "A7"}
    periods = metrics.execute("SELECT * FROM agency_performance.periods ORDER BY 1").fetchall()
    assert periods[0]["period_start"] == date(2023, 1, 1)
    assert periods[-1]["period_start"] == date(2026, 8, 1)
    assert periods[-1]["period_end"].isoformat() == AS_OF
    assert len(periods) == 44


def test_target_sums_separate_achievers_and_missing_targets(metrics):
    row = august(metrics)
    assert row["policy_target"] == 20
    assert row["premium_target"] == 4600
    assert row["policy_target_achievement"] == Decimal("0.2")
    assert float(row["premium_target_achievement"]) == pytest.approx(4800 / 4600)
    assert row["policy_target_achievers"] == row["premium_target_achievers"] == 1
    assert row["agents_with_policy_target"] == row["agents_with_premium_target"] == 3
    rows = metrics.execute(
        "SELECT * FROM agency_performance.agent_month WHERE period_start = '2026-08-01'"
    ).fetchall()
    agents = {r["agent_id"]: r for r in rows}
    assert agents["A5"]["policy_target_band"] == "Non-Producing"
    assert agents["A5"]["producing_agents"] == 0
    assert agents["A6"]["policy_target_band"] == "Missing/Invalid Target"
    assert agents["A7"]["premium_target_band"] == "Missing/Invalid Target"
    assert agents["A1"]["policy_target_achievement"] == 1
    assert agents["A1"]["premium_target_achievement"] == Decimal("0.5")
    assert agents["A2"]["premium_target_achievement"] == 2


@pytest.mark.parametrize(
    ("target", "band"),
    [
        (None, "Missing/Invalid Target"),
        (0, "Missing/Invalid Target"),
        (3, "Under Target"),
        (2.5, "Near Target"),
        (2, "Target Achiever"),
        (1, "High Achiever"),
    ],
)
def test_premium_band_boundaries(metrics, target, band):
    # Premium targets admit fractional amounts; 2400/3000 tests exactly 80%.
    if target is None:
        metrics.execute("DELETE FROM sales_targets WHERE agent_id = 'A2'")
    else:
        metrics.execute(
            "UPDATE sales_targets SET premium_target = %s WHERE agent_id = 'A2'",
            (target * 1200,),
        )
    assert (
        metrics.execute(
            "SELECT premium_target_band FROM agency_performance.agent_month "
            "WHERE agent_id = 'A2' AND period_start = '2026-08-01'"
        ).fetchone()["premium_target_band"]
        == band
    )


def test_zero_denominators_and_empty_unit(metrics):
    empty = metrics.execute(
        "SELECT * FROM agency_performance.performance WHERE grain = 'Unit' "
        "AND agency_unit_id = 'U3' AND period_start = '2026-08-01'"
    ).fetchone()
    assert empty["eligible_agents"] == empty["new_policies"] == 0
    for field in (
        "producing_agent_ratio",
        "policies_per_producing_agent",
        "avg_annualized_premium_per_policy",
        "policy_target_achievement",
        "premium_target_achievement",
        "lead_conversion",
    ):
        assert empty[field] is None
    first = metrics.execute(
        "SELECT * FROM agency_performance.monthly_trends ORDER BY period_start LIMIT 1"
    ).fetchone()
    assert first["policy_mom_growth"] is None
    july = metrics.execute(
        "SELECT * FROM agency_performance.monthly_trends WHERE period_start = '2026-07-01'"
    ).fetchone()
    assert july["policy_mom_growth"] is None  # June denominator is zero.


def test_hierarchy_reconciles_every_complete_month(metrics):
    assert (
        metrics.execute("""
        WITH levels AS (
            SELECT period_start, grain, SUM(new_policies) AS policies,
                   SUM(new_business_annualized_premium) AS premium,
                   SUM(eligible_agents) AS eligible, SUM(producing_agents) AS producers,
                   SUM(policy_target) AS targets, SUM(leads_created) AS leads
            FROM agency_performance.performance GROUP BY 1,2
            UNION ALL
            SELECT period_start, 'Agent', SUM(new_policies),
                   SUM(new_business_annualized_premium), COUNT(*), SUM(producing_agents),
                   SUM(NULLIF(policy_target,0)), SUM(leads_created)
            FROM agency_performance.agent_month GROUP BY 1
        ) SELECT period_start FROM levels GROUP BY 1
          HAVING COUNT(DISTINCT (policies,premium,eligible,producers,targets,leads)) > 1
    """).fetchall()
        == []
    )


def test_payment_join_cannot_inflate_production(metrics):
    before = august(metrics)
    metrics.execute("""
        INSERT INTO premium_payments (payment_id,policy_id,due_date,amount_due,
            amount_paid,payment_status)
        VALUES ('PM1','P3','2026-08-31',100,0,'Missed'),
               ('PM2','P3','2026-09-30',100,0,'Missed'),
               ('PM3','P3','2026-10-31',100,0,'Missed')
    """)
    assert august(metrics) == before


def test_lead_cohort_denominator_and_stage_evidence(metrics):
    row = august(metrics)
    assert row["leads_created"] == 3
    assert row["converted_leads"] == 1  # September conversion of an August lead.
    assert float(row["lead_conversion"]) == pytest.approx(1 / 3)
    funnel = metrics.execute(
        "SELECT * FROM agency_performance.lead_funnel "
        "WHERE period_start = '2026-08-01' ORDER BY stage_order"
    ).fetchall()
    assert [r["leads"] for r in funnel] == [3, 2, 2, 0, 1, 1, 1]
    assert all(r["leads_created"] == 3 for r in funnel)


def test_activation_dates_censoring_and_day_30_exclusion(metrics):
    metrics.execute("""
        INSERT INTO agents (agent_id,agency_unit_id,join_date,status,exit_date) VALUES
        ('Old','U1','2022-12-31','Active',NULL),
        ('Early','U1','2026-08-01','Exited','2026-08-10'),
        ('Zero','U1','2026-08-01','Active',NULL)
    """)
    rows = metrics.execute("SELECT * FROM agency_performance.agent_activation").fetchall()
    agents = {r["agent_id"]: r for r in rows}
    assert agents["A7"]["days_to_first_policy"] == 29
    assert agents["A7"]["activated_first_30_days"] is True
    assert agents["A2"]["window_mature"] is False
    assert agents["A2"]["activated_first_30_days"] is None
    assert agents["Old"]["history_observed"] is False
    assert agents["Old"]["days_to_first_policy"] is None
    assert agents["Early"]["first_30_day_eligible"] is False
    assert agents["Zero"]["activated_first_30_days"] is False
    metrics.execute("UPDATE policies SET issue_date = '2026-09-01' WHERE policy_id = 'P7'")
    late = metrics.execute(
        "SELECT * FROM agency_performance.agent_activation WHERE agent_id = 'A7'"
    ).fetchone()
    assert late["days_to_first_policy"] == 30
    assert late["activated_first_30_days"] is False


def test_mom_and_concentration(metrics):
    row = august(metrics)
    assert row["previous_new_policies"] == 2
    assert row["policy_mom_growth"] == row["premium_mom_growth"] == 1
    concentration = august(metrics, "concentration")
    assert concentration["top_agent_count"] == 1
    assert concentration["top_policy_share"] == concentration["top_premium_share"] == Decimal("0.5")
    metrics.execute("UPDATE policies SET annualized_premium = 10000 WHERE policy_id = 'P2'")
    concentration = august(metrics, "concentration")
    assert concentration["top_policy_share"] == Decimal("0.5")
    assert float(concentration["top_premium_share"]) == pytest.approx(10000 / 13600)


def test_metric_layer_has_no_clock_or_payment_dependency():
    text = (ROOT / "sql/04_agency_performance.sql").read_text().lower()
    assert "current_date" not in text
    assert "premium_payments" not in text
    assert "materialized" not in text


@pytest.mark.parametrize(
    ("target", "band"),
    [(16, "Under Target"), (15, "Near Target"), (12, "Target Achiever"), (10, "High Achiever")],
)
def test_exact_policy_band_boundaries(metrics, target, band):
    metrics.execute("""
        INSERT INTO policies (policy_id,customer_id,agent_id,product_name,issue_date,
            policy_term_years,payment_frequency,premium_amount,annualized_premium,
            sum_assured,maturity_date,policy_status)
        SELECT 'Extra' || n,'C1','A2','Test','2026-08-31',10,'Monthly',100,1200,
            10000,'2036-08-31','Active' FROM generate_series(1,10) n
    """)
    metrics.execute("UPDATE sales_targets SET policy_target=%s WHERE agent_id='A2'", (target,))
    assert (
        metrics.execute(
            "SELECT policy_target_band FROM agency_performance.agent_month "
            "WHERE agent_id='A2' AND period_start='2026-08-01'"
        ).fetchone()["policy_target_band"]
        == band
    )


def test_validated_sql_export_and_snapshot_rejection(connection, csv_directory):
    load(connection, csv_directory)
    connection.execute((ROOT / "sql/04_agency_performance.sql").read_text())
    outputs, provenance = read_analysis(connection, csv_directory)
    assert provenance["validation_failures"] == 0
    assert len(outputs["monthly_trends"]) == 44
    connection.execute("UPDATE insurance_analytics.policies SET annualized_premium=2400")
    with pytest.raises(ValueError, match="Snapshot validation failed"):
        read_analysis(connection, csv_directory)
