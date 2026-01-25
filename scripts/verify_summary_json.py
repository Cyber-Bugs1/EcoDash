import sys
from pathlib import Path
import json

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src" / "api"))
sys.path.insert(0, str(project_root))

from main_backend_server import app

def verify_summary():
    with app.test_client() as client:
        print("--- Verifying Dashboard Summary Request (Delhi) ---")
        
        # State-only request (triggers summary logic)
        r = client.get('/api/data?state=Delhi')
        print(f"Status Code: {r.status_code}")
        
        if r.status_code == 200:
            data = r.get_json()
            print("Successfully received JSON response.")
            print(f"Summary Keys: {list(data.get('summary', {}).keys())}")
            # Check a specific value for Crop Yield (the one that failed before)
            crop_yield_summary = data.get('summary', {}).get('Crop Yield', {})
            print(f"Crop Yield Mean Value: {crop_yield_summary.get('mean_value')}")
            print(f"Crop Yield Pct of Max: {crop_yield_summary.get('mean_percentage_of_max')}")
            print("[PASS] JSON serialization issue resolved.")
        else:
            print("[FAIL] Request failed with status code", r.status_code)
            print(f"Response Data: {r.data[:500]}")

if __name__ == "__main__":
    verify_summary()
