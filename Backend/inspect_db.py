"""Inspect database schema."""
import sqlite3

databases = ['processed_data.db', 'pollution.db', 'raw_data.db']

with open('db_schema_output.txt', 'w') as f:
    for db_name in databases:
        f.write(f"\n{'='*50}\n")
        f.write(f"DATABASE: {db_name}\n")
        f.write('='*50 + '\n')
        
        try:
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [t[0] for t in cursor.fetchall()]
            f.write(f"Tables: {tables}\n")
            
            # Get schema for each table
            for table in tables:
                f.write(f"\n--- {table} ---\n")
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                for col in columns:
                    f.write(f"  {col[1]}: {col[2]}\n")
                
                # Get sample row count
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                f.write(f"  Row count: {count}\n")
                
                # Get sample data
                cursor.execute(f"SELECT * FROM {table} LIMIT 2")
                samples = cursor.fetchall()
                if samples:
                    f.write(f"  Sample: {samples[0]}\n")
            
            conn.close()
        except Exception as e:
            f.write(f"Error: {e}\n")

print("Database schema written to db_schema_output.txt")
