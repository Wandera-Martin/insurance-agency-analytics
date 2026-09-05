"""Shared CSV contract, provenance and connection configuration for Phase 2."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "insurance_analytics"
CONTRACT = json.loads((Path(__file__).with_name("dataset_contract.json")).read_text())
TABLES = tuple(CONTRACT)
AS_OF = "2026-09-01"


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_csvs(directory: Path) -> dict[str, pd.DataFrame]:
    """Keep raw strings so invalid dates/booleans cannot silently become valid nulls."""
    frames = {}
    for table, fields in CONTRACT.items():
        path = directory / f"{table}.csv"
        frame = pd.read_csv(path, dtype="string", keep_default_na=False)
        if list(frame.columns) != list(fields):
            raise ValueError(f"{table}: CSV header must exactly match the dataset contract")
        frames[table] = frame.replace("", pd.NA)
    return frames


def manifest(directory: Path) -> dict:
    return {
        "synthetic": True,
        "seed": 42,
        "as_of": AS_OF,
        "generator_sha256": sha256(ROOT / "src/generate_synthetic_data.py"),
        "files": {f"{table}.csv": sha256(directory / f"{table}.csv") for table in TABLES},
    }


def verify_manifest(directory: Path) -> dict:
    value = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    if value != manifest(directory):
        raise ValueError(
            "Synthetic manifest mismatch: regenerate all nine CSVs with this generator"
        )
    return value


def connection_string() -> str:
    value = os.environ.get("DATABASE_URL")
    if not value:
        raise ValueError("Set DATABASE_URL to a dedicated synthetic PostgreSQL database")
    return value
