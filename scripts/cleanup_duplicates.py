"""
Remove duplicate vegetation data and reload fresh 2023 data.
"""

import sqlite3
from pathlib import Path

db_path = str(Path(__file__).parent.parent / "pollution.db")

print("=" * 60)
print("Cleaning Duplicate Vegetation Data")
print("=" * 60)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check current counts
cursor.execute("SELECT COUNT(*) FROM Vegetation")
before_count = cursor.fetchone()[0]
print(f"\nRecords before cleanup: {before_count}")

# Remove all 2023 and 2024 data (will reload fresh)
cursor.execute("DELETE FROM Vegetation WHERE year IN (2023, 2024)")
deleted = cursor.rowcount
print(f"Deleted {deleted} records for 2023-2024")

# Check for any duplicates in remaining data
cursor.execute("""
    SELECT state_name, year, COUNT(*) as count
    FROM Vegetation
    GROUP BY state_name, year
    HAVING count > 1
""")

duplicates = cursor.fetchall()
if duplicates:
    print(f"\nFound {len(duplicates)} duplicate groups:")
    for state, year, count in duplicates:
        print(f"  {state} {year}: {count} copies")
        # Keep only the most recent one
        cursor.execute("""
            DELETE FROM Vegetation 
            WHERE id NOT IN (
                SELECT MAX(id) 
                FROM Vegetation 
                WHERE state_name = ? AND year = ?
            ) AND state_name = ? AND year = ?
        """, (state, year, state, year))
    print(f"  Removed {cursor.rowcount} duplicate records")

conn.commit()

# Final count
cursor.execute("SELECT COUNT(*) FROM Vegetation")
after_count = cursor.fetchone()[0]

print(f"\nRecords after cleanup: {after_count}")
print(f"Total removed: {before_count - after_count}")

conn.close()

print("\n✓ Database cleanup complete!")
print("\nNow run: uv run python scripts/load_vegetation_data.py")
