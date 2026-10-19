"""Train, validate, freeze, test, and operationalize the Phase 6 lapse-risk model."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg
import sklearn
from psycopg import sql
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from dataset import AS_OF, ROOT, connection_string, sha256

TRAIN_END = pd.Timestamp("2025-12-31")
VALIDATION_START = pd.Timestamp("2026-01-31")
VALIDATION_END = pd.Timestamp("2026-03-31")
TEST_START = pd.Timestamp("2026-04-30")
TEST_END = pd.Timestamp("2026-05-31")
RANDOM_STATE = 42
TOP_K = (0.05, 0.10, 0.20)

CATEGORICAL_FEATURES = [
    "region",
    "product_name",
    "payment_frequency",
    "status_at_observation",
    "income_band",
    "acquisition_channel",
    "customer_region",
]

NUMERIC_FEATURES = [
    "premium_amount",
    "annualized_premium",
    "sum_assured",
    "policy_term_years",
    "policy_age_days",
    "policy_age_months",
    "premium_to_sum_assured",
    "age_at_issue",
    "installments_due_to_date",
    "paid_count_to_date",
    "late_count_to_date",
    "missed_count_to_date",
    "partial_count_to_date",
    "paid_rate_to_date",
    "late_rate_to_date",
    "missed_rate_to_date",
    "partial_rate_to_date",
    "amount_due_to_date",
    "amount_paid_to_date",
    "payment_completion_rate_to_date",
    "installments_due_last_90d",
    "paid_count_last_90d",
    "late_count_last_90d",
    "missed_count_last_90d",
    "partial_count_last_90d",
    "paid_rate_last_90d",
    "late_rate_last_90d",
    "missed_rate_last_90d",
    "partial_rate_last_90d",
    "amount_due_last_90d",
    "amount_paid_last_90d",
    "payment_completion_rate_last_90d",
    "days_since_last_payment",
    "days_since_last_late_payment",
    "days_since_last_missed_installment",
]

MODEL_FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES
TRACE_COLUMNS = ["policy_id", "customer_id", "agent_id", "agency_unit_id"]
DIAGNOSTIC_COLUMNS = ["gender", "age_at_issue_band", "customer_region", "income_band"]
FORBIDDEN_FEATURE_TOKENS = (
    "_id",
    "lapse_date",
    "surrender_date",
    "future",
    "target",
    "outcome",
    "current_policy_status",
    "segment",
    "profile",
    "gender",
)


def _read_relation(conn, schema: str, relation: str, order_by: tuple[str, ...]) -> pd.DataFrame:
    identifier = sql.Identifier(schema, relation)
    ordering = sql.SQL(", ").join(map(sql.Identifier, order_by))
    with conn.cursor() as cursor:
        cursor.execute(sql.SQL("SELECT * FROM {} ORDER BY {}").format(identifier, ordering))
        columns = [column.name for column in cursor.description]
        return pd.DataFrame.from_records(cursor.fetchall(), columns=columns)


def load_inputs(conn) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load only trusted Phase 6 SQL relations from a repeatable-read snapshot."""
    required = (
        "lapse_risk.snapshot",
        "lapse_risk.model_dataset",
        "lapse_risk.monthly_target_distribution",
        "lapse_risk.current_scoring_population",
    )
    missing = [
        relation
        for relation in required
        if conn.execute("SELECT to_regclass(%s)", (relation,)).fetchone()[0] is None
    ]
    if missing:
        raise ValueError(f"Required Phase 6 relations are missing: {', '.join(missing)}")
    snapshot = conn.execute("SELECT as_of FROM lapse_risk.snapshot").fetchone()[0]
    if snapshot.isoformat() != AS_OF:
        raise ValueError(f"Phase 6 snapshot {snapshot} differs from locked {AS_OF}")
    panel = _read_relation(conn, "lapse_risk", "model_dataset", ("observation_date", "policy_id"))
    monthly = _read_relation(
        conn, "lapse_risk", "monthly_target_distribution", ("observation_date",)
    )
    current = _read_relation(conn, "lapse_risk", "current_scoring_population", ("policy_id",))
    return panel, monthly, current


