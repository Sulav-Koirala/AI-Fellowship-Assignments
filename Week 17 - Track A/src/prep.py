import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.model_selection import train_test_split

DATA_PATH = "data/telco_churn.csv"
TARGET = "Churn"
DROP = ["customerID"]
NUMERIC = ["tenure", "MonthlyCharges", "TotalCharges", "SeniorCitizen"]


def load_clean(path=DATA_PATH):
    df = pd.read_csv(path).drop(columns=DROP)
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"].astype(str).str.strip(), errors="coerce")
    df = df.dropna(subset=["TotalCharges"]).reset_index(drop=True)
    df[TARGET] = (df[TARGET] == "Yes").astype(int)
    return df


def feature_columns(df):
    nums = [c for c in NUMERIC if c in df.columns]
    cats = [c for c in df.columns if c != TARGET and c not in nums]
    return nums, cats


def split(df, test_size=0.2, seed=42):
    X, y = df.drop(columns=[TARGET]), df[TARGET]
    return train_test_split(X, y, test_size=test_size, stratify=y, random_state=seed)


def make_preprocessor(nums, cats):
    return ColumnTransformer([
        ("num", StandardScaler(), nums),
        ("cat", OneHotEncoder(handle_unknown="ignore"), cats),
    ])
