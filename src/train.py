import pandas as pd
import joblib
import os
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import mean_absolute_error, r2_score, accuracy_score, classification_report
import xgboost as xgb

def train_models(data_path):
    print("Loading ML-ready data...")
    df = pd.read_csv(data_path)
    
    # ==========================================
    # CRITICAL: Time-Aware Train/Test Split
    # ==========================================
    # We NEVER shuffle time-series data. We must train on the past to predict the future.
    df = df.sort_values('timestamp')
    
    target_reg = 'traffic_density'
    target_clf = 'congestion_level'
    
    # Drop identifiers and highly correlated variables to avoid data leakage
    # We drop vehicle_count and average_speed because in real-time future forecasting, 
    # we don't know the exact future vehicle count, we only know current weather/time!
    drop_cols = [target_reg, target_clf, 'timestamp', 'road_id', 'vehicle_count', 'average_speed']
    features = [col for col in df.columns if col not in drop_cols]
    
    X = df[features]
    y_reg = df[target_reg]
    y_clf = df[target_clf]
    
    # 80% Train (Past), 20% Test (Future)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_reg_train, y_reg_test = y_reg.iloc[:split_idx], y_reg.iloc[split_idx:]
    y_clf_train, y_clf_test = y_clf.iloc[:split_idx], y_clf.iloc[split_idx:]
    
    print(f"Training on {len(X_train)} samples, Testing on {len(X_test)} samples.")
    
    os.makedirs('models', exist_ok=True)
    
    # ---------------- REGRESSION MODELS (Exact Density) ----------------
    print("\n--- Training Regression Models ---")
    
    # Baseline: Linear Regression
    lr_model = LinearRegression()
    lr_model.fit(X_train, y_reg_train)
    lr_pred = lr_model.predict(X_test)
    print(f"Linear Regression -> MAE: {mean_absolute_error(y_reg_test, lr_pred):.2f} | R2: {r2_score(y_reg_test, lr_pred):.2f}")
    
    # Advanced: XGBoost Regressor
    xgb_reg = xgb.XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42)
    xgb_reg.fit(X_train, y_reg_train)
    xgb_pred = xgb_reg.predict(X_test)
    print(f"XGBoost Regressor -> MAE: {mean_absolute_error(y_reg_test, xgb_pred):.2f} | R2: {r2_score(y_reg_test, xgb_pred):.2f}")
    
    joblib.dump(xgb_reg, 'models/xgboost_regressor.pkl')
    
    # ---------------- CLASSIFICATION MODELS (Congestion Categories) ----------------
    print("\n--- Training Classification Models ---")
    
    rf_clf = RandomForestClassifier(n_estimators=100, random_state=42)
    rf_clf.fit(X_train, y_clf_train)
    rf_pred = rf_clf.predict(X_test)
    
    print(f"Random Forest Classifier Accuracy: {accuracy_score(y_clf_test, rf_pred) * 100:.2f}%")
    print("Classification Report:")
    print(classification_report(y_clf_test, rf_pred, target_names=['Low', 'Moderate', 'High', 'Very High']))
    
    joblib.dump(rf_clf, 'models/rf_classifier.pkl')
    
    # Save the feature column names so the API knows exactly what inputs the model expects
    joblib.dump(features, 'models/feature_names.pkl')
    print("\n[SUCCESS] Models saved to the 'models/' directory.")

if __name__ == "__main__":
    train_models('data/processed/ml_ready_data.csv')
