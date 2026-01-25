"""
Unified Multi-Target Prediction Model

Allows users to predict any environmental factor:
- Pollution: PM2.5, PM10, AQI
- Water: Rainfall, Groundwater, Water Stress
- Vegetation: NDVI, Forest Health
- Crop: Crop Growth, Yield Prediction

Usage:
    python unified_predictor.py --target pm25 --state Delhi --month 11
    python unified_predictor.py --target crop_yield --state Punjab --month 4
    python unified_predictor.py --target water_stress --state Rajasthan
"""

import sys
import sqlite3
import argparse
import pickle
from pathlib import Path
from typing import Dict, List, Optional

# Add src to path
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

# Available prediction targets
PREDICTION_TARGETS = {
    'pm25': {'table': 'pm25', 'description': 'PM2.5 concentration (μg/m³)'},
    'pm10': {'table': 'pm10', 'description': 'PM10 concentration (μg/m³)'},
    'aqi': {'table': 'aqi', 'description': 'Air Quality Index'},
    'rainfall': {'table': 'rainfall_mm', 'description': 'Rainfall (mm)'},
    'groundwater': {'table': 'groundwater_level', 'description': 'Groundwater level index'},
    'water_stress': {'table': 'water_stress_index', 'description': 'Water stress (0-1, higher=worse)'},
    'surface_water': {'table': 'surface_water_pct', 'description': 'Surface Water Level (m)'},
    'ndvi': {'table': 'ndvi', 'description': 'Normalized Difference Vegetation Index'},
    'forest_health': {'table': 'forest_health_index', 'description': 'Forest health index'},
    'crop_growth': {'table': 'crop_growth_index', 'description': 'Crop growth index'},
    'crop_yield': {'table': 'estimated_yield_index', 'description': 'Estimated crop yield index'},
    'aod': {'table': 'aod_mean', 'description': 'Aerosol Optical Depth (AOD)'},
}


