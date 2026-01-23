"""
AI Environmental Prediction Models.

This module provides machine learning models for:
1. PM2.5 Prediction - Predict air quality from environmental factors
2. Environmental Health Classification - Classify state-wise environmental health
3. Trend Analysis - Predict future environmental conditions

Uses data from: Pollution, Vegetation, Water, Crop tables.
"""

import sqlite3
import numpy as np
import pickle
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

# ML imports will be loaded on demand
try:
    from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, GradientBoostingRegressor
    from sklearn.linear_model import Ridge, LogisticRegression
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import mean_squared_error, r2_score, accuracy_score, classification_report
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("[WARNING] scikit-learn not installed. Run: uv add scikit-learn")

# Try XGBoost import
try:
    from xgboost import XGBRegressor
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

# Seasonal Climatology Curves for India (based on IMD data)
# Used to adjust predictions for extreme climate changes
SEASONAL_PM25_FACTORS = {
    1: 1.5,   # January: Winter inversion, high pollution
    2: 1.3,   # February: Post-winter
    3: 1.0,   # March: Transition
    4: 0.8,   # April: Pre-monsoon
    5: 0.7,   # May: Hot, some dust
    6: 0.5,   # June: Monsoon onset
    7: 0.4,   # July: Peak monsoon, low pollution
    8: 0.5,   # August: Monsoon
    9: 0.7,   # September: Monsoon retreat
    10: 1.0,  # October: Post-monsoon
    11: 1.6,  # November: Stubble burning + winter
    12: 1.7   # December: Peak winter inversion
}

# Extreme climate event multipliers
EXTREME_CLIMATE_FACTORS = {
    'heatwave': 1.3,           # High temp > 45°C
    'cold_wave': 1.5,          # Low temp < 5°C (inversion)
    'dust_storm': 2.0,         # Rajasthan/Gujarat dust events
    'monsoon_deficit': 1.2,    # Less washout effect
    'monsoon_excess': 0.6,     # More washout
    'stubble_burning': 1.8,    # Oct-Nov Punjab/Haryana
}


@dataclass
class ModelMetrics:
    """Container for model performance metrics."""
    model_name: str
    r2_score: Optional[float] = None
    rmse: Optional[float] = None
    accuracy: Optional[float] = None
    cv_scores: Optional[List[float]] = None
    feature_importance: Optional[Dict[str, float]] = None


