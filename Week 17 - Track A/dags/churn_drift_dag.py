from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator


def check_drift(**_):
    from sklearn.model_selection import train_test_split
    from src.prep import load_clean, TARGET
    from src.monitor import inject_drift, psi

    df = load_clean()
    ref, cur = train_test_split(df, test_size=0.3, random_state=42, stratify=df[TARGET])
    ref, cur = ref.reset_index(drop=True), inject_drift(cur.reset_index(drop=True))
    psis = {c: psi(ref[c], cur[c]) for c in ("MonthlyCharges", "tenure", "TotalCharges")}
    drifted = [c for c, v in psis.items() if v > 0.2]
    if drifted:
        print(f"DRIFT DETECTED on {drifted} (PSI>0.2) -> RECOMMENDATION: trigger retraining (src.train).")
        return "retrain_recommended"
    print("No significant drift; model retained.")
    return "ok"


default_args = {"owner": "sulav", "retries": 1, "retry_delay": timedelta(minutes=5)}

with DAG(
    dag_id="telco_churn_drift_check",
    default_args=default_args,
    description="Daily Telco churn drift check; recommends retraining when PSI>0.2",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["week17", "track-a", "drift"],
) as dag:
    PythonOperator(task_id="check_drift", python_callable=check_drift)
