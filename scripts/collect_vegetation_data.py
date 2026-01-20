"""
Script to collect vegetation data (NDVI) from Google Earth Engine.

NDVI (Normalized Difference Vegetation Index) measures vegetation health:
- 0.6-1.0: Dense vegetation (forests)
- 0.4-0.6: Moderate vegetation (crops, grasslands)  
- 0.2-0.4: Sparse vegetation
- < 0.2: Very sparse or no vegetation

Usage:
    uv run python scripts/collect_vegetation_data.py
"""

import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data_collection import VegetationDataCollector


def main():
    """Main function to collect vegetation data."""
    print("=" * 60)
    print("Vegetation Data Collector (NDVI)")
    print("=" * 60)
    
    # Configuration
    years = [2020, 2021, 2022, 2023, 2024]
    output_dir = Path(__file__).parent.parent / "data" / "vegetation"
    
    print(f"\nConfiguration:")
    print(f"  Years: {years}")
    print(f"  Output directory: {output_dir}")
    print(f"  Data source: MODIS NDVI (MOD13A2)")
    print()
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize collector
    collector = VegetationDataCollector(output_dir=str(output_dir))
    
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
            collector.save_to_csv(data, f"India_Vegetation_NDVI_{year}.csv")
            collector.save_to_json(data, f"India_Vegetation_NDVI_{year}.json")
            
            print(f"✓ Completed NDVI for {year}\n")
            
        except Exception as e:
            print(f"✗ Error collecting data for {year}: {e}")
    
    print("\n" + "=" * 60)
    print("Collection complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
