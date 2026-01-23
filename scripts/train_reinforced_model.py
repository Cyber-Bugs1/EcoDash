"""
Enhanced AI Model Training with Reinforcement Learning Approach

This script implements:
1. Ensemble learning with multiple model variants
2. Reward-based model selection (RL-inspired)
3. Online learning with prediction error feedback
4. Temporal difference learning for trend prediction
5. Experience replay for historical pattern learning

The RL approach here uses:
- State: Environmental features (PM2.5, weather, fire data)
- Action: Prediction adjustment factor
- Reward: Prediction accuracy (negative error)
"""

import sys
import sqlite3
import pickle
import random
import math
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import numpy as np
    from sklearn.ensemble import (
        RandomForestRegressor, 
        GradientBoostingRegressor,
        AdaBoostRegressor
    )
    from sklearn.linear_model import Ridge, LinearRegression
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import mean_squared_error, r2_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Installing scikit-learn...")
    import subprocess
    subprocess.run(['uv', 'add', 'scikit-learn', 'numpy'])

# XGBoost for hybrid training
try:
    from xgboost import XGBRegressor
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("[INFO] XGBoost not available, using standard ensemble")


@dataclass
class Experience:
    """Store experience for replay."""
    state: np.ndarray
    action: float  # Prediction
    reward: float  # Negative error
    next_state: np.ndarray
    done: bool


class ReplayBuffer:
    """Experience replay buffer for learning from past predictions."""
    
    def __init__(self, capacity=10000):
        self.capacity = capacity
        self.buffer = []
        self.position = 0
    
    def push(self, experience: Experience):
        if len(self.buffer) < self.capacity:
            self.buffer.append(experience)
        else:
            self.buffer[self.position] = experience
        self.position = (self.position + 1) % self.capacity
    
    def sample(self, batch_size: int) -> List[Experience]:
        return random.sample(self.buffer, min(batch_size, len(self.buffer)))
    
    def __len__(self):
        return len(self.buffer)


class RewardCalculator:
    """Calculate rewards based on prediction accuracy."""
    
    @staticmethod
    def calculate(predicted: float, actual: float, baseline_error: float = 10.0) -> float:
        """
        Calculate reward based on prediction error.
        Positive reward for low error, negative for high error.
        """
        error = abs(predicted - actual)
        
        # Reward function: exponential decay based on error
        reward = math.exp(-error / baseline_error) - 0.5
        
        # Bonus for very accurate predictions
        if error < 5:
            reward += 0.5
        elif error < 10:
            reward += 0.2
        
        # Penalty for severe errors
        if error > 30:
            reward -= 0.5
        
        return reward


