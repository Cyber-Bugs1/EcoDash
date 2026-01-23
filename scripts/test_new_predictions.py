"""Test the new prediction models."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ai.environmental_ai import EnvironmentalAISystem

ai = EnvironmentalAISystem()
ai.train_all_models()

print('\n' + '='*60)
print('Testing Predictions')
print('='*60)

# Test vegetation prediction
veg = ai.predict_vegetation(rainfall=1200, temp=28, dry_months=4, evi=0.35)
print(f'\nVegetation Prediction:')
print(f'  NDVI: {veg["predicted_ndvi"]}')
print(f'  Category: {veg["vegetation_category"]}')
print(f'  Recommendations: {veg["recommendations"]}')

# Test crop yield prediction
crop = ai.predict_crop_yield(ndvi=0.5, rainfall=1000, cropland=70, kharif_ndvi=0.55, rabi_ndvi=0.48)
print(f'\nCrop Yield Prediction:')
print(f'  EVI: {crop["predicted_evi"]}')
print(f'  Category: {crop["yield_category"]}')
print(f'  Recommendations: {crop["recommendations"]}')

# Test water prediction
water = ai.predict_water_level(rainfall=1500, ndvi=0.6, temp=25, humidity=70, dry_months=3)
print(f'\nWater Level Prediction:')
print(f'  Surface Water: {water["predicted_surface_water"]}%')
print(f'  Category: {water["water_stress_category"]}')
print(f'  Recommendations: {water["recommendations"]}')

print('\n' + '='*60)
print('All predictions successful!')
print('='*60)
