"""Build the Phase 6 executed-results notebook without retraining or retesting."""

from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "notebooks/05_lapse_risk_model.ipynb"
cells = []


def md(text):
    cells.append(nbf.v4.new_markdown_cell(text))


def code(text):
    cells.append(nbf.v4.new_code_cell(text))


md("""# Phase 6 — 90-day lapse-risk modelling

**Fixed synthetic snapshot: 1 September 2026**

This notebook presents the frozen executed artifacts. It does **not** retrain, reselect, or
reevaluate the held-out test set. SQL reconstructed every historical row as of its observation
date; Python fitted on train, selected on validation, froze the choice, evaluated test once, and
only then scored the current portfolio.

Read the [model contract](../docs/phase6_model_definitions.md),
[panel checkpoint](../docs/phase6_panel_checkpoint.md), and
[executed findings](../docs/phase6_findings.md).""")

code("""import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from IPython.display import display
from sklearn.metrics import precision_recall_curve, roc_curve

ROOT = Path.cwd() if (Path.cwd() / "src").is_dir() else Path.cwd().parent
ARTIFACTS = ROOT / "data/processed/phase6"
FIGURES = ARTIFACTS / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)

metadata = json.loads((ARTIFACTS / "model_metadata.json").read_text())
panel = pd.read_csv(ARTIFACTS / "panel_summary.csv")
monthly = pd.read_csv(
    ARTIFACTS / "monthly_target_distribution.csv", parse_dates=["observation_date"]
)
metrics = pd.read_csv(ARTIFACTS / "model_metrics.csv")
topk = pd.read_csv(ARTIFACTS / "topk_metrics.csv")
calibration = pd.read_csv(ARTIFACTS / "calibration_summary.csv")
calibration_bins = pd.read_csv(ARTIFACTS / "calibration_bins.csv")
importance = pd.read_csv(ARTIFACTS / "feature_importance.csv")
fairness = pd.read_csv(ARTIFACTS / "fairness_diagnostics.csv")
validation_predictions = pd.read_csv(ARTIFACTS / "validation_predictions.csv")
test_predictions = pd.read_csv(ARTIFACTS / "test_predictions.csv")
current_scores = pd.read_csv(ARTIFACTS / "current_policy_scores.csv")

plt.rcParams.update({"figure.dpi": 110, "font.size": 9, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.titleweight": "bold"})
BLUE, TEAL, ORANGE, RED, GREY = "#235789", "#187D78", "#C77727", "#B44C43", "#7A7A7A"

def finish(fig, name):
    fig.tight_layout()
    fig.savefig(FIGURES / f"{name}.png", bbox_inches="tight")
    plt.show()
    plt.close(fig)

display(pd.Series({
    "Selected model": metadata["selected_model"],
    "Frozen before test": metadata["frozen_before_test"],
    "Test evaluated once": metadata["test_evaluated_once"],
    "Current scoring after test": metadata["current_scoring_after_test"],
    "SQL SHA-256": metadata["sql_sha256"],
    "Python SHA-256": metadata["python_sha256"],
}, name="Execution evidence").to_frame())""")

md("""## 1–4. Business problem, lapse meaning, prediction versus reporting, and target

The model estimates whether a policy that is in force at a historical month-end will enter
`Lapsed` status in the next 90 days. Unlike persistency reporting, this creates repeated forward-
looking risk assessments. A lapse strictly after observation and on or before day 90 is positive.""")

md("""## 5–8. Observation dates, risk set, right censoring, and leakage

Rows are policy × month-end. Active, Grace, and chronologically Reinstated policies aged at least
30 days enter the risk set. Only observations with a fully visible 90-day future window are
labelled. Final policy status, future status events, future payments, stored final payment status,
identifiers, gender, and Phase 5 segments are excluded from predictors.""")

md("""## 9–12. Historical panel, features, payment reconstruction, and prevalence

Payment features use only installments due by observation and only receipts known by observation.
A later receipt cannot rewrite an earlier feature snapshot. The increasing monthly rate is a
central model-risk finding, not background noise.""")