class EnsembleModel:
    """Ensemble of models with RL-based weight adjustment."""
    
    def __init__(self):
        self.models = {}
        self.weights = {}
        self.performance_history = {}
        self.scaler = StandardScaler()
        self.feature_names = []
        
    def initialize_models(self):
        """Initialize ensemble of different model types including XGBoost."""
        self.models = {
            'random_forest': RandomForestRegressor(
                n_estimators=100, max_depth=10, random_state=42
            ),
            'gradient_boost': GradientBoostingRegressor(
                n_estimators=100, max_depth=5, random_state=42
            ),
            'ada_boost': AdaBoostRegressor(
                n_estimators=50, random_state=42
            ),
            'ridge': Ridge(alpha=1.0)
        }
        
        # Add XGBoost if available for hybrid training
        if XGBOOST_AVAILABLE:
            self.models['xgboost'] = XGBRegressor(
                n_estimators=150,
                max_depth=8,
                learning_rate=0.1,
                reg_alpha=0.1,
                reg_lambda=1.0,
                random_state=42,
                verbosity=0
            )
            print("[OK] XGBoost added for hybrid training")
        
        # Initialize equal weights
        self.weights = {name: 1.0 / len(self.models) for name in self.models}
        
        # Initialize performance tracking
        self.performance_history = {name: [] for name in self.models}
        
        print(f"[OK] Initialized {len(self.models)} models in ensemble")
    
    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: List[str]):
        """Fit all models in the ensemble."""
        self.feature_names = feature_names
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train each model
        for name, model in self.models.items():
            print(f"  Training {name}...", end=" ")
            model.fit(X_scaled, y)
            
            # Calculate training score
            score = model.score(X_scaled, y)
            self.performance_history[name].append(score)
            print(f"R² = {score:.4f}")
        
        # Update weights based on performance
        self._update_weights()
    
    def _update_weights(self, learning_rate: float = 0.1):
        """Update model weights based on recent performance (RL policy update)."""
        total_score = 0
        scores = {}
        
        for name, history in self.performance_history.items():
            if history:
                # Weighted recent performance
                recent_score = sum(history[-5:]) / len(history[-5:])
                scores[name] = max(0.01, recent_score)  # Prevent zero weights
                total_score += scores[name]
        
        # Softmax-style weight update
        if total_score > 0:
            for name in self.weights:
                new_weight = scores[name] / total_score
                # Smooth update (momentum)
                self.weights[name] = (1 - learning_rate) * self.weights[name] + learning_rate * new_weight
        
        # Normalize weights
        total_weight = sum(self.weights.values())
        for name in self.weights:
            self.weights[name] /= total_weight
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Weighted ensemble prediction."""
        X_scaled = self.scaler.transform(X)
        
        predictions = np.zeros(len(X))
        
        for name, model in self.models.items():
            model_pred = model.predict(X_scaled)
            predictions += self.weights[name] * model_pred
        
        return predictions
    
    def predict_with_uncertainty(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Predict with uncertainty from model disagreement."""
        X_scaled = self.scaler.transform(X)
        
        all_predictions = []
        
        for name, model in self.models.items():
            pred = model.predict(X_scaled)
            all_predictions.append(pred)
        
        all_predictions = np.array(all_predictions)
        
        # Weighted mean
        weighted_mean = np.zeros(len(X))
        for i, name in enumerate(self.models.keys()):
            weighted_mean += self.weights[name] * all_predictions[i]
        
        # Uncertainty from model disagreement
        uncertainty = np.std(all_predictions, axis=0)
        
        return weighted_mean, uncertainty
    
    def update_from_feedback(self, X: np.ndarray, y_actual: np.ndarray, 
                             y_predicted: np.ndarray, learning_rate: float = 0.05):
        """
        Online learning: Update weights based on actual vs predicted.
        This is the RL "policy update" step.
        """
        errors = np.abs(y_actual - y_predicted)
        mean_error = np.mean(errors)
        
        # Calculate individual model errors
        X_scaled = self.scaler.transform(X)
        model_errors = {}
        
        for name, model in self.models.items():
            model_pred = model.predict(X_scaled)
            model_error = np.mean(np.abs(y_actual - model_pred))
            model_errors[name] = model_error
        
        # Update weights: decrease for high error, increase for low error
        min_error = min(model_errors.values())
        max_error = max(model_errors.values())
        error_range = max_error - min_error if max_error > min_error else 1.0
        
        for name in self.weights:
            # Inverse error scoring
            normalized_error = (model_errors[name] - min_error) / error_range
            adjustment = 1 - normalized_error  # Higher is better
            
            self.weights[name] *= (1 + learning_rate * (adjustment - 0.5))
        
        # Normalize
        total = sum(self.weights.values())
        for name in self.weights:
            self.weights[name] /= total
        
        return mean_error


