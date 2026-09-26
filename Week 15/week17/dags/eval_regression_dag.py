from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

THRESHOLD = 80.0


def evaluate(**_):
    import subprocess
    import sys
    subprocess.run([sys.executable, "-m", "week17.run_versions"], check=True)
    subprocess.run([sys.executable, "-m", "week17.regression"], check=True)


def check_threshold(**_):
    import mlflow
    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    df = mlflow.search_runs(experiment_names=["assistant_prompt_regression"])
    latest = df.sort_values("start_time").groupby("params.version").tail(1)
    low = latest[latest["metrics.pct_tests_passed"] < THRESHOLD]["params.version"].tolist()
    if low:
        print(f"REGRESSION ALERT: prompt versions below {THRESHOLD}% pass rate: {low}")
        return "alert"
    print("All prompt versions above threshold; no regression.")
    return "ok"


default_args = {"owner": "sulav", "retries": 1, "retry_delay": timedelta(minutes=5)}

with DAG(
    dag_id="assistant_prompt_regression",
    default_args=default_args,
    description="Re-run the golden-set LLM-judge regression on the assistant and alert on degradation",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["week17", "track-b", "regression"],
) as dag:
    PythonOperator(task_id="evaluate", python_callable=evaluate) >> \
        PythonOperator(task_id="check_threshold", python_callable=check_threshold)
