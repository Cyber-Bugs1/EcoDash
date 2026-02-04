"""
Optimized PM2.5 Satellite Data Collector using Google Earth Engine.

Processes states individually to avoid timeout errors.
Uses MODIS Aerosol Optical Depth (AOD) data which correlates with PM2.5.
"""

import ee
import json
import csv
from pathlib import Path
from typing import Optional, List, Dict, Any
from .india_states import INDIAN_STATES
from .gee_auth import PROJECT_ID


class PM25DataCollector:
    """
    Collects PM2.5 related satellite data from Google Earth Engine.
    
    Uses MODIS products for Aerosol Optical Depth (AOD) which correlates with PM2.5.
    Processes each state individually to avoid Earth Engine timeout errors.
    """
    
    def __init__(self, output_dir: str = "data/raw"):
        """Initialize the PM2.5 data collector."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.initialized = False
        
    def initialize(self) -> bool:
        """Initialize Google Earth Engine."""
        try:
            ee.Initialize(project=PROJECT_ID)
            self.initialized = True
            print("✓ Earth Engine initialized successfully")
            return True
        except Exception as e:
            print(f"✗ Failed to initialize Earth Engine: {e}")
            print("  Run: earthengine authenticate")
            return False
    
    def get_state_geometry(self, state_name: str) -> ee.Geometry:
        """Get geometry for a specific Indian state."""
        gaul = ee.FeatureCollection("FAO/GAUL/2015/level1")
        state = gaul.filter(ee.Filter.And(
            ee.Filter.eq('ADM0_NAME', 'India'),
            ee.Filter.eq('ADM1_NAME', state_name)
        )).first()
        return state.geometry()
    
    def get_india_geometry(self) -> ee.Geometry:
        """Get geometry for entire India."""
        gaul = ee.FeatureCollection("FAO/GAUL/2015/level0")
        india = gaul.filter(ee.Filter.eq('ADM0_NAME', 'India')).first()
        return india.geometry()
    
    def get_available_states(self) -> List[str]:
        """Get list of state names available in FAO GAUL dataset."""
        gaul = ee.FeatureCollection("FAO/GAUL/2015/level1")
        india_states = gaul.filter(ee.Filter.eq('ADM0_NAME', 'India'))
        states_info = india_states.aggregate_array('ADM1_NAME').getInfo()
        return sorted(states_info)
    
    def get_aod_for_state(
        self,
        state_name: str,
        year: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get annual AOD data for a single state.
        
        Args:
            state_name: Name of the state
            year: Year to collect data for
            
        Returns:
            Dictionary with AOD statistics for the state
        """
        if not self.initialized:
            if not self.initialize():
                return None
        
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        
        try:
            # Get state geometry
            geometry = self.get_state_geometry(state_name)
            
            # MODIS Terra/Aqua combined AOD product
            modis_aod = ee.ImageCollection('MODIS/061/MCD19A2_GRANULES') \
                .filterDate(start_date, end_date) \
                .filterBounds(geometry) \
                .select('Optical_Depth_047')
            
            # Calculate mean AOD
            mean_image = modis_aod.mean()
            
            # Get statistics for the state
            stats = mean_image.reduceRegion(
                reducer=ee.Reducer.mean().combine(
                    ee.Reducer.stdDev(), '', True
                ).combine(
                    ee.Reducer.minMax(), '', True
                ),
                geometry=geometry,
                scale=5000,  # 5km resolution for faster processing
                maxPixels=1e8
            )
            
            result = stats.getInfo()
            
            return {
                'state_name': state_name,
                'year': year,
                'aod_mean': result.get('Optical_Depth_047_mean'),
                'aod_stddev': result.get('Optical_Depth_047_stdDev'),
                'aod_min': result.get('Optical_Depth_047_min'),
                'aod_max': result.get('Optical_Depth_047_max'),
            }
            
        except Exception as e:
            print(f"  ✗ Error for {state_name}: {e}")
            return {
                'state_name': state_name,
                'year': year,
                'aod_mean': None,
                'aod_stddev': None,
                'aod_min': None,
                'aod_max': None,
                'error': str(e)
            }
    
    def get_aod_for_india(self, year: int) -> Optional[Dict[str, Any]]:
        """Get annual AOD data for entire India (country-wide average)."""
        if not self.initialized:
            if not self.initialize():
                return None
        
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        
        try:
            geometry = self.get_india_geometry()
            
            modis_aod = ee.ImageCollection('MODIS/061/MCD19A2_GRANULES') \
                .filterDate(start_date, end_date) \
                .filterBounds(geometry) \
                .select('Optical_Depth_047')
            
            mean_image = modis_aod.mean()
            
            stats = mean_image.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=geometry,
                scale=10000,  # 10km resolution for faster country-wide processing
                maxPixels=1e8
            )
            
            result = stats.getInfo()
            
            return {
                'country': 'India',
                'year': year,
                'aod_mean': result.get('Optical_Depth_047'),
            }
            
        except Exception as e:
            print(f"  ✗ Error for India: {e}")
            return None
    
    def collect_annual_data(self, year: int) -> Dict[str, Any]:
        """
        Collect annual AOD data for all Indian states.
        
        Args:
            year: Year to collect data for
            
        Returns:
            Dictionary with all state data and country-wide data
        """
        print(f"\nCollecting AOD data for {year}...")
        
        # Get available states from GEE
        states = self.get_available_states()
        print(f"Found {len(states)} states in FAO GAUL dataset")
        
        results = []
        
        # Process each state individually
        for i, state in enumerate(states):
            print(f"  [{i+1}/{len(states)}] Processing {state}...", end=" ", flush=True)
            state_data = self.get_aod_for_state(state, year)
            if state_data:
                results.append(state_data)
                if state_data.get('aod_mean') is not None:
                    print(f"AOD: {state_data['aod_mean']:.4f}")
                else:
                    print("No data")
            else:
                print("Failed")
        
        # Get country-wide average
        print("  Processing India (country-wide)...", end=" ", flush=True)
        india_data = self.get_aod_for_india(year)
        if india_data and india_data.get('aod_mean'):
            print(f"AOD: {india_data['aod_mean']:.4f}")
        else:
            print("No data")
        
        return {
            'data_type': 'MODIS_AOD',
            'year': year,
            'states': results,
            'country': india_data
        }
    
    def save_to_csv(self, data: Dict[str, Any], filename: str):
        """Save collected data to CSV file."""
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            if not data.get('states'):
                print(f"No data to save for {filename}")
                return
            
            fieldnames = ['state_name', 'year', 'aod_mean', 'aod_stddev', 'aod_min', 'aod_max']
            
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            
            for state_data in data['states']:
                writer.writerow(state_data)
        
        print(f"✓ Saved data to {filepath}")
    
    def save_to_json(self, data: Dict[str, Any], filename: str):
        """Save collected data to JSON file."""
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"✓ Saved data to {filepath}")


def download_pm25_data(
    years: List[int],
    output_dir: str = "data/raw"
):
    """
    Download PM2.5 related satellite data for specified years.
    
    Args:
        years: List of years to download data for
        output_dir: Directory to save data
    """
    collector = PM25DataCollector(output_dir=output_dir)
    
    if not collector.initialize():
        print("Failed to initialize Earth Engine. Please authenticate first.")
        return
    
    for year in years:
        try:
            data = collector.collect_annual_data(year)
            
            # Save as both CSV and JSON
            collector.save_to_csv(data, f"India_Pollution_AOD_{year}.csv")
            collector.save_to_json(data, f"India_Pollution_AOD_{year}.json")
            
            print(f"✓ Completed AOD for {year}\n")
            
        except Exception as e:
            print(f"✗ Error collecting data for {year}: {e}")


if __name__ == "__main__":
    # Download AOD data for 2020-2024
    download_pm25_data(years=[2020, 2021, 2022, 2023, 2024])
