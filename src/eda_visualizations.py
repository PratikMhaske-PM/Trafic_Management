import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def run_eda(file_path):
    print("Loading cleaned data for EDA...")
    df = pd.read_csv(file_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Extract time features for plotting
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.day_name()
    
    # Create output directory
    out_dir = "notebooks/eda_plots"
    os.makedirs(out_dir, exist_ok=True)
    
    sns.set_theme(style="whitegrid")

    # 1. Distribution of Traffic Density
    plt.figure(figsize=(8, 5))
    sns.histplot(df['traffic_density'], bins=30, kde=True, color='purple')
    plt.title('Distribution of Traffic Density')
    plt.savefig(f"{out_dir}/01_density_distribution.png")
    plt.close()

    # 2. Traffic by Hour of Day
    plt.figure(figsize=(10, 5))
    sns.boxplot(x='hour', y='traffic_density', data=df, palette='viridis')
    plt.title('Traffic Density by Hour of Day')
    plt.savefig(f"{out_dir}/02_density_by_hour.png")
    plt.close()

    # 3. Traffic by Day of Week
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    plt.figure(figsize=(10, 5))
    sns.barplot(x='day_of_week', y='traffic_density', data=df, order=days_order, palette='coolwarm')
    plt.title('Average Traffic Density by Day of Week')
    plt.savefig(f"{out_dir}/03_density_by_day.png")
    plt.close()

    # 4. Average Speed vs Traffic Density
    plt.figure(figsize=(8, 5))
    sns.scatterplot(x='traffic_density', y='average_speed', hue='weather_condition', data=df, alpha=0.6)
    plt.title('Average Speed vs. Traffic Density')
    plt.savefig(f"{out_dir}/04_speed_vs_density.png")
    plt.close()

    # 5. Weather vs Traffic Density
    plt.figure(figsize=(8, 5))
    sns.boxplot(x='weather_condition', y='traffic_density', data=df, palette='Set2')
    plt.title('Impact of Weather on Traffic Density')
    plt.savefig(f"{out_dir}/05_weather_impact.png")
    plt.close()

    # 6. Correlation Heatmap
    plt.figure(figsize=(10, 8))
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
    corr = df[numeric_cols].corr()
    sns.heatmap(corr, annot=True, cmap='RdBu_r', fmt=".2f")
    plt.title('Correlation Heatmap')
    plt.savefig(f"{out_dir}/06_correlation_heatmap.png")
    plt.close()

    print(f"EDA Complete! 6 high-quality visualizations have been saved to the '{out_dir}' folder.")

if __name__ == "__main__":
    run_eda('data/processed/cleaned_traffic_data.csv')
