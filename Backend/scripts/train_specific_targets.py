import sys
from pathlib import Path
import os

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

from unified_predictor import UnifiedEnvironmentalPredictor, PREDICTION_TARGETS

def train_selected():
    print("="*60)
    print("Training ONLY Water, Vegetation, and Crop models")
    print("="*60)
    
    db_path = str(project_root / "processed_data.db")
    model_path = project_root / "models" / "unified_predictor.pkl"
    
    predictor = UnifiedEnvironmentalPredictor(db_path)
    
    # Load existing models if available (to preserve Pollution models)
    if model_path.exists():
        try:
            print(f"Loading existing models from {model_path}...")
            predictor.load(str(model_path))
        except Exception as e:
            print(f"Could not load existing models: {e}. Starting fresh.")
    
    # Targets to retrain
    targets = [
        'groundwater', 
        'water_stress', 
        'surface_water',
        'ndvi', 
        'crop_growth', 
        'crop_yield',
        # Adding 'rainfall' as it impacts others
        'rainfall' 
    ]
    
    for t in targets:
        if t in PREDICTION_TARGETS:
            try:
                predictor.train(t, verbose=True)
            except Exception as e:
                print(f"[ERROR] Failed to train {t}: {e}")
        else:
            print(f"[WARN] Target {t} not found in definitions.")
            
    # Save back
    print("Saving models...")
    predictor.save(str(model_path))
    print("Done!")

if __name__ == "__main__":
    train_selected()
