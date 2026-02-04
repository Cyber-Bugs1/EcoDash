import sqlite3

conn = sqlite3.connect('processed_data.db')
cursor = conn.cursor()

# Drop RefreshTokens
cursor.execute("DROP TABLE IF EXISTS RefreshTokens")
conn.commit()
print("Dropped: RefreshTokens")

# Show remaining tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
remaining = [t[0] for t in cursor.fetchall()]
print(f"Remaining tables: {remaining}")

conn.close()
