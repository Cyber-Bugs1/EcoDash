"""
Enhanced Environmental Prediction Tool with Reinforced Learning

Features:
- Reinforced Learning AI for PM2.5 prediction
- Automatic weather & fire data retrieval
- Uncertainty analysis and confidence intervals
- Seasonal variation patterns
"""

import sys
import sqlite3
import math
import pickle
import numpy as np
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))  # For RL model pickles

from ai.spike_predictor import PollutionSpikePredictor

# Import RL model classes (needed for unpickling)
try:
    from train_reinforced_model import (
        EnsembleModel, ReplayBuffer, TemporalDifferencePredictor,
        RewardCalculator, Experience, ReinforcedEnvironmentalAI
    )
except ImportError:
    pass


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

    def _get_fallback_weather(self, month):
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


def load_reinforced_model(models_dir):
    """Load the reinforced learning model."""
    model_path = Path(models_dir) / "reinforced_model.pkl"
    if model_path.exists():
        with open(model_path, 'rb') as f:
            return pickle.load(f)
    return None


def get_available_states(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    states = set()
    try:
        cursor.execute("SELECT DISTINCT state_name FROM MonthlyPollution")
        for row in cursor.fetchall():
            if row[0]: states.add(row[0])
    except:
        pass
    conn.close()
    return sorted(list(states))


def calculate_trend_with_confidence(values):
    """Calculate trend with confidence interval."""
    if len(values) < 2:
        return {'slope': 0, 'direction': "Stable", 'confidence': "Low", 'r_squared': 0}
    
    n = len(values)
    x_mean = (n - 1) / 2
    y_mean = sum(values) / n
    
    numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    
    if denominator == 0:
        return {'slope': 0, 'direction': "Stable", 'confidence': "Low", 'r_squared': 0}
    
    slope = numerator / denominator
    
    # Calculate R-squared for confidence
    y_pred = [slope * i + (y_mean - slope * x_mean) for i in range(n)]
    ss_res = sum((v - p) ** 2 for v, p in zip(values, y_pred))
    ss_tot = sum((v - y_mean) ** 2 for v in values)
    
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    
    # Determine confidence based on R-squared
    if r_squared > 0.8: confidence = "High"
    elif r_squared > 0.5: confidence = "Moderate"
    else: confidence = "Low"
    
    # Determine trend direction
    if abs(slope) < 0.01 * abs(y_mean): direction = "Stable"
    elif slope > 0: direction = "Increasing"
    else: direction = "Decreasing"
    
    return {
        'slope': slope,
        'direction': direction,
        'confidence': confidence,
        'r_squared': r_squared
    }


def predict_with_uncertainty(values, years_ahead):
    """Predict future value with uncertainty range."""
    if not values: return None
    
    mean = sum(values) / len(values)
    std = math.sqrt(sum((x - mean) ** 2 for x in values) / len(values)) if len(values) > 1 else 0
    
    trend = calculate_trend_with_confidence(values)
    predicted = values[-1] + (trend['slope'] * years_ahead)
    
    uncertainty = std * (1 + 0.2 * years_ahead)
    if trend['confidence'] == "Low": uncertainty *= 1.5
    
    return {
        'predicted': max(0, predicted),
        'low': max(0, predicted - 1.96 * uncertainty),
        'high': max(0, predicted + 1.96 * uncertainty),
        'uncertainty': uncertainty,
        'confidence': trend['confidence'],
        'variability': std / mean * 100 if mean > 0 else 0
    }


def main():
    db_path = str(Path(__file__).parent.parent / "processed_data.db")
    models_dir = str(Path(__file__).parent.parent / "models")
    
    print("=" * 76)
    print("🌍 AI Environmental Prediction System")
    print("   Powered by Reinforced Learning Model")
    print("=" * 76)
    
    # Initialize Data Provider
    provider = EnvironmentalDataProvider(db_path)
    
    # Load RL Model
    print("Loading AI Model...", end=" ")
    rl_model_data = load_reinforced_model(models_dir)
    if rl_model_data:
        ensemble = rl_model_data.get('ensemble')
        print("Done.")
    else:
        print("\nUsing Basic Statistical Model (RL Model not found)")
        ensemble = None
    
    # Get State
    state_input = input("\nEnter State/City: ").strip()
    
    # Find closest match
    states = get_available_states(db_path)
    state = state_input
    matches = [s for s in states if state_input.lower() in s.lower()]
    if matches:
        state = matches[0]
        if state != state_input:
            print(f"Using location: {state}")
            
    # Get Date
    try:
        month = int(input("Enter Month (1-12): ").strip())
        year = int(input("Enter Year (e.g., 2025): ").strip())
    except ValueError:
        print("Invalid date input.")
        return

    # Auto-fetch data
    weather = provider.get_weather_forecast(state, month)
    fire = provider.get_fire_activity(state, month)
    
    # Determine Season
    if month in [12, 1, 2]: season, w, m, s = "Winter", 1, 0, 0
    elif month in [3, 4, 5]: season, w, m, s = "Summer", 0, 0, 1
    elif month in [6, 7, 8, 9]: season, w, m, s = "Monsoon", 0, 1, 0
    else: season, w, m, s = "Post-Monsoon", 0, 0, 0
    
    print("\n" + "=" * 76)
    print(f"🔮 PREDICTION REPORT: {state.upper()}")
    print(f"   {season} {year} (Month {month})")
    print("=" * 76)
    
    # Display Auto-Retrieved Data
    print("\n🌤️  ENVIRONMENTAL CONDITIONS (AI Retrieved)")
    print(f"   Temperature:   {weather['temp']:.1f}°C")
    print(f"   Humidity:      {weather['humidity']:.1f}%")
    print(f"   Precipitation: {weather['precipitation']:.1f} mm")
    print(f"   Fire Activity: {fire['count']} fires (Intensity: {fire['frp']:.1f})")
    print(f"   Data Source:   {weather['source']}")

    # Prediction Logic
    print("\n📊 AIR QUALITY FORECAST")
    print("-" * 76)
    
    if ensemble:
        # Prepare features for RL model
        features = [
            weather['temp'], weather['humidity'], weather['precipitation'],
            fire['count'], fire['frp'], year, month, w, m, s
        ]
        X = np.array([features])
        
        # Predict
        pm25, unc = ensemble.predict_with_uncertainty(X)
        pm25 = pm25[0]
        unc = unc[0]
        
        # Limits
        pm25_low = max(0, pm25 - unc)
        pm25_high = pm25 + unc
        
        # AQI Conversion
        def get_aqi(pm):
            if pm < 30: return pm * 50/30
            elif pm < 60: return 50 + (pm-30)*50/30
            elif pm < 90: return 100 + (pm-60)*100/30
            elif pm < 120: return 200 + (pm-90)*100/30
            else: return 300 + (pm-120)*100/130
        
        aqi = get_aqi(pm25)
        
        # Category
        if aqi <= 50: cat, color = "Good", "Green"
        elif aqi <= 100: cat, color = "Satisfactory", "Yellow"
        elif aqi <= 200: cat, color = "Moderate", "Orange"
        elif aqi <= 300: cat, color = "Poor", "Red"
        elif aqi <= 400: cat, color = "Very Poor", "Purple"
        else: cat, color = "Severe", "Maroon"
        
        print(f"   PM2.5 Level:   {pm25:.1f} μg/m³ (±{unc:.1f})")
        print(f"   AQI Estimate:  {int(aqi)}")
        print(f"   Category:      {cat} ({color})")
        
        # Confidence
        if unc < 10: conf = "High"
        elif unc < 20: conf = "Moderate"
        else: conf = "Low"
        print(f"   Confidence:    {conf}")
        
    else:
        print("   AI Model unavailable. Cannot generate prediction.")

    # Recommendations
    print("\n📌 AI RECOMMENDATIONS")
    if pm25 > 60:
        print("   ⚠️  High pollution levels predicted.")
        print("   • Avoid prolonged outdoor activities.")
        print("   • Use air purifiers indoors.")
        if fire['count'] > 10:
            print("   • Fire activity contributing to smog - wear N95 masks.")
    elif pm25 > 30:
        print("   ⚠️  Moderate air quality.")
        print("   • Sensitive groups should limit exposure.")
    else:
        print("   ✅  Air quality is expected to be good.")
        print("   • Enjoy outdoor activities!")
        
    print("\n" + "=" * 76)

if __name__ == "__main__":
    main()
