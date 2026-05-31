# Week 5: Tree-Based Models and Ensembles

This folder contains the Week 5 assignment notebook for tree-based machine learning models, focused on telecom customer churn.

## Contents

- `W5_Tree-Based Models & Ensembles_Assignment.ipynb`  
  Main Jupyter notebook with exercises, code, plots, and reflections.

- `telco_churn_v1.joblib`  
  Saved churn prediction pipeline/model artifact created from the notebook.

## Notebook Topics

The notebook walks through:

- Gini impurity, entropy, and information gain
- Decision tree overfitting and the bias-variance tradeoff
- Cleaning the IBM Telco Customer Churn dataset
- Naive decision tree classification and confusion matrix analysis
- Bagging and random forests
- XGBoost hyperparameters and grid search
- `ColumnTransformer` preprocessing pipelines
- Correct use of SMOTE inside cross-validation pipelines
- Full churn classification pipeline training
- SHAP global and local model explanations
- Model serialization with `joblib`
- Model card documentation
- Decision tree and XGBoost regression for tenure-style prediction

## Data

The notebook loads the Telco Customer Churn dataset directly from GitHub:

```text
https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv
```

An internet connection is required when running the data loading cell.

## Requirements

Use a Python environment with Jupyter and the main data science libraries installed:

```bash
pip install notebook numpy pandas matplotlib seaborn scikit-learn imbalanced-learn xgboost shap joblib
```

The notebook metadata shows Python 3.13 was used.

## How to Run

1. Open the notebook in Jupyter Notebook, JupyterLab, or VS Code.
2. Run the first setup cell to import libraries and load the dataset.
3. Work through the notebook cells in order.
4. Complete any remaining assignment fill-in sections before running the full notebook from top to bottom.
5. The trained pipeline can be saved or loaded with:

```python
import joblib

pipeline = joblib.load("telco_churn_v1.joblib")
```

## Notes

- The notebook is structured as a learning assignment, so some cells include `YOUR CODE HERE` prompts.
- The saved `.joblib` file is a generated model artifact and may be large.
- If dependency or version issues appear, recreate the environment and reinstall the packages listed above.
