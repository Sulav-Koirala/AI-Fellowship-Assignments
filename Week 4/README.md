# Week 4 - Statistical Machine Learning: Linear Models

This folder contains the Week 4 assignment notebook for building and evaluating linear machine learning models on the Telco Customer Churn dataset.

## Files

| File | Description |
| --- | --- |
| `W4_Linear_Models_Assignment.ipynb` | Main Jupyter notebook with the complete assignment, analysis, model training, evaluation, and written answers. |
| `WA_Fn-UseC_-Telco-Customer-Churn.csv` | Telco customer churn dataset used throughout the notebook. |

## Assignment Overview

The assignment focuses on using linear models for both classification and regression tasks. The main business problem is predicting customer churn and using model outputs to support retention decisions.

Key topics covered:

- Problem formulation for supervised machine learning
- Data profiling and preprocessing
- Handling the `TotalCharges` missing/blank value issue
- Target encoding for churn prediction
- Class imbalance and naive baseline evaluation
- Train, validation, and test splitting with stratification
- Feature scaling and one-hot encoding
- Linear classification models:
  - Logistic Regression
  - Ridge Classifier
  - SGD Classifier
- Model comparison using Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC, and Log Loss
- ROC and Precision-Recall curve analysis
- Threshold tuning for a 200-calls-per-week retention constraint
- Coefficient inspection for model interpretability
- Linear regression models for tenure and customer lifetime value analysis:
  - Linear Regression
  - Ridge
  - Lasso
  - Elastic Net
- Residual analysis and heteroscedasticity discussion
- Regularization path comparison for Ridge, Lasso, and Elastic Net
- CLV calculation using predicted tenure
- Cross-validation and learning curves
- Data leakage demonstration and prevention
- Final test-set evaluation and model card

## Dataset

The dataset contains 7,043 telecom customer records. Each row represents one customer and includes demographic information, subscribed services, account details, billing information, and whether the customer churned.

Important columns include:

- `customerID`: Unique customer identifier
- `gender`, `SeniorCitizen`, `Partner`, `Dependents`: Demographic attributes
- `tenure`: Number of months the customer has stayed with the company
- `PhoneService`, `InternetService`, `OnlineSecurity`, `TechSupport`, and related columns: Service subscriptions
- `Contract`, `PaperlessBilling`, `PaymentMethod`: Account and billing details
- `MonthlyCharges`: Customer's monthly charge
- `TotalCharges`: Total amount charged to the customer
- `Churn`: Target variable for classification

## Requirements

The notebook uses Python and common data science libraries:

- pandas
- numpy
- matplotlib
- seaborn
- scikit-learn
- jupyter

Install the required packages if they are not already available:

```bash
pip install pandas numpy matplotlib seaborn scikit-learn jupyter
```

## How to Run

1. Open a terminal in the `Week 4` folder.
2. Start Jupyter Notebook:

```bash
jupyter notebook
```

3. Open `W4_Linear_Models_Assignment.ipynb`.
4. Run the notebook cells from top to bottom.

The CSV file should stay in the same folder as the notebook because the notebook loads it using:

```python
pd.read_csv("WA_Fn-UseC_-Telco-Customer-Churn.csv")
```

## Main Results

The notebook identifies Logistic Regression as the chosen classification model for churn prediction and Ridge Regression as the chosen regression model for tenure/CLV estimation.

Final model-card results reported in the notebook:

| Model Type | Chosen Model | Key Results |
| --- | --- | --- |
| Classification | Logistic Regression | Test Precision: 0.6884, Recall: 0.5267, F1: 0.5968, PR-AUC: 0.6591 |
| Regression | Ridge Regression | MAE: 6.74, RMSE: 8.83, R2: 0.8673 |

The notebook also applies a top-200 customer threshold strategy to match the business constraint that the retention team can call only 200 customers per week.

## Notes

- `TotalCharges` is initially read as an object column because some rows contain blank values. The notebook converts it to numeric and fills missing values with `0.0`.
- The churn target is encoded as `Yes = 1` and `No = 0`.
- Stratified splitting is used because the churn class is imbalanced.
- Scaling is fit only on the training set to avoid data leakage.
- PR-AUC is emphasized because churn prediction is an imbalanced classification problem.