def validate_inputs(panel: pd.DataFrame, current: pd.DataFrame) -> None:
    required_panel = set(MODEL_FEATURES + TRACE_COLUMNS + DIAGNOSTIC_COLUMNS)
    required_panel.update(("observation_date", "lapse_next_90d"))
    missing = sorted(required_panel - set(panel.columns))
    if missing:
        raise ValueError(f"Historical panel is missing columns: {missing}")
    missing_current = sorted(
        (set(MODEL_FEATURES + TRACE_COLUMNS) | {"observation_date"}) - set(current)
    )
    if missing_current:
        raise ValueError(f"Current scoring population is missing columns: {missing_current}")
    if "lapse_next_90d" in current.columns:
        raise ValueError("Current scoring population must not contain a fabricated target")
    offending = [
        feature
        for feature in MODEL_FEATURES
        if any(token in feature.lower() for token in FORBIDDEN_FEATURE_TOKENS)
    ]
    if offending:
        raise ValueError(f"Forbidden or leaky training features selected: {offending}")
    if panel["lapse_next_90d"].isna().any():
        raise ValueError("Mature model dataset contains null targets")
    if panel.duplicated(["policy_id", "observation_date"]).any():
        raise ValueError("Historical panel is not unique by policy and observation date")
    if current.duplicated("policy_id").any():
        raise ValueError("Current scoring population is not unique by policy")
    if (pd.to_numeric(current["policy_age_days"]) < 30).any():
        raise ValueError("Current scoring population contains a policy younger than 30 days")
    if not current["status_at_observation"].isin(("Active", "Grace", "Reinstated")).all():
        raise ValueError("Current scoring population contains an ineligible historical status")
    if not (pd.to_datetime(current["observation_date"]) == pd.Timestamp(AS_OF)).all():
        raise ValueError("Current scoring population does not use the locked snapshot")


def prepare_types(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["observation_date"] = pd.to_datetime(result["observation_date"])
    for column in NUMERIC_FEATURES:
        result[column] = pd.to_numeric(result[column], errors="coerce")
    if "lapse_next_90d" in result:
        result["lapse_next_90d"] = pd.to_numeric(result["lapse_next_90d"]).astype("int8")
    return result


def temporal_split(panel: pd.DataFrame) -> dict[str, pd.DataFrame]:
    train = panel.loc[panel["observation_date"] <= TRAIN_END].copy()
    validation = panel.loc[
        panel["observation_date"].between(VALIDATION_START, VALIDATION_END)
    ].copy()
    test = panel.loc[panel["observation_date"].between(TEST_START, TEST_END)].copy()
    if any(frame.empty for frame in (train, validation, test)):
        raise ValueError("One or more locked temporal splits are empty")
    if not train["observation_date"].max() < validation["observation_date"].min():
        raise ValueError("Train dates do not strictly precede validation dates")
    if not validation["observation_date"].max() < test["observation_date"].min():
        raise ValueError("Validation dates do not strictly precede test dates")
    if validation["lapse_next_90d"].sum() < 100 or test["lapse_next_90d"].sum() < 100:
        raise ValueError("Validation or test positives are inadequate; stop before modelling")
    return {"train": train, "validation": validation, "test": test}


def build_pipeline(model) -> Pipeline:
    numeric = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
            ("scale", StandardScaler(with_mean=False)),
        ]
    )
    categorical = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    preprocess = ColumnTransformer(
        [("numeric", numeric, NUMERIC_FEATURES), ("categorical", categorical, CATEGORICAL_FEATURES)]
    )
    return Pipeline([("preprocess", preprocess), ("model", model)])


def topk_metrics(y_true, scores, percentages: tuple[float, ...] = TOP_K) -> list[dict]:
    y = np.asarray(y_true, dtype=int)
    probability = np.asarray(scores, dtype=float)
    positives = int(y.sum())
    prevalence = float(y.mean())
    order = np.argsort(-probability, kind="mergesort")
    rows = []
    for fraction in percentages:
        selected = order[: max(1, math.ceil(len(y) * fraction))]
        captured = int(y[selected].sum())
        selected_rate = float(y[selected].mean())
        rows.append(
            {
                "k_percent": int(fraction * 100),
                "selected_rows": len(selected),
                "captured_positives": captured,
                "recall_at_k": captured / positives if positives else np.nan,
                "lift_at_k": selected_rate / prevalence if prevalence else np.nan,
            }
        )
    return rows


def operational_threshold(scores, fraction: float = 0.10) -> float:
    probability = np.asarray(scores, dtype=float)
    rank = max(1, math.ceil(len(probability) * fraction))
    return float(np.sort(probability)[-rank])


