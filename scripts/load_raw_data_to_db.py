"""
Script to load raw AOD data from CSV files into the database.

Reads CSV files from data/raw/ directory and populates the raw_pollution_data table.
"""

import sys
import csv
from pathlib import Path
from datetime import datetime

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from database.schema import create_database, get_session, RawPollutionData


def load_aod_csv_to_database(
    csv_file: Path,
    db_path: str = "environmental_monitoring.db"
):
    """
    Load AOD data from CSV file into database.
    
    Args:
        csv_file: Path to CSV file
        db_path: Path to database file
    """
    session = get_session(db_path)
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            records_added = 0
            
            for row in reader:
                # Create raw pollution data record
                record = RawPollutionData(
                    state_name=row['state_name'],
                    year=int(row['year']),
                    aod_mean=float(row['aod_mean']) if row.get('aod_mean') else None,
                    aod_stddev=float(row['aod_stddev']) if row.get('aod_stddev') else None,
                    aod_min=float(row['aod_min']) if row.get('aod_min') else None,
                    aod_max=float(row['aod_max']) if row.get('aod_max') else None,
                    source='MODIS_MCD19A2_AOD',
                    collection_date=datetime.utcnow(),
                    notes=f"Loaded from {csv_file.name}"
                )
                
                session.add(record)
                records_added += 1
            
            session.commit()
            print(f"  ✓ Loaded {records_added} records from {csv_file.name}")
            
    except Exception as e:
        session.rollback()
        print(f"  ✗ Error loading {csv_file.name}: {e}")
    finally:
        session.close()


def load_meteorological_json_to_database(
    json_file: Path,
    db_path: str = "environmental_monitoring.db"
):
    """
    Update raw pollution data with meteorological parameters from JSON.
    
    Args:
        json_file: Path to meteorological JSON file
        db_path: Path to database file
    """
    import json
    
    session = get_session(db_path)
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        year = data['year']
        states_data = data['states']
        
        records_updated = 0
        
        for state_name, met_data in states_data.items():
            # Find matching raw pollution record
            record = session.query(RawPollutionData).filter_by(
                state_name=state_name,
                year=year
            ).first()
            
            if record:
                # Update with meteorological data
                record.blh = met_data.get('blh')
                record.temperature = met_data.get('temperature')
                record.relative_humidity = met_data.get('relative_humidity')
                records_updated += 1
        
        session.commit()
        print(f"  ✓ Updated {records_updated} records with met data from {json_file.name}")
        
    except Exception as e:
        session.rollback()
        print(f"  ✗ Error updating with {json_file.name}: {e}")
    finally:
        session.close()


def main():
    """Main function to load all raw data."""
    print("=" * 60)
    print("Loading Raw AOD Data to Database")
    print("=" * 60)
    
    # Paths
    data_dir = Path(__file__).parent.parent / "data" / "raw"
    met_dir = Path(__file__).parent.parent / "data" / "meteorological"
    db_path = str(Path(__file__).parent.parent / "environmental_monitoring.db")
    
    # Create database if it doesn't exist
    print("\nInitializing database...")
    create_database(db_path)
    print("✓ Database ready")
    
    # Load AOD CSV files
    print("\nLoading AOD data from CSV files...")
    aod_files = sorted(data_dir.glob("India_Pollution_AOD_*.csv"))
    
    if not aod_files:
        print("  No AOD CSV files found in data/raw/")
        return
    
    for csv_file in aod_files:
        load_aod_csv_to_database(csv_file, db_path)
    
    # Load meteorological data if available
    print("\nUpdating with meteorological data...")
    met_files = sorted(met_dir.glob("meteorological_data_*.json"))
    
    if not met_files:
        print("  No meteorological data files found")
        print("  Run: uv run python scripts/collect_meteorological_data.py")
    else:
        for json_file in met_files:
            load_meteorological_json_to_database(json_file, db_path)
    
    # Summary
    session = get_session(db_path)
    total_records = session.query(RawPollutionData).count()
    records_with_met = session.query(RawPollutionData).filter(
        RawPollutionData.blh.isnot(None)
    ).count()
    session.close()
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Total raw pollution records: {total_records}")
    print(f"Records with meteorological data: {records_with_met}")
    print(f"Records without met data: {total_records - records_with_met}")
    
    if records_with_met < total_records:
        print("\n⚠ Some records missing meteorological data")
        print("  They will use default values during PM2.5 conversion")
    
    print("\n✓ Data loading complete!")


if __name__ == "__main__":
    main()
