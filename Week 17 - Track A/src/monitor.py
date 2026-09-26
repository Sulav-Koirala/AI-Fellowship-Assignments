import os
import numpy as np
import mlflow
from sklearn.model_selection import train_test_split
from evidently import Report
from evidently.presets import DataDriftPreset
from evidently.metrics import DriftedColumnsCount, ValueDrift
from evidently.tests import lte
from src.prep import load_clean, TARGET

REPORTS = "reports"
TRACKING_URI = "sqlite:///mlflow.db"


def psi(ref, cur, bins=10):
    edges = np.quantile(ref, np.linspace(0, 1, bins + 1))
    edges[0], edges[-1] = -np.inf, np.inf
    r = np.clip(np.histogram(ref, edges)[0] / len(ref), 1e-6, None)
    c = np.clip(np.histogram(cur, edges)[0] / len(cur), 1e-6, None)
    return float(np.sum((c - r) * np.log(c / r)))


def inject_drift(df, seed=42):
    rng = np.random.default_rng(seed)
    d = df.copy()
    d["MonthlyCharges"] = d["MonthlyCharges"] + rng.normal(18, 10, len(d))
    d["tenure"] = (d["tenure"] * rng.uniform(0.4, 0.7, len(d))).round().clip(lower=0)
    d.loc[rng.random(len(d)) < 0.45, "Contract"] = "Month-to-month"
    flip = rng.random(len(d)) < 0.05
    d.loc[flip, TARGET] = 1 - d.loc[flip, TARGET]
    return d


def main():
    os.makedirs(REPORTS, exist_ok=True)
    df = load_clean()
    ref, cur = train_test_split(df, test_size=0.3, random_state=42, stratify=df[TARGET])
    ref, cur = ref.reset_index(drop=True), inject_drift(cur.reset_index(drop=True))
    feat = [c for c in df.columns if c != TARGET]

    data_report = Report([DataDriftPreset(), DriftedColumnsCount(share_tests=[lte(0.5)])])
    data_snap = data_report.run(current_data=cur[feat], reference_data=ref[feat])
    data_snap.save_html(f"{REPORTS}/data_drift.html")

    target_report = Report([ValueDrift(column=TARGET, tests=[lte(0.1)])])
    target_snap = target_report.run(current_data=cur[[TARGET]], reference_data=ref[[TARGET]])
    target_snap.save_html(f"{REPORTS}/target_drift.html")

    custom = {
        "psi_MonthlyCharges": psi(ref["MonthlyCharges"], cur["MonthlyCharges"]),
        "psi_tenure": psi(ref["tenure"], cur["tenure"]),
        "psi_TotalCharges": psi(ref["TotalCharges"], cur["TotalCharges"]),
        "contract_m2m_share_ref": float((ref["Contract"] == "Month-to-month").mean()),
        "contract_m2m_share_cur": float((cur["Contract"] == "Month-to-month").mean()),
        "target_rate_ref": float(ref[TARGET].mean()),
        "target_rate_cur": float(cur[TARGET].mean()),
    }

    mlflow.set_tracking_uri(TRACKING_URI)
    mlflow.set_experiment("telco_churn_monitoring")
    with mlflow.start_run(run_name="drift_check"):
        mlflow.log_metrics(custom)
        mlflow.log_artifact(f"{REPORTS}/data_drift.html")
        mlflow.log_artifact(f"{REPORTS}/target_drift.html")

    drifted = [c for c in ("MonthlyCharges", "tenure", "TotalCharges") if custom[f"psi_{c}"] > 0.2]
    print("Custom PSI metric (>0.2 = major population shift):")
    for c in ("MonthlyCharges", "tenure", "TotalCharges"):
        print(f"  {c}: {custom[f'psi_{c}']:.3f}")
    print(f"Perturbed numeric columns flagged by PSI: {drifted}")
    print(f"Contract Month-to-month share: {custom['contract_m2m_share_ref']:.2f} -> "
          f"{custom['contract_m2m_share_cur']:.2f}")
    print(f"Churn rate: {custom['target_rate_ref']:.3f} -> {custom['target_rate_cur']:.3f}")
    print("Saved reports/data_drift.html and reports/target_drift.html")


if __name__ == "__main__":
    main()