class EnvironmentalDataset:
    """
    Loads and prepares environmental data for ML models.
    """
    
    def __init__(self, db_path: str = "processed_data.db"):
        self.db_path = db_path
        self.data = None
        self.features = None
        self.targets = None
        
    def load_combined_data(self) -> 'EnvironmentalDataset':
        """
        Load and merge all environmental tables into a single dataset.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Join all tables on state_name and year (including weather for wind/humidity)
        cursor.execute("""
            SELECT 
                p.state_name,
                p.year,
                
                -- Pollution metrics
                p.pm25_mean,
                p.pm25_stddev,
                p.aqi_mean,
                
                -- Vegetation metrics
                v.ndvi_mean,
                v.ndvi_stddev,
                
                -- Water metrics
                wat.rainfall_annual_mm,
                wat.dry_months_count,
                wat.rainfall_variability_cv,
                wat.surface_water_mean,
                
                -- Crop metrics
                c.cropland_percent,
                c.kharif_ndvi,
                c.rabi_ndvi,
                c.evi_mean,
                
                -- Weather metrics (wind, humidity, temperature)
                COALESCE(wth.wind_speed_mean, 10.0) as wind_speed_mean,
                COALESCE(wth.humidity_mean, 60.0) as humidity_mean,
                COALESCE(wth.temp_mean, 25.0) as temp_mean
                
            FROM Pollution p
            LEFT JOIN Vegetation v ON p.state_name = v.state_name AND p.year = v.year
            LEFT JOIN Water wat ON p.state_name = wat.state_name AND p.year = wat.year
            LEFT JOIN Crop c ON p.state_name = c.state_name AND p.year = c.year
            LEFT JOIN (
                SELECT state_name, year, 
                       AVG(wind_speed_mean) as wind_speed_mean,
                       AVG(humidity_mean) as humidity_mean,
                       AVG(temp_mean) as temp_mean
                FROM MonthlyWeather
                GROUP BY state_name, year
            ) wth ON p.state_name = wth.state_name AND p.year = wth.year
            WHERE v.ndvi_mean IS NOT NULL 
              AND wat.rainfall_annual_mm IS NOT NULL
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        # Convert to list of dicts
        self.data = [dict(row) for row in rows]
        
        print(f"[OK] Loaded {len(self.data)} combined records")
        return self
    
    def get_pm25_prediction_data(self) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Prepare data for PM2.5 prediction.
        
        Features: NDVI, rainfall, dry months, cropland %, EVI
        Target: PM2.5 mean
        """
        if not self.data:
            self.load_combined_data()
        
        feature_names = [
            'ndvi_mean', 'rainfall_annual_mm', 'dry_months_count',
            'cropland_percent', 'evi_mean', 'surface_water_mean',
            'wind_speed_mean', 'humidity_mean', 'temp_mean'  # Added weather features
        ]
        
        X = []
        y = []
        
        for row in self.data:
            # Skip if any feature is missing
            if any(row.get(f) is None for f in feature_names):
                continue
            if row.get('pm25_mean') is None:
                continue
                
            features = [row[f] for f in feature_names]
            X.append(features)
            y.append(row['pm25_mean'])
        
        return np.array(X), np.array(y), feature_names
    
    def get_environmental_health_data(self) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Prepare data for environmental health classification.
        
        Features: All environmental metrics
        Target: Health category (Good/Moderate/Poor/Very Poor)
        """
        if not self.data:
            self.load_combined_data()
        
        feature_names = [
            'ndvi_mean', 'rainfall_annual_mm', 'dry_months_count',
            'cropland_percent', 'evi_mean'
        ]
        
        X = []
        y = []
        
        for row in self.data:
            # Skip if any feature is missing
            if any(row.get(f) is None for f in feature_names):
                continue
            if row.get('pm25_mean') is None:
                continue
            
            features = [row[f] for f in feature_names]
            X.append(features)
            
            # Classify based on PM2.5 (WHO standards)
            pm25 = row['pm25_mean']
            if pm25 <= 15:
                category = 'Good'
            elif pm25 <= 35:
                category = 'Moderate'
            elif pm25 <= 55:
                category = 'Poor'
            else:
                category = 'Very Poor'
            
            y.append(category)
        
        return np.array(X), np.array(y), feature_names

    def get_vegetation_prediction_data(self) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Prepare data for vegetation (NDVI) prediction.
        
        Features: rainfall, temperature, dry months, EVI
        Target: NDVI mean (vegetation health 0-1)
        """
        if not self.data:
            self.load_combined_data()
        
        feature_names = [
            'rainfall_annual_mm', 'temp_mean', 'dry_months_count', 'evi_mean'
        ]
        
        X = []
        y = []
        
        for row in self.data:
            if any(row.get(f) is None for f in feature_names):
                continue
            if row.get('ndvi_mean') is None:
                continue
                
            features = [row[f] for f in feature_names]
            X.append(features)
            y.append(row['ndvi_mean'])
        
        return np.array(X), np.array(y), feature_names

    def get_crop_yield_prediction_data(self) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Prepare data for crop yield (EVI) prediction.
        
        Features: NDVI, rainfall, cropland%, seasonal NDVI
        Target: EVI mean (crop productivity proxy)
        """
        if not self.data:
            self.load_combined_data()
        
        feature_names = [
            'ndvi_mean', 'rainfall_annual_mm', 'cropland_percent', 
            'kharif_ndvi', 'rabi_ndvi'
        ]
        
        X = []
        y = []
        
        for row in self.data:
            if any(row.get(f) is None for f in feature_names):
                continue
            if row.get('evi_mean') is None:
                continue
                
            features = [row[f] for f in feature_names]
            X.append(features)
            y.append(row['evi_mean'])
        
        return np.array(X), np.array(y), feature_names

    def get_water_prediction_data(self) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Prepare data for water level (surface water) prediction.
        
        Features: rainfall, NDVI, temperature, humidity, dry months
        Target: Surface water mean
        """
        if not self.data:
            self.load_combined_data()
        
        feature_names = [
            'rainfall_annual_mm', 'ndvi_mean', 'temp_mean', 
            'humidity_mean', 'dry_months_count'
        ]
        
        X = []
        y = []
        
        for row in self.data:
            if any(row.get(f) is None for f in feature_names):
                continue
            if row.get('surface_water_mean') is None:
                continue
                
            features = [row[f] for f in feature_names]
            X.append(features)
            y.append(row['surface_water_mean'])
        
        return np.array(X), np.array(y), feature_names


class PM25PredictionModel:
    """
    Machine learning model to predict PM2.5 from environmental factors.
    
    Uses Random Forest Regressor with feature importance analysis.
    """
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.metrics = None
        
    def train(self, X: np.ndarray, y: np.ndarray, feature_names: List[str]) -> ModelMetrics:
        """
        Train the PM2.5 prediction model.
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for ML models")
        
        self.feature_names = feature_names
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train Random Forest
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42
        )
        self.model.fit(X_train_scaled, y_train)
        
        # Predictions
        y_pred = self.model.predict(X_test_scaled)
        
        # Cross-validation
        cv_scores = cross_val_score(
            self.model, self.scaler.transform(X), y, 
            cv=5, scoring='r2'
        )
        
        # Feature importance
        importance = dict(zip(
            feature_names, 
            self.model.feature_importances_
        ))
        
        # Metrics
        self.metrics = ModelMetrics(
            model_name="PM2.5 Random Forest Predictor",
            r2_score=r2_score(y_test, y_pred),
            rmse=np.sqrt(mean_squared_error(y_test, y_pred)),
            cv_scores=cv_scores.tolist(),
            feature_importance=importance
        )
        
        return self.metrics
    
    def predict(self, features: Dict[str, float]) -> float:
        """
        Predict PM2.5 from environmental features.
        """
        if not self.model:
            raise ValueError("Model not trained yet")
        
        X = np.array([[features[f] for f in self.feature_names]])
        X_scaled = self.scaler.transform(X)
        
        return self.model.predict(X_scaled)[0]
    
    def save(self, path: str):
        """Save model to file."""
        with open(path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'scaler': self.scaler,
                'feature_names': self.feature_names,
                'metrics': self.metrics
            }, f)
        print(f"[OK] Model saved to {path}")
    
    def load(self, path: str):
        """Load model from file."""
        with open(path, 'rb') as f:
            data = pickle.load(f)
        self.model = data['model']
        self.scaler = data['scaler']
        self.feature_names = data['feature_names']
        self.metrics = data['metrics']
        print(f"[OK] Model loaded from {path}")


