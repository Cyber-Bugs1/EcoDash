"""
Generate Synthetic Weather Data Based on Known Climate Patterns

This generates realistic weather data based on Indian Meteorological Department (IMD)
historical averages when API connections fail.
"""

import sqlite3
import random
from datetime import datetime
from pathlib import Path

# Climate data by state (based on IMD historical averages)
CLIMATE_DATA = {
    'Delhi': {'temp_range': (5, 45), 'rainfall': 800, 'humidity_range': (30, 85)},
    'Maharashtra': {'temp_range': (15, 40), 'rainfall': 1200, 'humidity_range': (50, 85)},
    'Uttar Pradesh': {'temp_range': (5, 45), 'rainfall': 900, 'humidity_range': (35, 85)},
    'Bihar': {'temp_range': (8, 42), 'rainfall': 1100, 'humidity_range': (40, 90)},
    'West Bengal': {'temp_range': (10, 40), 'rainfall': 1800, 'humidity_range': (60, 95)},
    'Tamil Nadu': {'temp_range': (20, 40), 'rainfall': 1000, 'humidity_range': (60, 85)},
    'Karnataka': {'temp_range': (15, 38), 'rainfall': 1100, 'humidity_range': (50, 80)},
    'Gujarat': {'temp_range': (12, 42), 'rainfall': 600, 'humidity_range': (35, 75)},
    'Rajasthan': {'temp_range': (5, 48), 'rainfall': 400, 'humidity_range': (20, 60)},
    'Madhya Pradesh': {'temp_range': (8, 45), 'rainfall': 1000, 'humidity_range': (30, 80)},
    'Andhra Pradesh': {'temp_range': (18, 42), 'rainfall': 900, 'humidity_range': (55, 85)},
    'Kerala': {'temp_range': (22, 35), 'rainfall': 3000, 'humidity_range': (70, 95)},
    'Punjab': {'temp_range': (2, 45), 'rainfall': 600, 'humidity_range': (30, 80)},
    'Haryana': {'temp_range': (3, 45), 'rainfall': 500, 'humidity_range': (30, 75)},
    'Jharkhand': {'temp_range': (8, 42), 'rainfall': 1300, 'humidity_range': (45, 90)},
    'Chhattisgarh': {'temp_range': (10, 42), 'rainfall': 1200, 'humidity_range': (45, 85)},
    'Odisha': {'temp_range': (12, 42), 'rainfall': 1500, 'humidity_range': (55, 90)},
    'Assam': {'temp_range': (10, 35), 'rainfall': 2500, 'humidity_range': (70, 95)},
    'Uttarakhand': {'temp_range': (-5, 35), 'rainfall': 1500, 'humidity_range': (40, 85)},
    'Himachal Pradesh': {'temp_range': (-10, 30), 'rainfall': 1200, 'humidity_range': (40, 80)},
    'Goa': {'temp_range': (20, 35), 'rainfall': 2800, 'humidity_range': (65, 90)},
    'Tripura': {'temp_range': (10, 35), 'rainfall': 2000, 'humidity_range': (65, 95)},
    'Meghalaya': {'temp_range': (5, 28), 'rainfall': 4000, 'humidity_range': (70, 95)},
    'Sikkim': {'temp_range': (-5, 25), 'rainfall': 2500, 'humidity_range': (60, 90)},
}

# Monthly temperature factors (% of annual range)
MONTHLY_TEMP = {
    1: 0.15, 2: 0.25, 3: 0.45, 4: 0.65, 5: 0.85, 6: 0.80,
    7: 0.70, 8: 0.68, 9: 0.65, 10: 0.50, 11: 0.30, 12: 0.18
}

# Monthly rainfall distribution (% of annual)
MONTHLY_RAIN = {
    1: 0.02, 2: 0.02, 3: 0.02, 4: 0.03, 5: 0.05, 6: 0.18,
    7: 0.28, 8: 0.25, 9: 0.10, 10: 0.03, 11: 0.01, 12: 0.01
}