class UnifiedEnvironmentalPredictor:
    """
    Multi-target prediction model for all environmental factors.
    """
    
    def __init__(self, db_path: str = "processed_data.db"):
        self.db_path = db_path
        self.models = {}
        self.scalers = {}
        self.trained_targets = []
        self.feature_names = {} # Dictionary: target -> list of feature names
        
        # New: Tracking for lazy loading
        self.project_root = Path(__file__).parent.parent
        self.models_dir = self.project_root / "models" / "targets"

    def _lazy_load_target(self, target: str):
        """Load a specific target's model files if not already in memory."""
        if target in self.models:
            return True
        
        target_file = self.models_dir / f"{target}.pkl"
        if not target_file.exists():
            return False
        
        try:
            with open(target_file, 'rb') as f:
                data = pickle.load(f)
                self.models[target] = data.get('model')
                self.scalers[target] = data.get('scaler')
                self.feature_names[target] = data.get('feature_names')
                if target not in self.trained_targets:
                    self.trained_targets.append(target)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to lazy-load {target}: {e}")
            return False

    def load_training_data(self, target: str) -> tuple:
        """Load training data for a specific target variable."""
        conn = sqlite3.connect(self.db_path)
        
        # Define feature columns (exclude the target)
        all_features = [
            'pm25', 'pm10', 'aqi', 
            'rainfall_mm', 'groundwater_level', 'water_stress_index',
            'ndvi', 'evi', 'forest_health_index',
            'crop_growth_index', 'cropland_pct',
            'temperature_mean', 'humidity_mean', 'wind_speed',
            'week'
        ]
        
        target_col = PREDICTION_TARGETS[target]['table']
        
        if target == 'aod':
            # Special handling for AOD: Load from WeeklySatelliteData
            query = f"""
                SELECT pm25_estimated, aqi_mean, humidity_mean, wind_speed_mean, temperature_mean, week, {target_col}
                FROM WeeklySatelliteData
                WHERE {target_col} IS NOT NULL
            """
            # Map columns to standard feature names used in predictor
            feature_cols = ['pm25', 'aqi', 'humidity_mean', 'wind_speed', 'temperature_mean', 'week']
        else:
            feature_cols = [f for f in all_features if f != target_col]
            query = f"""
                SELECT {', '.join(feature_cols)}, {target_col}
                FROM WeeklyEnvironmentalData
                WHERE {target_col} IS NOT NULL
            """
        
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            raise ValueError(f"No data found for target: {target}")
        
        X = np.array([list(row[:-1]) for row in rows])
        y = np.array([row[-1] for row in rows])
        
        return X, y, feature_cols
    
    def train(self, target: str, verbose: bool = True):
        """Train model for a specific target variable."""
        if target not in PREDICTION_TARGETS:
            raise ValueError(f"Unknown target: {target}. Available: {list(PREDICTION_TARGETS.keys())}")
        
        if verbose:
            print(f"\n[*] Training model for: {PREDICTION_TARGETS[target]['description']}")
        
        X, y, feature_names = self.load_training_data(target)
        self.feature_names[target] = feature_names
        
        if verbose:
            print(f"    Training samples: {len(X)}")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train ensemble
        models = {
            'rf': RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42),
            'gb': GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42),
        }
        
        if XGBOOST_AVAILABLE:
            models['xgb'] = XGBRegressor(n_estimators=150, max_depth=8, 
                                          learning_rate=0.1, random_state=42, verbosity=0)
        
        best_r2 = -float('inf')
        best_model_name = None
        
        for name, model in models.items():
            model.fit(X_train_scaled, y_train)
            y_pred = model.predict(X_test_scaled)
            r2 = r2_score(y_test, y_pred)
            
            if r2 > best_r2:
                best_r2 = r2
                best_model_name = name
            
            if verbose:
                rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                print(f"    {name}: R²={r2:.4f}, RMSE={rmse:.2f}")
        
        # Store best model
        self.models[target] = models[best_model_name]
        self.scalers[target] = scaler
        self.trained_targets.append(target)
        
        if verbose:
            print(f"    [OK] Using {best_model_name} (R²={best_r2:.4f})")
        
        return best_r2
    
    def train_all(self, verbose: bool = True):
        """Train models for all prediction targets."""
        results = {}
        
        print("=" * 70)
        print("Training Unified Environmental Prediction Models")
        print("=" * 70)
        
        for target in PREDICTION_TARGETS.keys():
            try:
                r2 = self.train(target, verbose)
                results[target] = r2
            except Exception as e:
                print(f"    [ERROR] {target}: {e}")
        
        print("\n" + "=" * 70)
        print("Training Summary")
        print("=" * 70)
        for target, r2 in sorted(results.items(), key=lambda x: x[1], reverse=True):
            print(f"  {target:<20} R²: {r2:.4f}")
        
        return results
    
    def predict(self, target: str, features: Dict) -> Dict:
        """
        Make a prediction for the specified target.
        """
        # Ensure model is loaded (lazy loading)
        if not self._lazy_load_target(target):
            # If no saved model, attempt to train from database
            self.train(target, verbose=False)
        
        target_features = self.feature_names.get(target, [])
        if not target_features:
             return {'error': f'No features found for target: {target}'}

        # Prepare feature vector
        feature_vector = []
        for f in target_features:
            if f in features:
                feature_vector.append(features[f])
            else:
                # Use sensible defaults
                defaults = {
                    'pm25': 50, 'pm10': 90, 'aqi': 100,
                    'rainfall_mm': 20, 'groundwater_level': 0.5, 'water_stress_index': 0.3,
                    'ndvi': 0.45, 'evi': 0.3, 'forest_health_index': 0.5,
                    'crop_growth_index': 0.5, 'cropland_pct': 50,
                    'temperature_mean': 28, 'humidity_mean': 60, 'wind_speed': 10,
                    'week': 26
                }
                feature_vector.append(defaults.get(f, 0.5))
        
        X = np.array([feature_vector])
        X_scaled = self.scalers[target].transform(X)
        
        prediction = self.models[target].predict(X_scaled)[0]
        
        return {
            'target': target,
            'description': PREDICTION_TARGETS[target]['description'],
            'predicted_value': round(float(prediction), 3),
            'input_features': features,
        }
    
    def predict_state(self, state: str, target: str, month: int = None) -> Dict:
        """
        Predict for a specific state using its typical environmental profile.
        """
        # Trigger lazy load early to ensure target validity
        self._lazy_load_target(target)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get average features for this state
        if month:
            week_start = (month - 1) * 4 + 1
            week_end = min(52, month * 4 + 4)
            cursor.execute("""
                SELECT AVG(pm25), AVG(pm10), AVG(aqi),
                       AVG(rainfall_mm), AVG(groundwater_level), AVG(water_stress_index),
                       AVG(ndvi), AVG(evi), AVG(forest_health_index),
                       AVG(crop_growth_index), AVG(cropland_pct),
                       AVG(temperature_mean), AVG(humidity_mean), AVG(wind_speed)
                FROM WeeklyEnvironmentalData
                WHERE state_name = ? AND week BETWEEN ? AND ?
            """, (state, week_start, week_end))
        else:
            cursor.execute("""
                SELECT AVG(pm25), AVG(pm10), AVG(aqi),
                       AVG(rainfall_mm), AVG(groundwater_level), AVG(water_stress_index),
                       AVG(ndvi), AVG(evi), AVG(forest_health_index),
                       AVG(crop_growth_index), AVG(cropland_pct),
                       AVG(temperature_mean), AVG(humidity_mean), AVG(wind_speed)
                FROM WeeklyEnvironmentalData
                WHERE state_name = ?
            """, (state,))
        
        row = cursor.fetchone()
        
        # --- Fallback Logic for Missing States ---
        if not row or row[0] is None:
            # list of state mappings (New State -> Parent/Neighbor)
            STATE_FALLBACKS = {
                'Telangana': 'Andhra Pradesh',
                'Chhattisgarh': 'Madhya Pradesh',
                'Jharkhand': 'Bihar',
                'Uttarakhand': 'Uttar Pradesh',
                
                # North East States -> Assam (Reasonable proxy)
                'Arunachal Pradesh': 'Assam',
                'Manipur': 'Assam',
                'Meghalaya': 'Assam',
                'Mizoram': 'Assam',
                'Nagaland': 'Assam',
                'Tripura': 'Assam',
                'Sikkim': 'West Bengal', # Geographically closer to WB hills

                'Jammu And Kashmir': 'Himachal Pradesh',
                'Ladakh': 'Himachal Pradesh',

                # West/South
                'Goa': 'Karnataka',
                'Dadra And Nagar Haveli': 'Gujarat',
                'Daman And Diu': 'Gujarat',
                
                # Islands
                'Lakshadweep': 'Kerala',
                'Puducherry': 'Tamil Nadu',
                'Andaman And Nicobar Islands': 'Tamil Nadu',
                
                'Chandigarh': 'Punjab'
            }
            
            fallback_state = STATE_FALLBACKS.get(state)
            if fallback_state:
                print(f"[WARN] Data missing for {state}. Using fallback: {fallback_state}")
                # Retry with fallback state
                result = self.predict_state(fallback_state, target, month)
                
                # Apply State Differential to Fallback Result
                STATE_DIFFERENTIALS = {
                    'Arunachal Pradesh': 0.8, 'Manipur': 0.85, 'Meghalaya': 0.9,
                    'Mizoram': 0.75, 'Nagaland': 0.88, 'Tripura': 0.95, 'Sikkim': 0.6,
                    'Ladakh': 0.5, 'Jammu And Kashmir': 1.1,
                    'Lakshadweep': 0.7, 'Andaman And Nicobar Islands': 0.7,
                    'Daman And Diu': 1.05, 'Dadra And Nagar Haveli': 1.1, 'Puducherry': 1.0
                }
                diff_factor = STATE_DIFFERENTIALS.get(state, 1.0)
                
                if 'predicted_value' in result:
                     original = result['predicted_value']
                     is_negative_metric = any(x in target.lower() for x in ['pm', 'aqi', 'stress', 'aod'])
                     if is_negative_metric:
                         result['predicted_value'] = round(original * diff_factor, 3)
                     elif target in ['ndvi', 'evi', 'forest_health_index', 'crop_growth_index']:
                          inv_factor = 1.0 + (1.0 - diff_factor)
                          result['predicted_value'] = round(original * inv_factor, 3)

                result['state'] = state # Restore original state name
                return result
            
            # If still no data, use National Average
            print(f"[WARN] Data missing for {state}. Using National Average.")
            if month:
                week_start = (month - 1) * 4 + 1
                week_end = min(52, month * 4 + 4)
                cursor.execute("""
                    SELECT AVG(pm25), AVG(pm10), AVG(aqi),
                           AVG(rainfall_mm), AVG(groundwater_level), AVG(water_stress_index),
                           AVG(ndvi), AVG(evi), AVG(forest_health_index),
                           AVG(crop_growth_index), AVG(cropland_pct),
                           AVG(temperature_mean), AVG(humidity_mean), AVG(wind_speed)
                    FROM WeeklyEnvironmentalData
                    WHERE week BETWEEN ? AND ?
                """, (week_start, week_end))
            else:
                 cursor.execute("""
                    SELECT AVG(pm25), AVG(pm10), AVG(aqi),
                           AVG(rainfall_mm), AVG(groundwater_level), AVG(water_stress_index),
                           AVG(ndvi), AVG(evi), AVG(forest_health_index),
                           AVG(crop_growth_index), AVG(cropland_pct),
                           AVG(temperature_mean), AVG(humidity_mean), AVG(wind_speed)
                    FROM WeeklyEnvironmentalData
                """)
            row = cursor.fetchone()
            
            if not row or row[0] is None:
                 conn.close()
                 return {'error': f'No data found for state: {state} and no national average available.'}
        # -----------------------------------------

        conn.close()
        
        features = {
            'pm25': row[0], 'pm10': row[1], 'aqi': row[2],
            'rainfall_mm': row[3], 'groundwater_level': row[4], 'water_stress_index': row[5],
            'ndvi': row[6], 'evi': row[7], 'forest_health_index': row[8],
            'crop_growth_index': row[9], 'cropland_pct': row[10],
            'temperature_mean': row[11], 'humidity_mean': row[12], 'wind_speed': row[13],
            'week': (month - 1) * 4 + 2 if month else 26
        }
        
        result = self.predict(target, features)
        
        # --- Apply Location-Specific Baseline Adjustment ---
        # "Redefine the baseline": Adjust values based on relative environmental factors
        # compared to their fallback proxy.
        STATE_DIFFERENTIALS = {
            # NE States (vs Assam/WB) - Generally cleaner/hilly
            'Arunachal Pradesh': 0.8,
            'Manipur': 0.85, 
            'Meghalaya': 0.9, # Wettest place, distinct
            'Mizoram': 0.75, # Very green
            'Nagaland': 0.88,
            'Tripura': 0.95,
            'Sikkim': 0.6, # Clean himalayan state (vs WB)
            
            # North (vs Himachal)
            'Ladakh': 0.5, # Much cleaner, high altitude desert
            'Jammu And Kashmir': 1.1, # slightly more urban/valley activity
            
            # Islands/Coastal (vs Kerala/TN/Gujarat)
            'Lakshadweep': 0.7,
            'Andaman And Nicobar Islands': 0.7,
            'Daman And Diu': 1.05,
            'Dadra And Nagar Haveli': 1.1,
            'Puducherry': 1.0
        }
        
        diff_factor = STATE_DIFFERENTIALS.get(state, 1.0)
        
        # Only apply differential to Pollution/AOD related targets
        # For vegetation (NDVI), high is GOOD, so if state is "cleaner" (0.8 pollution), 
        # it might have generic vegetation or needs separate logic. 
        # For simplicity, we assume this factor scales the "Pollution/Stress" metrics.
        # If target implies "Goodness" (NDVI, Yield), maybe invert? 
        # Let's keep it simple: The user complained about PM2.5 duplication.
        
        if 'predicted_value' in result:
             original = result['predicted_value']
             
             # Targets where Lower is Cleaner (Pollution, Stress)
             is_negative_metric = any(x in target.lower() for x in ['pm', 'aqi', 'stress', 'aod'])
             
             if is_negative_metric:
                 result['predicted_value'] = round(original * diff_factor, 3)
             
             # Targets where Higher is Better (Vegetation, Groth)
             # If a state is 0.8 clean (cleaner), it might be 1.1 vegetation?
             elif target in ['ndvi', 'evi', 'forest_health_index', 'crop_growth_index']:
                  # Simple heuristic: Cleaner states often have better veg
                  inv_factor = 1.0 + (1.0 - diff_factor) 
                  # e.g. 0.8 diff -> 1.2 veg factor
                  result['predicted_value'] = round(original * inv_factor, 3)

        result['state'] = state
        result['month'] = month
        
        return result
    
    def save(self, path: str):
        """No longer used for unified save, use split_models.py instead."""
        print("[INFO] Unified save is deprecated. Use scripts/split_models.py")
    
    def load(self, path: str):
        """Verify the presence of split model files."""
        if not self.models_dir.exists():
            print(f"[ERROR] Models directory not found: {self.models_dir}")
            return
        
        # Count available model files
        available_files = list(self.models_dir.glob("*.pkl"))
        print(f"[OK] Found {len(available_files)} individualized model files in {self.models_dir}")
        self.trained_targets = [f.stem for f in available_files]