class EnvironmentalHealthClassifier:
    """
    Classifier to categorize environmental health status.
    
    Categories: Good, Moderate, Poor, Very Poor
    """
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.label_encoder = None
        self.feature_names = None
        self.metrics = None
    
    def train(self, X: np.ndarray, y: np.ndarray, feature_names: List[str]) -> ModelMetrics:
        """
        Train the environmental health classifier.
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for ML models")
        
        self.feature_names = feature_names
        
        # Encode labels
        self.label_encoder = LabelEncoder()
        y_encoded = self.label_encoder.fit_transform(y)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
        )
        
        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train Random Forest Classifier
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=8,
            min_samples_split=5,
            random_state=42
        )
        self.model.fit(X_train_scaled, y_train)
        
        # Predictions
        y_pred = self.model.predict(X_test_scaled)
        
        # Cross-validation
        cv_scores = cross_val_score(
            self.model, self.scaler.transform(X), y_encoded, 
            cv=5, scoring='accuracy'
        )
        
        # Feature importance
        importance = dict(zip(
            feature_names, 
            self.model.feature_importances_
        ))
        
        # Metrics
        self.metrics = ModelMetrics(
            model_name="Environmental Health Classifier",
            accuracy=accuracy_score(y_test, y_pred),
            cv_scores=cv_scores.tolist(),
            feature_importance=importance
        )
        
        return self.metrics
    
    def predict(self, features: Dict[str, float]) -> str:
        """
        Predict environmental health category.
        """
        if not self.model:
            raise ValueError("Model not trained yet")
        
        X = np.array([[features[f] for f in self.feature_names]])
        X_scaled = self.scaler.transform(X)
        
        pred = self.model.predict(X_scaled)[0]
        return self.label_encoder.inverse_transform([pred])[0]
    
    def predict_proba(self, features: Dict[str, float]) -> Dict[str, float]:
        """
        Get probability distribution over health categories.
        """
        if not self.model:
            raise ValueError("Model not trained yet")
        
        X = np.array([[features[f] for f in self.feature_names]])
        X_scaled = self.scaler.transform(X)
        
        proba = self.model.predict_proba(X_scaled)[0]
        classes = self.label_encoder.inverse_transform(range(len(proba)))
        
        return dict(zip(classes, proba))


class VegetationPredictionModel:
    """
    Machine learning model to predict vegetation health (NDVI).
    
    Uses Random Forest Regressor to predict NDVI from climate factors.
    """
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.metrics = None
        
    def train(self, X: np.ndarray, y: np.ndarray, feature_names: List[str]) -> ModelMetrics:
        """
        Train the vegetation prediction model.
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for ML models")
        
        self.feature_names = feature_names
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train Random Forest
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42
        )
        self.model.fit(X_train_scaled, y_train)
        
        # Predictions
        y_pred = self.model.predict(X_test_scaled)
        
        # Cross-validation
        cv_scores = cross_val_score(
            self.model, self.scaler.transform(X), y, 
            cv=5, scoring='r2'
        )
        
        # Feature importance
        importance = dict(zip(
            feature_names, 
            self.model.feature_importances_
        ))
        
        # Metrics
        self.metrics = ModelMetrics(
            model_name="Vegetation (NDVI) Predictor",
            r2_score=r2_score(y_test, y_pred),
            rmse=np.sqrt(mean_squared_error(y_test, y_pred)),
            cv_scores=cv_scores.tolist(),
            feature_importance=importance
        )
        
        return self.metrics
    
    def predict(self, features: Dict[str, float]) -> float:
        """
        Predict NDVI from environmental features.
        """
        if not self.model:
            raise ValueError("Model not trained yet")
        
        X = np.array([[features[f] for f in self.feature_names]])
        X_scaled = self.scaler.transform(X)
        
        return self.model.predict(X_scaled)[0]
    
    def save(self, path: str):
        """Save model to file."""
        with open(path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'scaler': self.scaler,
                'feature_names': self.feature_names,
                'metrics': self.metrics
            }, f)
        print(f"[OK] Model saved to {path}")
    
    def load(self, path: str):
        """Load model from file."""
        with open(path, 'rb') as f:
            data = pickle.load(f)
        self.model = data['model']
        self.scaler = data['scaler']
        self.feature_names = data['feature_names']
        self.metrics = data['metrics']
        print(f"[OK] Model loaded from {path}")


