import sqlite3

conn = sqlite3.connect('processed_data.db')
cursor = conn.cursor()

# Get tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]
print("Tables:")
for t in tables:
    print(f"  - {t}")

# Check each table
for table in tables:
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"\n=== {table} ===")
    print(f"Columns: {columns}")
    
    # Check for year data
    if 'year' in columns:
        cursor.execute(f"SELECT DISTINCT year FROM {table} ORDER BY year")
        years = [y[0] for y in cursor.fetchall()]
        print(f"Years: {years}")
    
    # Show sample data
    cursor.execute(f"SELECT * FROM {table} LIMIT 2")
    rows = cursor.fetchall()
    if rows:
        print(f"Sample: {rows[0]}")

conn.close()
