"""Inject defects that would distort Agency production and collections."""

import pandas as pd
import pytest

from data_quality import reconcile, validate
from dataset import read_csvs, verify_manifest


def test_valid_portfolio_and_expected_nulls(frames):
    assert not [c for c in validate(frames) if c.affected]


@pytest.mark.parametrize(
    ("table", "field", "value", "rule"),
    [
        ("agents", "agency_unit_id", "MISSING", "references agency_units"),
        ("policies", "customer_id", pd.NA, "required"),
        ("policies", "annualized_premium", "1300", "annualization"),
        ("policies", "premium_amount", "NaN", "finite number"),
        ("policies", "premium_amount", "inf", "finite number"),
        ("policies", "premium_amount", "100.001", "two decimals"),
        ("policies", "policy_term_years", "1.5", "whole number"),
        ("policies", "issue_date", "bad-date", "valid date"),
        ("policies", "issue_date", "2027-01-01", "within snapshot"),
        ("policies", "policy_status", "Lapsed", "status/date consistency"),
        ("policies", "payment_frequency", "Weekly", "allowed category"),
        ("leads", "converted", "yes", "valid boolean"),
        ("leads", "conversion_date", "2023-01-01", "conversion after lead"),
        ("leads", "contact_status", "Uncontacted", "converted lead contacted"),
        ("premium_payments", "payment_date", "2026-10-01", "within snapshot"),
        ("premium_payments", "payment_status", "Missed", "missed means"),
        ("premium_payments", "amount_paid", "50", "settled in full"),
        ("policy_status_history", "status", "Grace", "current status"),
        ("sales_targets", "target_month", "2024-01-15", "day one"),
        ("incentives", "start_date", "2025-01-01", "end on/after start"),
        ("incentives", "qualified", "False", "qualification agrees"),
    ],
)
def test_rejects_invalid_records(frames, table, field, value, rule):
    frames[table].loc[0, field] = value
    assert any(c.affected and rule in c.rule for c in validate(frames))


def test_rejects_duplicate_keys(frames):
    frames["policies"] = pd.concat([frames["policies"]] * 2, ignore_index=True)
    assert any(c.affected == 2 and c.rule == "policy_id: unique" for c in validate(frames))


def test_rejects_empty_dataset(frames):
    frames["incentives"] = frames["incentives"].iloc[:0]
    assert any(c.affected and c.rule == "nonempty dataset" for c in validate(frames))


def test_reconciliation_detects_changed_values_at_same_count(frames):
    changed = {name: frame.copy() for name, frame in frames.items()}
    changed["policies"].loc[0, "premium_amount"] = "101"
    assert any(c.affected and "values match" in c.rule for c in reconcile(frames, changed))


def test_manifest_detects_tampering(csv_directory):
    verify_manifest(csv_directory)
    with (csv_directory / "agents.csv").open("a") as stream:
        stream.write("\n")
    with pytest.raises(ValueError, match="manifest mismatch"):
        verify_manifest(csv_directory)


def test_csv_header_and_literal_none_category(csv_directory):
    path = csv_directory / "leads.csv"
    frame = pd.read_csv(path, keep_default_na=False)
    frame.loc[0, "appointment_status"] = "None"
    frame.to_csv(path, index=False)
    assert read_csvs(csv_directory)["leads"].loc[0, "appointment_status"] == "None"
    frame.rename(columns={"lead_id": "wrong_id"}).to_csv(path, index=False)
    with pytest.raises(ValueError, match="header"):
        read_csvs(csv_directory)