def discrimination_metrics(y_true, scores, threshold: float) -> dict:
    y = np.asarray(y_true, dtype=int)
    probability = np.asarray(scores, dtype=float)
    predicted = (probability >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, predicted, labels=[0, 1]).ravel()
    return {
        "pr_auc": average_precision_score(y, probability),
        "roc_auc": roc_auc_score(y, probability),
        "precision": precision_score(y, predicted, zero_division=0),
        "recall": recall_score(y, predicted, zero_division=0),
        "f1": f1_score(y, predicted, zero_division=0),
        "threshold": threshold,
        "true_negative": int(tn),
        "false_positive": int(fp),
        "false_negative": int(fn),
        "true_positive": int(tp),
    }


def calibration_diagnostics(y_true, scores, bins: int = 10) -> tuple[dict, pd.DataFrame]:
    y = np.asarray(y_true, dtype=int)
    probability = np.clip(np.asarray(scores, dtype=float), 1e-8, 1 - 1e-8)
    frame = pd.DataFrame({"target": y, "score": probability})
    frame["bin"] = pd.qcut(frame["score"].rank(method="first"), q=bins, labels=False)
    grouped = (
        frame.groupby("bin", observed=True)
        .agg(
            rows=("target", "size"),
            mean_predicted_risk=("score", "mean"),
            observed_rate=("target", "mean"),
        )
        .reset_index()
    )
    grouped["absolute_gap"] = (grouped["mean_predicted_risk"] - grouped["observed_rate"]).abs()
    expected_calibration_error = float(
        (grouped["rows"] * grouped["absolute_gap"]).sum() / grouped["rows"].sum()
    )
    if np.unique(probability).size == 1:
        slope = 0.0
        intercept = float(np.log(y.mean() / (1 - y.mean()))) if 0 < y.mean() < 1 else np.nan
    else:
        logits = np.log(probability / (1 - probability)).reshape(-1, 1)
        calibration_model = LogisticRegression(C=1_000_000, solver="lbfgs")
        calibration_model.fit(logits, y)
        slope = float(calibration_model.coef_[0, 0])
        intercept = float(calibration_model.intercept_[0])
    summary = {
        "brier_score": brier_score_loss(y, probability),
        "mean_predicted_risk": float(probability.mean()),
        "observed_rate": float(y.mean()),
        "calibration_in_the_large": float(probability.mean() - y.mean()),
        "calibration_intercept": intercept,
        "calibration_slope": slope,
        "expected_calibration_error": expected_calibration_error,
    }
    return summary, grouped


def select_model(validation: dict[str, dict]) -> tuple[str, str]:
    logistic = validation["logistic_regression"]
    challenger = validation["random_forest"]
    logistic_close = (
        logistic["pr_auc"] >= 0.95 * challenger["pr_auc"]
        and logistic["recall_at_10"] >= 0.95 * challenger["recall_at_10"]
        and logistic["brier_score"] <= 1.10 * challenger["brier_score"]
    )
    if logistic_close:
        return (
            "logistic_regression",
            "Logistic Regression was within 5% of challenger PR-AUC and Recall@10, "
            "within 10% on Brier score, and is easier to explain.",
        )
    if challenger["pr_auc"] > logistic["pr_auc"]:
        return (
            "random_forest",
            "Random Forest delivered a material validation PR-AUC advantage; validation "
            "top-K capture, calibration, and permutation importance were reviewed separately.",
        )
    return (
        "logistic_regression",
        "Logistic Regression had the stronger validation PR-AUC and the clearer explanation.",
    )


def coefficient_importance(pipeline: Pipeline) -> pd.DataFrame:
    names = pipeline.named_steps["preprocess"].get_feature_names_out()
    coefficients = pipeline.named_steps["model"].coef_[0]
    return pd.DataFrame(
        {
            "model": "logistic_regression",
            "method": "transformed_coefficient",
            "feature": names,
            "importance": coefficients,
            "absolute_importance": np.abs(coefficients),
        }
    ).sort_values("absolute_importance", ascending=False)


