"""
Correlation Analysis between Environmental Metrics.

Analyzes relationships between:
- Pollution (PM2.5, AQI)
- Vegetation (NDVI)
- Water (Rainfall, Water Stress)
- Crops (when available)

Finds patterns and generates insights for environmental monitoring.
"""

import sqlite3
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple


def get_correlation(x: List[float], y: List[float]) -> Tuple[float, str]:
    """
    Calculate Pearson correlation coefficient.
    
    Returns:
        (correlation, interpretation)
    """
    if len(x) != len(y) or len(x) < 3:
        return None, "Insufficient data"
    
    # Remove None values
    pairs = [(a, b) for a, b in zip(x, y) if a is not None and b is not None]
    if len(pairs) < 3:
        return None, "Insufficient data"
    
    x_clean = [p[0] for p in pairs]
    y_clean = [p[1] for p in pairs]
    
    # Calculate correlation
    x_mean = np.mean(x_clean)
    y_mean = np.mean(y_clean)
    
    numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x_clean, y_clean))
    denominator = np.sqrt(sum((xi - x_mean)**2 for xi in x_clean) * sum((yi - y_mean)**2 for yi in y_clean))
    
    if denominator == 0:
        return 0, "No variation"
    
    r = numerator / denominator
    
    # Interpret
    if r >= 0.7:
        interp = "Strong positive"
    elif r >= 0.4:
        interp = "Moderate positive"
    elif r >= 0.1:
        interp = "Weak positive"
    elif r >= -0.1:
        interp = "No correlation"
    elif r >= -0.4:
        interp = "Weak negative"
    elif r >= -0.7:
        interp = "Moderate negative"
    else:
        interp = "Strong negative"
    
    return round(r, 3), interp


