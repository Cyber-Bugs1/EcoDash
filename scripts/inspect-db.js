const Database = require('better-sqlite3');
const path = require('path');

const dbPath = path.join(process.cwd(), 'src/db/envdb.db');
const db = new Database(dbPath, { verbose: console.log });

try {
    const tables = db.prepare("SELECT name FROM sqlite_master WHERE type='table'").all();
    console.log('Tables:', tables);

    const pollution = db.prepare("SELECT * FROM pollution_data LIMIT 5").all();
    console.log('Pollution Data Sample:', pollution);

    const pm25 = db.prepare("SELECT * FROM pm25_data LIMIT 5").all();
    console.log('PM25 Data Sample:', pm25);

    const states = db.prepare("SELECT DISTINCT state FROM pollution_data").all();
    console.log('States:', states);

} catch (err) {
    console.error('Error:', err);
}
