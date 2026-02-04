"""
Crop and Agriculture Data Collector using Google Earth Engine.

Collects agricultural metrics from satellite data:
1. Cropland extent (% of state area under cultivation)
2. Crop health indicator (NDVI during growing season)
3. Enhanced Vegetation Index (EVI) for productivity estimation

Note: Actual crop yield requires ground truth data. This provides 
satellite-derived agricultural health indicators that correlate with yield.
"""

import ee
import json
import csv
from pathlib import Path
from typing import Dict, List
from datetime import datetime

from .india_states import INDIAN_STATES
from .gee_auth import PROJECT_ID


class CropDataCollector:
    """
    Collects agricultural data from satellite sources.
    
    Metrics:
    - Cropland percentage (MODIS Land Cover)
    - Growing season NDVI (crop health)
    - EVI (Enhanced Vegetation Index for productivity)
    """
    
    def __init__(self, output_dir: str = "data/crop"):
        """Initialize the crop data collector."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.initialized = False
        self.india = None
        
    def initialize(self) -> bool:
        """Initialize Google Earth Engine."""
        try:
            ee.Initialize(project=PROJECT_ID)
            self.initialized = True
            print("[OK] Earth Engine initialized successfully")
            
            # Load India boundary
            gaul = ee.FeatureCollection('FAO/GAUL/2015/level1')
            self.india = gaul.filter(ee.Filter.eq('ADM0_NAME', 'India'))
            
            return True
        except Exception as e:
            print(f"[X] Failed to initialize Earth Engine: {e}")
            return False
    
    def get_available_states(self) -> List[str]:
        """Get list of available Indian states."""
        try:
            states = self.india.aggregate_array('ADM1_NAME').getInfo()
            return sorted(states)
        except Exception as e:
            print(f"[X] Error getting states: {e}")
            return []
    
    def get_cropland_extent(self, state_name: str, year: int) -> Dict:
        """
        Get cropland extent for a state.
        
        Uses MODIS Land Cover to identify agricultural land.
        
        Args:
            state_name: Name of the state
            year: Year to collect data for
        
        Returns:
            Dictionary with cropland statistics
        """
        try:
            # Get state geometry
            state_geom = self.india.filter(
                ee.Filter.eq('ADM1_NAME', state_name)
            ).geometry()
            
            # MODIS Land Cover Type (MCD12Q1)
            # Class 12 = Croplands, Class 14 = Cropland/Natural vegetation mosaic
            lc_year = min(year, 2022)  # MODIS LC available up to 2022
            
            landcover = ee.ImageCollection('MODIS/061/MCD12Q1') \
                .filterDate(f'{lc_year}-01-01', f'{lc_year}-12-31') \
                .first() \
                .select('LC_Type1')
            
            # Create cropland mask (classes 12 and 14)
            cropland = landcover.eq(12).Or(landcover.eq(14))
            
            # Calculate cropland percentage
            stats = cropland.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=state_geom,
                scale=500,
                maxPixels=1e9
            ).getInfo()
            
            if stats and 'LC_Type1' in stats:
                return {
                    'cropland_percent': (stats['LC_Type1'] or 0) * 100,
                }
            else:
                return {}
                
        except Exception as e:
            print(f"    Cropland error: {e}")
            return {}
    
    def get_crop_health(self, state_name: str, year: int) -> Dict:
        """
        Get crop health indicators during growing season.
        
        Uses NDVI and EVI from MODIS during Kharif (June-Oct) and Rabi (Nov-Mar) seasons.
        
        Args:
            state_name: Name of the state
            year: Year to collect data for
        
        Returns:
            Dictionary with crop health statistics
        """
        try:
            # Get state geometry
            state_geom = self.india.filter(
                ee.Filter.eq('ADM1_NAME', state_name)
            ).geometry()
            
            # Kharif season (monsoon crop): June-October
            kharif_start = f'{year}-06-01'
            kharif_end = f'{year}-10-31'
            
            # Rabi season (winter crop): November-March
            rabi_start = f'{year}-11-01'
            rabi_end = f'{year+1}-03-31'
            
            # Get MODIS vegetation indices
            modis = ee.ImageCollection('MODIS/061/MOD13A2') \
                .filterBounds(state_geom)
            
            # Kharif season NDVI
            kharif_ndvi = modis \
                .filterDate(kharif_start, kharif_end) \
                .select('NDVI') \
                .mean()
            
            kharif_stats = kharif_ndvi.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=state_geom,
                scale=1000,
                maxPixels=1e9
            ).getInfo()
            
            # Rabi season NDVI (previous year's rabi for current year data)
            rabi_ndvi = modis \
                .filterDate(f'{year-1}-11-01', f'{year}-03-31') \
                .select('NDVI') \
                .mean()
            
            rabi_stats = rabi_ndvi.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=state_geom,
                scale=1000,
                maxPixels=1e9
            ).getInfo()
            
            # Get EVI for productivity
            evi_collection = modis \
                .filterDate(f'{year}-01-01', f'{year}-12-31') \
                .select('EVI')
            
            evi_mean = evi_collection.mean()
            evi_max = evi_collection.max()
            
            evi_stats = evi_mean.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=state_geom,
                scale=1000,
                maxPixels=1e9
            ).getInfo()
            
            evi_max_stats = evi_max.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=state_geom,
                scale=1000,
                maxPixels=1e9
            ).getInfo()
            
            result = {}
            
            if kharif_stats and 'NDVI' in kharif_stats:
                result['kharif_ndvi'] = kharif_stats['NDVI'] / 10000.0 if kharif_stats['NDVI'] else None
            
            if rabi_stats and 'NDVI' in rabi_stats:
                result['rabi_ndvi'] = rabi_stats['NDVI'] / 10000.0 if rabi_stats['NDVI'] else None
            
            if evi_stats and 'EVI' in evi_stats:
                result['evi_mean'] = evi_stats['EVI'] / 10000.0 if evi_stats['EVI'] else None
            
            if evi_max_stats and 'EVI' in evi_max_stats:
                result['evi_max'] = evi_max_stats['EVI'] / 10000.0 if evi_max_stats['EVI'] else None
            
            return result
                
        except Exception as e:
            print(f"    Crop health error: {e}")
            return {}
    
    def collect_annual_data(self, year: int) -> Dict[str, any]:
        """
        Collect all crop metrics for all states for a given year.
        
        Args:
            year: Year to collect data for
        
        Returns:
            Dictionary with all crop data
        """
        print(f"\nCollecting crop data for {year}...")
        
        # Get available states
        states = self.get_available_states()
        print(f"Found {len(states)} states")
        
        results = []
        
        # Process each state
        for i, state in enumerate(states):
            print(f"  [{i+1}/{len(states)}] Processing {state}...", end=" ", flush=True)
            
            state_data = {
                'state_name': state,
                'year': year,
            }
            
            # Get cropland extent
            cropland = self.get_cropland_extent(state, year)
            state_data.update(cropland)
            
            # Get crop health
            crop_health = self.get_crop_health(state, year)
            state_data.update(crop_health)
            
            if state_data.get('cropland_percent') is not None:
                print(f"Cropland: {state_data.get('cropland_percent', 0):.1f}%")
            else:
                print("No data")
            
            results.append(state_data)
        
        return {
            'data_type': 'CROP_DATA',
            'year': year,
            'states': results,
        }
    
    def save_to_csv(self, data: Dict, filename: str):
        """Save crop data to CSV."""
        filepath = self.output_dir / filename
        
        if not data['states']:
            print(f"[X] No data to save")
            return
        
        # Get all possible field names
        fieldnames = ['state_name', 'year']
        for state_data in data['states']:
            for key in state_data.keys():
                if key not in fieldnames:
                    fieldnames.append(key)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for state_data in data['states']:
                writer.writerow(state_data)
        
        print(f"[OK] Saved data to {filepath}")
    
    def save_to_json(self, data: Dict, filename: str):
        """Save crop data to JSON."""
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"[OK] Saved data to {filepath}")


if __name__ == "__main__":
    collector = CropDataCollector()
    
    if collector.initialize():
        data = collector.collect_annual_data(2023)
        collector.save_to_csv(data, "India_Crop_Data_2023.csv")
        collector.save_to_json(data, "India_Crop_Data_2023.json")
