"""Quick database status check."""
import sqlite3

conn = sqlite3.connect('pollution.db')
cursor = conn.cursor()

# Tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]
print("DATABASE TABLES:")
for t in tables:
    print(f"  - {t}")

print()

# Counts
cursor.execute('SELECT COUNT(*) FROM Pollution')
print(f"Pollution records: {cursor.fetchone()[0]}")

cursor.execute('SELECT COUNT(*) FROM Vegetation')
print(f"Vegetation records: {cursor.fetchone()[0]}")

# Sample data
print("\n=== 2023 Top Vegetation States ===")
cursor.execute("""
    SELECT state_name, ndvi_mean, vegetation_health 
    FROM Vegetation 
    WHERE year=2023 
    ORDER BY ndvi_mean DESC 
    LIMIT 5
""")

for state, ndvi, health in cursor.fetchall():
    print(f"  {state}: NDVI={ndvi:.3f} ({health})")

conn.close()
print("\n✓ Database verification complete!")
