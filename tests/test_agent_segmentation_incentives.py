"""Adversarial PostgreSQL cases for Phase 5 agent and campaign analytics."""

from decimal import Decimal

import pytest
from psycopg.rows import dict_row

from dataset import ROOT


def _base(conn, agents=6):
    conn.execute((ROOT / "sql/01_schema.sql").read_text())
    conn.execute("""
        INSERT INTO agency_units VALUES
            ('U1','One','Test','D1','Central',NULL,'2020-01-01','Active'),
            ('U2','Two','Test','D2','Eastern',NULL,'2020-01-01','Active');
        INSERT INTO customers (customer_id,date_of_birth,region,income_band,
            acquisition_channel,created_date)
        VALUES ('C1','1990-06-15','Central','Middle','Referral','2020-01-01');
    """)
    for number in range(1, agents + 1):
        conn.execute(
            """
            INSERT INTO agents (agent_id,agency_unit_id,join_date,status,agent_grade)
            VALUES (%s,%s,'2020-01-01','Active','Senior')
            """,
            (f"A{number}", "U1" if number % 2 else "U2"),
        )
    return conn


def _policy(conn, policy_id, agent, issue_date, premium=1000, persistent=True):
    status = "Active" if persistent else "Lapsed"
    conn.execute(
        """
        INSERT INTO policies (policy_id,customer_id,agent_id,product_name,issue_date,
            policy_term_years,payment_frequency,premium_amount,annualized_premium,
            sum_assured,maturity_date,policy_status)
        VALUES (%s,'C1',%s,'Test',%s,10,'Annual',%s,%s,100000,
                %s::date + INTERVAL '10 years',%s)
        """,
        (policy_id, agent, issue_date, premium, premium, issue_date, status),
    )
    conn.execute(
        "INSERT INTO policy_status_history VALUES (%s,%s,'Active',%s,NULL)",
        (f"H-{policy_id}-0", policy_id, issue_date),
    )
    if not persistent:
        conn.execute(
            "INSERT INTO policy_status_history VALUES (%s,%s,'Lapsed',%s::date + 365,NULL)",
            (f"H-{policy_id}-1", policy_id, issue_date),
        )


def _install(conn):
    for path in (
        "sql/04_agency_performance.sql",
        "sql/05_persistency_retention.sql",
        "sql/06_agent_segmentation_incentives.sql",
    ):
        conn.execute((ROOT / path).read_text())
    conn.row_factory = dict_row
    return conn


def _segmentation_portfolio(connection):
    conn = _base(connection)
    specs = {
        "A1": ([1000] * 20, 20),
        "A2": ([1000] * 20, 18),
        "A3": ([2000] * 20, 19),
        "A4": ([1000] * 20, 17),
        # 37,200 persistent AP / 40,000 eligible AP = exact 93% Agency benchmark.
        "A5": ([1200] + [1000] * 38 + [800], 37),
    }
    for agent, (premiums, persistent_count) in specs.items():
        for number, premium in enumerate(premiums):
            _policy(
                conn,
                f"Q-{agent}-{number}",
                agent,
                "2025-01-01",
                premium,
                number < persistent_count,
            )
    recent_ap = {"A1": 500, "A2": 400, "A3": 300, "A4": 200, "A6": 600}
    for agent, premium in recent_ap.items():
        _policy(conn, f"R-{agent}", agent, "2026-06-15", premium)
    for agent in specs | {"A6": None}:
        for month in (6, 7, 8):
            conn.execute(
                """
                INSERT INTO sales_targets VALUES (%s,%s,%s,1,1000,1)
                """,
                (f"T-{agent}-{month}", agent, f"2026-{month:02d}-01"),
            )
    return _install(conn)


