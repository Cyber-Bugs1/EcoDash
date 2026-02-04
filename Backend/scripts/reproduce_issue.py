import sys
from pathlib import Path
import json

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src" / "api"))
sys.path.insert(0, str(project_root))

from main_backend_server import app

def reproduce():
    with app.test_client() as client:
        # Check diverse states
        states = ['Delhi', 'Meghalaya', 'Kerala', 'Maharashtra']
        
        for state in states:
            print(f"\n--- Checking State: {state} ---")
            
            # Check 2025
            r25 = client.post('/api/data', json={'type': 'aod', 'state': state, 'year': 2025})
            d25 = r25.get_json()
            val25 = d25.get('annual_mean', 0)
            
            # Check 2026
            r26 = client.post('/api/data', json={'type': 'aod', 'state': state, 'year': 2026})
            d26 = r26.get_json()
            val26 = d26.get('annual_mean', 0)
            
            print(f"2025: {val25} (Source: {d25.get('monthly_averages', [])[0] if d25.get('monthly_averages') else 'N/A'})")
            print(f"2026: {val26}")
            
            if val25 == 0 and val26 > 0:
                print(f"[FAIL] 2025 is ZERO but 2026 is {val26}")
            elif val25 > 0 and val26 > 0:
                print(f"[PASS] Data present for both.")
            else:
                print(f"[WARN] Data missing for both or other issue.")

if __name__ == "__main__":
    reproduce()
