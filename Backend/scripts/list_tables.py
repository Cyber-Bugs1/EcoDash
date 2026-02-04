import sqlite3

conn = sqlite3.connect('processed_data.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]

print("Current tables in database:")
for t in tables:
    print(f"  - {t}")

print(f"\nTotal: {len(tables)} tables")
conn.close()