def test_locked_boundaries_segments_zero_production_and_history_gate(connection):
    conn = _segmentation_portfolio(connection)
    rows = {
        row["agent_id"]: row
        for row in conn.execute("SELECT * FROM agent_intelligence.agent_segmentation")
    }
    assert rows["A3"]["recent_annualized_premium"] == rows["A3"]["production_benchmark"]
    assert rows["A3"]["production_band"] == "High production"
    assert rows["A4"]["recent_annualized_premium"] < rows["A4"]["production_benchmark"]
    assert rows["A4"]["production_band"] == "Lower production"
    assert rows["A5"]["premium_persistency_13m"] == rows["A5"]["quality_benchmark"]
    assert rows["A5"]["quality_band"] == "Strong quality"
    assert rows["A2"]["premium_persistency_13m"] < rows["A2"]["quality_benchmark"]
    assert rows["A2"]["quality_band"] == "Weaker quality"
    assert rows["A1"]["segment"] == "Sustainable Leaders"
    assert rows["A2"]["segment"] == "Volume Risk"
    assert rows["A5"]["segment"] == "Quality Builders"
    assert rows["A4"]["segment"] == "Development Priority"
    assert rows["A6"]["segment"] == "Insufficient Mature History"
    assert rows["A5"]["recent_annualized_premium"] == 0
    assert rows["A5"]["production_band"] == "Lower production"


def test_payment_rows_cannot_inflate_recent_ap_and_segment_ratios_use_sums(connection):
    conn = _segmentation_portfolio(connection)
    for number in range(3):
        conn.execute(
            """
            INSERT INTO premium_payments VALUES
                (%s,'R-A1','2026-07-01','2026-07-01',100,100,'Paid','Cash')
            """,
            (f"PM-{number}",),
        )
    assert (
        conn.execute("""
        SELECT recent_annualized_premium FROM agent_intelligence.agent_segmentation
        WHERE agent_id='A1'
    """).fetchone()["recent_annualized_premium"]
        == 500
    )
    row = conn.execute("""
        SELECT * FROM agent_intelligence.segment_summary
        WHERE grain='Agency' AND segment='Sustainable Leaders'
    """).fetchone()
    assert float(row["premium_persistency_13m"]) == pytest.approx(
        float(row["persistent_13m_annualized_premium"])
        / float(row["eligible_13m_annualized_premium"])
    )
    average_agent_rates = conn.execute("""
        SELECT AVG(premium_persistency_13m) AS average_rate
        FROM agent_intelligence.agent_segmentation
        WHERE segment='Sustainable Leaders'
    """).fetchone()["average_rate"]
    assert row["premium_persistency_13m"] != average_agent_rates


def test_segment_hierarchy_totals_reconcile(connection):
    conn = _segmentation_portfolio(connection)
    mismatch = conn.execute("""
        WITH totals AS (
            SELECT grain, SUM(agent_count) agents, SUM(recent_policies) policies,
                   SUM(recent_annualized_premium) premium
            FROM agent_intelligence.segment_summary GROUP BY grain
        )
        SELECT 1 FROM totals
        HAVING COUNT(DISTINCT (agents, policies, premium)) > 1
    """).fetchall()
    assert mismatch == []


def _campaign_portfolio(connection):
    conn = _base(connection, agents=2)
    campaigns = (
        ("I1", "Q4 Growth Sprint", "2025-10-01", "2025-12-31", True),
        ("I2", "Protection Push", "2026-03-01", "2026-04-30", False),
        ("I3", "Mid-Year Agency Challenge", "2026-06-01", "2026-07-31", True),
    )
    for incentive_id, name, start, end, qualified in campaigns:
        conn.execute(
            "INSERT INTO incentives VALUES (%s,'A1',%s,%s,%s,999999,0,%s)",
            (incentive_id, name, start, end, qualified),
        )
    _policy(conn, "Q4-start", "A1", "2025-10-01", 1000)
    _policy(conn, "Q4-end", "A1", "2025-12-31", 2000)
    _policy(conn, "Q4-other", "A2", "2025-11-15", 3000)
    _policy(conn, "Protection", "A1", "2026-03-01", 1500)
    _policy(conn, "MidYear", "A1", "2026-06-01", 1800)
    for agent in ("A1", "A2"):
        for year, month in (
            (2025, 7),
            (2025, 8),
            (2025, 9),
            (2025, 10),
            (2025, 11),
            (2025, 12),
            (2026, 1),
            (2026, 2),
            (2026, 3),
            (2026, 4),
            (2026, 5),
            (2026, 6),
            (2026, 7),
            (2026, 8),
        ):
            conn.execute(
                "INSERT INTO sales_targets VALUES (%s,%s,%s,1,1000,1)",
                (f"T-{agent}-{year}-{month}", agent, f"{year}-{month:02d}-01"),
            )
    return _install(conn)


