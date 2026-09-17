import pandas as pd
import numpy as np
import os

def clean_traffic_data(input_path, output_path):
    print(f"Loading raw data from {input_path}...")
    df = pd.read_csv(input_path)

    # 1. Convert Timestamp to Datetime objects
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # 2. Handle Duplicates
    duplicates = df.duplicated().sum()
    if duplicates > 0:
        print(f"Removing {duplicates} duplicate rows...")
        df = df.drop_duplicates()

    # 3. Handle Missing Values (Simulated fallback for real-world APIs)
    # Forward-fill weather conditions because weather persists
    df['weather_condition'] = df['weather_condition'].ffill()
    
    # Fill numerical columns with median if any are missing
    for col in ['temperature', 'rainfall', 'average_speed']:
        if df[col].isnull().sum() > 0:
            df[col] = df[col].fillna(df[col].median())

    # 4. Outlier Detection & Handling
    # Cap absurdly high vehicle counts to the road's physical max capacity (e.g., 150%)
    df['vehicle_count'] = np.where(
        df['vehicle_count'] > df['road_capacity'] * 1.5,
        df['road_capacity'] * 1.5,
        df['vehicle_count']
    )
    
    # Ensure no negative speeds or counts
    df = df[(df['vehicle_count'] >= 0) & (df['average_speed'] >= 0)]

    # 5. Data Sorting (Crucial for time-series forecasting later)
    df = df.sort_values(by=['road_id', 'timestamp'])

    # Save processed data
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Data cleaning complete! Cleaned dataset saved to {output_path}")
    print(f"Cleaned Shape: {df.shape}")
    
    return df

if __name__ == "__main__":
    clean_traffic_data('data/raw/traffic_data.csv', 'data/processed/cleaned_traffic_data.csv')