class CropYieldPredictionModel:
    """
    Machine learning model to predict crop yield (EVI).
    
    Uses Gradient Boosting Regressor for agricultural productivity prediction.
    """
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.metrics = None
        
    def train(self, X: np.ndarray, y: np.ndarray, feature_names: List[str]) -> ModelMetrics:
        """
        Train the crop yield prediction model.
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for ML models")
        
        self.feature_names = feature_names
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train Gradient Boosting for better agricultural predictions
        self.model = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            min_samples_split=5,
            random_state=42
        )
        self.model.fit(X_train_scaled, y_train)
        
        # Predictions
        y_pred = self.model.predict(X_test_scaled)
        
        # Cross-validation
        cv_scores = cross_val_score(
            self.model, self.scaler.transform(X), y, 
            cv=5, scoring='r2'
        )
        
        # Feature importance
        importance = dict(zip(
            feature_names, 
            self.model.feature_importances_
        ))
        
        # Metrics
        self.metrics = ModelMetrics(
            model_name="Crop Yield (EVI) Predictor",
            r2_score=r2_score(y_test, y_pred),
            rmse=np.sqrt(mean_squared_error(y_test, y_pred)),
            cv_scores=cv_scores.tolist(),
            feature_importance=importance
        )
        
        return self.metrics
    
    def predict(self, features: Dict[str, float]) -> float:
        """
        Predict EVI (crop productivity) from features.
        """
        if not self.model:
            raise ValueError("Model not trained yet")
        
        X = np.array([[features[f] for f in self.feature_names]])
        X_scaled = self.scaler.transform(X)
        
        return self.model.predict(X_scaled)[0]
    
    def save(self, path: str):
        """Save model to file."""
        with open(path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'scaler': self.scaler,
                'feature_names': self.feature_names,
                'metrics': self.metrics
            }, f)
        print(f"[OK] Model saved to {path}")
    
    def load(self, path: str):
        """Load model from file."""
        with open(path, 'rb') as f:
            data = pickle.load(f)
        self.model = data['model']
        self.scaler = data['scaler']
        self.feature_names = data['feature_names']
        self.metrics = data['metrics']
        print(f"[OK] Model loaded from {path}")


class WaterLevelPredictionModel:
    """
    Machine learning model to predict water availability (surface water).
    
    Uses Random Forest Regressor for water resource prediction.
    """
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.metrics = None
        
    def train(self, X: np.ndarray, y: np.ndarray, feature_names: List[str]) -> ModelMetrics:
        """
        Train the water level prediction model.
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for ML models")
        
        self.feature_names = feature_names
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train Random Forest
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42
        )
        self.model.fit(X_train_scaled, y_train)
        
        # Predictions
        y_pred = self.model.predict(X_test_scaled)
        
        # Cross-validation
        cv_scores = cross_val_score(
            self.model, self.scaler.transform(X), y, 
            cv=5, scoring='r2'
        )
        
        # Feature importance
        importance = dict(zip(
            feature_names, 
            self.model.feature_importances_
        ))
        
        # Metrics
        self.metrics = ModelMetrics(
            model_name="Water Level Predictor",
            r2_score=r2_score(y_test, y_pred),
            rmse=np.sqrt(mean_squared_error(y_test, y_pred)),
            cv_scores=cv_scores.tolist(),
            feature_importance=importance
        )
        
        return self.metrics
    
    def predict(self, features: Dict[str, float]) -> float:
        """
        Predict surface water level from features.
        """
        if not self.model:
            raise ValueError("Model not trained yet")
        
        X = np.array([[features[f] for f in self.feature_names]])
        X_scaled = self.scaler.transform(X)
        
        return self.model.predict(X_scaled)[0]
    
    def save(self, path: str):
        """Save model to file."""
        with open(path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'scaler': self.scaler,
                'feature_names': self.feature_names,
                'metrics': self.metrics
            }, f)
        print(f"[OK] Model saved to {path}")
    
    def load(self, path: str):
        """Load model from file."""
        with open(path, 'rb') as f:
            data = pickle.load(f)
        self.model = data['model']
        self.scaler = data['scaler']
        self.feature_names = data['feature_names']
        self.metrics = data['metrics']
        print(f"[OK] Model loaded from {path}")


