import pandas as pd
import sqlite3
import glob
import os

conn = sqlite3.connect("db/environment.db")
cur = conn.cursor()

for file in glob.glob("data/raw/India_Pollution_AOD_2020_*.csv"):
    month = int(os.path.basename(file).split("_")[-1].split(".")[0])
    year = 2020

    df = pd.read_csv(file)[["ADM1_NAME", "mean"]].dropna()

    for _, row in df.iterrows():
        cur.execute("""
            INSERT INTO pollution_data (state, year, month, aod)
            VALUES (?, ?, ?, ?)
        """, (row["ADM1_NAME"], year, month, row["mean"]))

conn.commit()
conn.close()

print("Pollution data stored in database")
