
"""
Load water resources data from CSV files into the database.

Reads water CSV files and adds them to the processed_data.db database.
"""

import sys
import csv
import sqlite3
from pathlib import Path
from datetime import datetime

def load_water_data_to_db():
    """Load water resources data into database."""
    
    print("=" * 60)
    print("Loading Water Resources Data to Database")
    print("=" * 60)
    
    # Paths
    data_dir = Path(__file__).parent.parent / "data" / "water"
    db_path = str(Path(__file__).parent.parent / "processed_data.db")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create Water table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Water (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            state_name TEXT NOT NULL,
            year INTEGER NOT NULL,
            
            -- Surface Water Statistics (%)
            surface_water_mean REAL,
            surface_water_max REAL,
            surface_water_p25 REAL,
            surface_water_p75 REAL,
            
            -- Rainfall Statistics (mm)
            rainfall_annual_mm REAL,
            rainfall_stddev REAL,
            rainfall_min REAL,
            rainfall_max REAL,
            
            -- Water Stress Indicators
            dry_months_count INTEGER,
            rainfall_variability_cv REAL,
            wettest_month_mm REAL,
            driest_month_mm REAL,
            
            -- Derived Classifications
            rainfall_category TEXT,
            water_stress_level TEXT,
            
            -- Metadata
            data_source TEXT DEFAULT 'JRC_CHIRPS',
            collection_date TIMESTAMP,
            
            UNIQUE(state_name, year)
        )
    """)
    
    print("\n[OK] Created/verified Water table")
    
    # Find all water CSV files
    csv_files = sorted(data_dir.glob("India_Water_Resources_*.csv"))
    
    if not csv_files:
        print("[X] No water CSV files found")
        conn.close()
        return
    
    print(f"\nFound {len(csv_files)} CSV files to load")
    
    # Load each CSV file
    total_loaded = 0
    
    for csv_file in csv_files:
        print(f"\n  Loading {csv_file.name}...")
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            records_loaded = 0
            
            for row in reader:
                # Classify rainfall category
                rainfall = float(row.get('rainfall_annual_mm') or 0)
                if rainfall >= 2000:
                    rainfall_cat = 'Very High'
                elif rainfall >= 1200:
                    rainfall_cat = 'High'
                elif rainfall >= 800:
                    rainfall_cat = 'Moderate'
                elif rainfall >= 400:
                    rainfall_cat = 'Low'
                else:
                    rainfall_cat = 'Very Low'
                
                # Classify water stress level
                dry_months = int(row.get('dry_months_count') or 0)
                if dry_months >= 8:
                    stress_level = 'Severe'
                elif dry_months >= 6:
                    stress_level = 'High'
                elif dry_months >= 4:
                    stress_level = 'Moderate'
                else:
                    stress_level = 'Low'
                
                # Insert or replace
                cursor.execute("""
                    INSERT OR REPLACE INTO Water (
                        state_name, year,
                        surface_water_mean, surface_water_max, surface_water_p25, surface_water_p75,
                        rainfall_annual_mm, rainfall_stddev, rainfall_min, rainfall_max,
                        dry_months_count, rainfall_variability_cv, wettest_month_mm, driest_month_mm,
                        rainfall_category, water_stress_level,
                        data_source, collection_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row['state_name'],
                    int(row['year']),
                    float(row['surface_water_mean']) if row.get('surface_water_mean') else None,
                    float(row['surface_water_max']) if row.get('surface_water_max') else None,
                    float(row['surface_water_p25']) if row.get('surface_water_p25') else None,
                    float(row['surface_water_p75']) if row.get('surface_water_p75') else None,
                    float(row['rainfall_annual_mm']) if row.get('rainfall_annual_mm') else None,
                    float(row['rainfall_stddev']) if row.get('rainfall_stddev') else None,
                    float(row['rainfall_min']) if row.get('rainfall_min') else None,
                    float(row['rainfall_max']) if row.get('rainfall_max') else None,
                    int(row['dry_months_count']) if row.get('dry_months_count') else None,
                    float(row['rainfall_variability_cv']) if row.get('rainfall_variability_cv') else None,
                    float(row['wettest_month_mm']) if row.get('wettest_month_mm') else None,
                    float(row['driest_month_mm']) if row.get('driest_month_mm') else None,
                    rainfall_cat,
                    stress_level,
                    'JRC_CHIRPS',
                    datetime.utcnow()
                ))
                
                records_loaded += 1
            
            print(f"    [OK] Loaded {records_loaded} records")
            total_loaded += records_loaded
    
    conn.commit()
    
    # Summary statistics
    cursor.execute("""
        SELECT 
            year,
            COUNT(*) as states,
            ROUND(AVG(rainfall_annual_mm), 0) as avg_rainfall,
            ROUND(AVG(dry_months_count), 1) as avg_dry_months
        FROM Water
        GROUP BY year
        ORDER BY year
    """)
    
    print("\n" + "=" * 60)
    print("Water Data Summary by Year")
    print("=" * 60)
    print(f"{'Year':<6} {'States':<8} {'Avg Rainfall (mm)':<18} {'Avg Dry Months':<15}")
    print("-" * 60)
    
    for row in cursor.fetchall():
        year, states, avg_rain, avg_dry = row
        print(f"{year:<6} {states:<8} {avg_rain:<18} {avg_dry:<15}")
    
    # Stress distribution
    cursor.execute("""
        SELECT water_stress_level, COUNT(*) as count
        FROM Water
        GROUP BY water_stress_level
        ORDER BY count DESC
    """)
    
    print("\n" + "=" * 60)
    print("Water Stress Level Distribution")
    print("=" * 60)
    for level, count in cursor.fetchall():
        print(f"  {level}: {count} state-years")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print(f"[OK] Loaded {total_loaded} water records to database")
    print("=" * 60)


if __name__ == "__main__":
    load_water_data_to_db()
