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
    from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
    from sklearn.linear_model import Ridge, LogisticRegression
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import mean_squared_error, r2_score, accuracy_score, classification_report
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("[WARNING] scikit-learn not installed. Run: uv add scikit-learn")


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
        
        # Join all tables on state_name and year
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
                w.rainfall_annual_mm,
                w.dry_months_count,
                w.rainfall_variability_cv,
                w.surface_water_mean,
                
                -- Crop metrics
                c.cropland_percent,
                c.kharif_ndvi,
                c.rabi_ndvi,
                c.evi_mean
                
            FROM Pollution p
            LEFT JOIN Vegetation v ON p.state_name = v.state_name AND p.year = v.year
            LEFT JOIN Water w ON p.state_name = w.state_name AND p.year = w.year
            LEFT JOIN Crop c ON p.state_name = c.state_name AND p.year = c.year
            WHERE v.ndvi_mean IS NOT NULL 
              AND w.rainfall_annual_mm IS NOT NULL
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
            'cropland_percent', 'evi_mean', 'surface_water_mean'
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
        print("\n[1/3] Loading combined environmental data...")
        self.dataset.load_combined_data()
        
        # Train PM2.5 predictor
        print("\n[2/3] Training PM2.5 Prediction Model...")
        X, y, features = self.dataset.get_pm25_prediction_data()
        print(f"      Training samples: {len(X)}")
        pm25_metrics = self.pm25_model.train(X, y, features)
        results['pm25_prediction'] = pm25_metrics
        
        print(f"      R2 Score: {pm25_metrics.r2_score:.3f}")
        print(f"      RMSE: {pm25_metrics.rmse:.2f} ug/m3")
        print(f"      CV Scores: {[f'{s:.2f}' for s in pm25_metrics.cv_scores]}")
        
        # Train health classifier
        print("\n[3/3] Training Environmental Health Classifier...")
        X, y, features = self.dataset.get_environmental_health_data()
        print(f"      Training samples: {len(X)}")
        health_metrics = self.health_classifier.train(X, y, features)
        results['health_classification'] = health_metrics
        
        print(f"      Accuracy: {health_metrics.accuracy:.1%}")
        print(f"      CV Scores: {[f'{s:.1%}' for s in health_metrics.cv_scores]}")
        
        self.trained = True
        
        # Feature importance summary
        print("\n" + "=" * 60)
        print("Feature Importance Analysis")
        print("=" * 60)
        print("\nPM2.5 Prediction - Top Factors:")
        for feat, imp in sorted(pm25_metrics.feature_importance.items(), 
                                key=lambda x: x[1], reverse=True):
            print(f"  {feat}: {imp:.1%}")
        
        print("\n[OK] All models trained successfully!")
        
        return results
    
    def predict_pm25(self, ndvi: float, rainfall: float, dry_months: int,
                     cropland: float, evi: float, surface_water: float) -> Dict:
        """
        Predict PM2.5 for given environmental conditions.
        """
        if not self.trained:
            raise ValueError("Models not trained. Call train_all_models() first.")
        
        features = {
            'ndvi_mean': ndvi,
            'rainfall_annual_mm': rainfall,
            'dry_months_count': dry_months,
            'cropland_percent': cropland,
            'evi_mean': evi,
            'surface_water_mean': surface_water
        }
        
        pm25_pred = self.pm25_model.predict(features)
        
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
            'recommendations': self._get_recommendations(pm25_pred, features)
        }
    
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
        
        print(f"[OK] All models saved to {directory}/")


if __name__ == "__main__":
    # Test the AI system
    ai = EnvironmentalAISystem()
    ai.train_all_models()
    
    # Example prediction
    print("\n" + "=" * 60)
    print("Example Prediction")
    print("=" * 60)
    result = ai.predict_pm25(
        ndvi=0.5,
        rainfall=1500,
        dry_months=5,
        cropland=60,
        evi=0.35,
        surface_water=2.0
    )
    print(f"Predicted PM2.5: {result['predicted_pm25']} ug/m3")
    print(f"Health Category: {result['health_category']}")
    print(f"Recommendations: {result['recommendations']}")