code("""display(panel)
fig, ax = plt.subplots(figsize=(11, 4))
ax.plot(monthly.observation_date, monthly.positive_rate * 100, color=BLUE, linewidth=2)
ax.set(title="Monthly mature-panel lapse rate rises over time",
       xlabel="Observation month", ylabel="Positive rate (%)")
finish(fig, "01_monthly_positive_rate")

split = pd.DataFrame(metadata["split_summary"])
fig, ax = plt.subplots(figsize=(7, 4))
ax.bar(split["split"], split["positive_rate"] * 100, color=[BLUE, ORANGE, RED])
ax.set(title="Target prevalence by temporal split", ylabel="Positive rate (%)")
for i, row in split.iterrows():
    ax.text(i, row.positive_rate * 100, f"{row.positive_rate:.2%}", ha="center", va="bottom")
finish(fig, "02_target_class_balance")
display(split)""")

md("""## 13. Locked temporal split

Train ends 31 December 2025, validation covers January–March 2026, and test covers April–May 2026.
The same policy may appear in multiple months; no random row split or random cross-validation is
used.""")

md("""## 14–18. Base rate, Logistic Regression, challenger, validation, and frozen choice

The base-rate benchmark predicts train prevalence. Logistic Regression supplies the interpretable
linear baseline. One Random Forest is the nonlinear challenger. Both were fitted on train only and
compared on validation only. Random Forest was frozen because its validation PR-AUC and top-K
capture materially exceeded Logistic Regression under the predeclared simplicity rule.""")

code("""display(metrics.query("dataset == 'validation'")[
    ["model", "pr_auc", "roc_auc", "brier_score", "mean_predicted_risk", "observed_rate"]])
display(topk.query("dataset == 'validation'")[
    ["model", "k_percent", "recall_at_k", "lift_at_k"]])
print(metadata["selection_reason"])
print("Frozen operational cutoff:", metadata["operational_cutoff"])""")

md("""## 19–20. Held-out test and precision–recall analysis

The selected train-only model was evaluated once on test. The replacement execution persisted
this result immediately. PR-AUC is interpreted relative to test prevalence; modest improvement
over prevalence is not production-grade evidence.""")

code("""test_row = metrics.query("dataset == 'test'")
display(test_row.T.rename(columns={test_row.index[0]: "Frozen test"}))

y = test_predictions.lapse_next_90d.to_numpy()
p = test_predictions.risk_score.to_numpy()
precision, recall, _ = precision_recall_curve(y, p)
fpr, tpr, _ = roc_curve(y, p)
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
axes[0].plot(recall, precision, color=BLUE)
axes[0].axhline(y.mean(), color=GREY, linestyle="--", label="Test prevalence")
axes[0].set(title="Frozen test precision–recall curve", xlabel="Recall", ylabel="Precision")
axes[0].legend()
axes[1].plot(fpr, tpr, color=TEAL)
axes[1].plot([0, 1], [0, 1], color=GREY, linestyle="--")
axes[1].set(
    title="Frozen test ROC curve",
    xlabel="False-positive rate",
    ylabel="True-positive rate",
)
finish(fig, "03_test_pr_roc")""")

md("""## 21. Top-K capture and lift

Capacity metrics ask how many actual lapses appear in the highest-scored operational slice. They
are ranking measures and do not imply calibrated probabilities.""")

code("""test_topk = topk.query("dataset == 'test'")
display(test_topk)
fig, axes = plt.subplots(1, 2, figsize=(11, 4))
axes[0].bar(test_topk.k_percent.astype(str), test_topk.recall_at_k * 100, color=BLUE)
axes[0].set(title="Frozen test recall at capacity", xlabel="Top K%", ylabel="Recall (%)")
axes[1].bar(test_topk.k_percent.astype(str), test_topk.lift_at_k, color=TEAL)
axes[1].axhline(1, color=GREY, linestyle="--")
axes[1].set(title="Frozen test lift at capacity", xlabel="Top K%", ylabel="Lift")
finish(fig, "04_test_topk")""")

md("""## 22. Calibration—separate from discrimination

The model ranks above random yet underpredicts later absolute risk. On test, mean score is about
1.58% while observed lapse is 2.87%. Scores should therefore be communicated as prioritization
indices rather than exact probabilities.""")

