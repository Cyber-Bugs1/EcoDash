"""
Script to collect crop and agriculture data.

Collects:
1. Cropland extent (% of state under cultivation)
2. Kharif season NDVI (monsoon crop health)
3. Rabi season NDVI (winter crop health)
4. EVI for productivity estimation

Usage:
    uv run python scripts/collect_crop_data.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data_collection.crop_collector import CropDataCollector


def main():
    """Main function to collect crop data."""
    print("=" * 60)
    print("Crop and Agriculture Data Collector")
    print("=" * 60)
    
    # Configuration
    years = [2020, 2021, 2022, 2023]
    output_dir = Path(__file__).parent.parent / "data" / "crop"
    
    print(f"\nConfiguration:")
    print(f"  Years: {years}")
    print(f"  Output directory: {output_dir}")
    print(f"  Metrics: Cropland %, Kharif NDVI, Rabi NDVI, EVI")
    print()
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize collector
    collector = CropDataCollector(output_dir=str(output_dir))
    
    if not collector.initialize():
        print("Failed to initialize Earth Engine.")
        return
    
    # Collect data for each year
    for year in years:
        try:
            print(f"\n{'='*60}")
            print(f"Processing year {year}")
            print(f"{'='*60}")
            
            data = collector.collect_annual_data(year)
            
            # Save as both CSV and JSON
            collector.save_to_csv(data, f"India_Crop_Data_{year}.csv")
            collector.save_to_json(data, f"India_Crop_Data_{year}.json")
            
            print(f"\n[OK] Completed crop data for {year}")
            
        except Exception as e:
            print(f"[X] Error collecting data for {year}: {e}")
    
    print("\n" + "=" * 60)
    print("Collection complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