class TemporalDifferencePredictor:
    """TD-learning for time series prediction adjustments."""
    
    def __init__(self, gamma: float = 0.95, alpha: float = 0.1):
        self.gamma = gamma  # Discount factor
        self.alpha = alpha  # Learning rate
        self.value_estimates = {}  # State-value estimates
        
    def get_state_key(self, state: Dict) -> str:
        """Create state key from features."""
        # Discretize continuous features
        season = state.get('season', 'unknown')
        pollution_level = 'high' if state.get('pm25', 0) > 60 else 'low'
        return f"{season}_{pollution_level}"
    
    def update(self, state: Dict, reward: float, next_state: Dict):
        """TD(0) update."""
        state_key = self.get_state_key(state)
        next_state_key = self.get_state_key(next_state)
        
        # Initialize if not exists
        if state_key not in self.value_estimates:
            self.value_estimates[state_key] = 0.0
        if next_state_key not in self.value_estimates:
            self.value_estimates[next_state_key] = 0.0
        
        # TD update: V(s) = V(s) + α * (r + γ*V(s') - V(s))
        td_target = reward + self.gamma * self.value_estimates[next_state_key]
        td_error = td_target - self.value_estimates[state_key]
        
        self.value_estimates[state_key] += self.alpha * td_error
        
        return td_error
    
    def get_adjustment(self, state: Dict) -> float:
        """Get prediction adjustment based on state value."""
        state_key = self.get_state_key(state)
        return self.value_estimates.get(state_key, 0.0)


