import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                             roc_auc_score, confusion_matrix, RocCurveDisplay)
from src.prep import load_clean, feature_columns, split, make_preprocessor, TARGET

TRACKING_URI = "sqlite:///mlflow.db"
EXPERIMENT = "telco_churn"
MODEL_NAME = "TelcoChurn"
REPORTS = "reports"
LOG_PARAMS = ("C", "class_weight", "n_estimators", "max_depth", "min_samples_leaf",
              "max_iter", "learning_rate", "max_leaf_nodes", "l2_regularization")

CANDIDATES = {
    "logreg": LogisticRegression(max_iter=1000, C=0.5, class_weight="balanced"),
    "random_forest": RandomForestClassifier(n_estimators=300, max_depth=12, min_samples_leaf=20,
                                            class_weight="balanced", random_state=42, n_jobs=-1),
    "hist_gb": HistGradientBoostingClassifier(max_iter=400, learning_rate=0.05, max_leaf_nodes=31,
                                              l2_regularization=1.0, random_state=42),
}


def _metrics(y_test, y_pred, y_prob):
    return {"accuracy": accuracy_score(y_test, y_pred), "precision": precision_score(y_test, y_pred),
            "recall": recall_score(y_test, y_pred), "f1": f1_score(y_test, y_pred),
            "roc_auc": roc_auc_score(y_test, y_prob)}


def _plots(y_test, y_pred, y_prob, name):
    os.makedirs(REPORTS, exist_ok=True)
    cm = confusion_matrix(y_test, y_pred)
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.imshow(cm, cmap="Blues")
    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center")
    ax.set(xticks=[0, 1], yticks=[0, 1], xticklabels=["No", "Yes"], yticklabels=["No", "Yes"],
           xlabel="Predicted", ylabel="Actual", title=f"Confusion - {name}")
    cm_path = f"{REPORTS}/cm_{name}.png"
    fig.tight_layout(); fig.savefig(cm_path); plt.close(fig)
    disp = RocCurveDisplay.from_predictions(y_test, y_prob)
    disp.ax_.set_title(f"ROC - {name}")
    roc_path = f"{REPORTS}/roc_{name}.png"
    disp.figure_.savefig(roc_path); plt.close(disp.figure_)
    return cm_path, roc_path


def _export_table(best_name):
    df = mlflow.search_runs(experiment_names=[EXPERIMENT])
    cols = {"tags.mlflow.runName": "model", "metrics.accuracy": "accuracy",
            "metrics.precision": "precision", "metrics.recall": "recall",
            "metrics.f1": "f1", "metrics.roc_auc": "roc_auc"}
    df = df[[c for c in cols if c in df.columns]].rename(columns=cols).sort_values("roc_auc", ascending=False)
    lines = ["# Track A - Model Run Comparison", "",
             f"Registered to Production: **{best_name}** (chosen by ROC-AUC, the right lens on a ~27% churn base).",
             "", "| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |", "|---|---|---|---|---|---|"]
    for _, r in df.iterrows():
        lines.append(f"| {r['model']} | {r['accuracy']:.3f} | {r['precision']:.3f} | "
                     f"{r['recall']:.3f} | {r['f1']:.3f} | {r['roc_auc']:.3f} |")
    os.makedirs(REPORTS, exist_ok=True)
    with open(f"{REPORTS}/run_comparison.md", "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n" + "\n".join(lines))


def main():
    mlflow.set_tracking_uri(TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT)
    df = load_clean()
    nums, cats = feature_columns(df)
    X_train, X_test, y_train, y_test = split(df)

    results = []
    for name, est in CANDIDATES.items():
        with mlflow.start_run(run_name=name) as run:
            pipe = Pipeline([("pre", make_preprocessor(nums, cats)), ("model", est)])
            pipe.fit(X_train, y_train)
            y_pred = pipe.predict(X_test)
            y_prob = pipe.predict_proba(X_test)[:, 1]
            m = _metrics(y_test, y_pred, y_prob)
            mlflow.log_param("model", name)
            mlflow.log_params({k: v for k, v in est.get_params().items() if k in LOG_PARAMS})
            mlflow.log_metrics(m)
            for p in _plots(y_test, y_pred, y_prob, name):
                mlflow.log_artifact(p)
            mlflow.sklearn.log_model(pipe, artifact_path="model", input_example=X_test.head(2))
            results.append((name, run.info.run_id, m))
            print(f"{name}: " + "  ".join(f"{k}={v:.3f}" for k, v in m.items()))

    best_name, best_id, best_m = max(results, key=lambda r: r[2]["roc_auc"])
    client = MlflowClient()
    mv = mlflow.register_model(f"runs:/{best_id}/model", MODEL_NAME)
    client.transition_model_version_stage(MODEL_NAME, mv.version, "Staging")
    client.transition_model_version_stage(MODEL_NAME, mv.version, "Production", archive_existing_versions=True)
    print(f"\nregistered {MODEL_NAME} v{mv.version} ({best_name}) -> Staging -> Production")
    _export_table(best_name)


if __name__ == "__main__":
    main()