def create_tables(db_path):
    """Create weather tables."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS DailyWeather (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            state_name TEXT,
            date TEXT,
            temp_mean REAL,
            temp_max REAL,
            temp_min REAL,
            humidity_mean REAL,
            wind_speed_mean REAL,
            wind_speed_max REAL,
            precipitation_mm REAL,
            rain_mm REAL,
            weather_code INTEGER,
            data_source TEXT,
            UNIQUE(state_name, date)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS MonthlyWeather (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            state_name TEXT,
            year INTEGER,
            month INTEGER,
            temp_mean REAL,
            temp_max REAL,
            temp_min REAL,
            humidity_mean REAL,
            wind_speed_mean REAL,
            total_precipitation_mm REAL,
            rain_days INTEGER,
            data_source TEXT,
            collection_date TEXT,
            UNIQUE(state_name, year, month)
        )
    """)
    
    conn.commit()
    conn.close()
    print("[OK] Weather tables created")


def generate_weather_data(state, year, month, climate):
    """Generate realistic weather data for a state-month."""
    temp_min_base, temp_max_base = climate['temp_range']
    temp_range = temp_max_base - temp_min_base
    
    # Monthly temperature
    factor = MONTHLY_TEMP[month]
    temp_mean = temp_min_base + temp_range * factor
    temp_max = temp_mean + random.uniform(3, 8)
    temp_min = temp_mean - random.uniform(3, 8)
    
    # Humidity
    h_min, h_max = climate['humidity_range']
    # Higher humidity in monsoon
    if month in [6, 7, 8, 9]:
        humidity = random.uniform(h_max - 15, h_max)
    else:
        humidity = random.uniform(h_min, (h_min + h_max) / 2)
    
    # Rainfall
    annual_rain = climate['rainfall']
    monthly_rain = annual_rain * MONTHLY_RAIN[month]
    # Add variability
    monthly_rain *= (0.7 + random.random() * 0.6)
    
    # Rain days estimate
    if monthly_rain > 0:
        rain_days = max(1, int(monthly_rain / 15))
    else:
        rain_days = 0
    
    # Wind speed
    wind_mean = random.uniform(5, 15)
    wind_max = wind_mean + random.uniform(5, 15)
    
    return {
        'temp_mean': round(temp_mean, 1),
        'temp_max': round(temp_max, 1),
        'temp_min': round(temp_min, 1),
        'humidity_mean': round(humidity, 1),
        'wind_speed_mean': round(wind_mean, 1),
        'wind_speed_max': round(wind_max, 1),
        'precipitation_mm': round(monthly_rain, 1),
        'rain_days': rain_days
    }


def main():
    db_path = str(Path(__file__).parent.parent / "processed_data.db")
    
    print("=" * 70)
    print("Synthetic Weather Data Generation (IMD Calibrated)")
    print("=" * 70)
    
    create_tables(db_path)
    
    random.seed(42)  # Reproducibility
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    years = [2020, 2021, 2022, 2023, 2024]
    total = 0
    
    print(f"\nGenerating for {len(CLIMATE_DATA)} states, {len(years)} years\n")
    
    for state, climate in CLIMATE_DATA.items():
        print(f"{state}:", end=" ")
        
        for year in years:
            for month in range(1, 13):
                data = generate_weather_data(state, year, month, climate)
                
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO MonthlyWeather
                        (state_name, year, month, temp_mean, temp_max, temp_min,
                         humidity_mean, wind_speed_mean, total_precipitation_mm, rain_days,
                         data_source, collection_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        state, year, month, data['temp_mean'], data['temp_max'],
                        data['temp_min'], data['humidity_mean'], data['wind_speed_mean'],
                        data['precipitation_mm'], data['rain_days'],
                        'Synthetic-IMD-Calibrated', datetime.now().isoformat()
                    ))
                    total += 1
                except Exception as e:
                    pass
        
        print("✓")
    
    conn.commit()
    conn.close()
    
    print(f"\n{'='*70}")
    print(f"Complete! Generated {total} monthly weather records")
    print(f"{'='*70}")
    
    # Summary
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT state_name, 
               ROUND(AVG(temp_mean), 1) as avg_temp,
               ROUND(SUM(total_precipitation_mm)/5, 0) as annual_rain
        FROM MonthlyWeather
        GROUP BY state_name
        ORDER BY avg_temp DESC
    """)
    
    print("\nClimate summary:")
    print(f"  {'State':<20} {'Avg Temp':<12} {'Annual Rain'}")
    print(f"  {'-'*20} {'-'*12} {'-'*12}")
    for row in cursor.fetchall():
        print(f"  {row[0]:<20} {row[1]:>6.1f}°C    {row[2]:>6.0f} mm")
    
    conn.close()


if __name__ == "__main__":
    main()
