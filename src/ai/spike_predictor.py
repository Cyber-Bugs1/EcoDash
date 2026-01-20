"""
Pollution Spike Predictor - Forecasts future pollution trends and spikes.

Features:
1. Time-series based trend analysis
2. Year-specific pollution predictions
3. Spike probability calculation
4. Seasonal pattern detection
"""

import sqlite3
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

try:
    from sklearn.linear_model import LinearRegression
    from sklearn.ensemble import GradientBoostingRegressor
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


@dataclass
class SpikePrediction:
    """Container for spike prediction results."""
    year: int
    predicted_pm25: float
    spike_probability: float
    trend_direction: str
    confidence: float
    risk_level: str
    contributing_factors: List[str]


class PollutionSpikePredictor:
    """
    Predicts future pollution spikes using historical trend analysis.
    
    Uses:
    - Linear regression for basic trend
    - Gradient boosting for complex patterns
    - Historical pattern matching for spike detection
    """
    
    def __init__(self, db_path: str = "processed_data.db"):
        self.db_path = db_path
        self.trend_model = None
        self.spike_model = None
        self.historical_data = None
        self.trained = False
        
    def load_historical_data(self) -> Dict:
        """Load historical pollution data for all states."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                p.state_name,
                p.year,
                p.pm25_mean,
                p.pm25_stddev,
                p.aqi_mean,
                COALESCE(v.ndvi_mean, 0.5) as ndvi_mean,
                COALESCE(w.rainfall_annual_mm, 1500) as rainfall,
                COALESCE(w.dry_months_count, 6) as dry_months,
                COALESCE(c.cropland_percent, 50) as cropland
            FROM Pollution p
            LEFT JOIN Vegetation v ON p.state_name = v.state_name AND p.year = v.year
            LEFT JOIN Water w ON p.state_name = w.state_name AND p.year = w.year
            LEFT JOIN Crop c ON p.state_name = c.state_name AND p.year = c.year
            ORDER BY p.state_name, p.year
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        # Organize by state
        self.historical_data = {}
        for row in rows:
            state = row['state_name']
            if state not in self.historical_data:
                self.historical_data[state] = []
            self.historical_data[state].append(dict(row))
        
        return self.historical_data
    
    def train(self):
        """Train the spike prediction models."""
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required")
        
        if not self.historical_data:
            self.load_historical_data()
        
        # Prepare training data for trend prediction
        X_trend = []
        y_trend = []
        
        for state, records in self.historical_data.items():
            for i, record in enumerate(records):
                # Features: year, historical trend, environmental factors
                year = record['year']
                
                # Calculate year-over-year change
                if i > 0:
                    prev_pm25 = records[i-1]['pm25_mean']
                    change = record['pm25_mean'] - prev_pm25
                else:
                    change = 0
                
                features = [
                    year,
                    record['ndvi_mean'],
                    record['rainfall'],
                    record['dry_months'],
                    record['cropland'],
                    change  # Previous year change
                ]
                
                X_trend.append(features)
                y_trend.append(record['pm25_mean'])
        
        X_trend = np.array(X_trend)
        y_trend = np.array(y_trend)
        
        # Train gradient boosting for better predictions
        self.spike_model = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )
        self.spike_model.fit(X_trend, y_trend)
        
        # Train simple linear model for trend direction
        self.trend_model = LinearRegression()
        self.trend_model.fit(X_trend[:, :1], y_trend)  # Just year vs PM2.5
        
        self.trained = True
        print("[OK] Spike prediction models trained")
        
        return self
    
    def predict_for_year(self, state_name: str, target_year: int) -> SpikePrediction:
        """
        Predict pollution for a specific state and year.
        
        Args:
            state_name: Name of the state
            target_year: Year to predict for
        
        Returns:
            SpikePrediction with detailed forecasts
        """
        if not self.trained:
            self.train()
        
        if state_name not in self.historical_data:
            raise ValueError(f"No historical data for {state_name}")
        
        records = self.historical_data[state_name]
        latest = records[-1]
        
        # Calculate historical statistics
        pm25_values = [r['pm25_mean'] for r in records]
        avg_pm25 = np.mean(pm25_values)
        std_pm25 = np.std(pm25_values)
        
        # Calculate trend (year-over-year change)
        if len(records) >= 2:
            changes = [records[i]['pm25_mean'] - records[i-1]['pm25_mean'] 
                      for i in range(1, len(records))]
            avg_change = np.mean(changes)
        else:
            avg_change = 0
        
        # Prepare features for prediction
        years_ahead = target_year - latest['year']
        
        # Estimate environmental factors (slight degradation over time)
        estimated_ndvi = max(0.2, latest['ndvi_mean'] - 0.01 * years_ahead)
        estimated_rainfall = latest['rainfall']  # Assume stable
        estimated_dry_months = min(12, latest['dry_months'] + 0.1 * years_ahead)
        estimated_cropland = min(100, latest['cropland'] + 0.2 * years_ahead)
        
        features = np.array([[
            target_year,
            estimated_ndvi,
            estimated_rainfall,
            estimated_dry_months,
            estimated_cropland,
            avg_change
        ]])
        
        # Predict PM2.5
        predicted_pm25 = self.spike_model.predict(features)[0]
        
        # Calculate spike probability
        # A spike is when PM2.5 exceeds historical average by 1.5 std dev
        spike_threshold = avg_pm25 + 1.5 * std_pm25
        
        if predicted_pm25 > spike_threshold:
            spike_prob = 0.8 + 0.15 * min(1, (predicted_pm25 - spike_threshold) / std_pm25)
        elif predicted_pm25 > avg_pm25 + std_pm25:
            spike_prob = 0.5 + 0.3 * (predicted_pm25 - avg_pm25 - std_pm25) / (0.5 * std_pm25)
        elif predicted_pm25 > avg_pm25:
            spike_prob = 0.2 + 0.3 * (predicted_pm25 - avg_pm25) / std_pm25
        else:
            spike_prob = max(0.05, 0.2 * predicted_pm25 / avg_pm25)
        
        spike_prob = min(0.95, max(0.05, spike_prob))
        
        # Determine trend direction
        if avg_change > 5:
            trend = "Strongly Increasing"
        elif avg_change > 1:
            trend = "Increasing"
        elif avg_change > -1:
            trend = "Stable"
        elif avg_change > -5:
            trend = "Decreasing"
        else:
            trend = "Strongly Decreasing"
        
        # Risk level
        if predicted_pm25 > 100 or spike_prob > 0.7:
            risk = "Critical"
        elif predicted_pm25 > 60 or spike_prob > 0.5:
            risk = "High"
        elif predicted_pm25 > 35 or spike_prob > 0.3:
            risk = "Moderate"
        else:
            risk = "Low"
        
        # Contributing factors
        factors = []
        if estimated_cropland > 80:
            factors.append("High agricultural activity")
        if estimated_dry_months >= 7:
            factors.append("Extended dry season expected")
        if estimated_ndvi < 0.4:
            factors.append("Low vegetation cover")
        if estimated_rainfall < 1000:
            factors.append("Below average rainfall expected")
        if avg_change > 0:
            factors.append(f"Historical upward trend ({avg_change:.1f} ug/m3/year)")
        
        if not factors:
            factors.append("No major risk factors identified")
        
        # Confidence based on data availability
        confidence = min(0.9, 0.5 + 0.1 * len(records))
        
        return SpikePrediction(
            year=target_year,
            predicted_pm25=round(predicted_pm25, 1),
            spike_probability=round(spike_prob, 2),
            trend_direction=trend,
            confidence=round(confidence, 2),
            risk_level=risk,
            contributing_factors=factors
        )
    
    def predict_multi_year(self, state_name: str, start_year: int, 
                           end_year: int) -> List[SpikePrediction]:
        """
        Predict pollution for multiple years.
        """
        predictions = []
        for year in range(start_year, end_year + 1):
            pred = self.predict_for_year(state_name, year)
            predictions.append(pred)
        return predictions
    
    def get_national_forecast(self, target_year: int) -> Dict:
        """
        Get national-level pollution forecast.
        """
        if not self.trained:
            self.train()
        
        state_predictions = {}
        high_risk_states = []
        
        for state in self.historical_data.keys():
            pred = self.predict_for_year(state, target_year)
            state_predictions[state] = pred
            
            if pred.risk_level in ['Critical', 'High']:
                high_risk_states.append({
                    'state': state,
                    'predicted_pm25': pred.predicted_pm25,
                    'spike_probability': pred.spike_probability,
                    'risk_level': pred.risk_level
                })
        
        # National averages
        all_pm25 = [p.predicted_pm25 for p in state_predictions.values()]
        all_spike_prob = [p.spike_probability for p in state_predictions.values()]
        
        return {
            'year': target_year,
            'national_avg_pm25': round(np.mean(all_pm25), 1),
            'national_spike_probability': round(np.mean(all_spike_prob), 2),
            'high_risk_states': sorted(high_risk_states, 
                                       key=lambda x: x['predicted_pm25'], 
                                       reverse=True),
            'states_at_risk': len(high_risk_states),
            'total_states': len(state_predictions)
        }


if __name__ == "__main__":
    # Test spike predictor
    predictor = PollutionSpikePredictor()
    predictor.train()
    
    # Predict for Delhi 2025
    pred = predictor.predict_for_year("Delhi", 2025)
    print(f"\nDelhi 2025 Prediction:")
    print(f"  PM2.5: {pred.predicted_pm25} ug/m3")
    print(f"  Spike Probability: {pred.spike_probability:.0%}")
    print(f"  Risk Level: {pred.risk_level}")
    print(f"  Trend: {pred.trend_direction}")
    print(f"  Factors: {pred.contributing_factors}")
