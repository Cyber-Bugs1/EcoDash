import sqlite3

conn = sqlite3.connect('processed_data.db')
cursor = conn.cursor()

tables = ['Pollution', 'Vegetation', 'Water', 'Crop']

for table in tables:
    print(f"\n=== {table} ===")
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"Columns: {columns}")
    
    cursor.execute(f"SELECT * FROM {table} LIMIT 1")
    row = cursor.fetchone()
    if row:
        print(f"Sample: {dict(zip(columns, row))}")

conn.close()
