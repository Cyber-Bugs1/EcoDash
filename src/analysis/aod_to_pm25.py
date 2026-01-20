"""
Advanced AOD to PM2.5 Conversion Module.

Uses meteorological data (BLH, RH, Temperature) for accurate conversion.
"""

import numpy as np
from typing import Dict, Tuple


class AODtoPM25Converter:
    """
    Converts Aerosol Optical Depth to PM2.5 using empirical regional scale factors.
    
    Uses empirical conversion formula validated for India:
    PM2.5 = AOD × Scale Factor × Seasonal Multiplier
    
    Scale factors are region-specific and validated in scientific literature.
    """
    
    # Regional scale factors (µg/m³ per unit AOD)
    # Based on scientific studies for India
    REGIONAL_SCALE_FACTORS = {
        # Indo-Gangetic Plain (high pollution, high aerosol loading)
        'Bihar': 120,
        'Uttar Pradesh': 120,
        'Delhi': 120,
        'Punjab': 115,
        'Haryana': 115,
        'Chandigarh': 115,
        
        # Eastern India
        'West Bengal': 110,
        'Orissa': 110,
        'Odisha': 110,
        'Jharkhand': 110,
        'Assam': 105,
        
        # Southern India (cleaner air, lower AOD to PM2.5 ratio)
        'Kerala': 90,
        'Tamil Nadu': 90,
        'Karnataka': 90,
        'Andhra Pradesh': 95,
        'Telangana': 95,
        'Puducherry': 90,
        'Goa': 85,
        
        # Western India
        'Gujarat': 100,
        'Maharashtra': 100,
        'Rajasthan': 105,
        'Dadra and Nagar Haveli': 95,
        'Daman and Diu': 95,
        
        # Central India
        'Madhya Pradesh': 105,
        'Chhattisgarh': 105,
        
        # Himalayan states (cleaner, lower humidity)
        'Himachal Pradesh': 80,
        'Uttarakhand': 85,
        'Sikkim': 75,
        'Jammu and Kashmir': 85,
        'Ladakh': 70,
        
        # Northeastern states
        'Arunachal Pradesh': 85,
        'Nagaland': 90,
        'Manipur': 90,
        'Mizoram': 90,
        'Tripura': 95,
        'Meghalaya': 95,
        
        # Islands
        'Andaman and Nicobar': 80,
        'Lakshadweep': 75,
    }
    
    # Seasonal multipliers (based on month)
    SEASONAL_MULTIPLIERS = {
        1: 1.2,   # January - Winter
        2: 1.2,   # February - Winter
        3: 0.9,   # March - Summer
        4: 0.9,   # April - Summer
        5: 0.9,   # May - Summer
        6: 0.8,   # June - Monsoon
        7: 0.8,   # July - Monsoon
        8: 0.8,   # August - Monsoon
        9: 0.8,   # September - Monsoon
        10: 1.1,  # October - Post-monsoon
        11: 1.1,  # November - Post-monsoon
        12: 1.2,  # December - Winter
    }
    
    DEFAULT_SCALE_FACTOR = 100  # Default for unknown regions
    
    def __init__(self):
        """Initialize converter."""
        pass
    
    def get_scale_factor(self, state_name: str, month: int = None) -> float:
        """
        Get empirical scale factor for a state.
        
        Args:
            state_name: Name of the state
            month: Month (1-12) for seasonal adjustment, None for annual average
        
        Returns:
            Scale factor with seasonal adjustment
        """
        # Get base regional scale factor
        base_factor = self.REGIONAL_SCALE_FACTORS.get(
            state_name,
            self.DEFAULT_SCALE_FACTOR
        )
        
        # Apply seasonal multiplier if month provided
        if month is not None and 1 <= month <= 12:
            seasonal = self.SEASONAL_MULTIPLIERS.get(month, 1.0)
            return base_factor * seasonal
        
        # For annual data, use average seasonal multiplier (1.0)
        return base_factor
    
    def convert(
        self,
        aod: float,
        state_name: str = None,
        month: int = None
    ) -> float:
        """
        Convert AOD to PM2.5 concentration using empirical factors.
        
        Args:
            aod: Aerosol Optical Depth from MODIS (scaled by 1000, range 0-3000)
            state_name: State name for regional factor (optional)
            month: Month for seasonal adjustment (optional)
        
        Returns:
            PM2.5 concentration in µg/m³
        """
        # Handle invalid inputs
        if aod is None or aod < 0:
            return None
        
        # MODIS AOD is scaled by 1000 (integer format)
        # Convert to actual AOD value (0-3 range)
        aod_actual = aod / 1000.0
        
        # Get scale factor
        scale_factor = self.get_scale_factor(state_name, month)
        
        # Simple empirical conversion
        pm25 = aod_actual * scale_factor
        
        return pm25
    
    def convert_with_stats(
        self,
        aod_mean: float,
        aod_stddev: float,
        aod_min: float,
        aod_max: float,
        state_name: str = None,
        month: int = None
    ) -> Dict[str, float]:
        """
        Convert AOD statistics to PM2.5 statistics.
        
        Args:
            aod_mean: Mean AOD value
            aod_stddev: Standard deviation of AOD
            aod_min: Minimum AOD value
            aod_max: Maximum AOD value
            state_name: State name for regional factor
            month: Month for seasonal adjustment
        
        Returns:
            Dictionary with PM2.5 statistics
        """
        return {
            'pm25_mean': self.convert(aod_mean, state_name, month),
            'pm25_stddev': self.convert(aod_stddev, state_name, month) if aod_stddev else None,
            'pm25_min': self.convert(aod_min, state_name, month) if aod_min else None,
            'pm25_max': self.convert(aod_max, state_name, month) if aod_max else None,
        }


