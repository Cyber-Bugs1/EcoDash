"""
Train and test environmental AI models.

This script:
1. Trains PM2.5 prediction model
2. Trains environmental health classifier
3. Shows feature importance
4. Runs example predictions
5. Saves trained models
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai import EnvironmentalAISystem


def main():
    print("=" * 70)
    print("Environmental AI Modeling System")
    print("=" * 70)
    
    # Initialize AI system
    db_path = str(Path(__file__).parent.parent / "processed_data.db")
    ai = EnvironmentalAISystem(db_path)
    
    # Train all models
    results = ai.train_all_models()
    
    # Save models
    models_dir = Path(__file__).parent.parent / "models"
    ai.save_models(str(models_dir))
    
    # Example predictions for different scenarios
    print("\n" + "=" * 70)
    print("Example Predictions for Different Environmental Scenarios")
    print("=" * 70)
    
    scenarios = [
        {
            'name': 'Forest State (Low Pollution Expected)',
            'ndvi': 0.75,
            'rainfall': 2500,
            'dry_months': 3,
            'cropland': 10,
            'evi': 0.5,
            'surface_water': 5.0
        },
        {
            'name': 'Agricultural State (Moderate Pollution)',
            'ndvi': 0.45,
            'rainfall': 1200,
            'dry_months': 6,
            'cropland': 85,
            'evi': 0.35,
            'surface_water': 2.0
        },
        {
            'name': 'Industrial/Urban Area (High Pollution)',
            'ndvi': 0.30,
            'rainfall': 800,
            'dry_months': 8,
            'cropland': 40,
            'evi': 0.25,
            'surface_water': 1.0
        },
        {
            'name': 'Water-Stressed Region',
            'ndvi': 0.25,
            'rainfall': 400,
            'dry_months': 9,
            'cropland': 60,
            'evi': 0.2,
            'surface_water': 0.5
        }
    ]
    
    for scenario in scenarios:
        print(f"\n--- {scenario['name']} ---")
        result = ai.predict_pm25(
            ndvi=scenario['ndvi'],
            rainfall=scenario['rainfall'],
            dry_months=scenario['dry_months'],
            cropland=scenario['cropland'],
            evi=scenario['evi'],
            surface_water=scenario['surface_water']
        )
        print(f"  Predicted PM2.5: {result['predicted_pm25']} ug/m3")
        print(f"  Health Category: {result['health_category']}")
        print(f"  Health Probabilities:")
        for cat, prob in sorted(result['health_probabilities'].items(), 
                                 key=lambda x: x[1], reverse=True):
            print(f"    - {cat}: {prob:.1%}")
        print(f"  Recommendations:")
        for rec in result['recommendations']:
            print(f"    * {rec}")
    
    # Analyze specific states
    print("\n" + "=" * 70)
    print("State-wise Environmental Analysis (2023)")
    print("=" * 70)
    
    states_to_analyze = ['Delhi', 'Kerala', 'Punjab', 'Mizoram', 'Bihar']
    
    for state in states_to_analyze:
        print(f"\n--- {state} ---")
        analysis = ai.analyze_state(state, 2023)
        
        if 'error' not in analysis:
            print(f"  PM2.5: {analysis.get('pm25_mean', 'N/A')} ug/m3")
            print(f"  AQI: {analysis.get('aqi_mean', 'N/A')} ({analysis.get('aqi_category', 'N/A')})")
            print(f"  NDVI: {analysis.get('ndvi_mean', 'N/A')}")
            print(f"  Rainfall: {analysis.get('rainfall_annual_mm', 'N/A')} mm")
            print(f"  Cropland: {analysis.get('cropland_percent', 'N/A')}%")
            
            if 'ai_prediction' in analysis:
                pred = analysis['ai_prediction']
                print(f"  AI Predicted PM2.5: {pred['predicted_pm25']} ug/m3")
                print(f"  AI Health Category: {pred['health_category']}")
        else:
            print(f"  {analysis['error']}")
    
    print("\n" + "=" * 70)
    print("[OK] AI Modeling Complete!")
    print("=" * 70)
    print(f"\nModels saved to: {models_dir}")
    print("To use models in your application:")
    print("  from src.ai import EnvironmentalAISystem")
    print("  ai = EnvironmentalAISystem('processed_data.db')")
    print("  ai.train_all_models()")
    print("  result = ai.predict_pm25(ndvi=0.5, rainfall=1500, ...)")


if __name__ == "__main__":
    main()
