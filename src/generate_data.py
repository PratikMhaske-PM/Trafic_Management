import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def generate_traffic_data(num_days=90):
    print(f"Generating realistic traffic data for {num_days} days...")
    
    # Define realistic road network
    roads = [
        {'id': 'R101', 'type': 'Highway', 'capacity': 2000, 'lat': 40.7128, 'lon': -74.0060},
        {'id': 'R102', 'type': 'Highway', 'capacity': 1800, 'lat': 40.7135, 'lon': -74.0120},
        {'id': 'R201', 'type': 'Arterial', 'capacity': 1000, 'lat': 40.7200, 'lon': -73.9900},
        {'id': 'R202', 'type': 'Arterial', 'capacity': 1200, 'lat': 40.7250, 'lon': -73.9850},
        {'id': 'R301', 'type': 'Residential', 'capacity': 400, 'lat': 40.7300, 'lon': -73.9800},
    ]
    
    start_date = datetime.now() - timedelta(days=num_days)
    records = []
    
    # Weather states mapped to (temp_range, rain_prob)
    weather_states = {
        'Clear': ((20, 35), 0.0),
        'Cloudy': ((15, 25), 0.1),
        'Rainy': ((10, 20), 1.0),
        'Heavy Rain': ((10, 18), 1.0)
    }

    for day in range(num_days):
        current_date = start_date + timedelta(days=day)
        is_weekend = current_date.weekday() >= 5
        
        # Daily weather
        weather = np.random.choice(['Clear', 'Cloudy', 'Rainy', 'Heavy Rain'], p=[0.6, 0.25, 0.1, 0.05])
        temp_range, rain_prob = weather_states[weather]
        daily_temp = np.random.uniform(temp_range[0], temp_range[1])
        daily_rain = np.random.uniform(2, 15) if np.random.random() < rain_prob else 0
        
        for hour in range(24):
            # Calculate time-based modifiers
            time_modifier = 0.2 # Baseline off-peak
            
            if not is_weekend:
                # Morning peak (7 AM - 9 AM)
                if 7 <= hour <= 9: time_modifier = 0.9
                # Evening peak (4 PM - 7 PM)
                elif 16 <= hour <= 19: time_modifier = 0.95
                # Midday (10 AM - 3 PM)
                elif 10 <= hour <= 15: time_modifier = 0.6
            else:
                # Weekend peak (11 AM - 3 PM)
                if 11 <= hour <= 15: time_modifier = 0.7
                elif 16 <= hour <= 20: time_modifier = 0.6
                
            for road in roads:
                # Base volume based on capacity and time
                expected_vol = road['capacity'] * time_modifier
                
                # Add random noise (± 15%)
                noise = np.random.uniform(0.85, 1.15)
                vehicle_count = int(expected_vol * noise)
                
                # Weather impact on traffic (fewer cars in heavy rain, but slower speeds causing congestion)
                if weather == 'Heavy Rain':
                    vehicle_count = int(vehicle_count * 0.9)
                
                # Accident probability (higher during rain and peak hours)
                accident_prob = 0.05 if (weather in ['Rainy', 'Heavy Rain'] or time_modifier > 0.8) else 0.01
                accident = 1 if np.random.random() < accident_prob else 0
                
                if accident:
                    vehicle_count = int(vehicle_count * 1.2) # Congestion builds up
                
                # Ensure we don't exceed max realistic capacity (120% of design capacity in gridlock)
                vehicle_count = min(vehicle_count, int(road['capacity'] * 1.2))
                vehicle_count = max(0, vehicle_count)
                
                # Calculate speed based on volume (Speed-Density relationship)
                density_ratio = vehicle_count / road['capacity']
                max_speed = 100 if road['type'] == 'Highway' else (60 if road['type'] == 'Arterial' else 40)
                
                # Speed drops as density increases (exponential decay)
                speed_factor = np.exp(-1.5 * max(0, density_ratio - 0.3))
                average_speed = max_speed * speed_factor
                
                if accident:
                    average_speed *= 0.3 # Severe speed drop
                if weather in ['Rainy', 'Heavy Rain']:
                    average_speed *= 0.8 # Moderate speed drop
                    
                average_speed = max(5, int(average_speed)) # Minimum speed 5 km/h in gridlock
                
                records.append({
                    'timestamp': current_date.replace(hour=hour, minute=0, second=0, microsecond=0),
                    'road_id': road['id'],
                    'road_type': road['type'],
                    'road_capacity': road['capacity'],
                    'latitude': road['lat'],
                    'longitude': road['lon'],
                    'vehicle_count': vehicle_count,
                    'average_speed': average_speed,
                    'weather_condition': weather,
                    'temperature': round(daily_temp, 1),
                    'rainfall': round(daily_rain, 1),
                    'accident': accident
                })
                
    df = pd.DataFrame(records)
    
    # Calculate Traffic Density
    df['traffic_density'] = (df['vehicle_count'] / df['road_capacity']) * 100
    df['traffic_density'] = df['traffic_density'].round(2)
    
    # Generate previous density (simulating a lag for future ML features)
    df = df.sort_values(by=['road_id', 'timestamp'])
    df['previous_density'] = df.groupby('road_id')['traffic_density'].shift(1)
    
    # Save to data/raw
    os.makedirs('data/raw', exist_ok=True)
    output_path = 'data/raw/traffic_data.csv'
    df.to_csv(output_path, index=False)
    print(f"Dataset generated successfully! Shape: {df.shape}")
    print(f"Saved to: {output_path}")

if __name__ == "__main__":
    generate_traffic_data()
