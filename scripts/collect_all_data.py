"""
Master Data Collection Pipeline

This script runs all data collection scripts in sequence:
1. OpenAQ air quality data (monthly PM2.5, AQI)
2. Open-Meteo weather data (daily/monthly temp, humidity, rain)
3. NASA FIRMS fire data (fire events)
4. Process and merge all data

Run this single script to collect all enhanced environmental data.
"""

import subprocess
import sys
from pathlib import Path


def run_script(script_name, description):
    """Run a Python script and return success status."""
    script_path = Path(__file__).parent / script_name
    
    print(f"\n{'='*70}")
    print(f"Running: {description}")
    print(f"Script: {script_name}")
    print(f"{'='*70}")
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=False,
            text=True,
            timeout=1800  # 30 minute timeout
        )
        
        if result.returncode == 0:
            print(f"\n✅ {description} - Complete!")
            return True
        else:
            print(f"\n❌ {description} - Failed with code {result.returncode}")
            return False
    except subprocess.TimeoutExpired:
        print(f"\n⏰ {description} - Timeout!")
        return False
    except Exception as e:
        print(f"\n❌ {description} - Error: {e}")
        return False


def main():
    print("=" * 70)
    print("🌍 Enhanced Environmental Data Collection Pipeline")
    print("=" * 70)
    print("\nThis will collect data from multiple sources:")
    print("  1. OpenAQ - Air quality data (PM2.5, AQI, NO2, O3)")
    print("  2. Open-Meteo - Weather data (temperature, humidity, rain)")
    print("  3. NASA FIRMS - Fire data (forest fires, stubble burning)")
    print("  4. Process and merge all data")
    print("\n⚠️  Note: This may take 15-30 minutes depending on network speed.")
    
    # Ask for confirmation
    response = input("\nProceed with data collection? (y/n): ").strip().lower()
    if response != 'y':
        print("Cancelled.")
        return
    
    results = {}
    
    # 1. Collect OpenAQ data
    results['openaq'] = run_script(
        'collect_openaq_data.py',
        'OpenAQ Air Quality Data Collection'
    )
    
    # 2. Collect weather data
    results['weather'] = run_script(
        'collect_weather_data.py',
        'Open-Meteo Weather Data Collection'
    )
    
    # 3. Collect fire data
    results['fires'] = run_script(
        'collect_fire_data.py',
        'NASA FIRMS Fire Data Collection'
    )
    
    # 4. Process and merge data
    results['process'] = run_script(
        'process_enhanced_data.py',
        'Process and Merge Enhanced Data'
    )
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Collection Summary")
    print("=" * 70)
    
    for task, success in results.items():
        status = "✅ Success" if success else "❌ Failed"
        print(f"  {task.title()}: {status}")
    
    all_success = all(results.values())
    
    if all_success:
        print("\n🎉 All data collection tasks completed successfully!")
        print("\nNext steps:")
        print("  1. Run 'python scripts/train_ai_models.py' to retrain with enhanced data")
        print("  2. Run 'python scripts/predict_environment.py' for improved predictions")
    else:
        print("\n⚠️  Some tasks failed. Check the output above for details.")
        print("You can run individual scripts to retry failed tasks.")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
