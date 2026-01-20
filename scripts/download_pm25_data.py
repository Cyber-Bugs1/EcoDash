"""
Script to download raw PM2.5 satellite data from Google Earth Engine.

This script collects Aerosol Optical Depth (AOD) data from MODIS
for all Indian states across multiple years.

Usage:
    uv run python scripts/download_pm25_data.py

Prerequisites:
    1. Earth Engine authentication: uv run earthengine authenticate
    2. Dependencies installed: uv sync
"""

import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data_collection import PM25DataCollector


def main():
    """Main function to download PM2.5 data."""
    print("=" * 60)
    print("PM2.5 Satellite Data Downloader")
    print("=" * 60)
    y = int(input("Enter the year: "))
    # Configuration
    years = []  # 2023 already downloaded
    output_dir = Path(__file__).parent.parent / "data" / "raw"
    
    print(f"\nConfiguration:")
    print(f"  Years: {years}")
    print(f"  Output directory: {output_dir}")
    print()
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize collector
    collector = PM25DataCollector(output_dir=str(output_dir))
    
    if not collector.initialize():
        print("Failed to initialize Earth Engine. Please authenticate first.")
        return
    
    # Download data for each year
    for year in years:
        try:
            print(f"\n{'='*60}")
            print(f"Processing year {year}")
            print(f"{'='*60}")
            
            data = collector.collect_annual_data(year)
            
            # Save as both CSV and JSON
            collector.save_to_csv(data, f"India_Pollution_AOD_{year}.csv")
            collector.save_to_json(data, f"India_Pollution_AOD_{year}.json")
            
            print(f"✓ Completed AOD for {year}\n")
            
        except Exception as e:
            print(f"✗ Error collecting data for {year}: {e}")
    
    print("\n" + "=" * 60)
    print("Download complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