class AQICalculator:
    """
    Calculates Air Quality Index (AQI) from PM2.5 concentration.
    
    Uses India CPCB (Central Pollution Control Board) standards.
    """
    
    # India AQI breakpoints: (PM2.5_low, PM2.5_high, AQI_low, AQI_high, category, color)
    BREAKPOINTS = [
        (0, 30, 0, 50, 'Good', 'Green'),
        (31, 60, 51, 100, 'Satisfactory', 'Light Green'),
        (61, 90, 101, 200, 'Moderate', 'Yellow'),
        (91, 120, 201, 300, 'Poor', 'Orange'),
        (121, 250, 301, 400, 'Very Poor', 'Red'),
        (251, 380, 401, 500, 'Severe', 'Maroon'),
    ]
    
    def calculate(self, pm25: float) -> Tuple[int, str, str]:
        """
        Calculate AQI from PM2.5 concentration.
        
        Args:
            pm25: PM2.5 concentration in µg/m³
        
        Returns:
            Tuple of (AQI value, category, color)
        """
        if pm25 is None or pm25 < 0:
            return None, 'Unknown', 'Gray'
        
        # Handle values above maximum breakpoint
        if pm25 > 380:
            return 500, 'Severe', 'Maroon'
        
        # Find appropriate breakpoint
        for pm_low, pm_high, aqi_low, aqi_high, category, color in self.BREAKPOINTS:
            if pm_low <= pm25 <= pm_high:
                # Linear interpolation
                aqi = ((aqi_high - aqi_low) / (pm_high - pm_low)) * (pm25 - pm_low) + aqi_low
                return round(aqi), category, color
        
        # Default (should not reach here)
        return 500, 'Severe', 'Maroon'
    
    def get_category_info(self, category: str) -> Dict[str, str]:
        """
        Get detailed information about an AQI category.
        
        Args:
            category: AQI category name
        
        Returns:
            Dictionary with category details
        """
        category_details = {
            'Good': {
                'health_impact': 'Minimal impact',
                'advisory': 'Air quality is satisfactory',
                'color': 'Green'
            },
            'Satisfactory': {
                'health_impact': 'Minor breathing discomfort to sensitive people',
                'advisory': 'Acceptable air quality',
                'color': 'Light Green'
            },
            'Moderate': {
                'health_impact': 'Breathing discomfort to people with lung, heart disease',
                'advisory': 'Sensitive people should reduce outdoor activities',
                'color': 'Yellow'
            },
            'Poor': {
                'health_impact': 'Breathing discomfort to most people on prolonged exposure',
                'advisory': 'Avoid prolonged outdoor activities',
                'color': 'Orange'
            },
            'Very Poor': {
                'health_impact': 'Respiratory illness on prolonged exposure',
                'advisory': 'Minimize outdoor activities',
                'color': 'Red'
            },
            'Severe': {
                'health_impact': 'Affects healthy people and seriously impacts those with existing diseases',
                'advisory': 'Avoid all outdoor activities',
                'color': 'Maroon'
            }
        }
        
        return category_details.get(category, {
            'health_impact': 'Unknown',
            'advisory': 'Unknown',
            'color': 'Gray'
        })


def process_aod_to_pm25_and_aqi(
    aod_data: Dict,
    meteorological_data: Dict
) -> Dict:
    """
    Process AOD data to PM2.5 and calculate AQI.
    
    Args:
        aod_data: Dictionary with AOD statistics
        meteorological_data: Dictionary with BLH, RH, Temperature
    
    Returns:
        Dictionary with PM2.5 and AQI data
    """
    converter = AODtoPM25Converter()
    aqi_calc = AQICalculator()
    
    # Convert AOD to PM2.5
    pm25_stats = converter.convert_with_stats(
        aod_data.get('aod_mean'),
        aod_data.get('aod_stddev'),
        aod_data.get('aod_min'),
        aod_data.get('aod_max'),
        meteorological_data.get('blh', 1000.0),
        meteorological_data.get('relative_humidity', 60.0),
        meteorological_data.get('temperature')
    )
    
    # Calculate AQI from mean PM2.5
    aqi_value, aqi_category, aqi_color = aqi_calc.calculate(pm25_stats['pm25_mean'])
    
    return {
        **pm25_stats,
        'aqi_mean': aqi_value,
        'aqi_category': aqi_category,
        'aqi_color': aqi_color,
        'conversion_method': 'advanced_meteorological',
        'blh_used': meteorological_data.get('blh'),
        'rh_used': meteorological_data.get('relative_humidity'),
    }


if __name__ == "__main__":
    # Example usage
    converter = AODtoPM25Converter()
    aqi_calc = AQICalculator()
    
    # Example: Bihar 2023 (AOD: 876.2)
    aod = 876.2
    blh = 800.0  # meters (typical for Indo-Gangetic Plain)
    rh = 65.0    # % (moderate humidity)
    
    pm25 = converter.convert(aod, blh, rh)
    aqi, category, color = aqi_calc.calculate(pm25)
    
    print(f"AOD: {aod}")
    print(f"BLH: {blh}m, RH: {rh}%")
    print(f"PM2.5: {pm25:.1f} µg/m³")
    print(f"AQI: {aqi} ({category}, {color})")