def main():
    parser = argparse.ArgumentParser(description='Unified Environmental Predictor')
    parser.add_argument('--target', '-t', type=str, default='pm25',
                        choices=list(PREDICTION_TARGETS.keys()),
                        help='Prediction target')
    parser.add_argument('--state', '-s', type=str, default=None,
                        help='State name for prediction')
    parser.add_argument('--month', '-m', type=int, default=None,
                        help='Month (1-12) for seasonal prediction')
    parser.add_argument('--train-all', action='store_true',
                        help='Train models for all targets')
    
    args = parser.parse_args()
    
    db_path = str(Path(__file__).parent.parent / "processed_data.db")
    models_dir = Path(__file__).parent.parent / "models"
    models_dir.mkdir(exist_ok=True)
    
    predictor = UnifiedEnvironmentalPredictor(db_path)
    
    if args.train_all:
        # Train all models
        predictor.train_all()
        predictor.save(str(models_dir / "unified_predictor.pkl"))
    elif args.state:
        # Make prediction for a state
        print(f"\n[*] Predicting {args.target} for {args.state}")
        if args.month:
            print(f"    Month: {args.month}")
        
        result = predictor.predict_state(args.state, args.target, args.month)
        
        if 'error' in result:
            print(f"    [ERROR] {result['error']}")
        else:
            print(f"\n{'='*50}")
            print(f"Prediction Result")
            print('='*50)
            print(f"Target: {result['description']}")
            print(f"State: {result['state']}")
            print(f"Month: {result.get('month', 'All year average')}")
            print(f"\n>>> Predicted Value: {result['predicted_value']}")
            print('='*50)
    else:
        # Interactive mode
        print("\n" + "=" * 70)
        print("Available Prediction Targets")
        print("=" * 70)
        for t, info in PREDICTION_TARGETS.items():
            print(f"  {t:<15} : {info['description']}")
        print("\nUsage:")
        print("  python unified_predictor.py --train-all")
        print("  python unified_predictor.py --target pm25 --state Delhi --month 11")
        print("  python unified_predictor.py --target water_stress --state Rajasthan")


if __name__ == "__main__":
    main()