def forest_importance(
    pipeline: Pipeline, validation: pd.DataFrame, sample_size: int = 5_000
) -> pd.DataFrame:
    sample = validation.sample(min(sample_size, len(validation)), random_state=RANDOM_STATE)
    result = permutation_importance(
        pipeline,
        sample[MODEL_FEATURES],
        sample["lapse_next_90d"],
        scoring="average_precision",
        n_repeats=2,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    return pd.DataFrame(
        {
            "model": "random_forest",
            "method": "validation_permutation_pr_auc",
            "feature": MODEL_FEATURES,
            "importance": result.importances_mean,
            "importance_std": result.importances_std,
            "absolute_importance": np.abs(result.importances_mean),
        }
    ).sort_values("absolute_importance", ascending=False)


def fairness_diagnostics(test: pd.DataFrame, scores: np.ndarray, threshold: float) -> pd.DataFrame:
    working = test[DIAGNOSTIC_COLUMNS + ["lapse_next_90d"]].copy()
    working["predicted_risk"] = scores
    working["predicted_class"] = (scores >= threshold).astype(int)
    rows = []
    for attribute in DIAGNOSTIC_COLUMNS:
        for group, subset in working.groupby(attribute, dropna=False):
            y = subset["lapse_next_90d"].to_numpy(dtype=int)
            prediction = subset["predicted_class"].to_numpy(dtype=int)
            row = {
                "attribute": attribute,
                "group": "Missing" if pd.isna(group) else str(group),
                "sample_size": len(subset),
                "positives": int(y.sum()),
                "positive_prevalence": float(y.mean()),
                "average_predicted_risk": float(subset["predicted_risk"].mean()),
                "precision": precision_score(y, prediction, zero_division=0),
                "recall": recall_score(y, prediction, zero_division=0),
                "pr_auc": np.nan,
            }
            if len(subset) >= 100 and y.sum() >= 10 and y.sum() < len(subset):
                row["pr_auc"] = average_precision_score(y, subset["predicted_risk"])
            rows.append(row)
    return pd.DataFrame(rows)


def assign_risk_tiers(scores: pd.Series, policy_ids: pd.Series) -> pd.DataFrame:
    order = pd.DataFrame({"risk_score": scores, "policy_id": policy_ids}).sort_values(
        ["risk_score", "policy_id"], ascending=[False, True], kind="mergesort"
    )
    order["position"] = np.arange(1, len(order) + 1)
    order["risk_percentile"] = 1 - (order["position"] - 1) / len(order)
    priority_end = math.ceil(len(order) * 0.10)
    watch_end = math.ceil(len(order) * 0.30)
    order["risk_tier"] = np.select(
        [order["position"] <= priority_end, order["position"] <= watch_end],
        ["Priority", "Watch"],
        default="Routine",
    )
    return order.set_index("policy_id")[["risk_percentile", "risk_tier"]]


def observable_reason_flags(row: pd.Series) -> str:
    flags = []
    if row["missed_count_last_90d"] > 0:
        flags.append("Recent missed premium")
    if row["late_count_to_date"] >= 2:
        flags.append("Repeated late payments")
    if (
        pd.notna(row["payment_completion_rate_last_90d"])
        and row["payment_completion_rate_last_90d"] < 0.80
    ):
        flags.append("Low recent payment completion")
    if row["status_at_observation"] == "Grace":
        flags.append("Currently in Grace")
    if pd.notna(row["missed_rate_to_date"]) and row["missed_rate_to_date"] >= 0.20:
        flags.append("High missed-payment rate")
    if pd.notna(row["late_rate_to_date"]) and row["late_rate_to_date"] >= 0.20:
        flags.append("High late-payment rate")
    if row["policy_age_days"] < 180:
        flags.append("Short policy tenure")
    return "; ".join(flags) if flags else "No configured observable risk signal"


def _hash_code() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def _split_summary(splits: dict[str, pd.DataFrame]) -> list[dict]:
    return [
        {
            "split": name,
            "first_observation_date": frame["observation_date"].min().date().isoformat(),
            "last_observation_date": frame["observation_date"].max().date().isoformat(),
            "rows": len(frame),
            "positives": int(frame["lapse_next_90d"].sum()),
            "positive_rate": float(frame["lapse_next_90d"].mean()),
        }
        for name, frame in splits.items()
    ]


def run(output_dir: Path) -> dict:
    final_metadata = output_dir / "model_metadata.json"
    freeze_path = output_dir / "model_freeze.json"
    if final_metadata.exists() or freeze_path.exists():
        raise ValueError(
            "Frozen/test artifacts already exist. Refusing to evaluate the test set again; "
            "use a fresh output directory only when a documented defect invalidates the run."
        )
    print("Final training feature list:", flush=True)
    print("\n".join(f"- {feature}" for feature in MODEL_FEATURES), flush=True)
    with psycopg.connect(connection_string()) as conn:
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        panel, monthly, current = load_inputs(conn)
        postgresql_version = conn.info.server_version
    panel, current = prepare_types(panel), prepare_types(current)
    validate_inputs(panel, current)
    splits = temporal_split(panel)
    train, validation, test = (splits[name] for name in ("train", "validation", "test"))
    x_train, y_train = train[MODEL_FEATURES], train["lapse_next_90d"]
    x_validation, y_validation = (
        validation[MODEL_FEATURES],
        validation["lapse_next_90d"],
    )

    base_rate = float(y_train.mean())
    validation_probabilities = {"base_rate": np.full(len(validation), base_rate)}
    models = {
        "logistic_regression": build_pipeline(
            LogisticRegression(max_iter=1_000, random_state=RANDOM_STATE)
        ),
        "random_forest": build_pipeline(
            RandomForestClassifier(
                n_estimators=80,
                max_depth=12,
                min_samples_leaf=75,
                max_features="sqrt",
                max_samples=0.70,
                n_jobs=-1,
                random_state=RANDOM_STATE,
            )
        ),
    }
    for name, pipeline in models.items():
        print(f"Fitting {name} on train only ({len(train):,} rows)", flush=True)
        pipeline.fit(x_train, y_train)
        validation_probabilities[name] = pipeline.predict_proba(x_validation)[:, 1]

    metric_rows, topk_rows, calibration_rows, calibration_bins = [], [], [], []
    validation_summary = {}
    for name, probabilities in validation_probabilities.items():
        threshold = 0.5 if name == "base_rate" else operational_threshold(probabilities)
        discrimination = discrimination_metrics(y_validation, probabilities, threshold)
        calibration, bins = calibration_diagnostics(y_validation, probabilities)
        topk = topk_metrics(y_validation, probabilities)
        metric_rows.append(
            {"dataset": "validation", "model": name, **discrimination, **calibration}
        )
        calibration_rows.append({"dataset": "validation", "model": name, **calibration})
        bins.insert(0, "model", name)
        bins.insert(0, "dataset", "validation")
        calibration_bins.append(bins)
        for row in topk:
            topk_rows.append({"dataset": "validation", "model": name, **row})
        if name != "base_rate":
            summary = {**discrimination, **calibration}
            summary.update({f"recall_at_{row['k_percent']}": row["recall_at_k"] for row in topk})
            summary.update({f"lift_at_{row['k_percent']}": row["lift_at_k"] for row in topk})
            validation_summary[name] = summary

    selected_name, selection_reason = select_model(validation_summary)
    frozen_threshold = next(
        row["threshold"]
        for row in metric_rows
        if row["dataset"] == "validation" and row["model"] == selected_name
    )
    output_dir.mkdir(parents=True, exist_ok=False)
    freeze_record = {
        "frozen_before_test": True,
        "selected_model": selected_name,
        "selection_reason": selection_reason,
        "operational_cutoff": frozen_threshold,
        "selection_dataset": "validation only",
        "feature_list": MODEL_FEATURES,
        "frozen_at_utc": datetime.now(UTC).isoformat(),
    }
    freeze_path.write_text(json.dumps(freeze_record, indent=2) + "\n", encoding="utf-8")

    # This is the only test prediction/evaluation point in the workflow.
    selected_model = models[selected_name]
    test_probabilities = selected_model.predict_proba(test[MODEL_FEATURES])[:, 1]
    test_discrimination = discrimination_metrics(
        test["lapse_next_90d"], test_probabilities, frozen_threshold
    )
    test_calibration, test_bins = calibration_diagnostics(
        test["lapse_next_90d"], test_probabilities
    )
    test_topk = topk_metrics(test["lapse_next_90d"], test_probabilities)
    test_predictions = test[TRACE_COLUMNS + ["observation_date", "lapse_next_90d"]].copy()
    test_predictions["risk_score"] = test_probabilities
    test_predictions.to_csv(output_dir / "test_predictions.csv", index=False)
    test_evaluation = {
        "model": selected_name,
        "evaluated_once": True,
        "evaluated_at_utc": datetime.now(UTC).isoformat(),
        "discrimination": test_discrimination,
        "calibration": test_calibration,
        "topk": test_topk,
    }
    (output_dir / "test_evaluation.json").write_text(
        json.dumps(test_evaluation, indent=2) + "\n", encoding="utf-8"
    )
    metric_rows.append(
        {
            "dataset": "test",
            "model": selected_name,
            **test_discrimination,
            **test_calibration,
        }
    )
    calibration_rows.append({"dataset": "test", "model": selected_name, **test_calibration})
    test_bins.insert(0, "model", selected_name)
    test_bins.insert(0, "dataset", "test")
    calibration_bins.append(test_bins)
    topk_rows.extend({"dataset": "test", "model": selected_name, **row} for row in test_topk)

    logistic_importance = coefficient_importance(models["logistic_regression"])
    random_forest_importance = forest_importance(models["random_forest"], validation)
    importance = pd.concat([logistic_importance, random_forest_importance], ignore_index=True)
    fairness = fairness_diagnostics(test, test_probabilities, frozen_threshold)

    # Current scoring is intentionally after the frozen model's one-time test evaluation.
    current_probabilities = selected_model.predict_proba(current[MODEL_FEATURES])[:, 1]
    tiers = assign_risk_tiers(pd.Series(current_probabilities), current["policy_id"])
    scores = current[
        TRACE_COLUMNS
        + [
            "region",
            "product_name",
            "payment_frequency",
            "policy_age_days",
            "status_at_observation",
        ]
    ].copy()
    scores["risk_score"] = current_probabilities
    scores = scores.join(tiers, on="policy_id")
    scores["observable_reason_flags"] = current.apply(observable_reason_flags, axis=1)

    validation_predictions = validation[
        TRACE_COLUMNS + ["observation_date", "lapse_next_90d"]
    ].copy()
    for name, probability in validation_probabilities.items():
        validation_predictions[f"{name}_risk_score"] = probability
    panel_summary = pd.DataFrame(
        [
            {
                "rows": len(panel),
                "unique_policies": panel["policy_id"].nunique(),
                "observation_months": panel["observation_date"].nunique(),
                "first_observation_date": panel["observation_date"].min().date(),
                "last_observation_date": panel["observation_date"].max().date(),
                "positives": int(panel["lapse_next_90d"].sum()),
                "positive_rate": float(panel["lapse_next_90d"].mean()),
            }
        ]
    )
    monthly["observation_date"] = pd.to_datetime(monthly["observation_date"])
    outputs = {
        "panel_summary.csv": panel_summary,
        "monthly_target_distribution.csv": monthly,
        "model_metrics.csv": pd.DataFrame(metric_rows),
        "topk_metrics.csv": pd.DataFrame(topk_rows),
        "calibration_summary.csv": pd.DataFrame(calibration_rows),
        "calibration_bins.csv": pd.concat(calibration_bins, ignore_index=True),
        "feature_importance.csv": importance,
        "fairness_diagnostics.csv": fairness,
        "validation_predictions.csv": validation_predictions,
        "test_predictions.csv": test_predictions,
        "current_policy_scores.csv": scores,
    }
    for filename, frame in outputs.items():
        frame.to_csv(output_dir / filename, index=False)

    metadata = {
        **freeze_record,
        "as_of": AS_OF,
        "prediction_horizon_days": 90,
        "random_state": RANDOM_STATE,
        "model_class": type(selected_model.named_steps["model"]).__name__,
        "model_parameters": selected_model.named_steps["model"].get_params(),
        "split_summary": _split_summary(splits),
        "training_prevalence": base_rate,
        "test_evaluated_once": True,
        "test_evaluated_at_utc": datetime.now(UTC).isoformat(),
        "current_scoring_after_test": True,
        "current_scoring_rows": len(scores),
        "risk_tier_counts": scores["risk_tier"].value_counts().to_dict(),
        "sql_sha256": sha256(ROOT / "sql/07_lapse_risk_features.sql"),
        "python_sha256": _hash_code(),
        "python_version": platform.python_version(),
        "sklearn_version": sklearn.__version__,
        "postgresql_version": postgresql_version,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "output_sha256": {filename: sha256(output_dir / filename) for filename in outputs},
        "synthetic_data_warning": (
            "Performance is generator-specific and is not expected real-insurer performance."
        ),
    }
    metadata["output_sha256"]["test_evaluation.json"] = sha256(output_dir / "test_evaluation.json")
    final_metadata.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/processed/phase6")
    args = parser.parse_args()
    try:
        metadata = run(args.output_dir)
    except (ValueError, OSError, psycopg.Error) as exc:
        print(f"Phase 6 model workflow failed ({type(exc).__name__}): {exc}")
        return 1
    print(
        f"Frozen {metadata['selected_model']}; evaluated test once; "
        f"scored {metadata['current_scoring_rows']:,} current policies."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
