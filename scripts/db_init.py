"""
Database Initialization Script for Satellite Pollution Data
"""

import sqlite3
import os

# Ensure db directory exists
os.makedirs("db", exist_ok=True)

conn = sqlite3.connect("db/environment.db")
cur = conn.cursor()

# Drop existing table if it exists
cur.execute("DROP TABLE IF EXISTS pollution_data")

# Create simple pollution data table
cur.execute("""
CREATE TABLE pollution_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    state TEXT NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    aod REAL NOT NULL
)
""")

# Create indexes for monthly and yearly queries
cur.execute("CREATE INDEX idx_year ON pollution_data(year)")
cur.execute("CREATE INDEX idx_month ON pollution_data(month)")
cur.execute("CREATE INDEX idx_year_month ON pollution_data(year, month)")
cur.execute("CREATE INDEX idx_state ON pollution_data(state)")

conn.commit()
conn.close()

print("Database initialized: db/environment.db")
print("Table: pollution_data (state, year, month, aod)")
