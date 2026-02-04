"""
Regional Model Training and Testing

Trains separate models for:
- North India (higher pollution, more extreme weather)
- South India (coastal ventilation, lower pollution)

Incorporates fire data from NASA FIRMS for improved predictions.
Tests on cities from both regions.
"""

import sys
import sqlite3
import pickle
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import numpy as np
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_squared_error, r2_score
except ImportError:
    print("[ERROR] Install sklearn: uv add scikit-learn numpy")
    sys.exit(1)

try:
    from xgboost import XGBRegressor
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

# Regional Classification
NORTH_INDIA_STATES = [
    'Delhi', 'Uttar Pradesh', 'Bihar', 'Haryana', 'Punjab', 'Rajasthan',
    'Jharkhand', 'Madhya Pradesh', 'Gujarat', 'Chhattisgarh', 'Uttarakhand',
    'Himachal Pradesh', 'West Bengal', 'Assam'
]

SOUTH_INDIA_STATES = [
    'Maharashtra', 'Tamil Nadu', 'Karnataka', 'Kerala', 'Andhra Pradesh', 'Odisha'
]

# Test cities for each region
NORTH_TEST_CITIES = {
    'Delhi': {'state': 'Delhi', 'description': 'Capital - High Pollution'},
    'Lucknow': {'state': 'Uttar Pradesh', 'description': 'UP Capital'},
    'Jaipur': {'state': 'Rajasthan', 'description': 'Desert Region'},
    'Chandigarh': {'state': 'Punjab', 'description': 'Clean City'},
    'Patna': {'state': 'Bihar', 'description': 'Indo-Gangetic Plain'},
}

SOUTH_TEST_CITIES = {
    'Mumbai': {'state': 'Maharashtra', 'description': 'Coastal Metro'},
    'Chennai': {'state': 'Tamil Nadu', 'description': 'Coastal City'},
    'Bangalore': {'state': 'Karnataka', 'description': 'Tech Hub'},
    'Kochi': {'state': 'Kerala', 'description': 'Cleanest Region'},
    'Hyderabad': {'state': 'Andhra Pradesh', 'description': 'Deccan Plateau'},
}


