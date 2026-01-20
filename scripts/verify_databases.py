"""Quick database verification after renaming."""
import sqlite3
from pathlib import Path

print("=" * 60)
print("Database Verification")
print("=" * 60)

# Check processed_data.db
processed_db = Path("processed_data.db")
if processed_db.exists():
    print(f"\n✓ {processed_db.name} exists")
    conn = sqlite3.connect(str(processed_db))
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    print(f"  Tables: {', '.join([t[0] for t in cursor.fetchall()])}")
    
    cursor.execute("SELECT COUNT(*) FROM Pollution")
    print(f"  Pollution records: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM Vegetation")
    print(f"  Vegetation records: {cursor.fetchone()[0]}")
    
    conn.close()
else:
    print(f"\n✗ {processed_db.name} not found")

# Check raw_data.db
raw_db = Path("raw_data.db")
if raw_db.exists():
    print(f"\n✓ {raw_db.name} exists")
    conn = sqlite3.connect(str(raw_db))
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]
    print(f"  Tables: {', '.join(tables)}")
    
    if 'raw_pollution_data' in tables:
        cursor.execute("SELECT COUNT(*) FROM raw_pollution_data")
        print(f"  Raw pollution records: {cursor.fetchone()[0]}")
    
    if 'processed_pollution_data' in tables:
        cursor.execute("SELECT COUNT(*) FROM processed_pollution_data")
        print(f"  Processed pollution records: {cursor.fetchone()[0]}")
    
    conn.close()
else:
    print(f"\n✗ {raw_db.name} not found")

print("\n" + "=" * 60)
print("✓ Database verification complete")
print("=" * 60)
