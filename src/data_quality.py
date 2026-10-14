"""Validate synthetic Agency data before loading and against a PostgreSQL snapshot."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg
from psycopg import sql

from dataset import AS_OF, CONTRACT, ROOT, SCHEMA, connection_string, read_csvs, verify_manifest


@dataclass
class Check:
    table: str
    rule: str
    affected: int
    samples: str
    severity: str = "ERROR"
    scope: str = "CSV"


def validate(raw: dict[str, pd.DataFrame], as_of: str = AS_OF, scope: str = "CSV") -> list[Check]:
    """Return every rule, including passes; zero affected rows means the rule passed."""
    results = []
    frames = {}
    cutoff = pd.Timestamp(as_of)

    def check(table, rule, mask, severity="ERROR"):
        mask = pd.Series(mask, index=raw[table].index).fillna(False).astype(bool)
        key = next(iter(CONTRACT[table]))
        samples = ", ".join(raw[table].loc[mask, key].head(5).fillna("<missing>").astype(str))
        results.append(Check(table, rule, int(mask.sum()), samples, severity, scope))

    for table, fields in CONTRACT.items():
        source = raw[table]
        if list(source.columns) != list(fields):
            raise ValueError(f"{table}: columns do not match contract")
        results.append(Check(table, "nonempty dataset", int(source.empty), "", scope=scope))
        frame = source.copy()
        frames[table] = frame
        check(table, "duplicate complete rows", source.duplicated(keep=False))
        for name, spec in fields.items():
            values = source[name]
            if spec["required"]:
                check(table, f"{name}: required", values.isna() | values.eq(""))
            if spec.get("primary_key"):
                check(table, f"{name}: unique", values.notna() & values.duplicated(keep=False))
            if "allowed" in spec:
                check(
                    table,
                    f"{name}: allowed category",
                    values.notna() & ~values.isin(spec["allowed"]),
                )
            if "references" in spec:
                parent, key = spec["references"]
                check(
                    table,
                    f"{name}: references {parent}",
                    values.notna() & ~values.isin(raw[parent][key]),
                )
            kind = spec["type"]
            if kind == "DATE":
                parsed = pd.to_datetime(values, format="%Y-%m-%d", errors="coerce")
                check(table, f"{name}: valid date", values.notna() & parsed.isna())
                frame[name] = parsed
                if name != "maturity_date":
                    check(table, f"{name}: within snapshot", parsed > cutoff)
            elif kind == "BOOLEAN":
                normalized = values.astype("string").str.lower()
                check(
                    table,
                    f"{name}: valid boolean",
                    values.notna() & ~normalized.isin(["true", "false"]),
                )
                frame[name] = normalized.map({"true": True, "false": False}).astype("boolean")
            elif kind.startswith("NUMERIC") or kind == "INTEGER":
                parsed = pd.to_numeric(values, errors="coerce")
                check(
                    table,
                    f"{name}: finite number",
                    values.notna() & (parsed.isna() | ~np.isfinite(parsed)),
                )
                if kind == "INTEGER":
                    check(table, f"{name}: whole number", parsed.notna() & parsed.mod(1).ne(0))
                else:
                    # PostgreSQL NUMERIC rounds extra decimals: reject silent money changes.
                    check(
                        table,
                        f"{name}: at most two decimals",
                        parsed.notna() & (parsed * 100 - (parsed * 100).round()).abs().gt(0.0001),
                    )
                frame[name] = parsed
            elif kind.startswith("VARCHAR"):
                limit = int(kind.split("(")[1].rstrip(")"))
                check(table, f"{name}: text length", values.astype("string").str.len() > limit)

    customers, agents, policies, leads, payments, history, targets, incentives = (
        frames[name]
        for name in (
            "customers",
            "agents",
            "policies",
            "leads",
            "premium_payments",
            "policy_status_history",
            "sales_targets",
            "incentives",
        )
    )

    def parent_values(child, foreign_key, parent, field):
        # Duplicates are reported above; avoid multiplying rows in these lookups.
        lookup = frames[parent].drop_duplicates(foreign_key).set_index(foreign_key)[field]
        return child[foreign_key].map(lookup)

    check("customers", "birth before onboarding", customers.date_of_birth >= customers.created_date)
    check("agents", "nonnegative experience", agents.experience_years < 0)
    check(
        "agents",
        "exit date agrees with status",
        agents.status.eq("Exited") != agents.exit_date.notna(),
    )
    check("agents", "exit after join", agents.exit_date < agents.join_date)
    check(
        "agents",
        "join on/after unit launch",
        agents.join_date < parent_values(agents, "agency_unit_id", "agency_units", "launch_date"),
    )
    for table, field in (
        ("policies", "issue_date"),
        ("leads", "lead_date"),
        ("leads", "conversion_date"),
        ("sales_targets", "target_month"),
    ):
        frame = frames[table]
        joined = parent_values(frame, "agent_id", "agents", "join_date")
        exited = parent_values(frame, "agent_id", "agents", "exit_date")
        check(
            table,
            f"{field}: within agent service",
            (frame[field] < joined) | (frame[field] > exited),
        )
    check(
        "policies",
        "issue on/after customer onboarding",
        policies.issue_date < parent_values(policies, "customer_id", "customers", "created_date"),
    )
    check(
        "leads",
        "conversion on/after customer onboarding",
        leads.conversion_date < parent_values(leads, "customer_id", "customers", "created_date"),
    )
    check(
        "leads",
        "conversion flag agrees with date",
        leads.converted != leads.conversion_date.notna(),
    )
    check("leads", "conversion after lead", leads.conversion_date < leads.lead_date)
    check(
        "leads",
        "converted lead has customer and approved application",
        leads.converted & (leads.customer_id.isna() | leads.application_status.ne("Approved")),
    )
    check(
        "leads", "converted lead contacted", leads.converted & leads.contact_status.ne("Contacted")
    )
    for field in ("premium_amount", "annualized_premium", "sum_assured", "policy_term_years"):
        check("policies", f"{field}: positive", policies[field] <= 0)
    factor = policies.payment_frequency.map(
        {"Monthly": 12, "Quarterly": 4, "Semi-Annual": 2, "Annual": 1}
    )
    check(
        "policies",
        "annualization within UGX 0.01",
        (policies.annualized_premium - policies.premium_amount * factor).abs() > 0.010001,
    )
    check("policies", "Agency distribution only", policies.distribution_channel.ne("Agency"))
    check("policies", "maturity after issue", policies.maturity_date <= policies.issue_date)
    for status, field in (("Lapsed", "lapse_date"), ("Surrendered", "surrender_date")):
        check(
            "policies",
            f"{status}: status/date consistency",
            policies.policy_status.eq(status) != policies[field].notna(),
        )
        check("policies", f"{field}: after issue", policies[field] < policies.issue_date)
    check(
        "premium_payments",
        "unique installment",
        payments.duplicated(["policy_id", "due_date"], keep=False),
    )
    check(
        "premium_payments",
        "positive due and nonnegative paid",
        (payments.amount_due <= 0) | (payments.amount_paid < 0),
    )
    check(
        "premium_payments",
        "installment agrees with policy",
        (
            payments.amount_due - parent_values(payments, "policy_id", "policies", "premium_amount")
        ).abs()
        > 0.01,
    )
    check(
        "premium_payments",
        "due on/after issue",
        payments.due_date < parent_values(payments, "policy_id", "policies", "issue_date"),
    )
    for field in ("lapse_date", "surrender_date"):
        check(
            "premium_payments",
            f"due before {field}",
            payments.due_date > parent_values(payments, "policy_id", "policies", field),
        )
    check(
        "premium_payments",
        "payment date agrees with amount",
        payments.amount_paid.gt(0) != payments.payment_date.notna(),
    )
    check(
        "premium_payments",
        "missed means zero paid and no date",
        payments.payment_status.eq("Missed")
        & (payments.amount_paid.ne(0) | payments.payment_date.notna()),
    )
    check(
        "premium_payments",
        "partial amount between zero and due",
        payments.payment_status.eq("Partial")
        & ((payments.amount_paid <= 0) | (payments.amount_paid >= payments.amount_due)),
    )
    check(
        "premium_payments",
        "Paid/Late settled in full",
        payments.payment_status.isin(["Paid", "Late"])
        & payments.amount_paid.ne(payments.amount_due),
    )
    delay = (payments.payment_date - payments.due_date).dt.days
    check(
        "premium_payments",
        "Paid within synthetic two-day tolerance",
        payments.payment_status.eq("Paid") & ((delay < 0) | (delay > 2)),
    )
    check(
        "premium_payments",
        "Late exceeds two-day tolerance",
        payments.payment_status.eq("Late") & (delay <= 2),
    )
    check(
        "policy_status_history",
        "event on/after issue",
        history.status_date < parent_values(history, "policy_id", "policies", "issue_date"),
    )
    check(
        "policy_status_history",
        "unique policy event date",
        history.duplicated(["policy_id", "status_date"], keep=False),
    )
    latest = history.sort_values(["status_date", "status_history_id"]).drop_duplicates(
        "policy_id", keep="last"
    )
    latest_status = policies.policy_id.map(latest.set_index("policy_id").status).replace(
        "Reinstated", "Active"
    )
    check(
        "policies",
        "current status agrees with latest history",
        latest_status.isna() | latest_status.ne(policies.policy_status),
    )
    initial = (
        history.loc[history.status.eq("Active")]
        .drop_duplicates("policy_id")
        .set_index("policy_id")
        .status_date
    )
    for status, field in (("Lapsed", "lapse_date"), ("Surrendered", "surrender_date")):
        terminal = history.loc[history.status.eq(status)].drop_duplicates("policy_id")
        terminal_dates = policies.policy_id.map(terminal.set_index("policy_id").status_date)
        check(
            "policies",
            f"{status}: history date agrees with policy",
            policies.policy_status.eq(status) & terminal_dates.ne(policies[field]),
        )
    check(
        "policies",
        "initial Active event on issue date",
        policies.policy_id.map(initial).ne(policies.issue_date),
    )
    check("policies", "at least one installment", ~policies.policy_id.isin(payments.policy_id))
    check(
        "sales_targets",
        "unique agent/month",
        targets.duplicated(["agent_id", "target_month"], keep=False),
    )
    check("sales_targets", "month begins on day one", targets.target_month.dt.day.ne(1))
    for field in ("policy_target", "premium_target", "new_customer_target"):
        check("sales_targets", f"{field}: nonnegative", targets[field] < 0)
    check("incentives", "campaign end on/after start", incentives.end_date < incentives.start_date)
    check(
        "incentives",
        "unique agent/campaign",
        incentives.duplicated(["agent_id", "campaign_name"], keep=False),
    )
    check(
        "incentives",
        "nonnegative threshold and award",
        (incentives.threshold < 0) | (incentives.incentive_amount < 0),
    )
    check(
        "incentives",
        "qualification agrees with award",
        incentives.qualified != incentives.incentive_amount.gt(0),
    )
    joined = parent_values(incentives, "agent_id", "agents", "join_date")
    exited = parent_values(incentives, "agent_id", "agents", "exit_date")
    check(
        "incentives",
        "campaign overlaps agent service",
        (incentives.end_date < joined) | (incentives.start_date > exited),
    )
    return results


def read_database(conn) -> dict[str, pd.DataFrame]:
    frames = {}
    for table, fields in CONTRACT.items():
        query = sql.SQL("SELECT {} FROM {}.{}").format(
            sql.SQL(", ").join(map(sql.Identifier, fields)),
            sql.Identifier(SCHEMA),
            sql.Identifier(table),
        )
        cursor = conn.execute(query)
        # String normalization permits identical checks for PostgreSQL and CSV inputs.
        frames[table] = pd.DataFrame(cursor.fetchall(), columns=list(fields)).astype("string")
    return frames


def reconcile(source, loaded) -> list[Check]:
    results = []
    for table, fields in CONTRACT.items():
        key = next(iter(fields))
        left = source[table].sort_values(key).reset_index(drop=True)
        right = loaded[table].sort_values(key).reset_index(drop=True)
        results.append(
            Check(table, "PostgreSQL row count matches CSV", abs(len(left) - len(right)), "")
        )
        if len(left) != len(right):
            continue
        different = pd.Series(False, index=left.index)
        for field, spec in fields.items():
            a, b = left[field], right[field]
            if spec["type"].startswith("NUMERIC") or spec["type"] == "INTEGER":
                a, b = pd.to_numeric(a), pd.to_numeric(b)
            elif spec["type"] == "BOOLEAN":
                a, b = a.str.lower(), b.str.lower()
            equal = a.eq(b).fillna(False) | (a.isna() & b.isna())
            different |= ~equal
        results.append(
            Check(
                table,
                "PostgreSQL values match CSV",
                int(different.sum()),
                ", ".join(left.loc[different, key].head(5)),
            )
        )
    for result in results:
        result.scope = "Reconciliation"
    return results


def write_report(path: Path, frames, checks, scope: str, provenance: dict | None = None):
    failures = [item for item in checks if item.affected and item.severity == "ERROR"]
    status = (
        "FAIL — not ready"
        if failures
        else (
            "PASS — PostgreSQL validated"
            if scope == "PostgreSQL + CSV reconciliation"
            else "CSV checks passed — PostgreSQL readiness not yet established"
        )
    )
    lines = [
        "# Phase 2 data quality report",
        "",
        f"**Result: {status}**",
        "",
        f"- Run (UTC): {datetime.now(UTC).isoformat()}",
        f"- Scope: {scope}",
        f"- Synthetic snapshot: {AS_OF}; seed: 42",
        "- All records are synthetic.",
        f"- Rules evaluated: {len(checks)}; failing rules: {len(failures)}.",
        "",
        "## Dataset coverage",
        "",
        "| Table | Rows |",
        "|---|---:|",
    ]
    lines.extend(f"| {table} | {len(frame):,} |" for table, frame in frames.items())
    lines += [
        "",
        "## Validation results",
        "",
        "Affected counts are per rule and can overlap. Zero means the rule passed; "
        "sample IDs identify synthetic records for investigation.",
        "",
        "| Scope | Table | Rule | Failure severity | Affected | Sample IDs |",
        "|---|---|---|---|---:|---|",
    ]
    lines.extend(
        f"| {c.scope} | {c.table} | {c.rule} | {c.severity} | {c.affected:,} | {c.samples} |"
        for c in checks
    )
    lines += [
        "",
        "## Agency interpretation and limits",
        "",
        "Baseline defects and corrections: [phase2_baseline.md](phase2_baseline.md).",
        "",
        "Passing checks establishes structural and documented business-rule consistency, "
        "not commercial success or predictive validity. No agent rankings, persistency rates "
        "or incentive-effectiveness findings are asserted here.",
        "",
        "- Installments use fixed 30/91/182/365-day steps, not contract calendar anniversaries.",
        "- Paid permits a synthetic two-day tolerance; Late starts after two days.",
        "- Missed means unpaid at the snapshot, including recently due installments; it does "
        "not establish delinquency or a contractual grace-period breach.",
        "- Lead-to-policy linkage has no lead_id on policies. Customer/agent/date matching "
        "cannot prove a unique attribution; do not equate policy counts with converted leads.",
        "- Manager and supervisor IDs are external synthetic labels, not agent foreign keys.",
        "- Agent unit/status are current snapshots; transfers and inactivity histories are absent.",
        "- Incentive qualification and lapse are simulated, not derived from threshold "
        "achievement or a contractual arrears engine. They cannot support causal conclusions.",
        "- September 2026 is incomplete at the September 1 snapshot; targets cover full months.",
        "- Persistency eligibility, observation windows and reinstatement treatment belong "
        "to the next analysis phase.",
    ]
    if provenance:
        lines += [
            "",
            "## Reproduction provenance",
            "",
            "```json",
            json.dumps(provenance, indent=2),
            "```",
        ]
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data/raw")
    parser.add_argument("--database", action="store_true", help="Validate DATABASE_URL read-only")
    parser.add_argument("--report", type=Path, default=ROOT / "docs/data_quality_report.md")
    args = parser.parse_args()
    try:
        provenance = verify_manifest(args.data_dir)
        frames = read_csvs(args.data_dir)
        checks = validate(frames)
        scope = "CSV only"
        if args.database:
            with psycopg.connect(connection_string()) as conn:
                conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
                loaded = read_database(conn)
                checks += validate(loaded, scope="PostgreSQL") + reconcile(frames, loaded)
                provenance["postgresql_version"] = conn.info.server_version
            scope = "PostgreSQL + CSV reconciliation"
        write_report(args.report, frames, checks, scope, provenance)
    except (ValueError, OSError, psycopg.Error) as exc:
        # Never echo database connection strings or credentials in CLI errors.
        print(
            f"Validation could not complete ({type(exc).__name__}); any previous report is stale."
        )
        return 2
    failures = sum(c.affected > 0 and c.severity == "ERROR" for c in checks)
    print(f"{len(checks)} rules; {failures} failures. Report: {args.report}")
    return int(failures > 0)


if __name__ == "__main__":
    raise SystemExit(main())