class EnvironmentalAISystem:
    """
    Main AI system that integrates all environmental models.
    
    Provides:
    - PM2.5 prediction
    - Environmental health classification
    - Feature importance analysis
    - State-wise recommendations
    """
    
    def __init__(self, db_path: str = "processed_data.db"):
        self.db_path = db_path
        self.dataset = EnvironmentalDataset(db_path)
        self.pm25_model = PM25PredictionModel()
        self.health_classifier = EnvironmentalHealthClassifier()
        self.vegetation_model = VegetationPredictionModel()
        self.crop_model = CropYieldPredictionModel()
        self.water_model = WaterLevelPredictionModel()
        self.trained = False
        
    def train_all_models(self) -> Dict[str, ModelMetrics]:
        """
        Train all AI models on the environmental data.
        """
        print("=" * 60)
        print("Training Environmental AI Models")
        print("=" * 60)
        
        results = {}
        
        # Load data
        print("\n[1/6] Loading combined environmental data...")
        self.dataset.load_combined_data()
        
        # Train PM2.5 predictor
        print("\n[2/6] Training PM2.5 Prediction Model...")
        X, y, features = self.dataset.get_pm25_prediction_data()
        print(f"      Training samples: {len(X)}")
        pm25_metrics = self.pm25_model.train(X, y, features)
        results['pm25_prediction'] = pm25_metrics
        print(f"      R2 Score: {pm25_metrics.r2_score:.3f}")
        print(f"      RMSE: {pm25_metrics.rmse:.2f} ug/m3")
        
        # Train health classifier
        print("\n[3/6] Training Environmental Health Classifier...")
        X, y, features = self.dataset.get_environmental_health_data()
        print(f"      Training samples: {len(X)}")
        health_metrics = self.health_classifier.train(X, y, features)
        results['health_classification'] = health_metrics
        print(f"      Accuracy: {health_metrics.accuracy:.1%}")
        
        # Train Vegetation predictor
        print("\n[4/6] Training Vegetation (NDVI) Prediction Model...")
        X, y, features = self.dataset.get_vegetation_prediction_data()
        print(f"      Training samples: {len(X)}")
        veg_metrics = self.vegetation_model.train(X, y, features)
        results['vegetation_prediction'] = veg_metrics
        print(f"      R2 Score: {veg_metrics.r2_score:.3f}")
        print(f"      RMSE: {veg_metrics.rmse:.4f}")
        
        # Train Crop Yield predictor
        print("\n[5/6] Training Crop Yield (EVI) Prediction Model...")
        X, y, features = self.dataset.get_crop_yield_prediction_data()
        print(f"      Training samples: {len(X)}")
        crop_metrics = self.crop_model.train(X, y, features)
        results['crop_yield_prediction'] = crop_metrics
        print(f"      R2 Score: {crop_metrics.r2_score:.3f}")
        print(f"      RMSE: {crop_metrics.rmse:.4f}")
        
        # Train Water Level predictor
        print("\n[6/6] Training Water Level Prediction Model...")
        X, y, features = self.dataset.get_water_prediction_data()
        print(f"      Training samples: {len(X)}")
        water_metrics = self.water_model.train(X, y, features)
        results['water_level_prediction'] = water_metrics
        print(f"      R2 Score: {water_metrics.r2_score:.3f}")
        print(f"      RMSE: {water_metrics.rmse:.2f}")
        
        self.trained = True
        
        # Feature importance summary
        print("\n" + "=" * 60)
        print("Feature Importance Analysis")
        print("=" * 60)
        
        print("\nPM2.5 Prediction - Top Factors:")
        for feat, imp in sorted(pm25_metrics.feature_importance.items(), 
                                key=lambda x: x[1], reverse=True):
            print(f"  {feat}: {imp:.1%}")
        
        print("\nVegetation Prediction - Top Factors:")
        for feat, imp in sorted(veg_metrics.feature_importance.items(), 
                                key=lambda x: x[1], reverse=True):
            print(f"  {feat}: {imp:.1%}")
        
        print("\nCrop Yield Prediction - Top Factors:")
        for feat, imp in sorted(crop_metrics.feature_importance.items(), 
                                key=lambda x: x[1], reverse=True):
            print(f"  {feat}: {imp:.1%}")
        
        print("\nWater Level Prediction - Top Factors:")
        for feat, imp in sorted(water_metrics.feature_importance.items(), 
                                key=lambda x: x[1], reverse=True):
            print(f"  {feat}: {imp:.1%}")
        
        print("\n[OK] All 5 models trained successfully!")
        
        return results
    
    def predict_pm25(self, ndvi: float, rainfall: float, dry_months: int,
                     cropland: float, evi: float, surface_water: float,
                     wind_speed: float = 10.0, humidity: float = 60.0, 
                     temp: float = 25.0, month: int = None) -> Dict:
        """
        Predict PM2.5 for given environmental conditions.
        
        Args:
            ndvi: Vegetation index (0-1)
            rainfall: Annual rainfall in mm
            dry_months: Number of dry months
            cropland: Cropland percentage
            evi: Enhanced vegetation index
            surface_water: Surface water coverage
            wind_speed: Wind speed in km/h (affects dispersion)
            humidity: Relative humidity % (affects particle formation)
            temp: Temperature in Celsius (affects inversions)
            month: Optional month for seasonal adjustment (1-12)
        """
        if not self.trained:
            raise ValueError("Models not trained. Call train_all_models() first.")
        
        features = {
            'ndvi_mean': ndvi,
            'rainfall_annual_mm': rainfall,
            'dry_months_count': dry_months,
            'cropland_percent': cropland,
            'evi_mean': evi,
            'surface_water_mean': surface_water,
            'wind_speed_mean': wind_speed,
            'humidity_mean': humidity,
            'temp_mean': temp
        }
        
        pm25_pred = self.pm25_model.predict(features)
        
        # Apply seasonal climatology adjustment if month provided
        if month and month in SEASONAL_PM25_FACTORS:
            seasonal_factor = SEASONAL_PM25_FACTORS[month]
            pm25_pred = pm25_pred * seasonal_factor
        
        # Apply extreme climate adjustments
        extreme_factor = 1.0
        if temp > 45:
            extreme_factor *= EXTREME_CLIMATE_FACTORS['heatwave']
        elif temp < 5:
            extreme_factor *= EXTREME_CLIMATE_FACTORS['cold_wave']
        if humidity < 30 and wind_speed > 25:
            extreme_factor *= EXTREME_CLIMATE_FACTORS['dust_storm']
        pm25_pred *= extreme_factor
        
        # Get health category using health classifier features
        health_features = {
            'ndvi_mean': ndvi,
            'rainfall_annual_mm': rainfall,
            'dry_months_count': dry_months,
            'cropland_percent': cropland,
            'evi_mean': evi
        }
        health_category = self.health_classifier.predict(health_features)
        health_proba = self.health_classifier.predict_proba(health_features)
        
        return {
            'predicted_pm25': round(pm25_pred, 1),
            'health_category': health_category,
            'health_probabilities': {k: round(v, 3) for k, v in health_proba.items()},
            'recommendations': self._get_recommendations(pm25_pred, features),
            'seasonal_adjusted': month is not None,
            'extreme_climate_factor': round(extreme_factor, 2)
        }
    
    def predict_vegetation(self, rainfall: float, temp: float, 
                          dry_months: int, evi: float) -> Dict:
        """
        Predict vegetation health (NDVI) from climate factors.
        
        Args:
            rainfall: Annual rainfall in mm
            temp: Average temperature in Celsius
            dry_months: Number of dry months
            evi: Enhanced vegetation index
            
        Returns:
            Dictionary with predicted NDVI and vegetation health category
        """
        if not self.trained:
            raise ValueError("Models not trained. Call train_all_models() first.")
        
        features = {
            'rainfall_annual_mm': rainfall,
            'temp_mean': temp,
            'dry_months_count': dry_months,
            'evi_mean': evi
        }
        
        ndvi_pred = self.vegetation_model.predict(features)
        
        # Categorize vegetation health
        if ndvi_pred >= 0.6:
            category = 'Healthy'
        elif ndvi_pred >= 0.4:
            category = 'Moderate'
        elif ndvi_pred >= 0.2:
            category = 'Stressed'
        else:
            category = 'Sparse/Degraded'
        
        return {
            'predicted_ndvi': round(ndvi_pred, 4),
            'vegetation_category': category,
            'recommendations': self._get_vegetation_recommendations(ndvi_pred, features)
        }
    
    def predict_crop_yield(self, ndvi: float, rainfall: float, 
                          cropland: float, kharif_ndvi: float, 
                          rabi_ndvi: float) -> Dict:
        """
        Predict crop productivity (EVI) from agricultural factors.
        
        Args:
            ndvi: Vegetation index
            rainfall: Annual rainfall in mm
            cropland: Cropland percentage
            kharif_ndvi: Kharif season NDVI
            rabi_ndvi: Rabi season NDVI
            
        Returns:
            Dictionary with predicted EVI and yield category
        """
        if not self.trained:
            raise ValueError("Models not trained. Call train_all_models() first.")
        
        features = {
            'ndvi_mean': ndvi,
            'rainfall_annual_mm': rainfall,
            'cropland_percent': cropland,
            'kharif_ndvi': kharif_ndvi,
            'rabi_ndvi': rabi_ndvi
        }
        
        evi_pred = self.crop_model.predict(features)
        
        # Categorize crop productivity
        if evi_pred >= 0.45:
            category = 'High Productivity'
        elif evi_pred >= 0.35:
            category = 'Good Productivity'
        elif evi_pred >= 0.25:
            category = 'Moderate Productivity'
        else:
            category = 'Low Productivity'
        
        return {
            'predicted_evi': round(evi_pred, 4),
            'yield_category': category,
            'seasonal_comparison': {
                'kharif_input': round(kharif_ndvi, 3),
                'rabi_input': round(rabi_ndvi, 3)
            },
            'recommendations': self._get_crop_recommendations(evi_pred, features)
        }
    
    def predict_water_level(self, rainfall: float, ndvi: float, temp: float,
                           humidity: float, dry_months: int) -> Dict:
        """
        Predict water availability (surface water) from climate factors.
        
        Args:
            rainfall: Annual rainfall in mm
            ndvi: Vegetation index
            temp: Average temperature in Celsius
            humidity: Average humidity percentage
            dry_months: Number of dry months
            
        Returns:
            Dictionary with predicted water level and stress category
        """
        if not self.trained:
            raise ValueError("Models not trained. Call train_all_models() first.")
        
        features = {
            'rainfall_annual_mm': rainfall,
            'ndvi_mean': ndvi,
            'temp_mean': temp,
            'humidity_mean': humidity,
            'dry_months_count': dry_months
        }
        
        water_pred = self.water_model.predict(features)
        
        # Categorize water stress
        if water_pred >= 70:
            category = 'Adequate'
        elif water_pred >= 50:
            category = 'Moderate'
        elif water_pred >= 30:
            category = 'Stressed'
        else:
            category = 'Critical'
        
        return {
            'predicted_surface_water': round(water_pred, 2),
            'water_stress_category': category,
            'recommendations': self._get_water_recommendations(water_pred, features)
        }
    
    def _get_vegetation_recommendations(self, ndvi: float, features: Dict) -> List[str]:
        """Generate vegetation health recommendations."""
        recommendations = []
        
        if ndvi < 0.3:
            recommendations.append("CRITICAL: Urgent reforestation/afforestation needed")
        if ndvi < 0.4:
            recommendations.append("LOW VEGETATION: Consider green cover restoration programs")
        if features['dry_months_count'] > 6 and ndvi < 0.5:
            recommendations.append("DROUGHT STRESS: Implement irrigation for vegetation")
        if features['rainfall_annual_mm'] < 600:
            recommendations.append("LOW RAINFALL: Consider drought-resistant species")
        
        if not recommendations:
            recommendations.append("Vegetation health is satisfactory")
        
        return recommendations
    
    def _get_crop_recommendations(self, evi: float, features: Dict) -> List[str]:
        """Generate crop yield recommendations."""
        recommendations = []
        
        if evi < 0.25:
            recommendations.append("LOW PRODUCTIVITY: Review irrigation and fertilization")
        if features['kharif_ndvi'] < features['rabi_ndvi'] * 0.8:
            recommendations.append("KHARIF STRESS: Monsoon crop management needed")
        if features['rabi_ndvi'] < features['kharif_ndvi'] * 0.8:
            recommendations.append("RABI STRESS: Winter crop irrigation review needed")
        if features['rainfall_annual_mm'] < 800 and evi < 0.35:
            recommendations.append("WATER DEFICIT: Consider water-efficient crops")
        
        if not recommendations:
            recommendations.append("Crop productivity is on track")
        
        return recommendations
    
    def _get_water_recommendations(self, water_level: float, features: Dict) -> List[str]:
        """Generate water resource recommendations."""
        recommendations = []
        
        if water_level < 30:
            recommendations.append("CRITICAL: Immediate water conservation measures required")
        if water_level < 50:
            recommendations.append("LOW WATER: Implement rainwater harvesting")
        if features['dry_months_count'] > 7:
            recommendations.append("EXTENDED DRY SEASON: Groundwater management needed")
        if features['rainfall_annual_mm'] < 700:
            recommendations.append("LOW RAINFALL REGION: Long-term water storage planning")
        
        if not recommendations:
            recommendations.append("Water resources are adequate")
        
        return recommendations
    
    def _get_recommendations(self, pm25: float, features: Dict) -> List[str]:
        """
        Generate environmental health recommendations.
        """
        recommendations = []
        
        # Air quality recommendations
        if pm25 > 60:
            recommendations.append("HIGH POLLUTION: Implement stricter emission controls")
        if pm25 > 35:
            recommendations.append("Consider air quality advisories for sensitive groups")
        
        # Vegetation recommendations
        if features['ndvi_mean'] < 0.4:
            recommendations.append("LOW VEGETATION: Increase green cover through afforestation")
        
        # Water recommendations
        if features['dry_months_count'] >= 6:
            recommendations.append("WATER STRESS: Implement water conservation measures")
        
        if features['rainfall_annual_mm'] < 800:
            recommendations.append("LOW RAINFALL: Consider drought preparedness")
        
        # Cropland recommendations
        if features['cropland_percent'] > 80:
            recommendations.append("HIGH CROPLAND: Monitor agricultural pollution sources")
        
        if not recommendations:
            recommendations.append("Environmental conditions are within acceptable range")
        
        return recommendations
    
    def analyze_state(self, state_name: str, year: int = 2023) -> Dict:
        """
        Get comprehensive environmental analysis for a state.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                p.pm25_mean, p.aqi_mean, p.aqi_category,
                v.ndvi_mean, v.vegetation_health,
                w.rainfall_annual_mm, w.dry_months_count, w.water_stress_level,
                c.cropland_percent, c.agricultural_intensity
            FROM Pollution p
            LEFT JOIN Vegetation v ON p.state_name = v.state_name AND p.year = v.year
            LEFT JOIN Water w ON p.state_name = w.state_name AND p.year = w.year
            LEFT JOIN Crop c ON p.state_name = c.state_name AND p.year = c.year
            WHERE p.state_name = ? AND p.year = ?
        """, (state_name, year))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return {'error': f'No data found for {state_name} in {year}'}
        
        data = dict(row)
        
        # Add AI predictions if model is trained
        if self.trained and all(data.get(k) for k in ['ndvi_mean', 'rainfall_annual_mm']):
            prediction = self.predict_pm25(
                ndvi=data['ndvi_mean'],
                rainfall=data['rainfall_annual_mm'],
                dry_months=data['dry_months_count'] or 6,
                cropland=data['cropland_percent'] or 50,
                evi=0.3,
                surface_water=1.0
            )
            data['ai_prediction'] = prediction
        
        return data
    
    def save_models(self, directory: str = "models"):
        """Save all trained models."""
        model_dir = Path(directory)
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # Save PM2.5 model
        self.pm25_model.save(str(model_dir / "pm25_model.pkl"))
        
        # Save health classifier
        with open(model_dir / "health_classifier.pkl", 'wb') as f:
            pickle.dump({
                'model': self.health_classifier.model,
                'scaler': self.health_classifier.scaler,
                'label_encoder': self.health_classifier.label_encoder,
                'feature_names': self.health_classifier.feature_names,
                'metrics': self.health_classifier.metrics
            }, f)
        
        # Save vegetation model
        self.vegetation_model.save(str(model_dir / "vegetation_model.pkl"))
        
        # Save crop yield model
        self.crop_model.save(str(model_dir / "crop_yield_model.pkl"))
        
        # Save water level model
        self.water_model.save(str(model_dir / "water_level_model.pkl"))
        
        print(f"[OK] All 5 models saved to {directory}/")


if __name__ == "__main__":
    # Test the AI system
    ai = EnvironmentalAISystem()
    ai.train_all_models()
    
    
