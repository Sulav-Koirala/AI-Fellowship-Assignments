# Week 17 - Track A: Telco Churn MLOps

This is the Data Science track: a standalone churn-prediction pipeline that trains several models, tracks every run in MLflow, registers and promotes the best one, serves it behind an API, and watches for data/target drift with Evidently. It's self-contained (its own uv env and a local copy of the dataset) and touches nothing from the Weeks 15/16 assistant.

> Week 17 has two tracks. **Track B** (the same MLOps discipline applied to the agentic assistant - versioned prompts, per-query traces, LLM-as-judge regression tests) lives in [`../Week 15/week17/`](../Week%2015/week17/).

## a. Environment & Reproducibility

Managed with [uv](https://docs.astral.sh/uv/). The environment is pinned two ways: `pyproject.toml` lists the direct deps, `.python-version` pins Python 3.12, and the committed `uv.lock` pins the exact resolved versions of everything transitive. A clean clone reproduces the same env with one command:

```bash
cd "Week 17 - Track A"
uv sync
```

Two version pins are deliberate and worth calling out, because both are load-bearing for the assignment:

- **`mlflow>=2.18,<3`** — the Model Registry stage transitions (`Staging`/`Production`) this assignment asks for were **removed in MLflow 3**. 2.x still has them, so the pipeline pins below 3.
- **Python 3.12** — MLflow 2.x and Evidently top out at 3.12; my machine runs 3.14, so the pin is what makes `uv sync` resolve at all.

MLflow's tracking URI is `sqlite:///mlflow.db` (a file-backed SQLite DB in the project root), not the default file store, because **the Model Registry requires a database backend** — you can't register or promote a model against the plain `./mlruns` file store.

Run everything through uv so it uses the locked env:

```bash
uv run python -m src.train      # train 3 models, log runs, register + promote best
uv run python -m src.monitor    # inject drift, build Evidently reports, log custom metric
uv run uvicorn src.serve:app --port 8000   # serve the Production model
```

## b. Experiment Tracking

`src/train.py` trains **three genuinely different model families** — Logistic Regression, Random Forest, HistGradientBoosting — each with its own hyperparameters, all inside one scikit-learn `Pipeline` (a `ColumnTransformer` doing `StandardScaler` on the numerics + `OneHotEncoder` on the categoricals, so preprocessing is fit inside cross-val-safe boundaries and travels with the model when it's served). Every run logs its params, five test metrics, a confusion-matrix PNG, an ROC-curve PNG, and the serialized model.

The full comparison (exported to [`reports/run_comparison.md`](reports/run_comparison.md) from `mlflow.search_runs`, so it's the actual logged numbers, not hand-copied):

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|
| **random_forest** | 0.739 | 0.506 | 0.799 | 0.620 | **0.837** |
| logreg | 0.727 | 0.492 | 0.794 | 0.607 | 0.835 |
| hist_gb | **0.777** | 0.589 | 0.529 | 0.558 | 0.822 |

**Why `random_forest` was registered and promoted — and why *not* by accuracy.** This is an imbalanced problem: only ~27% of customers churn. That single fact makes accuracy the wrong yardstick, and this run shows exactly why. `hist_gb` has the **highest accuracy (0.777)** but the **lowest recall (0.529)** — it wins on accuracy largely by being reluctant to predict churn, so it misses nearly half the customers who actually leave. On a churn problem the whole point is to *catch churners* while there's still time to intervene; a model that quietly optimizes for the majority "No" class by scoring well on accuracy is the classic trap.

So I selected on **ROC-AUC** (threshold-independent ranking quality, robust to the class imbalance), with F1 as the tie-breaker. `random_forest` leads on both (ROC-AUC 0.837, F1 0.620) and catches **80% of churners** (recall 0.799) versus hist_gb's 53% — at the cost of some precision, which is the right trade when a missed churner is more expensive than a wasted retention offer. It edges out logreg on both headline metrics too. It's registered as `TelcoChurn` and transitioned **v1 → Staging → Production** (`archive_existing_versions=True`, so re-running cleanly supersedes the prior Production version).

The confusion-matrix and ROC PNGs per model are in `reports/` and attached to each MLflow run. (No MLflow-UI screenshots — the exported table above is the run comparison, straight from the tracking DB.)

## c. Monitoring & Drift

`src/monitor.py` splits the data ~70/30 into a **reference** and a **current** window, then injects synthetic drift into *current only* so the detectors have something real to catch:

- Gaussian shift on `MonthlyCharges` (+18 mean, σ10) and a downward scale on `tenure`,
- skews `Contract` toward `Month-to-month` (45% of rows),
- flips 5% of the `Churn` label (target drift).

It builds two Evidently reports — a **Data Drift** report (`DataDriftPreset` over the features) and a **Target Drift** report (`ValueDrift` on `Churn`) — saved as HTML in `reports/` and logged to the `telco_churn_monitoring` MLflow experiment. The **custom metric** is a from-scratch numpy **PSI (Population Stability Index)** on the numeric columns, logged alongside the reports (PSI > 0.2 is the usual "major population shift" line).

Actual output from the last run:

| Column | PSI | Verdict |
|---|---|---|
| tenure | 3.630 | drifted (injected) |
| MonthlyCharges | 0.712 | drifted (injected) |
| TotalCharges | 0.003 | **stable — not injected** |

That last row is the honest check: `TotalCharges` was left untouched, and PSI correctly reads it at ~0, so the detector is discriminating between real drift and noise rather than flagging everything. The categorical skew and target flip land too — `Contract` month-to-month share moves **0.55 → 0.77**, and the churn rate moves **0.266 → 0.286**, which Evidently's target-drift report picks up. The takeaway a monitoring dashboard would surface: retrain is warranted, and the driver is the pricing/tenure/contract mix, not the billing totals.

## d. Orchestration (bonus)

`dags/churn_drift_dag.py` is an Airflow DAG (`telco_churn_drift_check`, `@daily`) with a single `check_drift` task that recomputes PSI on the live-vs-reference split and prints a **retrain recommendation** when any column crosses PSI 0.2. It's provided as a well-formed DAG file (the bonus asks for the DAG, not a stood-up scheduler) — dropping it into an Airflow `dags/` folder schedules the drift check that `monitor.py` runs by hand here.

## Serving check

`src/serve.py` loads `models:/TelcoChurn/Production` from the registry at startup and exposes `/health` + `/predict`. Smoke-tested against a real customer row (tenure 1, month-to-month): it returned **churn probability 0.74 → "Yes"**, which is the sensible call for a brand-new month-to-month customer.

## Layout

```
Week 17 - Track A/
  data/telco_churn.csv        # local copy, pipeline is self-contained
  src/prep.py                 # load + clean + stratified split + preprocessor
  src/train.py                # 3 models -> MLflow -> register + promote best
  src/serve.py                # FastAPI, loads Production model
  src/monitor.py              # Evidently data/target drift + PSI custom metric
  dags/churn_drift_dag.py     # Airflow DAG (file only)
  reports/                    # run_comparison.md + drift HTML + PNGs
  pyproject.toml / uv.lock / .python-version
```
