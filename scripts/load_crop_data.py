"""
Load crop data from CSV files into the database.
"""

import sys
import csv
import sqlite3
from pathlib import Path
from datetime import datetime

def load_crop_data_to_db():
    """Load crop data into database."""
    
    print("=" * 60)
    print("Loading Crop Data to Database")
    print("=" * 60)
    
    # Paths
    data_dir = Path(__file__).parent.parent / "data" / "crop"
    db_path = str(Path(__file__).parent.parent / "processed_data.db")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create Crop table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Crop (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            state_name TEXT NOT NULL,
            year INTEGER NOT NULL,
            
            -- Cropland Extent
            cropland_percent REAL,
            
            -- Seasonal Crop Health (NDVI)
            kharif_ndvi REAL,
            rabi_ndvi REAL,
            
            -- Enhanced Vegetation Index
            evi_mean REAL,
            evi_max REAL,
            
            -- Derived Classifications
            agricultural_intensity TEXT,
            crop_health_category TEXT,
            
            -- Metadata
            data_source TEXT DEFAULT 'MODIS_MCD12Q1_MOD13A2',
            collection_date TIMESTAMP,
            
            UNIQUE(state_name, year)
        )
    """)
    
    print("\n[OK] Created/verified Crop table")
    
    # Find all crop CSV files
    csv_files = sorted(data_dir.glob("India_Crop_Data_*.csv"))
    
    if not csv_files:
        print("[X] No crop CSV files found")
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
                # Classify agricultural intensity
                cropland = float(row.get('cropland_percent') or 0)
                if cropland >= 80:
                    ag_intensity = 'Very High'
                elif cropland >= 60:
                    ag_intensity = 'High'
                elif cropland >= 40:
                    ag_intensity = 'Moderate'
                elif cropland >= 20:
                    ag_intensity = 'Low'
                else:
                    ag_intensity = 'Very Low'
                
                # Classify crop health
                kharif = float(row.get('kharif_ndvi') or 0)
                if kharif >= 0.5:
                    health_cat = 'Excellent'
                elif kharif >= 0.4:
                    health_cat = 'Good'
                elif kharif >= 0.3:
                    health_cat = 'Moderate'
                else:
                    health_cat = 'Poor'
                
                # Insert or replace
                cursor.execute("""
                    INSERT OR REPLACE INTO Crop (
                        state_name, year,
                        cropland_percent,
                        kharif_ndvi, rabi_ndvi,
                        evi_mean, evi_max,
                        agricultural_intensity, crop_health_category,
                        data_source, collection_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row['state_name'],
                    int(row['year']),
                    float(row['cropland_percent']) if row.get('cropland_percent') else None,
                    float(row['kharif_ndvi']) if row.get('kharif_ndvi') else None,
                    float(row['rabi_ndvi']) if row.get('rabi_ndvi') else None,
                    float(row['evi_mean']) if row.get('evi_mean') else None,
                    float(row['evi_max']) if row.get('evi_max') else None,
                    ag_intensity,
                    health_cat,
                    'MODIS_MCD12Q1_MOD13A2',
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
            ROUND(AVG(cropland_percent), 1) as avg_cropland,
            ROUND(AVG(kharif_ndvi), 3) as avg_kharif_ndvi
        FROM Crop
        GROUP BY year
        ORDER BY year
    """)
    
    print("\n" + "=" * 60)
    print("Crop Data Summary by Year")
    print("=" * 60)
    print(f"{'Year':<6} {'States':<8} {'Avg Cropland %':<15} {'Avg Kharif NDVI':<15}")
    print("-" * 60)
    
    for row in cursor.fetchall():
        year, states, avg_crop, avg_kharif = row
        print(f"{year:<6} {states:<8} {avg_crop:<15} {avg_kharif:<15}")
    
    # Agricultural intensity distribution
    cursor.execute("""
        SELECT agricultural_intensity, COUNT(*) as count
        FROM Crop
        GROUP BY agricultural_intensity
        ORDER BY count DESC
    """)
    
    print("\n" + "=" * 60)
    print("Agricultural Intensity Distribution")
    print("=" * 60)
    for intensity, count in cursor.fetchall():
        print(f"  {intensity}: {count} state-years")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print(f"[OK] Loaded {total_loaded} crop records to database")
    print("=" * 60)


if __name__ == "__main__":
    load_crop_data_to_db()
