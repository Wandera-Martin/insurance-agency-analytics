"""Load all nine synthetic CSVs atomically and validate before commit."""

from __future__ import annotations

import argparse
from pathlib import Path

import psycopg
from psycopg import sql

from data_quality import read_database, reconcile, validate, write_report
from dataset import CONTRACT, ROOT, SCHEMA, connection_string, read_csvs, verify_manifest


def load(conn, directory: Path, replace: bool = False):
    """The caller owns the transaction. Any exception must roll back the complete load."""
    provenance = verify_manifest(directory)
    source = read_csvs(directory)
    checks = validate(source)
    if any(c.affected and c.severity == "ERROR" for c in checks):
        raise ValueError("Source validation failed; run data_quality.py for rule-level diagnostics")
    # Serialize this workflow, including initialization, without touching unrelated schemas.
    conn.execute("SELECT pg_advisory_xact_lock(240902, 2)")
    existing = conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = %s",
        (SCHEMA,),
    ).fetchall()
    if not existing:
        conn.execute((ROOT / "sql/01_schema.sql").read_text(encoding="utf-8"))
    elif set(CONTRACT) != {row[0] for row in existing}:
        raise ValueError(
            "Existing schema differs from the nine-table contract; use a fresh database"
        )
    tables = sql.SQL(", ").join(sql.Identifier(SCHEMA, table) for table in CONTRACT)
    conn.execute(sql.SQL("LOCK TABLE {} IN ACCESS EXCLUSIVE MODE").format(tables))
    populated = any(
        conn.execute(
            sql.SQL("SELECT EXISTS (SELECT 1 FROM {})").format(sql.Identifier(SCHEMA, table))
        ).fetchone()[0]
        for table in CONTRACT
    )
    if populated and not replace:
        raise ValueError(
            "Tables contain rows; use --replace to explicitly replace this synthetic snapshot"
        )
    if replace:
        # All FK participants are named; no CASCADE into objects outside this workflow.
        conn.execute(sql.SQL("TRUNCATE TABLE {}").format(tables))
    for table, fields in CONTRACT.items():
        statement = sql.SQL("COPY {} ({}) FROM STDIN WITH (FORMAT CSV, HEADER TRUE)").format(
            sql.Identifier(SCHEMA, table), sql.SQL(", ").join(map(sql.Identifier, fields))
        )
        with (
            conn.cursor() as cursor,
            cursor.copy(statement) as copy,
            (directory / f"{table}.csv").open("rb") as stream,
        ):
            while chunk := stream.read(1024 * 1024):
                copy.write(chunk)
    # Detect a file edited while validation/COPY was in progress.
    if verify_manifest(directory) != provenance:
        raise ValueError("Source changed during load")
    loaded = read_database(conn)
    checks += validate(loaded, scope="PostgreSQL") + reconcile(source, loaded)
    if any(c.affected and c.severity == "ERROR" for c in checks):
        raise ValueError("Database validation or reconciliation failed; transaction will roll back")
    provenance["postgresql_version"] = conn.info.server_version
    for table in CONTRACT:
        conn.execute(sql.SQL("ANALYZE {}").format(sql.Identifier(SCHEMA, table)))
    return source, checks, provenance


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data/raw")
    parser.add_argument(
        "--replace", action="store_true", help="Replace existing synthetic rows atomically"
    )
    parser.add_argument("--report", type=Path, default=ROOT / "docs/data_quality_report.md")
    args = parser.parse_args()
    try:
        with psycopg.connect(connection_string()) as conn:
            conn.execute("SET LOCAL lock_timeout = '15s'")
            conn.execute("SET LOCAL statement_timeout = '120s'")
            frames, checks, provenance = load(conn, args.data_dir, args.replace)
    except ValueError as exc:
        print(f"Load not committed: {exc}")
        return 1
    except (OSError, psycopg.Error) as exc:
        print(
            f"Load not committed ({type(exc).__name__}); check files, database access and schema."
        )
        return 1
    try:
        # A PASS report is only published after the database commit succeeds.
        write_report(args.report, frames, checks, "PostgreSQL + CSV reconciliation", provenance)
    except OSError:
        print("Load committed, but report write failed. Rerun data_quality.py --database.")
        return 2
    print(f"Committed nine validated tables. Report: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
