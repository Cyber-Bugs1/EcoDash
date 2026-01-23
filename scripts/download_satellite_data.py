"""
Download Actual Satellite Data from NASA FIRMS and Other APIs

Data Sources:
1. NASA FIRMS - Fire/Active Fire data (VIIRS, MODIS)
2. OpenAQ - Air Quality monitoring data
3. ERA5 (via CDS) - Weather data

Set your API keys in environment variables or .env file:
- FIRMS_API_KEY: Get from https://firms.modaps.eosdis.nasa.gov/api/area/
- OPENAQ_API_KEY: Get from https://openaq.org/

Usage:
    python download_satellite_data.py --key YOUR_FIRMS_KEY
"""

import os
import sys
import sqlite3
import argparse
from datetime import datetime, timedelta
from pathlib import Path

try:
    import requests
except ImportError:
    import subprocess
    subprocess.run(['uv', 'add', 'requests'])
    import requests

# India bounding box (approximate)
INDIA_BBOX = {
    'west': 68.0,
    'south': 6.0,
    'east': 97.5,
    'north': 37.5
}

# State capitals for location-based queries
STATE_LOCATIONS = {
    'Delhi': (28.6139, 77.2090),
    'Maharashtra': (19.0760, 72.8777),  # Mumbai
    'Uttar Pradesh': (26.8467, 80.9462),  # Lucknow
    'Bihar': (25.5941, 85.1376),  # Patna
    'West Bengal': (22.5726, 88.3639),  # Kolkata
    'Tamil Nadu': (13.0827, 80.2707),  # Chennai
    'Karnataka': (12.9716, 77.5946),  # Bangalore
    'Gujarat': (23.0225, 72.5714),  # Ahmedabad
    'Rajasthan': (26.9124, 75.7873),  # Jaipur
    'Madhya Pradesh': (23.2599, 77.4126),  # Bhopal
    'Andhra Pradesh': (17.6868, 83.2185),  # Visakhapatnam
    'Kerala': (9.9312, 76.2673),  # Kochi
    'Punjab': (30.9000, 75.8573),  # Ludhiana
    'Haryana': (28.4595, 77.0266),  # Gurugram
    'Jharkhand': (23.3441, 85.3096),  # Ranchi
    'Chhattisgarh': (21.2514, 81.6296),  # Raipur
    'Odisha': (20.2961, 85.8245),  # Bhubaneswar
    'Assam': (26.1445, 91.7362),  # Guwahati
    'Uttarakhand': (30.3165, 78.0322),  # Dehradun
    'Himachal Pradesh': (31.1048, 77.1734),  # Shimla
}


def create_download_tables(db_path):
    """Create tables for downloaded satellite data."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # NASA FIRMS fire data
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS SatelliteFireData (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            latitude REAL,
            longitude REAL,
            brightness REAL,
            scan REAL,
            track REAL,
            acq_date TEXT,
            acq_time TEXT,
            satellite TEXT,
            confidence TEXT,
            version TEXT,
            bright_t31 REAL,
            frp REAL,
            daynight TEXT,
            state_name TEXT,
            downloaded_at TEXT,
            UNIQUE(latitude, longitude, acq_date, acq_time)
        )
    """)
    
    # Air quality from OpenAQ
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS SatelliteAQData (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location TEXT,
            state_name TEXT,
            parameter TEXT,
            value REAL,
            unit TEXT,
            date TEXT,
            latitude REAL,
            longitude REAL,
            source TEXT,
            downloaded_at TEXT
        )
    """)
    
    conn.commit()
    conn.close()
    print("[OK] Download tables created")


def download_firms_data(api_key, days=7, source='VIIRS_SNPP_NRT'):
    """
    Download fire data from NASA FIRMS API.
    
    Args:
        api_key: Your FIRMS API key
        days: Number of days to fetch (1, 2, 7, 10)
        source: VIIRS_SNPP_NRT, VIIRS_NOAA20_NRT, MODIS_NRT, etc.
    
    Returns:
        List of fire records
    """
    # NASA FIRMS API endpoints
    # Country code for India: IND
    url = f"https://firms.modaps.eosdis.nasa.gov/api/country/csv/{api_key}/{source}/IND/{days}"
    
    print(f"\n[*] Downloading {source} data for India ({days} days)...")
    print(f"    URL: {url[:80]}...")
    
    try:
        response = requests.get(url, timeout=60)
        
        if response.status_code == 200:
            lines = response.text.strip().split('\n')
            if len(lines) > 1:
                headers = lines[0].split(',')
                records = []
                
                for line in lines[1:]:
                    values = line.split(',')
                    if len(values) >= len(headers):
                        record = dict(zip(headers, values))
                        records.append(record)
                
                print(f"    [OK] Downloaded {len(records)} fire records")
                return records
            else:
                print("    [!] No data in response")
                return []
        else:
            print(f"    [ERROR] HTTP {response.status_code}: {response.text[:200]}")
            return []
            
    except requests.exceptions.Timeout:
        print("    [ERROR] Request timed out")
        return []
    except Exception as e:
        print(f"    [ERROR] {e}")
        return []


def download_firms_area(api_key, days=1, source='VIIRS_SNPP_NRT'):
    """
    Download fire data for a specific area (world or custom bbox).
    """
    # Using area endpoint for more flexibility
    url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{api_key}/{source}/world/{days}"
    
    print(f"\n[*] Downloading {source} global data ({days} day)...")
    
    try:
        response = requests.get(url, timeout=120)
        
        if response.status_code == 200:
            lines = response.text.strip().split('\n')
            if len(lines) > 1:
                headers = lines[0].split(',')
                records = []
                
                for line in lines[1:]:
                    values = line.split(',')
                    if len(values) >= len(headers):
                        record = dict(zip(headers, values))
                        # Filter for India bbox
                        try:
                            lat = float(record.get('latitude', 0))
                            lon = float(record.get('longitude', 0))
                            if (INDIA_BBOX['south'] <= lat <= INDIA_BBOX['north'] and
                                INDIA_BBOX['west'] <= lon <= INDIA_BBOX['east']):
                                records.append(record)
                        except:
                            pass
                
                print(f"    [OK] Downloaded {len(records)} fire records for India region")
                return records
        else:
            print(f"    [ERROR] HTTP {response.status_code}")
            return []
            
    except Exception as e:
        print(f"    [ERROR] {e}")
        return []


def assign_state(lat, lon):
    """Assign a state based on proximity to state capitals."""
    min_dist = float('inf')
    nearest_state = 'Unknown'
    
    for state, (slat, slon) in STATE_LOCATIONS.items():
        dist = ((lat - slat) ** 2 + (lon - slon) ** 2) ** 0.5
        if dist < min_dist:
            min_dist = dist
            nearest_state = state
    
    return nearest_state


def save_fire_data(db_path, records):
    """Save fire data to database."""
    if not records:
        return 0
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    count = 0
    for rec in records:
        try:
            lat = float(rec.get('latitude', 0))
            lon = float(rec.get('longitude', 0))
            state = assign_state(lat, lon)
            
            cursor.execute("""
                INSERT OR IGNORE INTO SatelliteFireData
                (latitude, longitude, brightness, scan, track, acq_date, acq_time,
                 satellite, confidence, version, bright_t31, frp, daynight,
                 state_name, downloaded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lat, lon,
                float(rec.get('brightness', 0) or 0),
                float(rec.get('scan', 0) or 0),
                float(rec.get('track', 0) or 0),
                rec.get('acq_date', ''),
                rec.get('acq_time', ''),
                rec.get('satellite', ''),
                rec.get('confidence', ''),
                rec.get('version', ''),
                float(rec.get('bright_t31', 0) or 0),
                float(rec.get('frp', 0) or 0),
                rec.get('daynight', ''),
                state,
                datetime.now().isoformat()
            ))
            count += 1
        except Exception as e:
            pass
    
    conn.commit()
    conn.close()
    
    print(f"    [OK] Saved {count} records to database")
    return count


