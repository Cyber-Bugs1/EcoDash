"""
Water Resources Data Collector using Google Earth Engine.

Collects three water-related metrics:
1. Surface Water - JRC Global Surface Water (reservoir/lake coverage)
2. Rainfall - GPM precipitation data
3. Groundwater Indicator - GRACE water storage anomaly (when available)

These metrics help understand:
- Water availability and drought conditions
- Relationship with vegetation health
- Impact on air quality (dust from dry areas)
"""

import ee
import json
import csv
from pathlib import Path
from typing import Dict, List
from datetime import datetime

from .india_states import INDIAN_STATES
from .gee_auth import PROJECT_ID


class WaterDataCollector:
    """
    Collects water resources data from multiple satellite sources.
    
    Metrics:
    - Surface water percentage (JRC)
    - Annual rainfall (GPM)
    - Water storage anomaly (from precipitation as proxy)
    """
    
    def __init__(self, output_dir: str = "data/water"):
        """Initialize the water data collector."""
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
    
    def get_surface_water(self, state_name: str, year: int) -> Dict:
        """
        Get surface water coverage for a state.
        
        Uses JRC Global Surface Water dataset.
        
        Args:
            state_name: Name of the state
            year: Year to collect data for
        
        Returns:
            Dictionary with surface water statistics
        """
        try:
            # Get state geometry
            state_geom = self.india.filter(
                ee.Filter.eq('ADM1_NAME', state_name)
            ).geometry()
            
            # JRC Global Surface Water - yearly history
            # Use occurrence (percentage of time water was present)
            jrc = ee.Image('JRC/GSW1_4/GlobalSurfaceWater')
            
            # Get water occurrence (0-100%)
            water_occurrence = jrc.select('occurrence')
            
            # Calculate statistics
            stats = water_occurrence.reduceRegion(
                reducer=ee.Reducer.mean().combine(
                    ee.Reducer.max(), '', True
                ).combine(
                    ee.Reducer.percentile([25, 75]), '', True
                ),
                geometry=state_geom,
                scale=1000,
                maxPixels=1e9
            ).getInfo()
            
            if stats and 'occurrence_mean' in stats:
                return {
                    'surface_water_mean': stats.get('occurrence_mean'),
                    'surface_water_max': stats.get('occurrence_max'),
                    'surface_water_p25': stats.get('occurrence_p25'),
                    'surface_water_p75': stats.get('occurrence_p75'),
                }
            else:
                return {}
                
        except Exception as e:
            print(f"    Surface water error: {e}")
            return {}
    
    def get_rainfall(self, state_name: str, year: int) -> Dict:
        """
        Get annual rainfall for a state.
        
        Uses CHIRPS (Climate Hazards Group InfraRed Precipitation with Station data).
        
        Args:
            state_name: Name of the state
            year: Year to collect data for
        
        Returns:
            Dictionary with rainfall statistics
        """
        try:
            # Get state geometry
            state_geom = self.india.filter(
                ee.Filter.eq('ADM1_NAME', state_name)
            ).geometry()
            
            # Date range
            start_date = f'{year}-01-01'
            end_date = f'{year}-12-31'
            
            # CHIRPS precipitation (mm/day) - more reliable than GPM
            chirps = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY') \
                .filterDate(start_date, end_date) \
                .filterBounds(state_geom) \
                .select('precipitation')
            
            # Calculate total annual rainfall (sum of daily values)
            total_precip = chirps.sum()
            
            # Get statistics
            stats = total_precip.reduceRegion(
                reducer=ee.Reducer.mean().combine(
                    ee.Reducer.stdDev(), '', True
                ).combine(
                    ee.Reducer.min(), '', True
                ).combine(
                    ee.Reducer.max(), '', True
                ),
                geometry=state_geom,
                scale=5000,  # 5km resolution
                maxPixels=1e9
            ).getInfo()
            
            if stats and 'precipitation_mean' in stats:
                return {
                    'rainfall_annual_mm': stats.get('precipitation_mean'),
                    'rainfall_stddev': stats.get('precipitation_stdDev'),
                    'rainfall_min': stats.get('precipitation_min'),
                    'rainfall_max': stats.get('precipitation_max'),
                }
            else:
                return {}
                
        except Exception as e:
            print(f"    Rainfall error: {e}")
            return {}
    
    def get_water_stress_indicator(self, state_name: str, year: int) -> Dict:
        """
        Calculate water stress indicator from rainfall patterns.
        
        Uses monthly rainfall to calculate dry season length and variability.
        
        Args:
            state_name: Name of the state
            year: Year to collect data for
        
        Returns:
            Dictionary with water stress indicators
        """
        try:
            # Get state geometry
            state_geom = self.india.filter(
                ee.Filter.eq('ADM1_NAME', state_name)
            ).geometry()
            
            # Get monthly rainfall using CHIRPS
            months_data = []
            for month in range(1, 13):
                start = f'{year}-{month:02d}-01'
                if month == 12:
                    end = f'{year+1}-01-01'
                else:
                    end = f'{year}-{month+1:02d}-01'
                
                monthly = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY') \
                    .filterDate(start, end) \
                    .select('precipitation') \
                    .sum()
                
                mean_val = monthly.reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=state_geom,
                    scale=5000,
                    maxPixels=1e9
                ).getInfo()
                
                if mean_val and 'precipitation' in mean_val and mean_val['precipitation'] is not None:
                    months_data.append(mean_val['precipitation'])
            
            if len(months_data) >= 6:  # Need at least 6 months
                # Count dry months (< 50mm/month)
                dry_months = sum(1 for m in months_data if m < 50)
                
                # Calculate coefficient of variation
                import numpy as np
                mean_rainfall = np.mean(months_data) if months_data else 0
                cv = (np.std(months_data) / mean_rainfall) * 100 if mean_rainfall > 0 else 0
                
                return {
                    'dry_months_count': dry_months,
                    'rainfall_variability_cv': round(cv, 1),
                    'wettest_month_mm': round(max(months_data), 1),
                    'driest_month_mm': round(min(months_data), 1),
                }
            else:
                return {}
                
        except Exception as e:
            print(f"    Water stress error: {e}")
            return {}
    
    def collect_annual_data(self, year: int) -> Dict[str, any]:
        """
        Collect all water metrics for all states for a given year.
        
        Args:
            year: Year to collect data for
        
        Returns:
            Dictionary with all water data
        """
        print(f"\nCollecting water resources data for {year}...")
        
        # Get available states
        states = self.get_available_states()
        print(f"Found {len(states)} states")
        
        results = []
        
        # Process each state
        for i, state in enumerate(states):
            print(f"  [{i+1}/{len(states)}] Processing {state}...")
            
            state_data = {
                'state_name': state,
                'year': year,
            }
            
            # Get surface water
            print(f"    - Surface water...", end=" ", flush=True)
            surface_water = self.get_surface_water(state, year)
            state_data.update(surface_water)
            if surface_water:
                print(f"[OK] {surface_water.get('surface_water_mean', 0):.1f}%")
            else:
                print("No data")
            
            # Get rainfall
            print(f"    - Rainfall...", end=" ", flush=True)
            rainfall = self.get_rainfall(state, year)
            state_data.update(rainfall)
            if rainfall and rainfall.get('rainfall_annual_mm'):
                print(f"[OK] {rainfall['rainfall_annual_mm']:.0f} mm")
            else:
                print("No data")
            
            # Get water stress
            print(f"    - Water stress...", end=" ", flush=True)
            water_stress = self.get_water_stress_indicator(state, year)
            state_data.update(water_stress)
            if water_stress:
                print(f"[OK] {water_stress.get('dry_months_count', 0)} dry months")
            else:
                print("No data")
            
            results.append(state_data)
        
        return {
            'data_type': 'WATER_RESOURCES',
            'year': year,
            'states': results,
        }
    
    def save_to_csv(self, data: Dict, filename: str):
        """Save water data to CSV."""
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
        """Save water data to JSON."""
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"[OK] Saved data to {filepath}")


if __name__ == "__main__":
    # Test collection
    collector = WaterDataCollector()
    
    if collector.initialize():
        data = collector.collect_annual_data(2023)
        collector.save_to_csv(data, "India_Water_Resources_2023.csv")
        collector.save_to_json(data, "India_Water_Resources_2023.json")
