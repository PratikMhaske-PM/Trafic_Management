import pandas as pd
import os

def engineer_features(input_path, output_path):
    print("Loading cleaned data for Feature Engineering...")
    df = pd.read_csv(input_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # 1. Time-based features
    print("Extracting time features...")
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    df['month'] = df['timestamp'].dt.month
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
    
    # Peak hour flag (7-9 AM, 4-7 PM)
    df['is_peak_hour'] = df['hour'].apply(lambda x: 1 if (7 <= x <= 9) or (16 <= x <= 19) else 0)
    
    # 2. Phase 6: Congestion Categories
    def categorize_density(density):
        if density <= 30: return 0    # Low
        elif density <= 60: return 1  # Moderate
        elif density <= 80: return 2  # High
        else: return 3                # Very High
        
    df['congestion_level'] = df['traffic_density'].apply(categorize_density)
    
    # 3. Lag and Rolling features (CRITICAL for forecasting)
    # We must sort and group by road_id to avoid mixing data from different roads!
    print("Calculating historical lag features...")
    df = df.sort_values(by=['road_id', 'timestamp'])
    
    df['density_lag_1'] = df.groupby('road_id')['traffic_density'].shift(1)
    df['density_lag_2'] = df.groupby('road_id')['traffic_density'].shift(2)
    df['density_lag_3'] = df.groupby('road_id')['traffic_density'].shift(3)
    
    # Rolling 3-hour mean density
    df['rolling_density'] = df.groupby('road_id')['traffic_density'].transform(lambda x: x.rolling(window=3, min_periods=1).mean())
    
    # Drop the first 3 hours (rows) per road since they now have NaN lag values
    df = df.dropna()
    
    # 4. One-Hot Encoding for categorical ML inputs
    print("Encoding categorical features...")
    df = pd.get_dummies(df, columns=['road_type', 'weather_condition'], drop_first=True)
    
    # Save the strictly formatted ML data
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Feature engineering complete! Final ML shape: {df.shape}")
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    engineer_features('data/processed/cleaned_traffic_data.csv', 'data/processed/ml_ready_data.csv')
