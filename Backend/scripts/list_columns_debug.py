import sqlite3
import sys
from pathlib import Path

db_path = Path(__file__).parent.parent / "processed_data.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("PRAGMA table_info(WeeklyEnvironmentalData)")
    cols = cursor.fetchall()
    print("WeeklyEnvironmentalData Columns:")
    for c in cols:
        print(f"  {c[1]} ({c[2]})")
except:
    print("Table WeeklyEnvironmentalData not found.")

try:
    cursor.execute("PRAGMA table_info(Water)")
    cols = cursor.fetchall()
    print("\nWater Table Columns:")
    for c in cols:
        print(f"  {c[1]} ({c[2]})")
except:
    pass

conn.close()
