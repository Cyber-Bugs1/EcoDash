"""
Script to collect comprehensive water resources data.

Collects three water metrics:
1. Surface Water - % coverage from JRC Global Surface Water
2. Annual Rainfall - Total mm from GPM satellite
3. Water Stress - Dry months and rainfall variability

Usage:
    uv run python scripts/collect_water_data.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data_collection import WaterDataCollector


def main():
    """Main function to collect water resources data."""
    print("=" * 60)
    print("Water Resources Data Collector")
    print("=" * 60)
    
    # Configuration
    years = [2020, 2021, 2022, 2023]
    output_dir = Path(__file__).parent.parent / "data" / "water"
    
    print(f"\nConfiguration:")
    print(f"  Years: {years}")
    print(f"  Output directory: {output_dir}")
    print(f"  Metrics: Surface water, Rainfall, Water stress")
    print()
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize collector
    collector = WaterDataCollector(output_dir=str(output_dir))
    
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
            collector.save_to_csv(data, f"India_Water_Resources_{year}.csv")
            collector.save_to_json(data, f"India_Water_Resources_{year}.json")
            
            print(f"\n✓ Completed water data for {year}")
            
        except Exception as e:
            print(f"✗ Error collecting data for {year}: {e}")
    
    print("\n" + "=" * 60)
    print("Collection complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
