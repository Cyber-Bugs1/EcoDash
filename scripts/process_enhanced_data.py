"""
Process and Merge Enhanced Environmental Data

This script:
1. Merges all collected data (pollution, weather, fires)
2. Creates a unified training dataset
3. Computes seasonal factors from actual data
4. Prepares data for enhanced model training
"""

import sqlite3
from datetime import datetime
from pathlib import Path


def create_enhanced_tables(db_path):
    """Create tables for processed/merged data."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Enhanced monthly environmental data (merged)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS EnhancedMonthlyData (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            state_name TEXT,
            year INTEGER,
            month INTEGER,
            season TEXT,
            
            -- Pollution metrics
            pm25_mean REAL,
            pm25_max REAL,
            pm25_min REAL,
            aqi_mean REAL,
            pm10_mean REAL,
            no2_mean REAL,
            
            -- Weather metrics
            temp_mean REAL,
            temp_max REAL,
            temp_min REAL,
            humidity_mean REAL,
            wind_speed_mean REAL,
            precipitation_mm REAL,
            rain_days INTEGER,
            
            -- Fire metrics
            fire_count INTEGER,
            fire_frp_avg REAL,
            fire_frp_total REAL,
            
            -- Derived features
            pollution_severity TEXT,
            weather_pollution_correlation REAL,
            seasonal_factor REAL,
            
            collection_date TEXT,
            UNIQUE(state_name, year, month)
        )
    """)
    
    # Seasonal patterns table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS SeasonalPatterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            state_name TEXT,
            season TEXT,
            
            -- Pollution seasonal averages
            pm25_seasonal_avg REAL,
            pm25_seasonal_std REAL,
            pm25_seasonal_factor REAL,
            
            -- Weather seasonal averages
            temp_seasonal_avg REAL,
            humidity_seasonal_avg REAL,
            precip_seasonal_total REAL,
            
            -- Fire seasonal averages
            fire_seasonal_avg REAL,
            
            data_years TEXT,
            UNIQUE(state_name, season)
        )
    """)
    
    conn.commit()
    conn.close()
    print("[OK] Enhanced tables created")


def get_season(month):
    """Get Indian season from month."""
    if month in [12, 1, 2]:
        return 'Winter'
    elif month in [3, 4, 5]:
        return 'Summer'
    elif month in [6, 7, 8, 9]:
        return 'Monsoon'
    else:
        return 'Post-Monsoon'


def get_pollution_severity(pm25):
    """Classify pollution severity."""
    if pm25 is None:
        return 'Unknown'
    elif pm25 < 30:
        return 'Good'
    elif pm25 < 60:
        return 'Moderate'
    elif pm25 < 90:
        return 'Poor'
    elif pm25 < 120:
        return 'Very Poor'
    else:
        return 'Severe'


def merge_monthly_data(db_path):
    """Merge pollution, weather, and fire data into unified table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\nMerging monthly data...")
    
    # Get all state-year-month combinations from pollution data
    cursor.execute("""
        SELECT DISTINCT state_name, year, month FROM MonthlyPollution
        UNION
        SELECT DISTINCT state_name, year, month FROM MonthlyWeather
        UNION
        SELECT DISTINCT state_name, year, month FROM MonthlyFires
    """)
    combinations = cursor.fetchall()
    
    print(f"Found {len(combinations)} state-year-month combinations")
    
    merged_count = 0
    for state, year, month in combinations:
        # Get pollution data
        cursor.execute("""
            SELECT AVG(pm25_mean), MAX(pm25_max), MIN(pm25_min), 
                   AVG(aqi_mean), AVG(pm10_mean), AVG(no2_mean)
            FROM MonthlyPollution
            WHERE state_name = ? AND year = ? AND month = ?
        """, (state, year, month))
        pollution = cursor.fetchone()
        
        # Get weather data
        cursor.execute("""
            SELECT temp_mean, temp_max, temp_min, humidity_mean, 
                   wind_speed_mean, total_precipitation_mm, rain_days
            FROM MonthlyWeather
            WHERE state_name = ? AND year = ? AND month = ?
        """, (state, year, month))
        weather = cursor.fetchone()
        
        # Get fire data
        cursor.execute("""
            SELECT fire_count, avg_frp, total_frp
            FROM MonthlyFires
            WHERE state_name = ? AND year = ? AND month = ?
        """, (state, year, month))
        fires = cursor.fetchone() or (0, 0, 0)
        
        # Merge data
        season = get_season(month)
        pm25 = pollution[0] if pollution else None
        severity = get_pollution_severity(pm25)
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO EnhancedMonthlyData
                (state_name, year, month, season,
                 pm25_mean, pm25_max, pm25_min, aqi_mean, pm10_mean, no2_mean,
                 temp_mean, temp_max, temp_min, humidity_mean, wind_speed_mean,
                 precipitation_mm, rain_days,
                 fire_count, fire_frp_avg, fire_frp_total,
                 pollution_severity, collection_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                state, year, month, season,
                pollution[0] if pollution else None,
                pollution[1] if pollution else None,
                pollution[2] if pollution else None,
                pollution[3] if pollution else None,
                pollution[4] if pollution else None,
                pollution[5] if pollution else None,
                weather[0] if weather else None,
                weather[1] if weather else None,
                weather[2] if weather else None,
                weather[3] if weather else None,
                weather[4] if weather else None,
                weather[5] if weather else None,
                weather[6] if weather else None,
                fires[0] if fires else 0,
                fires[1] if fires else 0,
                fires[2] if fires else 0,
                severity,
                datetime.now().isoformat()
            ))
            merged_count += 1
        except Exception as e:
            pass
    
    conn.commit()
    print(f"Merged {merged_count} records into EnhancedMonthlyData")
    
    conn.close()


