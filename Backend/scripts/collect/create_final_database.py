"""
Create final pollution database with simplified Pollution table.
Consolidates all processed data into a clean, ready-to-use format.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from database.schema import get_session, ProcessedPollutionData
import sqlite3

def create_final_database():
    """Create final pollution.db with clean Pollution table."""
    
    print("="*60)
    print("Creating Final Pollution Database")
    print("="*60)
    
    # Source database
    source_db = str(Path(__file__).parent.parent / "environmental_monitoring.db")
    
    # Final database
    final_db = str(Path(__file__).parent.parent / "pollution.db")
    
    # Get all processed data
    session = get_session(source_db)
    all_data = session.query(ProcessedPollutionData).order_by(
        ProcessedPollutionData.year,
        ProcessedPollutionData.state_name
    ).all()
    
    print(f"\nFound {len(all_data)} records to export")
    
    # Create new database with simplified schema
    conn = sqlite3.connect(final_db)
    cursor = conn.cursor()
    
    # Drop existing table if exists
    cursor.execute("DROP TABLE IF EXISTS Pollution")
    
    # Create Pollution table
    cursor.execute("""
        CREATE TABLE Pollution (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            state_name TEXT NOT NULL,
            year INTEGER NOT NULL,
            
            -- AOD Data
            aod_mean REAL,
            aod_stddev REAL,
            aod_min REAL,
            aod_max REAL,
            
            -- PM2.5 Data (µg/m³)
            pm25_mean REAL NOT NULL,
            pm25_stddev REAL,
            pm25_min REAL,
            pm25_max REAL,
            
            -- AQI Data (India CPCB)
            aqi_mean INTEGER,
            aqi_category TEXT,
            aqi_color TEXT,
            
            -- Safety Flags
            exceeds_who_limit BOOLEAN,
            exceeds_india_limit BOOLEAN,
            
            -- Trends
            year_over_year_change REAL,
            trend_direction TEXT,
            
            -- Metadata
            conversion_method TEXT,
            scale_factor REAL,
            processing_date TIMESTAMP,
            
            UNIQUE(state_name, year)
        )
    """)
    
    print("\n✓ Created Pollution table")
    
    # Insert data
    inserted = 0
    for record in all_data:
        cursor.execute("""
            INSERT INTO Pollution (
                state_name, year,
                aod_mean, aod_stddev, aod_min, aod_max,
                pm25_mean, pm25_stddev, pm25_min, pm25_max,
                aqi_mean, aqi_category, aqi_color,
                exceeds_who_limit, exceeds_india_limit,
                year_over_year_change, trend_direction,
                conversion_method, scale_factor, processing_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.state_name, record.year,
            record.aod_mean, record.aod_stddev, record.aod_min, record.aod_max,
            record.pm25_mean, record.pm25_stddev, record.pm25_min, record.pm25_max,
            record.aqi_mean, record.aqi_category, record.aqi_color,
            record.exceeds_who_limit, record.exceeds_india_limit,
            record.year_over_year_change, record.trend_direction,
            record.conversion_method, record.hygroscopic_factor, record.processing_date
        ))
        inserted += 1
    
    conn.commit()
    
    print(f"✓ Inserted {inserted} records")
    
    # Summary statistics
    cursor.execute("""
        SELECT 
            year,
            COUNT(*) as states,
            ROUND(AVG(pm25_mean), 1) as avg_pm25,
            MAX(pm25_mean) as max_pm25,
            MIN(pm25_mean) as min_pm25,
            SUM(CASE WHEN exceeds_india_limit = 1 THEN 1 ELSE 0 END) as exceeds_limit
        FROM Pollution
        GROUP BY year
        ORDER BY year
    """)
    
    print("\n" + "="*60)
    print("Summary by Year")
    print("="*60)
    print(f"{'Year':<6} {'States':<8} {'Avg PM2.5':<12} {'Max':<10} {'Min':<10} {'Exceeds':<10}")
    print("-"*60)
    
    for row in cursor.fetchall():
        year, states, avg_pm25, max_pm25, min_pm25, exceeds = row
        print(f"{year:<6} {states:<8} {avg_pm25:<12} {max_pm25:<10.1f} {min_pm25:<10.1f} {exceeds}/{states}")
    
    conn.close()
    session.close()
    
    print("\n" + "="*60)
    print(f"✓ Final database created: {final_db}")
    print("="*60)
    print(f"\nTable: Pollution")
    print(f"Records: {inserted}")
    print(f"Years: 2020-2024")
    print(f"States: 34 per year")
    
    return final_db

if __name__ == "__main__":
    create_final_database()