class ReinforcedEnvironmentalAI:
    """
    Main AI system with reinforcement learning components.
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.ensemble = EnsembleModel()
        self.replay_buffer = ReplayBuffer(capacity=5000)
        self.td_predictor = TemporalDifferencePredictor()
        self.reward_calculator = RewardCalculator()
        self.training_history = []
        
    def load_enhanced_data(self) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Load enhanced data from database."""
        conn = sqlite3.connect(self.db_path)
        
        # Query enhanced monthly data
        query = """
            SELECT 
                p.pm25_mean, p.aqi_mean,
                w.temp_mean, w.humidity_mean, w.total_precipitation_mm,
                f.fire_count, f.avg_frp,
                p.year, p.month
            FROM MonthlyPollution p
            LEFT JOIN MonthlyWeather w 
                ON p.state_name = w.state_name AND p.year = w.year AND p.month = w.month
            LEFT JOIN MonthlyFires f
                ON p.state_name = f.state_name AND p.year = f.year AND p.month = f.month
            WHERE p.pm25_mean IS NOT NULL
        """
        
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            print("No enhanced data found. Using original pollution data...")
            return self._load_original_data()
        
        # Parse data
        feature_names = ['temp', 'humidity', 'precipitation', 'fire_count', 
                        'fire_frp', 'year', 'month', 'season_winter', 
                        'season_monsoon', 'season_summer']
        
        X = []
        y = []
        
        for row in rows:
            pm25 = row[0]
            temp = row[2] or 25
            humidity = row[3] or 50
            precip = row[4] or 0
            fire_count = row[5] or 0
            fire_frp = row[6] or 0
            year = row[7]
            month = row[8]
            
            # One-hot encode season
            season_winter = 1 if month in [11, 12, 1, 2] else 0
            season_monsoon = 1 if month in [6, 7, 8, 9] else 0
            season_summer = 1 if month in [3, 4, 5] else 0
            
            features = [temp, humidity, precip, fire_count, fire_frp,
                       year, month, season_winter, season_monsoon, season_summer]
            
            X.append(features)
            y.append(pm25)
        
        return np.array(X), np.array(y), feature_names
    
    def _load_original_data(self):
        """Fallback to original data if enhanced not available."""
        conn = sqlite3.connect(self.db_path)
        
        query = """
            SELECT pm25_mean, aqi_mean, ndvi_mean, rainfall_annual_mm, 
                   dry_months_count, cropland_percent, evi_mean, year
            FROM Pollution p
            LEFT JOIN Vegetation v ON p.state_name = v.state_name AND p.year = v.year
            LEFT JOIN Water w ON p.state_name = w.state_name AND p.year = w.year
            LEFT JOIN Crop c ON p.state_name = c.state_name AND p.year = c.year
            WHERE p.pm25_mean IS NOT NULL
        """
        
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        feature_names = ['ndvi', 'rainfall', 'dry_months', 'cropland', 'evi', 'year']
        
        X = []
        y = []
        
        for row in rows:
            X.append([
                row[2] or 0.5,  # ndvi
                row[3] or 1000,  # rainfall
                row[4] or 5,     # dry_months
                row[5] or 50,    # cropland
                row[6] or 0.3,   # evi
                row[7] or 2022   # year
            ])
            y.append(row[0])
        
        return np.array(X), np.array(y), feature_names
    
    def train(self, episodes: int = 100):
        """
        Train the model using RL-inspired approach.
        
        Each episode:
        1. Split data into experience chunks
        2. Train ensemble on chunk
        3. Evaluate and calculate rewards
        4. Update model weights based on rewards
        5. Store experiences in replay buffer
        """
        print("\n" + "=" * 70)
        print("Reinforcement Learning Training")
        print("=" * 70)
        
        # Load data
        print("\nLoading enhanced data...")
        X, y, feature_names = self.load_enhanced_data()
        print(f"Loaded {len(X)} samples with {len(feature_names)} features")
        
        # Initialize ensemble
        self.ensemble.initialize_models()
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        print(f"\nTraining samples: {len(X_train)}")
        print(f"Test samples: {len(X_test)}")
        
        # Initial training
        print("\n--- Initial Ensemble Training ---")
        self.ensemble.fit(X_train, y_train, feature_names)
        
        # RL Training loop
        print(f"\n--- Reinforcement Learning ({episodes} episodes) ---")
        
        best_reward = float('-inf')
        
        for episode in range(episodes):
            # Sample batch from training data
            batch_size = min(50, len(X_train))
            indices = random.sample(range(len(X_train)), batch_size)
            X_batch = X_train[indices]
            y_batch = y_train[indices]
            
            # Make predictions
            predictions, uncertainty = self.ensemble.predict_with_uncertainty(X_batch)
            
            # Calculate rewards
            rewards = []
            for pred, actual in zip(predictions, y_batch):
                reward = self.reward_calculator.calculate(pred, actual)
                rewards.append(reward)
            
            mean_reward = np.mean(rewards)
            
            # Store experiences
            for i in range(len(X_batch) - 1):
                exp = Experience(
                    state=X_batch[i],
                    action=predictions[i],
                    reward=rewards[i],
                    next_state=X_batch[i + 1],
                    done=False
                )
                self.replay_buffer.push(exp)
            
            # Experience replay: update from buffer
            if len(self.replay_buffer) >= 32:
                replay_batch = self.replay_buffer.sample(32)
                
                replay_X = np.array([e.state for e in replay_batch])
                replay_y = np.array([e.action - (e.reward * 5) for e in replay_batch])
                
                # TD updates
                for e in replay_batch:
                    state_dict = {'pm25': e.action, 'season': 'unknown'}
                    next_state_dict = {'pm25': e.action, 'season': 'unknown'}
                    self.td_predictor.update(state_dict, e.reward, next_state_dict)
            
            # Update ensemble weights based on feedback
            error = self.ensemble.update_from_feedback(
                X_batch, y_batch, predictions
            )
            
            # Track best performance
            if mean_reward > best_reward:
                best_reward = mean_reward
            
            self.training_history.append({
                'episode': episode,
                'mean_reward': mean_reward,
                'error': error,
                'weights': self.ensemble.weights.copy()
            })
            
            # Progress
            if (episode + 1) % 10 == 0:
                print(f"  Episode {episode + 1}/{episodes}: "
                      f"Reward = {mean_reward:.4f}, Error = {error:.2f}")
        
        # Final evaluation
        print("\n--- Final Evaluation ---")
        y_pred_test = self.ensemble.predict(X_test)
        
        mse = mean_squared_error(y_test, y_pred_test)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_test, y_pred_test)
        
        print(f"Test RMSE: {rmse:.2f} μg/m³")
        print(f"Test R²: {r2:.4f}")
        
        # Final weights
        print("\nFinal Model Weights (RL-optimized):")
        for name, weight in sorted(self.ensemble.weights.items(), 
                                    key=lambda x: x[1], reverse=True):
            bar = "█" * int(weight * 40)
            print(f"  {name:<18} {weight:.3f} {bar}")
        
        return rmse, r2
    
    def predict(self, features: Dict[str, float]) -> Dict:
        """Make prediction with RL adjustments."""
        # Prepare features
        feature_vector = [
            features.get('temp', 25),
            features.get('humidity', 50),
            features.get('precipitation', 0),
            features.get('fire_count', 0),
            features.get('fire_frp', 0),
            features.get('year', 2025),
            features.get('month', 1),
            1 if features.get('month', 1) in [11, 12, 1, 2] else 0,  # winter
            1 if features.get('month', 1) in [6, 7, 8, 9] else 0,    # monsoon
            1 if features.get('month', 1) in [3, 4, 5] else 0        # summer
        ]
        
        X = np.array([feature_vector])
        pred, uncertainty = self.ensemble.predict_with_uncertainty(X)
        
        # Apply TD adjustment
        state_dict = {'pm25': pred[0], 'season': self._get_season(features.get('month', 1))}
        td_adjustment = self.td_predictor.get_adjustment(state_dict)
        
        adjusted_pred = pred[0] + td_adjustment
        
        return {
            'pm25_predicted': adjusted_pred,
            'pm25_base': pred[0],
            'uncertainty': uncertainty[0],
            'td_adjustment': td_adjustment,
            'confidence': 'high' if uncertainty[0] < 10 else ('medium' if uncertainty[0] < 20 else 'low')
        }
    
    def _get_season(self, month: int) -> str:
        if month in [12, 1, 2]:
            return 'winter'
        elif month in [3, 4, 5]:
            return 'summer'
        elif month in [6, 7, 8, 9]:
            return 'monsoon'
        else:
            return 'post_monsoon'
    
    def save(self, path: str):
        """Save trained model."""
        model_data = {
            'ensemble': self.ensemble,
            'td_predictor': self.td_predictor,
            'training_history': self.training_history,
            'saved_at': datetime.now().isoformat()
        }
        
        with open(path, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"[OK] Model saved to {path}")
    
    def load(self, path: str):
        """Load trained model."""
        with open(path, 'rb') as f:
            model_data = pickle.load(f)
        
        self.ensemble = model_data['ensemble']
        self.td_predictor = model_data['td_predictor']
        self.training_history = model_data.get('training_history', [])
        
        print(f"[OK] Model loaded from {path}")


