"""
Interactive Test for All Environmental AI Models

Asks user for location and time, then automatically fetches environmental data
and provides predictions for:
1. PM2.5 Air Quality
2. Vegetation Health (NDVI)
3. Crop Yield (EVI)
4. Water Level (Surface Water)
"""

import sys
import pickle
import sqlite3
from pathlib import Path
from datetime import datetime

# Add paths so pickle can find all modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

# Import classes needed for unpickling the reinforced model
try:
    from train_reinforced_model import (
        EnsembleModel, ReplayBuffer, TemporalDifferencePredictor,
        RewardCalculator, Experience, ReinforcedEnvironmentalAI
    )
except ImportError:
    pass

import numpy as np

# Import Environmental AI System for new models
try:
    from src.ai.environmental_ai import EnvironmentalAISystem
    ENVIRONMENTAL_AI_AVAILABLE = True
except ImportError:
    ENVIRONMENTAL_AI_AVAILABLE = False


class EnvironmentalDataProvider:
    """Provides environmental data from database."""
    
    def __init__(self, db_path):
        self.db_path = db_path
    
    def get_weather_forecast(self, state, month):
        """Get typical weather conditions for state and month."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Try to get average from historical data
        cursor.execute("""
            SELECT AVG(temp_mean), AVG(humidity_mean), AVG(total_precipitation_mm)
            FROM MonthlyWeather
            WHERE state_name LIKE ? AND month = ?
        """, (f"%{state}%", month))
        
        row = cursor.fetchone()
        conn.close()
        
        if row and row[0] is not None:
            return {
                'temp': row[0],
                'humidity': row[1],
                'precipitation': row[2],
                'source': 'Historical Database'
            }
        
        # Fallback values if no data found
        return self._get_fallback_weather(month)
    
    def get_fire_activity(self, state, month):
        """Get typical fire activity."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT AVG(fire_count), AVG(avg_frp)
            FROM MonthlyFires
            WHERE state_name LIKE ? AND month = ?
        """, (f"%{state}%", month))
        
        row = cursor.fetchone()
        conn.close()
        
        if row and row[0] is not None:
            return {
                'count': int(row[0]),
                'frp': row[1],
                'source': 'Historical Database'
            }
        
        return {'count': 0, 'frp': 0, 'source': 'Default/No Data'}
    
    def get_environmental_data(self, state, year=2023):
        """Get comprehensive environmental data for a state."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                v.ndvi_mean,
                w.rainfall_annual_mm,
                w.dry_months_count,
                w.surface_water_mean,
                c.cropland_percent,
                c.kharif_ndvi,
                c.rabi_ndvi,
                c.evi_mean
            FROM Vegetation v
            LEFT JOIN Water w ON v.state_name = w.state_name AND v.year = w.year
            LEFT JOIN Crop c ON v.state_name = c.state_name AND v.year = c.year
            WHERE v.state_name LIKE ? AND v.year = ?
        """, (f"%{state}%", year))
        
        row = cursor.fetchone()
        conn.close()
        
        if row and row[0] is not None:
            return {
                'ndvi_mean': row[0],
                'rainfall_annual_mm': row[1] or 1000,
                'dry_months_count': row[2] or 6,
                'surface_water_mean': row[3] or 50,
                'cropland_percent': row[4] or 50,
                'kharif_ndvi': row[5] or 0.5,
                'rabi_ndvi': row[6] or 0.5,
                'evi_mean': row[7] or 0.3,
                'source': 'Historical Database'
            }
        
        # Fallback values
        return {
            'ndvi_mean': 0.5,
            'rainfall_annual_mm': 1000,
            'dry_months_count': 6,
            'surface_water_mean': 50,
            'cropland_percent': 50,
            'kharif_ndvi': 0.5,
            'rabi_ndvi': 0.5,
            'evi_mean': 0.3,
            'source': 'Default (No Data)'
        }

    def _get_fallback_weather(self, month):
        """Fallback weather if database empty."""
        season = self._get_season(month)
        if season == "Winter":
            return {'temp': 15, 'humidity': 60, 'precipitation': 10, 'source': 'Season (Fallback)'}
        elif season == "Summer":
            return {'temp': 35, 'humidity': 40, 'precipitation': 20, 'source': 'Season (Fallback)'}
        elif season == "Monsoon":
            return {'temp': 28, 'humidity': 85, 'precipitation': 300, 'source': 'Season (Fallback)'}
        else:
            return {'temp': 25, 'humidity': 50, 'precipitation': 5, 'source': 'Season (Fallback)'}

    def _get_season(self, month):
        if month in [12, 1, 2]: return "Winter"
        elif month in [3, 4, 5]: return "Summer"
        elif month in [6, 7, 8, 9]: return "Monsoon"
        else: return "Post-Monsoon"


def load_model(model_path):
    """Load a trained model from pickle file."""
    with open(model_path, 'rb') as f:
        return pickle.load(f)


def get_user_input(data_provider):
    """Get inputs and fetch automatic data."""
    print("\n" + "-" * 60)
    print("Enter Prediction Details:")
    print("-" * 60)
    
    # Location
    city = input("  City/Region (e.g., Delhi, Mumbai): ").strip()
    state = input("  State (e.g., Delhi, Maharashtra): ").strip()
    
    # Date
    while True:
        try:
            month = int(input("  Month (1-12): ").strip())
            if 1 <= month <= 12: break
        except ValueError: pass
    
    year_input = input("  Year (default 2023): ").strip()
    year = int(year_input) if year_input else 2023
    
    # Automatic Data Retrieval
    print("\n  Auto-fetching environmental data...")
    
    weather = data_provider.get_weather_forecast(state, month)
    fire = data_provider.get_fire_activity(state, month)
    env_data = data_provider.get_environmental_data(state, year)
    
    # Season logic
    if month in [12, 1, 2]:
        season = "Winter"
        winter, monsoon, summer = 1, 0, 0
    elif month in [3, 4, 5]:
        season = "Summer"
        winter, monsoon, summer = 0, 0, 1
    elif month in [6, 7, 8, 9]:
        season = "Monsoon"
        winter, monsoon, summer = 0, 1, 0
    else:
        season = "Post-Monsoon"
        winter, monsoon, summer = 0, 0, 0
        
    return {
        'city': city,
        'state': state,
        'month': month,
        'year': year,
        'season': season,
        'temp': weather['temp'],
        'humidity': weather['humidity'],
        'precipitation': weather['precipitation'],
        'weather_source': weather['source'],
        'fire_count': fire['count'],
        'fire_frp': fire['frp'],
        'fire_source': fire['source'],
        'winter': winter,
        'monsoon': monsoon,
        'summer': summer,
        # Environmental data
        'ndvi_mean': env_data['ndvi_mean'],
        'rainfall_annual_mm': env_data['rainfall_annual_mm'],
        'dry_months_count': env_data['dry_months_count'],
        'surface_water_mean': env_data['surface_water_mean'],
        'cropland_percent': env_data['cropland_percent'],
        'kharif_ndvi': env_data['kharif_ndvi'],
        'rabi_ndvi': env_data['rabi_ndvi'],
        'evi_mean': env_data['evi_mean'],
        'env_source': env_data['source']
    }


def predict_pm25_with_model(ensemble, inputs):
    """Make PM2.5 prediction using reinforced model."""
    features = [
        inputs['temp'],
        inputs['humidity'],
        inputs['precipitation'],
        inputs['fire_count'],
        inputs['fire_frp'],
        inputs['year'],
        inputs['month'],
        inputs['winter'],
        inputs['monsoon'],
        inputs['summer']
    ]
    
    X = np.array([features])
    pred, uncertainty = ensemble.predict_with_uncertainty(X)
    return pred[0], uncertainty[0]


def display_all_predictions(inputs, pm25_result, veg_result, crop_result, water_result):
    """Display all prediction results."""
    
    print("\n" + "=" * 70)
    print("🌍 COMPREHENSIVE ENVIRONMENTAL PREDICTION RESULTS")
    print("=" * 70)
    
    print(f"\n📍 Location: {inputs['city']}, {inputs['state']}")
    print(f"📅 Date: {inputs['season']} {inputs['year']} (Month {inputs['month']})")
    
    print("\n" + "-" * 70)
    print("🌦️  INPUT DATA (Auto-Retrieved)")
    print("-" * 70)
    print(f"  Temperature:    {inputs['temp']:.1f}°C")
    print(f"  Humidity:       {inputs['humidity']:.1f}%")
    print(f"  Rainfall:       {inputs['rainfall_annual_mm']:.0f} mm/year")
    print(f"  Dry Months:     {inputs['dry_months_count']}")
    print(f"  Cropland:       {inputs['cropland_percent']:.1f}%")
    print(f"  Data Source:    {inputs['env_source']}")
    
    print("\n" + "=" * 70)
    print("📊 PREDICTION RESULTS")
    print("=" * 70)
    
    # PM2.5 Result
    if pm25_result:
        pm25, uncertainty = pm25_result
        if pm25 < 30: cat, color = "Good", "🟢"
        elif pm25 < 60: cat, color = "Moderate", "🟡"
        elif pm25 < 90: cat, color = "Poor", "🟠"
        elif pm25 < 120: cat, color = "Very Poor", "🔴"
        else: cat, color = "Severe", "🟤"
        
        print(f"\n💨 PM2.5 AIR QUALITY")
        print(f"   Predicted:    {pm25:.1f} μg/m³")
        print(f"   Uncertainty:  ±{uncertainty:.1f}")
        print(f"   Category:     {color} {cat}")
    
    # Vegetation Result
    if veg_result:
        print(f"\n🌿 VEGETATION HEALTH (NDVI)")
        print(f"   Predicted:    {veg_result['predicted_ndvi']:.4f}")
        print(f"   Category:     {veg_result['vegetation_category']}")
        print(f"   Advice:       {veg_result['recommendations'][0]}")
    
    # Crop Yield Result
    if crop_result:
        print(f"\n🌾 CROP YIELD (EVI)")
        print(f"   Predicted:    {crop_result['predicted_evi']:.4f}")
        print(f"   Category:     {crop_result['yield_category']}")
        print(f"   Advice:       {crop_result['recommendations'][0]}")
    
    # Water Level Result  
    if water_result:
        print(f"\n💧 WATER LEVEL")
        print(f"   Predicted:    {water_result['predicted_surface_water']:.2f}%")
        print(f"   Category:     {water_result['water_stress_category']}")
        print(f"   Advice:       {water_result['recommendations'][0]}")
    
    print("\n" + "=" * 70)


def show_menu():
    """Show prediction options menu."""
    print("\n" + "-" * 40)
    print("Select Prediction Type:")
    print("-" * 40)
    print("  1. All Predictions (Full Analysis)")
    print("  2. PM2.5 Air Quality Only")
    print("  3. Vegetation Health Only")
    print("  4. Crop Yield Only")
    print("  5. Water Level Only")
    print("  0. Exit")
    print("-" * 40)
    
    while True:
        try:
            choice = int(input("  Your choice: ").strip())
            if 0 <= choice <= 5:
                return choice
        except ValueError:
            pass
        print("  Invalid choice. Try again.")


def main():
    models_dir = Path(__file__).parent.parent / "models"
    db_path = Path(__file__).parent.parent / "processed_data.db"
    
    print("=" * 70)
    print("🤖 AI ENVIRONMENTAL PREDICTOR")
    print("   Comprehensive Environmental Analysis System")
    print("=" * 70)
    
    # Load reinforced model for PM2.5
    reinforced_path = models_dir / "reinforced_model.pkl"
    ensemble = None
    if reinforced_path.exists():
        print("\n  Loading PM2.5 model...", end=" ")
        try:
            model_data = load_model(reinforced_path)
            ensemble = model_data.get('ensemble')
            print("✓")
        except Exception as e:
            print(f"✗ ({e})")
    else:
        print("\n  PM2.5 reinforced model not found (using basic model)")
    
    # Load Environmental AI System for new models
    env_ai = None
    if ENVIRONMENTAL_AI_AVAILABLE:
        print("  Loading Environmental AI models...", end=" ")
        try:
            env_ai = EnvironmentalAISystem()
            env_ai.train_all_models()
            print("✓")
        except Exception as e:
            print(f"✗ ({e})")
    else:
        print("  Environmental AI not available")
    
    # Initialize data provider
    provider = EnvironmentalDataProvider(db_path)
    
    while True:
        choice = show_menu()
        
        if choice == 0:
            print("\nGoodbye! 👋")
            break
        
        # Get user input
        inputs = get_user_input(provider)
        
        # Initialize results
        pm25_result = None
        veg_result = None
        crop_result = None
        water_result = None
        
        # Make predictions based on choice
        if choice in [1, 2] and ensemble:
            pm25, unc = predict_pm25_with_model(ensemble, inputs)
            pm25_result = (pm25, unc)
        
        if choice in [1, 3] and env_ai:
            veg_result = env_ai.predict_vegetation(
                rainfall=inputs['rainfall_annual_mm'],
                temp=inputs['temp'],
                dry_months=inputs['dry_months_count'],
                evi=inputs['evi_mean']
            )
        
        if choice in [1, 4] and env_ai:
            crop_result = env_ai.predict_crop_yield(
                ndvi=inputs['ndvi_mean'],
                rainfall=inputs['rainfall_annual_mm'],
                cropland=inputs['cropland_percent'],
                kharif_ndvi=inputs['kharif_ndvi'],
                rabi_ndvi=inputs['rabi_ndvi']
            )
        
        if choice in [1, 5] and env_ai:
            water_result = env_ai.predict_water_level(
                rainfall=inputs['rainfall_annual_mm'],
                ndvi=inputs['ndvi_mean'],
                temp=inputs['temp'],
                humidity=inputs['humidity'],
                dry_months=inputs['dry_months_count']
            )
        
        # Display results
        display_all_predictions(inputs, pm25_result, veg_result, crop_result, water_result)
        
        if input("\nPredict again? (y/n): ").lower() != 'y':
            break


if __name__ == "__main__":
    main()
