import sys
from pathlib import Path
import json

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src" / "api"))
sys.path.insert(0, str(project_root))

from main_backend_server import app

def verify_high_yield():
    with app.test_client() as client:
        print("--- Checking Punjab Yield (Goal: 3-5+ t/ha) ---")
        
        # 2025 (Database - Low?) vs 2026 (Predicted - Should be High?)
        # Actually both should be High because I regenerated the DB.
        
        # 2026 (Predicted)
        r26 = client.post('/api/data', json={'type': 'crop_yield', 'state': 'Punjab', 'year': 2026})
        print(f"Status: {r26.status_code}")
        d26 = r26.get_json()
        
        if d26:
            print(f"2026 Avg Yield: {d26.get('annual_mean')} (Max: {d26.get('annual_max')}) Source: {d26.get('source')}")
            if d26.get('annual_max', 0) > 10.0:
                print("[PASS] 2026 Yield is very high.")
            else:
                print("[FAIL] 2026 Yield is still low.")
        else:
            print("[ERROR] Could not decode JSON")

if __name__ == "__main__":
    verify_high_yield()
