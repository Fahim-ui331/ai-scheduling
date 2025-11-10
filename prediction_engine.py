# prediction_engine.py
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from joblib import dump, load

# Train: historical_df columns → ['semester','course_id','enrollment']
def train_rf(historical_df: pd.DataFrame, model_path="rf_demand.joblib"):
    X = historical_df[['semester', 'course_id']]
    y = historical_df['enrollment'].astype(float)

    ct = ColumnTransformer(
        transformers=[
            ('ohe', OneHotEncoder(handle_unknown='ignore'), ['semester','course_id'])
        ],
        remainder='drop'
    )
    rf = RandomForestRegressor(n_estimators=200, random_state=42)
    pipe = Pipeline(steps=[('prep', ct), ('rf', rf)])
    pipe.fit(X, y)
    dump(pipe, model_path)
    return pipe

def load_rf(model_path="rf_demand.joblib"):
    return load(model_path)

# Predict demand per section/course; output Series aligned with input rows
def predict_demand(model, upcoming_df: pd.DataFrame) -> np.ndarray:
    return model.predict(upcoming_df[['semester','course_id']])
