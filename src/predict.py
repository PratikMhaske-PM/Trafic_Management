import joblib
import pandas as pd
import numpy as np
import os

def load_models():
    if not os.path.exists('models/xgboost_regressor.pkl'):
        raise FileNotFoundError("Models not found. Train them first!")
    xgb = joblib.load('models/xgboost_regressor.pkl')
    rf = joblib.load('models/rf_classifier.pkl')
    features = joblib.load('models/feature_names.pkl')
    return xgb, rf, features

def forecast_traffic(input_dict):
    xgb_model, rf_model, expected_features = load_models()
    
    # Convert input to DataFrame
    df = pd.DataFrame([input_dict])
    
    # Ensure all expected features exist, fill missing with 0
    for col in expected_features:
        if col not in df.columns:
            df[col] = 0
            
    # Order columns exactly as trained
    df = df[expected_features]
    
    # Base prediction (Current)
    current_density = xgb_model.predict(df)[0]
    congestion_class = rf_model.predict(df)[0]
    
    # Phase 8: Forecast for next 15, 30, and 60 minutes
    # We simulate this by mathematically decaying/escalating based on peak hours and lag
    # In a full production system, we would iteratively feed the prediction back as 'lag_1' for the next step.
    trend_factor = 1.05 if input_dict.get('is_peak_hour', 0) == 1 else 0.95
    
    pred_15 = current_density * (trend_factor ** 0.25)
    pred_30 = current_density * (trend_factor ** 0.5)
    pred_60 = current_density * trend_factor
    
    # Cap densities at 100%
    return {
        "current_density": round(float(min(current_density, 100)), 2),
        "prediction_15_min": round(float(min(pred_15, 100)), 2),
        "prediction_30_min": round(float(min(pred_30, 100)), 2),
        "prediction_60_min": round(float(min(pred_60, 100)), 2),
        "congestion_class": int(congestion_class)
    }

if __name__ == "__main__":
    # Test Prediction
    test_input = {
        'hour': 18, 
        'is_peak_hour': 1, 
        'temperature': 25.0, 
        'rainfall': 0.0,
        'density_lag_1': 70.0,
        'rolling_density': 68.0
    }
    print("Testing Forecasting Engine:")
    print(forecast_traffic(test_input))
