"""
Vegetation Data Collector using NDVI from Google Earth Engine.

Collects Normalized Difference Vegetation Index (NDVI) data from MODIS satellite
for vegetation health monitoring across Indian states.

NDVI ranges from -1 to +1:
- 0.6-1.0: Dense vegetation (forests)
- 0.4-0.6: Moderate vegetation (grasslands, crops)
- 0.2-0.4: Sparse vegetation
- 0.0-0.2: Very sparse vegetation
- < 0.0: Water, snow, clouds
"""

import ee
import json
import csv
from pathlib import Path
from typing import Dict, List
from datetime import datetime

from .india_states import INDIAN_STATES
from .gee_auth import PROJECT_ID


class VegetationDataCollector:
    """
    Collects vegetation health data using NDVI from MODIS satellite.
    
    Uses MODIS NDVI dataset (MOD13A2) - 16-day 1km resolution.
    """
    
    def __init__(self, output_dir: str = "data/vegetation"):
        """Initialize the vegetation data collector."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.initialized = False
        self.india = None
        
    def initialize(self) -> bool:
        """Initialize Google Earth Engine."""
        try:
            ee.Initialize(project=PROJECT_ID)
            self.initialized = True
            print("✓ Earth Engine initialized successfully")
            
            # Load India boundary from FAO GAUL dataset
            gaul = ee.FeatureCollection('FAO/GAUL/2015/level1')
            self.india = gaul.filter(ee.Filter.eq('ADM0_NAME', 'India'))
            
            return True
        except Exception as e:
            print(f"✗ Failed to initialize Earth Engine: {e}")
            return False
    
    def get_available_states(self) -> List[str]:
        """Get list of available Indian states from FAO GAUL dataset."""
        try:
            states = self.india.aggregate_array('ADM1_NAME').getInfo()
            return sorted(states)
        except Exception as e:
            print(f"✗ Error getting states: {e}")
            return []
    
    def get_ndvi_for_state(self, state_name: str, year: int) -> Dict:
        """
        Get annual NDVI statistics for a state.
        
        Args:
            state_name: Name of the state
            year: Year to collect data for
        
        Returns:
            Dictionary with NDVI statistics
        """
        try:
            # Get state geometry
            state_geom = self.india.filter(
                ee.Filter.eq('ADM1_NAME', state_name)
            ).geometry()
            
            # Date range for the year
            start_date = f'{year}-01-01'
            end_date = f'{year}-12-31'
            
            # Load MODIS NDVI dataset (MOD13A2 - 16-day 1km)
            # NDVI values are scaled by 10000
            ndvi_collection = ee.ImageCollection('MODIS/006/MOD13A2') \
                .filterDate(start_date, end_date) \
                .filterBounds(state_geom) \
                .select('NDVI')
            
            # Calculate annual statistics
            # Mean NDVI across the year
            mean_ndvi = ndvi_collection.mean()
            
            # Get statistics for the state
            stats = mean_ndvi.reduceRegion(
                reducer=ee.Reducer.mean().combine(
                    ee.Reducer.stdDev(), '', True
                ).combine(
                    ee.Reducer.min(), '', True
                ).combine(
                    ee.Reducer.max(), '', True
                ),
                geometry=state_geom,
                scale=1000,  # 1km resolution
                maxPixels=1e9
            ).getInfo()
            
            # NDVI is scaled by 10000 in MODIS, convert to actual values (-1 to 1)
            if stats and 'NDVI_mean' in stats:
                return {
                    'state_name': state_name,
                    'year': year,
                    'ndvi_mean': stats['NDVI_mean'] / 10000.0 if stats['NDVI_mean'] else None,
                    'ndvi_stddev': stats['NDVI_stdDev'] / 10000.0 if stats.get('NDVI_stdDev') else None,
                    'ndvi_min': stats['NDVI_min'] / 10000.0 if stats.get('NDVI_min') else None,
                    'ndvi_max': stats['NDVI_max'] / 10000.0 if stats.get('NDVI_max') else None,
                }
            else:
                return None
                
        except Exception as e:
            print(f"  ✗ Error processing {state_name}: {e}")
            return None
    
    def get_india_ndvi(self, year: int) -> Dict:
        """
        Get country-wide NDVI statistics for India.
        
        Args:
            year: Year to collect data for
        
        Returns:
            Dictionary with country-wide NDVI statistics
        """
        try:
            # Date range
            start_date = f'{year}-01-01'
            end_date = f'{year}-12-31'
            
            # India geometry
            india_geom = self.india.geometry()
            
            # Load NDVI
            ndvi_collection = ee.ImageCollection('MODIS/006/MOD13A2') \
                .filterDate(start_date, end_date) \
                .filterBounds(india_geom) \
                .select('NDVI')
            
            mean_ndvi = ndvi_collection.mean()
            
            # Country-wide statistics (use larger scale for faster computation)
            stats = mean_ndvi.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=india_geom,
                scale=10000,  # 10km for country level
                maxPixels=1e9
            ).getInfo()
            
            if stats and 'NDVI' in stats:
                return {
                    'country': 'India',
                    'year': year,
                    'ndvi_mean': stats['NDVI'] / 10000.0 if stats['NDVI'] else None
                }
            else:
                return None
                
        except Exception as e:
            print(f"  ✗ Error for India: {e}")
            return None
    
    def collect_annual_data(self, year: int) -> Dict[str, any]:
        """
        Collect annual NDVI data for all Indian states.
        
        Args:
            year: Year to collect data for
        
        Returns:
            Dictionary with all state data and country-wide data
        """
        print(f"\nCollecting NDVI vegetation data for {year}...")
        
        # Get available states
        states = self.get_available_states()
        print(f"Found {len(states)} states in FAO GAUL dataset")
        
        results = []
        
        # Process each state individually
        for i, state in enumerate(states):
            print(f"  [{i+1}/{len(states)}] Processing {state}...", end=" ", flush=True)
            state_data = self.get_ndvi_for_state(state, year)
            if state_data and state_data.get('ndvi_mean') is not None:
                results.append(state_data)
                print(f"NDVI: {state_data['ndvi_mean']:.3f}")
            else:
                print("No data")
        
        # Get country-wide average
        print("  Processing India (country-wide)...", end=" ", flush=True)
        india_data = self.get_india_ndvi(year)
        if india_data and india_data.get('ndvi_mean'):
            print(f"NDVI: {india_data['ndvi_mean']:.3f}")
        else:
            print("No data")
        
        return {
            'data_type': 'MODIS_NDVI',
            'year': year,
            'states': results,
            'country': india_data
        }
    
    def save_to_csv(self, data: Dict, filename: str):
        """Save vegetation data to CSV."""
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['state_name', 'year', 'ndvi_mean', 'ndvi_stddev', 'ndvi_min', 'ndvi_max']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for state_data in data['states']:
                writer.writerow(state_data)
        
        print(f"✓ Saved data to {filepath}")
    
    def save_to_json(self, data: Dict, filename: str):
        """Save vegetation data to JSON."""
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"✓ Saved data to {filepath}")


if __name__ == "__main__":
    # Test collection for 2023
    collector = VegetationDataCollector()
    
    if collector.initialize():
        data = collector.collect_annual_data(2023)
        collector.save_to_csv(data, "India_Vegetation_NDVI_2023.csv")
        collector.save_to_json(data, "India_Vegetation_NDVI_2023.json")