def compute_seasonal_patterns(db_path):
    """Compute seasonal patterns from actual data."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\nComputing seasonal patterns...")
    
    # Get all states
    cursor.execute("SELECT DISTINCT state_name FROM EnhancedMonthlyData")
    states = [row[0] for row in cursor.fetchall()]
    
    seasons = ['Winter', 'Summer', 'Monsoon', 'Post-Monsoon']
    pattern_count = 0
    
    for state in states:
        # Get annual average PM2.5 for this state
        cursor.execute("""
            SELECT AVG(pm25_mean) FROM EnhancedMonthlyData 
            WHERE state_name = ? AND pm25_mean IS NOT NULL
        """, (state,))
        annual_avg = cursor.fetchone()[0]
        
        if not annual_avg:
            continue
        
        for season in seasons:
            # Get seasonal statistics
            cursor.execute("""
                SELECT 
                    AVG(pm25_mean), 
                    AVG(CASE WHEN pm25_mean IS NOT NULL THEN (pm25_mean - ?)*(pm25_mean - ?) ELSE NULL END),
                    AVG(temp_mean),
                    AVG(humidity_mean),
                    SUM(precipitation_mm),
                    AVG(fire_count),
                    GROUP_CONCAT(DISTINCT year)
                FROM EnhancedMonthlyData
                WHERE state_name = ? AND season = ? AND pm25_mean IS NOT NULL
            """, (annual_avg, annual_avg, state, season))
            
            result = cursor.fetchone()
            
            if result and result[0]:
                pm25_avg = result[0]
                pm25_var = result[1] if result[1] else 0
                pm25_std = pm25_var ** 0.5 if pm25_var > 0 else 0
                seasonal_factor = pm25_avg / annual_avg if annual_avg > 0 else 1.0
                
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO SeasonalPatterns
                        (state_name, season, pm25_seasonal_avg, pm25_seasonal_std,
                         pm25_seasonal_factor, temp_seasonal_avg, humidity_seasonal_avg,
                         precip_seasonal_total, fire_seasonal_avg, data_years)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        state, season,
                        pm25_avg, pm25_std, seasonal_factor,
                        result[2], result[3], result[4], result[5],
                        result[6]
                    ))
                    pattern_count += 1
                except Exception as e:
                    pass
    
    conn.commit()
    print(f"Computed {pattern_count} seasonal patterns")
    
    conn.close()


def show_summary(db_path):
    """Show summary of processed data."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n" + "=" * 70)
    print("DATA SUMMARY")
    print("=" * 70)
    
    # Enhanced monthly data
    cursor.execute("SELECT COUNT(*) FROM EnhancedMonthlyData")
    print(f"\nEnhanced Monthly Records: {cursor.fetchone()[0]}")
    
    cursor.execute("""
        SELECT state_name, COUNT(*), 
               ROUND(AVG(pm25_mean), 1) as avg_pm25,
               ROUND(AVG(temp_mean), 1) as avg_temp,
               SUM(fire_count) as total_fires
        FROM EnhancedMonthlyData
        WHERE pm25_mean IS NOT NULL
        GROUP BY state_name
        ORDER BY avg_pm25 DESC
        LIMIT 10
    """)
    print("\nTop 10 Most Polluted States (from enhanced data):")
    print(f"  {'State':<25} {'Records':<10} {'Avg PM2.5':<12} {'Avg Temp':<12} {'Fires'}")
    print(f"  {'-'*25} {'-'*10} {'-'*12} {'-'*12} {'-'*10}")
    for row in cursor.fetchall():
        print(f"  {row[0]:<25} {row[1]:<10} {row[2]:<12} {row[3]:<12} {row[4]}")
    
    # Seasonal patterns
    cursor.execute("SELECT COUNT(*) FROM SeasonalPatterns")
    print(f"\nSeasonal Patterns: {cursor.fetchone()[0]}")
    
    cursor.execute("""
        SELECT season, 
               ROUND(AVG(pm25_seasonal_factor), 2) as avg_factor,
               ROUND(AVG(pm25_seasonal_avg), 1) as avg_pm25,
               ROUND(AVG(temp_seasonal_avg), 1) as avg_temp
        FROM SeasonalPatterns
        GROUP BY season
        ORDER BY avg_factor DESC
    """)
    print("\nSeasonal Factors (from actual data):")
    print(f"  {'Season':<20} {'Pollution Factor':<18} {'Avg PM2.5':<12} {'Avg Temp'}")
    print(f"  {'-'*20} {'-'*18} {'-'*12} {'-'*10}")
    for row in cursor.fetchall():
        print(f"  {row[0]:<20} {row[1]:<18} {row[2]:<12} {row[3]}")
    
    # Winter pollution spikes
    cursor.execute("""
        SELECT state_name, 
               ROUND(AVG(pm25_mean), 1) as winter_pm25,
               ROUND(AVG(fire_count), 1) as avg_fires
        FROM EnhancedMonthlyData
        WHERE season = 'Winter' AND pm25_mean IS NOT NULL
        GROUP BY state_name
        ORDER BY winter_pm25 DESC
        LIMIT 5
    """)
    print("\nWinter Pollution Hotspots:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} μg/m³ (Avg fires: {row[2]})")
    
    conn.close()


def main():
    db_path = str(Path(__file__).parent.parent / "processed_data.db")
    
    print("=" * 70)
    print("Process and Merge Enhanced Environmental Data")
    print("=" * 70)
    
    # Create tables
    create_enhanced_tables(db_path)
    
    # Merge data
    merge_monthly_data(db_path)
    
    # Compute seasonal patterns
    compute_seasonal_patterns(db_path)
    
    # Show summary
    show_summary(db_path)
    
    print("\n" + "=" * 70)
    print("Data processing complete!")
    print("You can now re-train the AI models with enhanced data.")
    print("=" * 70)


if __name__ == "__main__":
    main()