code("""display(calibration)
fig, ax = plt.subplots(figsize=(6, 5))
for (dataset, model), subset in calibration_bins.groupby(["dataset", "model"]):
    if model == "base_rate":
        continue
    ax.plot(subset.mean_predicted_risk * 100, subset.observed_rate * 100,
            marker="o", label=f"{dataset}: {model}")
limit = max(ax.get_xlim()[1], ax.get_ylim()[1])
ax.plot([0, limit], [0, limit], color=GREY, linestyle="--", label="Perfect calibration")
ax.set(title="Observed versus predicted risk by score decile",
       xlabel="Mean predicted risk (%)", ylabel="Observed lapse rate (%)")
ax.legend(fontsize=7)
finish(fig, "05_calibration")""")

md("""## 23. Explainability

Permutation importance measures validation PR-AUC change when a raw feature is shuffled. Small or
negative values can reflect sampling variation and interactions. They must not be interpreted as
causal effects.""")

code("""selected_name = metadata["selected_model"]
selected_importance = importance.query(
    "model == @selected_name"
).sort_values("absolute_importance", ascending=False).head(15).sort_values("absolute_importance")
display(selected_importance.sort_values("absolute_importance", ascending=False))
fig, ax = plt.subplots(figsize=(8, 6))
ax.barh(selected_importance.feature, selected_importance.importance, color=BLUE)
ax.axvline(0, color=GREY, linewidth=1)
ax.set(title="Validation permutation importance", xlabel="Change in PR-AUC")
finish(fig, "06_feature_importance")""")

md("""## 24. Descriptive fairness/model-risk diagnostics

Gender is not a predictor. Group metrics describe test behaviour and sample-size differences; they
are not legal fairness certification.""")

code("""gender = fairness.query("attribute == 'gender'").copy()
display(fairness)
fig, axes = plt.subplots(1, 2, figsize=(10, 4))
axes[0].bar(gender.group, gender.recall * 100, color=[ORANGE, BLUE])
axes[0].set(title="Recall by gender diagnostic", ylabel="Recall (%)")
axes[1].bar(gender.group, gender.pr_auc * 100, color=[ORANGE, BLUE])
axes[1].set(title="PR-AUC by gender diagnostic", ylabel="PR-AUC (%)")
finish(fig, "07_fairness_gender")""")

md("""## 25–27. Current scoring, capacity tiers, and observable signals

Only after frozen test evaluation were 29,360 current policies scored. Priority is the highest
10%, Watch the next 20%, and Routine the remaining 70%. Reason flags are observed servicing
signals—not SHAP values and not proof of why the model assigned a score.""")

code("""fig, axes = plt.subplots(1, 2, figsize=(11, 4))
axes[0].hist(current_scores.risk_score, bins=30, color=BLUE, alpha=.85)
axes[0].set(title="Current risk-score distribution", xlabel="Risk score", ylabel="Policies")
tier_order = ["Priority", "Watch", "Routine"]
tier_counts = current_scores.risk_tier.value_counts().reindex(tier_order)
axes[1].bar(tier_counts.index, tier_counts.values, color=[RED, ORANGE, TEAL])
axes[1].set(title="Current capacity tiers", ylabel="Policies")
finish(fig, "08_current_scores_tiers")
display(tier_counts.rename("policies").to_frame())
display(current_scores.query("risk_tier == 'Priority'").head(20))""")

md("""## 28–30. Retention workflow, limitations, and interview summary

**Workflow:** score → prioritize → human review → customer outreach/service support → record
outcomes. Never use the output for automatic cancellation, pricing, benefit reduction, or
underwriting denial.

**Limitations:** synthetic generator structure, repeated policy observations, no agent-transfer
history, no real intervention outcomes, modest test ranking, material later-period
underprediction, and no causal interpretation.

**Interview summary:** “I reconstructed what was knowable at each month-end, trained only on past
periods, selected on validation, froze the model, tested once, and scored the current portfolio
afterward. The model provides modest top-K prioritization lift but underpredicts later absolute
risk, so I separate discrimination from calibration and frame scores for human retention review.”""")

notebook = nbf.v4.new_notebook(cells=cells)
notebook["metadata"]["kernelspec"] = {
    "display_name": "Python 3",
    "language": "python",
    "name": "python3",
}
notebook["metadata"]["language_info"] = {"name": "python", "version": "3.11"}
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
nbf.write(notebook, OUTPUT)
print(f"Built {OUTPUT}")