def download_openaq_data(state, days=7):
    """
    Download air quality data from OpenAQ API (v3).
    """
    lat, lon = STATE_LOCATIONS.get(state, (20.5937, 78.9629))
    
    url = "https://api.openaq.org/v3/locations"
    params = {
        'limit': 100,
        'country': 'IN',
        'radius': 100000,  # 100km radius
        'coordinates': f"{lat},{lon}"
    }
    
    headers = {
        'Accept': 'application/json',
        'User-Agent': 'Environmental-AI-Project/2.0'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data.get('results', [])
        return []
    except:
        return []


def main():
    parser = argparse.ArgumentParser(description='Download satellite data from NASA FIRMS')
    parser.add_argument('--key', '-k', type=str, required=True,
                        help='NASA FIRMS API key')
    parser.add_argument('--days', '-d', type=int, default=7,
                        help='Number of days to download (1, 2, 7, 10)')
    parser.add_argument('--source', '-s', type=str, default='VIIRS_SNPP_NRT',
                        choices=['VIIRS_SNPP_NRT', 'VIIRS_NOAA20_NRT', 'MODIS_NRT'],
                        help='Data source satellite')
    
    args = parser.parse_args()
    
    db_path = str(Path(__file__).parent.parent / "processed_data.db")
    
    print("=" * 70)
    print("NASA FIRMS Satellite Data Download")
    print("=" * 70)
    print(f"\nAPI Key: {args.key[:8]}...{args.key[-4:]}")
    print(f"Source: {args.source}")
    print(f"Days: {args.days}")
    print(f"Database: {db_path}")
    
    # Create tables
    create_download_tables(db_path)
    
    # Download FIRMS fire data (country-specific for India)
    print("\n" + "=" * 70)
    print("Downloading NASA FIRMS Fire Data")
    print("=" * 70)
    
    fire_records = download_firms_data(args.key, args.days, args.source)
    
    if fire_records:
        save_fire_data(db_path, fire_records)
    else:
        print("\n[!] No fire data downloaded. Trying area endpoint...")
        fire_records = download_firms_area(args.key, min(args.days, 2), args.source)
        if fire_records:
            save_fire_data(db_path, fire_records)
    
    # Summary
    print("\n" + "=" * 70)
    print("Download Summary")
    print("=" * 70)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM SatelliteFireData")
    fire_count = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT state_name, COUNT(*), ROUND(AVG(frp), 1) as avg_frp
        FROM SatelliteFireData
        GROUP BY state_name
        ORDER BY COUNT(*) DESC
        LIMIT 10
    """)
    
    print(f"\nTotal fire records: {fire_count}")
    print("\nTop 10 states by fire activity:")
    print(f"{'State':<20} {'Count':<10} {'Avg FRP'}")
    print("-" * 40)
    for row in cursor.fetchall():
        print(f"{row[0]:<20} {row[1]:<10} {row[2] or 0:.1f}")
    
    conn.close()
    
    print("\n" + "=" * 70)
    print("[OK] Satellite data download complete!")
    print("=" * 70)
    print("\nTo download more data sources, you can also use:")
    print("  - ERA5 Climate Data: https://cds.climate.copernicus.eu/")
    print("  - Sentinel-5P: https://sentinel.esa.int/web/sentinel/missions/sentinel-5p")
    print("  - MODIS AOD: https://ladsweb.modaps.eosdis.nasa.gov/")


if __name__ == "__main__":
    main()
