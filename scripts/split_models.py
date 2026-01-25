import pickle
from pathlib import Path
import os

def split_models():
    # Paths
    project_root = Path(__file__).parent.parent
    original_model_path = project_root / "models" / "unified_predictor.pkl"
    target_dir = project_root / "models" / "targets"
    target_dir.mkdir(parents=True, exist_ok=True)

    if not original_model_path.exists():
        print(f"[ERROR] Source model not found: {original_model_path}")
        return

    print(f"[*] Reading unified model: {original_model_path}")
    with open(original_model_path, 'rb') as f:
        data = pickle.load(f)

    models = data.get('models', {})
    scalers = data.get('scalers', {})
    feature_names = data.get('feature_names', {})
    targets = data.get('trained_targets', [])

    print(f"[*] Found {len(targets)} trained targets.")

    for target in targets:
        target_file = target_dir / f"{target}.pkl"
        
        # Bundle data specific to this target
        model_data = {
            'model': models.get(target),
            'scaler': scalers.get(target),
            'feature_names': feature_names.get(target)
        }
        
        with open(target_file, 'wb') as f:
            pickle.dump(model_data, f)
        
        # Check size
        size_kb = os.path.getsize(target_file) / 1024
        print(f"  [OK] Saved {target:<15} -> {target_file.name} ({size_kb:.1f} KB)")

    print(f"\n[DONE] Split complete. Models are in {target_dir}")

if __name__ == "__main__":
    split_models()
