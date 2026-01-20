"""
Load vegetation NDVI data from CSV files into the database.

Reads vegetation CSV files and adds them to the pollution.db database.
"""

import sys
import csv
import sqlite3
from pathlib import Path
from datetime import datetime

def load_vegetation_data_to_db():
    """Load vegetation NDVI data into database."""
    
    print("=" * 60)
    print("Loading Vegetation Data to Database")
    print("=" * 60)
    
    # Paths
    data_dir = Path(__file__).parent.parent / "data" / "vegetation"
    db_path = str(Path(__file__).parent.parent / "pollution.db")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create Vegetation table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Vegetation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            state_name TEXT NOT NULL,
            year INTEGER NOT NULL,
            
            -- NDVI Statistics (-1 to 1 scale)
            ndvi_mean REAL,
            ndvi_stddev REAL,
            ndvi_min REAL,
            ndvi_max REAL,
            
            -- Vegetation Health Classification
            vegetation_health TEXT,
            
            -- Metadata
            data_source TEXT DEFAULT 'MODIS_MOD13A2',
            collection_date TIMESTAMP,
            
            UNIQUE(state_name, year)
        )
    """)
    
    print("\n✓ Created/verified Vegetation table")
    
    # Find all vegetation CSV files
    csv_files = sorted(data_dir.glob("India_Vegetation_NDVI_*.csv"))
    
    if not csv_files:
        print("✗ No vegetation CSV files found")
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
                # Classify vegetation health based on NDVI
                ndvi_mean = float(row['ndvi_mean']) if row.get('ndvi_mean') else None
                
                if ndvi_mean is not None:
                    if ndvi_mean >= 0.6:
                        veg_health = 'Dense'  # Forests
                    elif ndvi_mean >= 0.4:
                        veg_health = 'Moderate'  # Crops, grasslands
                    elif ndvi_mean >= 0.2:
                        veg_health = 'Sparse'
                    else:
                        veg_health = 'Very Sparse'
                else:
                    veg_health = 'Unknown'
                
                # Insert or replace
                cursor.execute("""
                    INSERT OR REPLACE INTO Vegetation (
                        state_name, year,
                        ndvi_mean, ndvi_stddev, ndvi_min, ndvi_max,
                        vegetation_health,
                        data_source, collection_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row['state_name'],
                    int(row['year']),
                    float(row['ndvi_mean']) if row.get('ndvi_mean') else None,
                    float(row['ndvi_stddev']) if row.get('ndvi_stddev') else None,
                    float(row['ndvi_min']) if row.get('ndvi_min') else None,
                    float(row['ndvi_max']) if row.get('ndvi_max') else None,
                    veg_health,
                    'MODIS_MOD13A2',
                    datetime.utcnow()
                ))
                
                records_loaded += 1
            
            print(f"    ✓ Loaded {records_loaded} records")
            total_loaded += records_loaded
    
    conn.commit()
    
    # Summary statistics
    cursor.execute("""
        SELECT 
            year,
            COUNT(*) as states,
            ROUND(AVG(ndvi_mean), 3) as avg_ndvi,
            MAX(ndvi_mean) as max_ndvi,
            MIN(ndvi_mean) as min_ndvi
        FROM Vegetation
        GROUP BY year
        ORDER BY year
    """)
    
    print("\n" + "=" * 60)
    print("Vegetation Data Summary by Year")
    print("=" * 60)
    print(f"{'Year':<6} {'States':<8} {'Avg NDVI':<12} {'Max NDVI':<12} {'Min NDVI':<12}")
    print("-" * 60)
    
    for row in cursor.fetchall():
        year, states, avg_ndvi, max_ndvi, min_ndvi = row
        print(f"{year:<6} {states:<8} {avg_ndvi:<12} {max_ndvi:<12.3f} {min_ndvi:<12.3f}")
    
    # Health distribution
    cursor.execute("""
        SELECT vegetation_health, COUNT(*) as count
        FROM Vegetation
        GROUP BY vegetation_health
        ORDER BY count DESC
    """)
    
    print("\n" + "=" * 60)
    print("Vegetation Health Distribution")
    print("=" * 60)
    for health, count in cursor.fetchall():
        print(f"  {health}: {count} state-years")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print(f"✓ Loaded {total_loaded} vegetation records to database")
    print("=" * 60)


if __name__ == "__main__":
    load_vegetation_data_to_db()
