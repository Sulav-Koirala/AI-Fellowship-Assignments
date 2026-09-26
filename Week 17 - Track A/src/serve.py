import mlflow
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel

mlflow.set_tracking_uri("sqlite:///mlflow.db")
MODEL_URI = "models:/TelcoChurn/Production"
model = mlflow.sklearn.load_model(MODEL_URI)
app = FastAPI(title="Telco Churn Predictor (Week 17 Track A)")


class Customer(BaseModel):
    gender: str
    SeniorCitizen: int
    Partner: str
    Dependents: str
    tenure: int
    PhoneService: str
    MultipleLines: str
    InternetService: str
    OnlineSecurity: str
    OnlineBackup: str
    DeviceProtection: str
    TechSupport: str
    StreamingTV: str
    StreamingMovies: str
    Contract: str
    PaperlessBilling: str
    PaymentMethod: str
    MonthlyCharges: float
    TotalCharges: float


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_URI}


@app.post("/predict")
def predict(c: Customer):
    X = pd.DataFrame([c.model_dump()])
    prob = float(model.predict_proba(X)[0, 1])
    return {"churn_probability": round(prob, 4), "prediction": "Yes" if prob >= 0.5 else "No"}
