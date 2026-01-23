"""
Comprehensive Model Accuracy Test with Real-World Data

Compares model predictions against actual recorded values from the database
to evaluate real-world accuracy.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3
import numpy as np
from src.ai.environmental_ai import EnvironmentalAISystem


def load_test_data(db_path):
    """Load actual data from database for testing."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get combined data with all environmental metrics
    cursor.execute("""
        SELECT 
            p.state_name,
            p.year,
            p.pm25_mean,
            v.ndvi_mean,
            w.rainfall_annual_mm,
            w.dry_months_count,
            w.surface_water_mean,
            c.cropland_percent,
            c.kharif_ndvi,
            c.rabi_ndvi,
            c.evi_mean,
            COALESCE(
                (SELECT AVG(temp_mean) FROM MonthlyWeather mw 
                 WHERE mw.state_name = p.state_name AND mw.year = p.year), 25
            ) as temp_mean,
            COALESCE(
                (SELECT AVG(humidity_mean) FROM MonthlyWeather mw 
                 WHERE mw.state_name = p.state_name AND mw.year = p.year), 60
            ) as humidity_mean
        FROM Pollution p
        LEFT JOIN Vegetation v ON p.state_name = v.state_name AND p.year = v.year
        LEFT JOIN Water w ON p.state_name = w.state_name AND p.year = w.year
        LEFT JOIN Crop c ON p.state_name = c.state_name AND p.year = c.year
        WHERE v.ndvi_mean IS NOT NULL 
          AND w.rainfall_annual_mm IS NOT NULL
          AND c.evi_mean IS NOT NULL
        ORDER BY p.state_name, p.year
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def test_model_accuracy(ai, test_data):
    """Test all models and compare predictions with actual values."""
    
    results = {
        'vegetation': {'actual': [], 'predicted': [], 'errors': []},
        'crop_yield': {'actual': [], 'predicted': [], 'errors': []},
        'water_level': {'actual': [], 'predicted': [], 'errors': []},
        'pm25': {'actual': [], 'predicted': [], 'errors': []}
    }
    
    state_results = []
    
    for record in test_data:
        state = record['state_name']
        year = record['year']
        
        try:
            # Test Vegetation Model (predict NDVI)
            veg_pred = ai.predict_vegetation(
                rainfall=record['rainfall_annual_mm'],
                temp=record['temp_mean'],
                dry_months=record['dry_months_count'],
                evi=record['evi_mean']
            )
            actual_ndvi = record['ndvi_mean']
            pred_ndvi = veg_pred['predicted_ndvi']
            veg_error = abs(actual_ndvi - pred_ndvi)
            results['vegetation']['actual'].append(actual_ndvi)
            results['vegetation']['predicted'].append(pred_ndvi)
            results['vegetation']['errors'].append(veg_error)
            
            # Test Crop Yield Model (predict EVI)
            crop_pred = ai.predict_crop_yield(
                ndvi=record['ndvi_mean'],
                rainfall=record['rainfall_annual_mm'],
                cropland=record['cropland_percent'],
                kharif_ndvi=record['kharif_ndvi'],
                rabi_ndvi=record['rabi_ndvi']
            )
            actual_evi = record['evi_mean']
            pred_evi = crop_pred['predicted_evi']
            crop_error = abs(actual_evi - pred_evi)
            results['crop_yield']['actual'].append(actual_evi)
            results['crop_yield']['predicted'].append(pred_evi)
            results['crop_yield']['errors'].append(crop_error)
            
            # Test Water Level Model (predict surface water)
            water_pred = ai.predict_water_level(
                rainfall=record['rainfall_annual_mm'],
                ndvi=record['ndvi_mean'],
                temp=record['temp_mean'],
                humidity=record['humidity_mean'],
                dry_months=record['dry_months_count']
            )
            actual_water = record['surface_water_mean']
            pred_water = water_pred['predicted_surface_water']
            water_error = abs(actual_water - pred_water)
            results['water_level']['actual'].append(actual_water)
            results['water_level']['predicted'].append(pred_water)
            results['water_level']['errors'].append(water_error)
            
            # Store state-level results
            state_results.append({
                'state': state,
                'year': year,
                'veg_actual': round(actual_ndvi, 4),
                'veg_pred': round(pred_ndvi, 4),
                'veg_error': round(veg_error, 4),
                'crop_actual': round(actual_evi, 4),
                'crop_pred': round(pred_evi, 4),
                'crop_error': round(crop_error, 4),
                'water_actual': round(actual_water, 2),
                'water_pred': round(pred_water, 2),
                'water_error': round(water_error, 2)
            })
            
        except Exception as e:
            print(f"  Error for {state} ({year}): {e}")
    
    return results, state_results


def calculate_metrics(results):
    """Calculate comprehensive accuracy metrics."""
    metrics = {}
    
    for model_name, data in results.items():
        if len(data['actual']) == 0:
            continue
            
        actual = np.array(data['actual'])
        predicted = np.array(data['predicted'])
        errors = np.array(data['errors'])
        
        # Mean Absolute Error
        mae = np.mean(errors)
        
        # Root Mean Square Error
        rmse = np.sqrt(np.mean((actual - predicted) ** 2))
        
        # Mean Absolute Percentage Error
        mape = np.mean(np.abs((actual - predicted) / actual)) * 100
        
        # R² Score
        ss_res = np.sum((actual - predicted) ** 2)
        ss_tot = np.sum((actual - np.mean(actual)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # Correlation
        correlation = np.corrcoef(actual, predicted)[0, 1]
        
        metrics[model_name] = {
            'n_samples': len(actual),
            'MAE': mae,
            'RMSE': rmse,
            'MAPE': mape,
            'R2': r2,
            'Correlation': correlation,
            'Min_Error': np.min(errors),
            'Max_Error': np.max(errors)
        }
    
    return metrics


def main():
    print("=" * 70)
    print("🧪 MODEL ACCURACY TEST WITH REAL-WORLD DATA")
    print("=" * 70)
    
    db_path = Path(__file__).parent.parent / "processed_data.db"
    
    # Load test data
    print("\n📊 Loading test data from database...")
    test_data = load_test_data(db_path)
    print(f"   Loaded {len(test_data)} records for testing")
    
    # Initialize and train AI system
    print("\n🤖 Initializing AI system...")
    ai = EnvironmentalAISystem()
    ai.train_all_models()
    
    # Test predictions
    print("\n🔬 Testing predictions against actual values...")
    results, state_results = test_model_accuracy(ai, test_data)
    
    # Calculate metrics
    metrics = calculate_metrics(results)
    
    # Display results
    print("\n" + "=" * 70)
    print("📈 ACCURACY METRICS SUMMARY")
    print("=" * 70)
    
    for model_name, m in metrics.items():
        print(f"\n{'—' * 40}")
        print(f"📊 {model_name.upper().replace('_', ' ')} MODEL")
        print(f"{'—' * 40}")
        print(f"  Samples Tested:  {m['n_samples']}")
        print(f"  R² Score:        {m['R2']:.4f}")
        print(f"  Correlation:     {m['Correlation']:.4f}")
        print(f"  MAE:             {m['MAE']:.4f}")
        print(f"  RMSE:            {m['RMSE']:.4f}")
        print(f"  MAPE:            {m['MAPE']:.2f}%")
        print(f"  Error Range:     {m['Min_Error']:.4f} - {m['Max_Error']:.4f}")
    
    # Show sample state comparisons
    print("\n" + "=" * 70)
    print("🗺️  SAMPLE STATE-WISE COMPARISONS (First 10)")
    print("=" * 70)
    print(f"\n{'State':<20} {'Year':<6} {'Metric':<8} {'Actual':<10} {'Predicted':<10} {'Error':<10}")
    print("-" * 70)
    
    for i, sr in enumerate(state_results[:10]):
        print(f"{sr['state']:<20} {sr['year']:<6} NDVI     {sr['veg_actual']:<10} {sr['veg_pred']:<10} {sr['veg_error']:<10}")
        print(f"{'':<20} {'':6} EVI      {sr['crop_actual']:<10} {sr['crop_pred']:<10} {sr['crop_error']:<10}")
        print(f"{'':<20} {'':6} Water    {sr['water_actual']:<10} {sr['water_pred']:<10} {sr['water_error']:<10}")
        if i < 9:
            print("-" * 70)
    
    # Show best and worst predictions
    print("\n" + "=" * 70)
    print("🎯 BEST & WORST PREDICTIONS")
    print("=" * 70)
    
    # Vegetation
    veg_errors = [(sr['state'], sr['year'], sr['veg_error']) for sr in state_results]
    veg_errors.sort(key=lambda x: x[2])
    print("\n📗 Vegetation (NDVI):")
    print(f"  Best:  {veg_errors[0][0]} ({veg_errors[0][1]}) - Error: {veg_errors[0][2]:.4f}")
    print(f"  Worst: {veg_errors[-1][0]} ({veg_errors[-1][1]}) - Error: {veg_errors[-1][2]:.4f}")
    
    # Crop
    crop_errors = [(sr['state'], sr['year'], sr['crop_error']) for sr in state_results]
    crop_errors.sort(key=lambda x: x[2])
    print("\n🌾 Crop Yield (EVI):")
    print(f"  Best:  {crop_errors[0][0]} ({crop_errors[0][1]}) - Error: {crop_errors[0][2]:.4f}")
    print(f"  Worst: {crop_errors[-1][0]} ({crop_errors[-1][1]}) - Error: {crop_errors[-1][2]:.4f}")
    
    # Water
    water_errors = [(sr['state'], sr['year'], sr['water_error']) for sr in state_results]
    water_errors.sort(key=lambda x: x[2])
    print("\n💧 Water Level:")
    print(f"  Best:  {water_errors[0][0]} ({water_errors[0][1]}) - Error: {water_errors[0][2]:.2f}%")
    print(f"  Worst: {water_errors[-1][0]} ({water_errors[-1][1]}) - Error: {water_errors[-1][2]:.2f}%")
    
    print("\n" + "=" * 70)
    print("✅ ACCURACY TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
