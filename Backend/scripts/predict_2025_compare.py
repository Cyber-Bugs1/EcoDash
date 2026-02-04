"""
Predict PM2.5 for 2025 using trained models.
Compare model accuracy by predicting for a known year (2024) and comparing with actual data.
"""

import sys
import sqlite3
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai.spike_predictor import PollutionSpikePredictor


def get_actual_data(db_path, year):
    """Get actual pollution data for a specific year."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    actual_data = {}
    
    # Get from Pollution table
    try:
        cursor.execute(f"""
            SELECT state, AVG(pm25_mean) as avg_pm25
            FROM Pollution 
            WHERE year = {year} 
            GROUP BY state
        """)
        for row in cursor.fetchall():
            if row[0] and row[1]:
                actual_data[row[0]] = row[1]
    except Exception as e:
        print(f"Error reading Pollution table: {e}")
    
    conn.close()
    return actual_data


def get_all_states(db_path):
    """Get list of all states from the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    states = set()
    
    try:
        cursor.execute("SELECT DISTINCT state FROM Pollution")
        for row in cursor.fetchall():
            if row[0]:
                states.add(row[0])
    except:
        pass
    
    conn.close()
    return sorted(list(states))


def main():
    db_path = str(Path(__file__).parent.parent / "processed_data.db")
    
    print("=" * 80)
    print("PM2.5 Prediction Validation - Comparing Model Predictions with Actual Data")
    print("=" * 80)
    
    # Get all states
    states = get_all_states(db_path)
    print(f"\nFound {len(states)} states in database")
    
    # Initialize and train spike predictor
    print("\n--- Training Spike Predictor on 2020-2023 data ---")
    predictor = PollutionSpikePredictor(db_path)
    predictor.train()
    
    # =========================================================================
    # PART 1: Validate model by predicting 2024 and comparing with actual 2024
    # =========================================================================
    print("\n" + "=" * 80)
    print("VALIDATION: Predicting 2024 and Comparing with Actual 2024 Data")
    print("=" * 80)
    
    actual_2024 = get_actual_data(db_path, 2024)
    actual_2023 = get_actual_data(db_path, 2023)
    
    # Use 2024 if available, else 2023
    if actual_2024:
        comparison_year = 2024
        actual_data = actual_2024
        print(f"Using actual {comparison_year} data for validation")
    else:
        comparison_year = 2023
        actual_data = actual_2023
        print(f"2024 data not available, using {comparison_year} data for validation")
    
    print(f"Found actual data for {len(actual_data)} states")
    
    print(f"\n{'State':<25} {'Predicted':<15} {'Actual':<15} {'Error':<15} {'Accuracy'}")
    print("-" * 85)
    
    validation_results = []
    
    for state in sorted(actual_data.keys()):
        try:
            prediction = predictor.predict_for_year(state, comparison_year)
            predicted = prediction.predicted_pm25
            actual = actual_data[state]
            
            error = predicted - actual
            accuracy = max(0, 100 - abs(error / actual * 100))
            
            print(f"{state:<25} {predicted:<15.2f} {actual:<15.2f} {error:+.2f}{'':8} {accuracy:.1f}%")
            
            validation_results.append({
                'state': state,
                'predicted': predicted,
                'actual': actual,
                'error': error,
                'accuracy': accuracy
            })
        except Exception as e:
            pass  # Skip states without enough historical data
    
    # Calculate validation metrics
    if validation_results:
        errors = [abs(r['error']) for r in validation_results]
        accuracies = [r['accuracy'] for r in validation_results]
        
        print("\n--- Validation Summary ---")
        print(f"States validated: {len(validation_results)}")
        print(f"Mean Absolute Error: {sum(errors)/len(errors):.2f} μg/m³")
        print(f"Mean Accuracy: {sum(accuracies)/len(accuracies):.1f}%")
        print(f"Best Accuracy: {max(accuracies):.1f}%")
        print(f"Worst Accuracy: {min(accuracies):.1f}%")
    
    # =========================================================================
    # PART 2: Future Predictions for 2025
    # =========================================================================
    print("\n" + "=" * 80)
    print("FUTURE PREDICTIONS: PM2.5 Levels for 2025")
    print("=" * 80)
    
    print(f"\n{'State':<25} {'PM2.5 (μg/m³)':<15} {'Spike Prob':<12} {'Risk Level':<15} {'Trend'}")
    print("-" * 85)
    
    predictions_2025 = []
    
    for state in states:
        try:
            pred = predictor.predict_for_year(state, 2025)
            print(f"{state:<25} {pred.predicted_pm25:<15.2f} {pred.spike_probability*100:<12.0f}% {pred.risk_level:<15} {pred.trend_direction}")
            
            predictions_2025.append({
                'state': state,
                'pm25': pred.predicted_pm25,
                'spike_prob': pred.spike_probability,
                'risk': pred.risk_level,
                'trend': pred.trend_direction
            })
        except:
            pass
    
    # Summary
    print("\n" + "=" * 80)
    print("2025 Predictions Summary")
    print("=" * 80)
    
    if predictions_2025:
        # Risk level breakdown
        risk_counts = {}
        for p in predictions_2025:
            risk = p['risk']
            risk_counts[risk] = risk_counts.get(risk, 0) + 1
        
        print("\nRisk Level Distribution:")
        for risk, count in sorted(risk_counts.items()):
            print(f"  {risk}: {count} states")
        
        # Top 5 most polluted
        print("\nTop 5 Most Polluted States (2025 Prediction):")
        sorted_pred = sorted(predictions_2025, key=lambda x: x['pm25'], reverse=True)
        for i, p in enumerate(sorted_pred[:5], 1):
            print(f"  {i}. {p['state']}: {p['pm25']:.2f} μg/m³ ({p['risk']})")
        
        # Top 5 cleanest
        print("\nTop 5 Cleanest States (2025 Prediction):")
        for i, p in enumerate(sorted_pred[-5:], 1):
            print(f"  {i}. {p['state']}: {p['pm25']:.2f} μg/m³ ({p['risk']})")
        
        # States with high spike probability
        high_spike = [p for p in predictions_2025 if p['spike_prob'] > 0.5]
        if high_spike:
            print(f"\n⚠️ States with High Spike Probability (>50%):")
            for p in sorted(high_spike, key=lambda x: x['spike_prob'], reverse=True):
                print(f"  {p['state']}: {p['spike_prob']*100:.0f}% chance of spike")


if __name__ == "__main__":
    main()