class RegionalEnvironmentalModel:
    """
    Region-specific model with fire data integration.
    """
    
    def __init__(self, db_path: str, region: str):
        self.db_path = db_path
        self.region = region
        self.models = {}
        self.scalers = {}
        self.feature_names = []
        self.training_stats = {}
    
    def load_regional_data(self) -> tuple:
        """Load data for specific region with fire data."""
        conn = sqlite3.connect(self.db_path)
        
        # Get environmental data with fire counts
        query = """
            SELECT 
                e.state_name, e.year, e.week, e.region,
                e.pm25, e.pm10, e.aqi,
                e.rainfall_mm, e.groundwater_level, e.water_stress_index,
                e.ndvi, e.evi, e.forest_health_index,
                e.crop_growth_index, e.cropland_pct,
                e.temperature_mean, e.humidity_mean, e.wind_speed,
                COALESCE(f.fire_count, 0) as fire_count,
                COALESCE(f.avg_frp, 0) as avg_frp
            FROM WeeklyEnvironmentalData e
            LEFT JOIN (
                SELECT state_name, COUNT(*) as fire_count, AVG(frp) as avg_frp
                FROM SatelliteFireData
                GROUP BY state_name
            ) f ON e.state_name = f.state_name
            WHERE e.region = ?
        """
        
        cursor = conn.cursor()
        cursor.execute(query, (self.region,))
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            raise ValueError(f"No data found for region: {self.region}")
        
        return rows
    
    def train(self, target: str = 'pm25'):
        """Train regional model."""
        print(f"\n{'='*60}")
        print(f"Training {self.region} Model")
        print(f"{'='*60}")
        
        rows = self.load_regional_data()
        print(f"Loaded {len(rows)} records for {self.region}")
        
        # Feature extraction
        self.feature_names = [
            'rainfall_mm', 'groundwater_level', 'water_stress_index',
            'ndvi', 'evi', 'forest_health_index',
            'crop_growth_index', 'cropland_pct',
            'temperature_mean', 'humidity_mean', 'wind_speed',
            'fire_count', 'avg_frp', 'week'
        ]
        
        # Target index based on column order in query
        target_indices = {'pm25': 4, 'pm10': 5, 'aqi': 6}
        target_idx = target_indices.get(target, 4)
        
        X = []
        y = []
        
        for row in rows:
            features = [
                row[7],   # rainfall_mm
                row[8],   # groundwater_level
                row[9],   # water_stress_index
                row[10],  # ndvi
                row[11],  # evi
                row[12],  # forest_health_index
                row[13],  # crop_growth_index
                row[14],  # cropland_pct
                row[15],  # temperature_mean
                row[16],  # humidity_mean
                row[17],  # wind_speed
                row[18],  # fire_count
                row[19],  # avg_frp
                row[2],   # week
            ]
            X.append(features)
            y.append(row[target_idx])
        
        X = np.array(X)
        y = np.array(y)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train models
        models = {
            'RandomForest': RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42),
            'GradientBoost': GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42),
        }
        
        if XGBOOST_AVAILABLE:
            models['XGBoost'] = XGBRegressor(
                n_estimators=150, max_depth=8, learning_rate=0.1, 
                random_state=42, verbosity=0
            )
        
        best_r2 = -float('inf')
        best_model_name = None
        
        print(f"\nTraining for target: {target}")
        print(f"Training samples: {len(X_train)}, Test samples: {len(X_test)}")
        print("-" * 40)
        
        for name, model in models.items():
            model.fit(X_train_scaled, y_train)
            y_pred = model.predict(X_test_scaled)
            
            r2 = r2_score(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            
            print(f"  {name:<15} R²: {r2:.4f}  RMSE: {rmse:.2f}")
            
            if r2 > best_r2:
                best_r2 = r2
                best_model_name = name
        
        # Store best model
        self.models[target] = models[best_model_name]
        self.scalers[target] = scaler
        
        self.training_stats[target] = {
            'best_model': best_model_name,
            'r2': best_r2,
            'samples': len(X)
        }
        
        print(f"\n✓ Best model: {best_model_name} (R²: {best_r2:.4f})")
        
        # Feature importance
        if hasattr(models[best_model_name], 'feature_importances_'):
            importance = dict(zip(self.feature_names, models[best_model_name].feature_importances_))
            print("\nTop 5 Features:")
            for feat, imp in sorted(importance.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {feat}: {imp:.1%}")
        
        return best_r2
    
    def predict(self, features: dict) -> float:
        """Make prediction for PM2.5."""
        if 'pm25' not in self.models:
            self.train('pm25')
        
        feature_vector = [features.get(f, 0) for f in self.feature_names]
        X = np.array([feature_vector])
        X_scaled = self.scalers['pm25'].transform(X)
        
        return self.models['pm25'].predict(X_scaled)[0]
    
    def save(self, path: str):
        """Save model."""
        data = {
            'region': self.region,
            'models': self.models,
            'scalers': self.scalers,
            'feature_names': self.feature_names,
            'training_stats': self.training_stats,
        }
        with open(path, 'wb') as f:
            pickle.dump(data, f)
        print(f"[OK] {self.region} model saved to {path}")


def test_regional_predictions(db_path: str, north_model: RegionalEnvironmentalModel, 
                               south_model: RegionalEnvironmentalModel):
    """Test predictions on cities from both regions."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n" + "=" * 70)
    print("Regional Prediction Testing")
    print("=" * 70)
    
    # Test North India cities
    print("\n--- NORTH INDIA CITIES ---")
    print(f"{'City':<15} {'State':<18} {'Predicted PM2.5':<18} {'Description'}")
    print("-" * 70)
    
    for city, info in NORTH_TEST_CITIES.items():
        state = info['state']
        
        # Get average features for the state
        cursor.execute("""
            SELECT AVG(rainfall_mm), AVG(groundwater_level), AVG(water_stress_index),
                   AVG(ndvi), AVG(evi), AVG(forest_health_index),
                   AVG(crop_growth_index), AVG(cropland_pct),
                   AVG(temperature_mean), AVG(humidity_mean), AVG(wind_speed)
            FROM WeeklyEnvironmentalData
            WHERE state_name = ?
        """, (state,))
        
        row = cursor.fetchone()
        if row and row[0]:
            # Get fire data
            cursor.execute("""
                SELECT COUNT(*), AVG(frp) FROM SatelliteFireData WHERE state_name = ?
            """, (state,))
            fire_row = cursor.fetchone()
            
            features = {
                'rainfall_mm': row[0], 'groundwater_level': row[1], 
                'water_stress_index': row[2], 'ndvi': row[3], 'evi': row[4],
                'forest_health_index': row[5], 'crop_growth_index': row[6],
                'cropland_pct': row[7], 'temperature_mean': row[8],
                'humidity_mean': row[9], 'wind_speed': row[10],
                'fire_count': fire_row[0] or 0, 'avg_frp': fire_row[1] or 0,
                'week': 46  # November (high pollution season)
            }
            
            pred = north_model.predict(features)
            print(f"{city:<15} {state:<18} {pred:<18.1f} {info['description']}")
    
    # Test South India cities
    print("\n--- SOUTH INDIA CITIES ---")
    print(f"{'City':<15} {'State':<18} {'Predicted PM2.5':<18} {'Description'}")
    print("-" * 70)
    
    for city, info in SOUTH_TEST_CITIES.items():
        state = info['state']
        
        cursor.execute("""
            SELECT AVG(rainfall_mm), AVG(groundwater_level), AVG(water_stress_index),
                   AVG(ndvi), AVG(evi), AVG(forest_health_index),
                   AVG(crop_growth_index), AVG(cropland_pct),
                   AVG(temperature_mean), AVG(humidity_mean), AVG(wind_speed)
            FROM WeeklyEnvironmentalData
            WHERE state_name = ?
        """, (state,))
        
        row = cursor.fetchone()
        if row and row[0]:
            cursor.execute("""
                SELECT COUNT(*), AVG(frp) FROM SatelliteFireData WHERE state_name = ?
            """, (state,))
            fire_row = cursor.fetchone()
            
            features = {
                'rainfall_mm': row[0], 'groundwater_level': row[1], 
                'water_stress_index': row[2], 'ndvi': row[3], 'evi': row[4],
                'forest_health_index': row[5], 'crop_growth_index': row[6],
                'cropland_pct': row[7], 'temperature_mean': row[8],
                'humidity_mean': row[9], 'wind_speed': row[10],
                'fire_count': fire_row[0] or 0, 'avg_frp': fire_row[1] or 0,
                'week': 46
            }
            
            pred = south_model.predict(features)
            print(f"{city:<15} {state:<18} {pred:<18.1f} {info['description']}")
    
    conn.close()


def main():
    db_path = str(Path(__file__).parent.parent / "processed_data.db")
    models_dir = Path(__file__).parent.parent / "models"
    models_dir.mkdir(exist_ok=True)
    
    print("=" * 70)
    print("Regional Environmental Model Training with Fire Data")
    print("=" * 70)
    print("\nIncorporating NASA FIRMS fire data for improved predictions")
    print("Training separate models for North India and South India")
    
    # Train North India model
    north_model = RegionalEnvironmentalModel(db_path, "North India")
    north_model.train('pm25')
    north_model.save(str(models_dir / "north_india_model.pkl"))
    
    # Train South India model
    south_model = RegionalEnvironmentalModel(db_path, "South India")
    south_model.train('pm25')
    south_model.save(str(models_dir / "south_india_model.pkl"))
    
    # Test on both regions
    test_regional_predictions(db_path, north_model, south_model)
    
    # Summary
    print("\n" + "=" * 70)
    print("Training Summary")
    print("=" * 70)
    print(f"\n{'Region':<15} {'Best Model':<15} {'R² Score':<12} {'Samples'}")
    print("-" * 50)
    print(f"{'North India':<15} {north_model.training_stats['pm25']['best_model']:<15} "
          f"{north_model.training_stats['pm25']['r2']:.4f}       "
          f"{north_model.training_stats['pm25']['samples']}")
    print(f"{'South India':<15} {south_model.training_stats['pm25']['best_model']:<15} "
          f"{south_model.training_stats['pm25']['r2']:.4f}       "
          f"{south_model.training_stats['pm25']['samples']}")
    
    print("\n" + "=" * 70)
    print("[OK] Regional training complete!")
    print("=" * 70)
    print("\nModels saved:")
    print(f"  - {models_dir / 'north_india_model.pkl'}")
    print(f"  - {models_dir / 'south_india_model.pkl'}")


if __name__ == "__main__":
    main()
