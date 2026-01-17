import pandas as pd
import sqlite3
import glob
import os
from collections import defaultdict

conn = sqlite3.connect("db/environment.db")
cur = conn.cursor()

# Dictionary to track records per year and month
records_by_year_month = defaultdict(lambda: defaultdict(int))

# Iterate over all pollution data files (handles any year)
for file in glob.glob("data/raw/India_Pollution_AOD_*.csv"):
    filename = os.path.basename(file)
    # Extract year and month from filename pattern: India_Pollution_AOD_YYYY_MM.csv
    parts = filename.replace(".csv", "").split("_")
    year = int(parts[3])  # YYYY
    month = int(parts[4])  # MM

    print(f"Processing: {filename} (Year: {year}, Month: {month})")

    df = pd.read_csv(file)[["ADM1_NAME", "mean"]].dropna()

    record_count = 0
    for _, row in df.iterrows():
        cur.execute("""
            INSERT INTO pollution_data (state, year, month, aod)
            VALUES (?, ?, ?, ?)
        """, (row["ADM1_NAME"], year, month, row["mean"]))
        record_count += 1

    records_by_year_month[year][month] = record_count

conn.commit()
conn.close()

# Print summary of stored data
print("\n" + "=" * 50)
print("Data Extraction Summary")
print("=" * 50)

for year in sorted(records_by_year_month.keys()):
    year_total = sum(records_by_year_month[year].values())
    print(f"\nYear {year}: {year_total} total records")
    for month in sorted(records_by_year_month[year].keys()):
        print(f"  Month {month:02d}: {records_by_year_month[year][month]} records")

print("\n" + "=" * 50)
print("Pollution data stored in database - ready for monthly/yearly queries")