def test_campaign_windows_availability_and_partial_label(connection):
    conn = _campaign_portfolio(connection)
    rows = {
        (row["campaign_name"], row["period_label"]): row
        for row in conn.execute("SELECT * FROM agent_intelligence.campaign_periods")
    }
    assert (
        rows[("Q4 Growth Sprint", "Before")]["period_start"].isoformat(),
        rows[("Q4 Growth Sprint", "After")]["period_end"].isoformat(),
    ) == ("2025-07-01", "2026-03-31")
    assert (
        rows[("Protection Push", "Before")]["period_start"].isoformat(),
        rows[("Protection Push", "After")]["period_end"].isoformat(),
    ) == ("2026-01-01", "2026-06-30")
    assert rows[("Q4 Growth Sprint", "After")]["primary_comparable"] is True
    assert rows[("Protection Push", "After")]["primary_comparable"] is True
    assert rows[("Mid-Year Agency Challenge", "After")]["window_available"] is False
    partial = rows[("Mid-Year Agency Challenge", "Partial post (August only)")]
    assert partial["window_status"] == "Partial"
    assert partial["primary_comparable"] is False


def test_campaign_roster_qualification_attribution_and_production_reconcile(connection):
    conn = _campaign_portfolio(connection)
    roster = conn.execute("""
        SELECT qualified, threshold FROM agent_intelligence.campaign_roster
        WHERE campaign_name='Q4 Growth Sprint'
    """).fetchone()
    assert roster["qualified"] is True
    assert roster["threshold"] == 999999
    attributed = conn.execute("""
        SELECT COUNT(DISTINCT policy_id) AS policies
        FROM agent_intelligence.campaign_policy_followup
        WHERE campaign_name='Q4 Growth Sprint'
    """).fetchone()["policies"]
    assert attributed == 2  # The non-rostered agent's policy is excluded.
    during = conn.execute("""
        SELECT policies, annualized_premium
        FROM agent_intelligence.campaign_agent_performance
        WHERE campaign_name='Q4 Growth Sprint' AND period_label='During'
    """).fetchone()
    assert (during["policies"], during["annualized_premium"]) == (2, 3000)
    labels = {
        row["comparison_group"]
        for row in conn.execute(
            "SELECT DISTINCT comparison_group FROM agent_intelligence.campaign_summary"
        )
    }
    assert labels == {"Campaign roster", "Descriptive comparison group"}


def test_campaign_followup_reuses_milestones_and_flags_partial_maturity(connection):
    conn = _campaign_portfolio(connection)
    rows = {
        (row["campaign_name"], row["milestone_months"]): row
        for row in conn.execute("SELECT * FROM agent_intelligence.campaign_maturity")
    }
    assert rows[("Q4 Growth Sprint", 3)]["maturity_status"] == "Complete"
    assert rows[("Q4 Growth Sprint", 6)]["maturity_status"] == "Complete"
    assert rows[("Q4 Growth Sprint", 13)]["primary_comparable"] is False
    assert rows[("Protection Push", 3)]["maturity_status"] == "Complete"
    assert rows[("Protection Push", 6)]["maturity_status"] == "Partial"
    assert rows[("Mid-Year Agency Challenge", 3)]["maturity_status"] == "Partial"
    assert rows[("Mid-Year Agency Challenge", 6)]["milestone_mature_policies"] == 0
    assert rows[("Mid-Year Agency Challenge", 6)]["maturity_status"] == "Not mature"
    q4 = rows[("Q4 Growth Sprint", 3)]
    assert q4["maturity_coverage"] == Decimal(q4["milestone_mature_policies"]) / Decimal(
        q4["campaign_policies"]
    )
    assert (
        conn.execute("""
        SELECT COUNT(*) AS mismatches FROM agent_intelligence.campaign_policy_followup f
        JOIN persistency_analytics.persistency_facts p
          USING (policy_id, milestone_months)
        WHERE (f.anniversary_date, f.milestone_eligible, f.persistent_flag)
           IS DISTINCT FROM (p.anniversary_date, p.milestone_eligible, p.persistent_flag)
    """).fetchone()["mismatches"]
        == 0
    )


def test_phase5_sql_has_fixed_clock_and_no_predictive_or_causal_model():
    text = (ROOT / "sql/06_agent_segmentation_incentives.sql").read_text().lower()
    assert "current_date" not in text
    assert "kmeans" not in text
    assert "difference-in-differences" not in text
    assert "control group" not in text
    assert "2026-09-01" in text
