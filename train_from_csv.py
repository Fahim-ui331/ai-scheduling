# train_from_csv.py
"""
Train Random-Forest model from a CSV file.
CSV must have columns: semester, course_id, enrollment
"""

import pandas as pd
from prediction_engine import train_rf

def train_from_csv(history_csv="data/history.csv", model_path="rf_demand.joblib"):
    """
    Reads historical course-enrollment data and trains the RF model.
    Saves model as rf_demand.joblib (or custom path).
    """
    df = pd.read_csv(history_csv)

    # Basic sanity check
    required = {"semester", "course_id", "enrollment"}
    if not required.issubset(df.columns):
        raise ValueError(f"CSV missing columns: {required - set(df.columns)}")

    model = train_rf(df, model_path=model_path)
    print(f"✅ Random-Forest model trained and saved to: {model_path}")

if __name__ == "__main__":
    # Example run
    train_from_csv("rf_history_from_combined.csv")