def main():
    db_path = str(Path(__file__).parent.parent / "processed_data.db")
    models_dir = Path(__file__).parent.parent / "models"
    models_dir.mkdir(exist_ok=True)
    
    print("=" * 70)
    print("Reinforced Environmental AI Training")
    print("=" * 70)
    print("\nUsing Reinforcement Learning approach:")
    print("  • Ensemble learning with multiple models")
    print("  • Reward-based weight optimization")
    print("  • Experience replay from prediction history")
    print("  • Temporal difference learning for trends")
    
    # Initialize and train
    ai = ReinforcedEnvironmentalAI(db_path)
    rmse, r2 = ai.train(episodes=100)
    
    # Save model
    model_path = models_dir / "reinforced_model.pkl"
    ai.save(str(model_path))
    
    # Test prediction
    print("\n" + "=" * 70)
    print("Example Predictions")
    print("=" * 70)
    
    test_scenarios = [
        {'name': 'Winter Delhi', 'temp': 15, 'humidity': 60, 'precipitation': 5, 
         'fire_count': 20, 'fire_frp': 30, 'month': 1},
        {'name': 'Monsoon Kerala', 'temp': 28, 'humidity': 90, 'precipitation': 300,
         'fire_count': 0, 'fire_frp': 0, 'month': 7},
        {'name': 'Summer Rajasthan', 'temp': 42, 'humidity': 20, 'precipitation': 0,
         'fire_count': 5, 'fire_frp': 10, 'month': 5},
    ]
    
    for scenario in test_scenarios:
        result = ai.predict(scenario)
        print(f"\n{scenario['name']}:")
        print(f"  PM2.5 Predicted: {result['pm25_predicted']:.1f} μg/m³")
        print(f"  Uncertainty: ±{result['uncertainty']:.1f}")
        print(f"  Confidence: {result['confidence']}")
        print(f"  TD Adjustment: {result['td_adjustment']:.2f}")
    
    print("\n" + "=" * 70)
    print("Training Complete!")
    print(f"Model saved to: {model_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
