import sqlite3

conn = sqlite3.connect("db/environment.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS pollution_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    state TEXT,
    year INTEGER,
    month INTEGER,
    aod REAL
)
""")

conn.commit()
conn.close()

print("Database initialized")