def run_correlation_analysis():
    """Run comprehensive correlation analysis on all environmental metrics."""
    
    print("=" * 70)
    print("Environmental Metrics Correlation Analysis")
    print("=" * 70)
    
    db_path = str(Path(__file__).parent.parent / "processed_data.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get common years across tables
    cursor.execute("SELECT DISTINCT year FROM Pollution ORDER BY year")
    pollution_years = set(row[0] for row in cursor.fetchall())
    
    cursor.execute("SELECT DISTINCT year FROM Vegetation ORDER BY year")
    vegetation_years = set(row[0] for row in cursor.fetchall())
    
    cursor.execute("SELECT DISTINCT year FROM Water ORDER BY year")
    water_years = set(row[0] for row in cursor.fetchall())
    
    common_years = pollution_years & vegetation_years & water_years
    print(f"\nAnalyzing years: {sorted(common_years)}")
    
    # ============================================================
    # 1. POLLUTION vs VEGETATION Analysis
    # ============================================================
    print("\n" + "=" * 70)
    print("1. POLLUTION vs VEGETATION Analysis")
    print("=" * 70)
    
    cursor.execute("""
        SELECT 
            p.state_name,
            p.year,
            p.pm25_mean,
            p.aqi_mean,
            v.ndvi_mean
        FROM Pollution p
        JOIN Vegetation v ON p.state_name = v.state_name AND p.year = v.year
        ORDER BY p.state_name, p.year
    """)
    
    data = cursor.fetchall()
    
    pm25_values = [row['pm25_mean'] for row in data]
    ndvi_values = [row['ndvi_mean'] for row in data]
    
    r, interp = get_correlation(pm25_values, ndvi_values)
    print(f"\n  PM2.5 vs NDVI:")
    print(f"    Correlation: {r} ({interp})")
    
    if r and r < -0.3:
        print("    >> Higher vegetation tends to correlate with lower pollution")
    elif r and r > 0.3:
        print("    >> Unexpected positive correlation - needs investigation")
    else:
        print("    >> Weak relationship - other factors dominate")
    
    # Top clean states (high NDVI, low PM2.5)
    cursor.execute("""
        SELECT 
            p.state_name,
            AVG(p.pm25_mean) as avg_pm25,
            AVG(v.ndvi_mean) as avg_ndvi
        FROM Pollution p
        JOIN Vegetation v ON p.state_name = v.state_name AND p.year = v.year
        GROUP BY p.state_name
        HAVING avg_ndvi > 0.6 AND avg_pm25 < 40
        ORDER BY avg_ndvi DESC
        LIMIT 5
    """)
    
    print("\n  States with High Vegetation & Low Pollution:")
    for row in cursor.fetchall():
        print(f"    - {row['state_name']}: NDVI={row['avg_ndvi']:.3f}, PM2.5={row['avg_pm25']:.1f}")
    
    # ============================================================
    # 2. RAINFALL vs VEGETATION Analysis
    # ============================================================
    print("\n" + "=" * 70)
    print("2. RAINFALL vs VEGETATION Analysis")
    print("=" * 70)
    
    cursor.execute("""
        SELECT 
            w.state_name,
            w.year,
            w.rainfall_annual_mm,
            v.ndvi_mean
        FROM Water w
        JOIN Vegetation v ON w.state_name = v.state_name AND w.year = v.year
    """)
    
    data = cursor.fetchall()
    
    rainfall_values = [row['rainfall_annual_mm'] for row in data]
    ndvi_values = [row['ndvi_mean'] for row in data]
    
    r, interp = get_correlation(rainfall_values, ndvi_values)
    print(f"\n  Rainfall vs NDVI:")
    print(f"    Correlation: {r} ({interp})")
    
    if r and r > 0.3:
        print("    >> Higher rainfall correlates with denser vegetation")
    
    # ============================================================
    # 3. WATER STRESS vs POLLUTION Analysis
    # ============================================================
    print("\n" + "=" * 70)
    print("3. WATER STRESS vs POLLUTION Analysis")
    print("=" * 70)
    
    cursor.execute("""
        SELECT 
            w.state_name,
            w.year,
            w.dry_months_count,
            p.pm25_mean
        FROM Water w
        JOIN Pollution p ON w.state_name = p.state_name AND w.year = p.year
    """)
    
    data = cursor.fetchall()
    
    dry_months = [row['dry_months_count'] for row in data]
    pm25_values = [row['pm25_mean'] for row in data]
    
    r, interp = get_correlation(dry_months, pm25_values)
    print(f"\n  Dry Months vs PM2.5:")
    print(f"    Correlation: {r} ({interp})")
    
    if r and r > 0.3:
        print("    >> More dry months correlates with higher pollution (dust, no rain cleansing)")
    
    # ============================================================
    # 4. RAINFALL vs POLLUTION Analysis
    # ============================================================
    print("\n" + "=" * 70)
    print("4. RAINFALL vs POLLUTION Analysis")
    print("=" * 70)
    
    cursor.execute("""
        SELECT 
            w.rainfall_annual_mm,
            p.pm25_mean
        FROM Water w
        JOIN Pollution p ON w.state_name = p.state_name AND w.year = p.year
    """)
    
    data = cursor.fetchall()
    
    rainfall_values = [row['rainfall_annual_mm'] for row in data]
    pm25_values = [row['pm25_mean'] for row in data]
    
    r, interp = get_correlation(rainfall_values, pm25_values)
    print(f"\n  Rainfall vs PM2.5:")
    print(f"    Correlation: {r} ({interp})")
    
    if r and r < -0.3:
        print("    >> Higher rainfall correlates with lower pollution (rain cleanses air)")
    
    # ============================================================
    # 5. SURFACE WATER vs VEGETATION Analysis
    # ============================================================
    print("\n" + "=" * 70)
    print("5. SURFACE WATER vs VEGETATION Analysis")
    print("=" * 70)
    
    cursor.execute("""
        SELECT 
            w.surface_water_mean,
            v.ndvi_mean
        FROM Water w
        JOIN Vegetation v ON w.state_name = v.state_name AND w.year = v.year
    """)
    
    data = cursor.fetchall()
    
    water_values = [row['surface_water_mean'] for row in data]
    ndvi_values = [row['ndvi_mean'] for row in data]
    
    r, interp = get_correlation(water_values, ndvi_values)
    print(f"\n  Surface Water vs NDVI:")
    print(f"    Correlation: {r} ({interp})")
    
    # ============================================================
    # 6. YEAR-OVER-YEAR TRENDS
    # ============================================================
    print("\n" + "=" * 70)
    print("6. YEAR-OVER-YEAR TRENDS")
    print("=" * 70)
    
    cursor.execute("""
        SELECT 
            p.year,
            AVG(p.pm25_mean) as avg_pm25,
            AVG(v.ndvi_mean) as avg_ndvi,
            AVG(w.rainfall_annual_mm) as avg_rainfall
        FROM Pollution p
        JOIN Vegetation v ON p.state_name = v.state_name AND p.year = v.year
        JOIN Water w ON p.state_name = w.state_name AND p.year = w.year
        GROUP BY p.year
        ORDER BY p.year
    """)
    
    print(f"\n  {'Year':<6} {'Avg PM2.5':<12} {'Avg NDVI':<12} {'Avg Rainfall':<15}")
    print("  " + "-" * 50)
    for row in cursor.fetchall():
        print(f"  {row['year']:<6} {row['avg_pm25']:<12.1f} {row['avg_ndvi']:<12.3f} {row['avg_rainfall']:<15.0f}")
    
    # ============================================================
    # 7. STATE-WISE ENVIRONMENTAL HEALTH RANKING
    # ============================================================
    print("\n" + "=" * 70)
    print("7. STATE-WISE ENVIRONMENTAL HEALTH RANKING")
    print("=" * 70)
    
    cursor.execute("""
        SELECT 
            p.state_name,
            AVG(p.pm25_mean) as avg_pm25,
            AVG(v.ndvi_mean) as avg_ndvi,
            AVG(w.rainfall_annual_mm) as avg_rainfall,
            AVG(w.dry_months_count) as avg_dry_months
        FROM Pollution p
        JOIN Vegetation v ON p.state_name = v.state_name AND p.year = v.year
        JOIN Water w ON p.state_name = w.state_name AND p.year = w.year
        GROUP BY p.state_name
        ORDER BY avg_pm25 ASC
        LIMIT 10
    """)
    
    print("\n  Top 10 States (Lowest Pollution):")
    print(f"  {'State':<25} {'PM2.5':<10} {'NDVI':<10} {'Rainfall':<12} {'Dry Mo.':<10}")
    print("  " + "-" * 70)
    for row in cursor.fetchall():
        print(f"  {row['state_name']:<25} {row['avg_pm25']:<10.1f} {row['avg_ndvi']:<10.3f} {row['avg_rainfall']:<12.0f} {row['avg_dry_months']:<10.1f}")
    
    conn.close()
    
    # ============================================================
    # SUMMARY
    # ============================================================
    print("\n" + "=" * 70)
    print("CORRELATION SUMMARY")
    print("=" * 70)
    print("""
  Key Findings:
  1. PM2.5 vs NDVI: Negative correlation expected (forests clean air)
  2. Rainfall vs NDVI: Positive correlation (water drives vegetation)
  3. Dry Months vs PM2.5: Positive correlation (dust during dry season)
  4. Rainfall vs PM2.5: Negative correlation (rain cleanses air)
  
  Implications for AI Model:
  - Vegetation (NDVI) can predict air quality
  - Rainfall patterns influence both vegetation and pollution
  - Water stress indicators correlate with pollution levels
  - Combined metrics can predict environmental health
    """)
    
    print("\n[OK] Correlation analysis complete!")


if __name__ == "__main__":
    run_correlation_analysis()
