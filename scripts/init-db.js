const Database = require('better-sqlite3');
const path = require('path');
const fs = require('fs');

const DB_PATH = path.join(__dirname, '../src/db/environmental.db');
const DB_DIR = path.dirname(DB_PATH);

if (!fs.existsSync(DB_DIR)) {
    fs.mkdirSync(DB_DIR, { recursive: true });
}

if (fs.existsSync(DB_PATH)) {
    fs.unlinkSync(DB_PATH);
}

const db = new Database(DB_PATH);

db.exec(`
  CREATE TABLE environmental_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    state TEXT NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    aqi REAL,
    co2 REAL,
    forest_cover REAL,
    water_level REAL,
    crop_yield REAL
  )
`);

const states = ['Delhi', 'Maharashtra', 'Karnataka', 'Tamil Nadu', 'Gujarat', 'Kerala', 'Uttar Pradesh', 'West Bengal'];
const years = [2021, 2022, 2023, 2024];

const insert = db.prepare(`
  INSERT INTO environmental_records (state, year, month, aqi, co2, forest_cover, water_level, crop_yield)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?)
`);

db.transaction(() => {
    for (const state of states) {
        for (const year of years) {
            // Base values for the state/year
            let baseAQI = 100 + Math.random() * 200;
            let baseCO2 = 400 + Math.random() * 100;
            let baseForest = 10 + Math.random() * 40;
            let baseWater = 50 + Math.random() * 40;
            let baseCrop = 3 + Math.random() * 4;

            // Seasonal variations
            for (let month = 1; month <= 12; month++) {
                // AQI higher in winter/summer, lower in monsoon
                const aqiFactor = 1 + 0.3 * Math.sin((month + 1) / 12 * Math.PI * 2);
                const co2Factor = 1 + 0.05 * Math.random();
                // Water level high in monsoon
                const waterFactor = 1 + 0.4 * Math.sin((month - 6) / 12 * Math.PI * 2);

                insert.run(
                    state,
                    year,
                    month,
                    (baseAQI * aqiFactor + Math.random() * 20).toFixed(1),
                    (baseCO2 * co2Factor).toFixed(1),
                    (baseForest + (Math.random() - 0.5)).toFixed(1),
                    Math.min(100, Math.max(0, baseWater * waterFactor + Math.random() * 10)).toFixed(1),
                    (baseCrop + (Math.random() - 0.5) * 2).toFixed(1)
                );
            }
        }
    }
})();

console.log('Database initialized successfully at ' + DB_PATH);
db.close();
