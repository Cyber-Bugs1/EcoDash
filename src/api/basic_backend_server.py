import sys
import os
import logging
import sqlite3
import datetime
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import pandas as pd
import time

# Standard Python imports for prediction
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SCRIPTS_DIR))

try:
    from unified_predictor import UnifiedEnvironmentalPredictor, PREDICTION_TARGETS
except ImportError:
    sys.path.append(str(SCRIPTS_DIR))
    from unified_predictor import UnifiedEnvironmentalPredictor, PREDICTION_TARGETS

app = Flask(__name__)
CORS(app)
app.logger.setLevel(logging.INFO)

@app.before_request
def log_request():
    request.start_time = time.time()
    msg = f"➡️ {request.method} {request.path} | args={dict(request.args)} | json={request.get_json(silent=True)}"
    app.logger.info(msg)
    print(msg, file=sys.stderr, flush=True)

@app.after_request
def log_response(response):
    duration = round((time.time() - request.start_time) * 1000, 2)
    # Safely get response data for logging
    try:
        res_data = response.get_json() if response.is_json else f"Non-JSON ({response.status_code})"
    except:
        res_data = "Data Unreadable"
    msg = f"⬅️ {request.method} {request.path} | status={response.status_code} | {duration}ms | res={res_data}"
    app.logger.info(msg)
    print(msg, file=sys.stderr, flush=True)
    return response

# Initialize Predictor
DB_PATH = PROJECT_ROOT / "processed_data.db"
predictor = UnifiedEnvironmentalPredictor(str(DB_PATH))
MODEL_PATH = PROJECT_ROOT / "models" / "unified_predictor.pkl"
if MODEL_PATH.exists():
    try:
        predictor.load(str(MODEL_PATH))
        print(f"Loaded pre-trained models from {MODEL_PATH}")
    except Exception as e:
        print(f"Failed to load models: {e}")

# --- Helper Functions ---

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_current_year():
    return datetime.datetime.now().year

def clean_state_name(state):
    if not state:
        return state
    cleaned = state.replace('20%', ' ').replace('%20', ' ')
    cleaned = cleaned.replace('_', ' ').strip()
    return cleaned.title()

def get_month_name(month_num):
    try:
        return datetime.date(2000, int(month_num), 1).strftime('%B')
    except:
        return str(month_num)

def get_request_data():
    if request.method == 'POST':
        return request.json or {}
    else:
        return request.args

# --- Root Endpoint ---
@app.route('/', methods=['GET'])
def index():
    print("Health check endpoint called")
    return jsonify({
        "status": "online",
        "message": "Basic Backend Server Running (Standard Logging)",
        "endpoints": {
            "/api/data": "GET/POST - Retrieve environmental data",
            "/api/predict/pollution": "Placeholder",
            "/api/history/diff": "Placeholder",
            "/api/compare": "Placeholder",
            "/api/notification": "Placeholder"
        }
    })

# --- Service 1: Data Output Service ---
@app.route('/api/data', methods=['GET', 'POST'])
def data_output_service():
    data = get_request_data()
    data_type = data.get('type')
    city = data.get('city')
    state = clean_state_name(data.get('state'))
    month = data.get('month')
    year = data.get('year', get_current_year())

    print(f"Data Service called: type={data_type}, state={state}, month={month}, year={year}")

    # --- State-Only Summary Request ---
    if state and not data_type:
        summary = {}
        targets = [
            {'key': 'PM2.5', 'pred_target': 'pm25', 'thresh': 100, 'ref': 100},
            {'key': 'AOD', 'pred_target': 'aod', 'thresh': 1.0, 'ref': 1.0},
            {'key': 'Vegetation', 'pred_target': 'ndvi', 'thresh': None, 'ref': 1.0}, 
            {'key': 'Crop Yield (t/ha)', 'pred_target': 'crop_yield', 'thresh': 5.0, 'ref': 6.0},
            {'key': 'Water Level', 'pred_target': 'surface_water', 'thresh': 2.0, 'ref': 25.0} 
        ]
        
        current_m = datetime.datetime.now().month
        current_y = get_current_year()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for t in targets:
            yearly_vals = []
            for m in range(1, 13):
                try:
                    res = predictor.predict_state(state, t['pred_target'], m)
                    if res.get('predicted_value'): yearly_vals.append(res['predicted_value'])
                except: pass
            
            mean_val = float(round(np.mean(yearly_vals), 3)) if yearly_vals else 0.0
            if t['key'] == 'Crop Yield (t/ha)':
                mean_val = float(round(mean_val / 3, 3))
            
            pct_val = 0.0
            category = "Unknown"
            
            if t['ref'] > 0:
                pct_val = float(round((mean_val / t['ref']) * 100, 1))
                if t['key'] == 'PM2.5':
                    if pct_val < 50: category = "Good"
                    elif pct_val < 100: category = "Moderate"
                    elif pct_val < 200: category = "Poor"
                    else: category = "Severe"
                elif t['key'] == 'AOD':
                    if pct_val < 40: category = "Clear"
                    elif pct_val < 80: category = "Hazy"
                    else: category = "Very Hazy"
                elif t['key'] == 'Water Level':
                    if pct_val < 30: category = "Safe"
                    elif pct_val < 70: category = "Moderate"
                    else: category = "Critical"
                else:
                    if pct_val < 30: category = "Poor"
                    elif pct_val < 60: category = "Average"
                    else: category = "Good"
            
            spike = False
            start_y, start_m = current_y, current_m
            for i in range(1, 11):
                m_idx = start_m + i
                t_year = start_y + ((m_idx - 1) // 12)
                t_month = ((m_idx - 1) % 12) + 1
                try:
                    p_res = predictor.predict_state(state, t['pred_target'], t_month)
                    val = p_res.get('predicted_value', 0)
                    if t['thresh'] and val > t['thresh']:
                        spike = True
                        break
                    elif t['thresh'] is None and mean_val > 0:
                        if val > mean_val * 1.5:
                            spike = True
                            break
                except: pass

            summary[t['key']] = {
                "mean_value": mean_val,
                "mean_percentage_of_max": pct_val,
                "category": category,
                "spike_detected_next_10_months": spike
            }

        trend_years = range(current_y - 4, current_y)
        trend_data = {'years': list(trend_years), 'pm25': [], 'aod': []}

        for y in trend_years:
            pm25_y_val = 0
            cursor.execute("SELECT pm25_mean FROM Pollution WHERE state_name=? AND year=?", (state, y))
            row = cursor.fetchone()
            if row and row[0] is not None:
                pm25_y_val = row[0]
            else:
                preds = []
                for m in range(1, 13):
                     try:
                         res = predictor.predict_state(state, 'pm25', m)
                         preds.append(res['predicted_value'])
                     except: pass
                base_val = np.mean(preds) if preds else 0
                if base_val > 0:
                    year_diff = y - 2023
                    trend_factor = 1.0 + (year_diff * 0.015)
                    pm25_y_val = float(base_val * trend_factor)
                else: pm25_y_val = 0.0
            trend_data['pm25'].append(float(round(pm25_y_val, 2)))

            aod_y_val = 0
            cursor.execute("SELECT AVG(aod_mean) FROM WeeklySatelliteData WHERE state_name=? AND year=?", (state, y))
            row = cursor.fetchone()
            if row and row[0] is not None:
                aod_y_val = row[0]
            else:
                preds = []
                for m in range(1, 13):
                     try:
                         res = predictor.predict_state(state, 'aod', m)
                         preds.append(res['predicted_value'])
                     except: pass
                base_aod = np.mean(preds) if preds else 0
                if base_aod > 0:
                    year_diff = y - 2023
                    trend_factor = 1.0 + (year_diff * 0.01)
                    aod_y_val = float(base_aod * trend_factor)
                else: aod_y_val = 0.0
            trend_data['aod'].append(float(round(aod_y_val, 3)))

        conn.close()
        return jsonify({
            "state": state,
            "year": current_y,
            "summary": summary,
            "trend": trend_data
        })

    # --- Annual Stats & Monthly Array ---
    if state and data_type and not month:
        table_map = {
            'PM2.5': {'table': 'Pollution', 'col': 'pm25_mean'},
            'AOD': {'table': 'WeeklySatelliteData', 'col': 'aod_mean'},
            'vegetation': {'table': 'Vegetation', 'col': 'ndvi_mean'},
            'crop_yield': {'table': 'Crop', 'col': 'evi_mean'},
            'water_levels': {'table': 'Water', 'col': 'surface_water_mean'}
        }
        type_key = None
        for k in table_map:
            if k.lower() == data_type.lower().replace(" ", "_"):
                type_key = k
                break
        
        query_col = None
        query_table = 'WeeklyEnvironmentalData' 
        if type_key == 'AOD':
            query_col = 'aod_mean'
            query_table = 'WeeklySatelliteData'
        elif data_type.lower() == 'pm2.5': query_col = 'pm25'
        elif 'vegetation' in data_type.lower(): query_col = 'ndvi'
        elif 'yield' in data_type.lower(): query_col = 'estimated_yield_index'
        elif 'crop' in data_type.lower(): query_col = 'crop_growth_index' 
        elif 'water' in data_type.lower(): query_col = 'surface_water_pct'

        if not query_col and data_type in PREDICTION_TARGETS:
             query_col = PREDICTION_TARGETS[data_type]['table'] # approximate

        if not query_col:
             return jsonify({"error": f"Unknown data type: {data_type}"}), 400

        monthly_values = []
        conn = get_db_connection()
        cursor = conn.cursor()
        overall_source = "Database"
        
        for m in range(1, 13):
            val = None
            week_start = (m - 1) * 4 + 1
            week_end = min(52, m * 4 + 4)
            try:
                cursor.execute(f"SELECT AVG({query_col}) FROM {query_table} WHERE state_name=? AND year=? AND week BETWEEN ? AND ?", 
                               (state, year, week_start, week_end))
                row = cursor.fetchone()
                if row and row[0] is not None:
                    val = row[0]
            except: pass
            
            if val is None:
                overall_source = "Predicted"
                try:
                    target_key = query_col
                    if query_col == 'aod_mean': target_key = 'aod'
                    elif query_col == 'water_stress_index': target_key = 'water_stress'
                    elif query_col == 'surface_water_pct': target_key = 'surface_water'
                    elif query_col == 'crop_growth_index': target_key = 'crop_growth'
                    elif query_col == 'estimated_yield_index': target_key = 'crop_yield'
                    elif query_col == 'ndvi_mean': target_key = 'ndvi'
                    elif query_col == 'evi_mean': target_key = 'crop_yield'
                    
                    pred = predictor.predict_state(state, target_key, m)
                    base_val = pred.get('predicted_value')
                    
                    try:
                        year_int = int(year)
                        if base_val is not None and year_int > 2023:
                            year_diff = year_int - 2023
                            trend_factor = 1.0
                            qt_lower = query_col.lower()
                            if 'pm' in qt_lower or 'aod' in qt_lower or 'no2' in qt_lower:
                                trend_factor = 1.0 + (year_diff * 0.015) 
                            elif 'water' in qt_lower or 'stress' in qt_lower:
                                trend_factor = 1.0 + (year_diff * 0.02)
                            elif 'yield' in qt_lower or 'growth' in qt_lower or 'ndvi' in qt_lower or 'evi' in qt_lower:
                                trend_factor = 1.0 + (year_diff * 0.005)
                            val = round(base_val * trend_factor, 3)
                        else:
                            val = base_val
                    except:
                        val = base_val
                except: val = 0
            
            monthly_values.append(float(val) if val is not None else 0.0)
        
        if 'crop' in data_type.lower() or 'yield' in data_type.lower():
            monthly_values = [float(round(v / 3, 3)) for v in monthly_values]

        conn.close()
        valid_vals = [v for v in monthly_values if v > 0]
        annual_mean = float(round(np.mean(valid_vals), 3)) if valid_vals else 0.0
        annual_min = float(round(np.min(valid_vals), 3)) if valid_vals else 0.0
        annual_max = float(round(np.max(valid_vals), 3)) if valid_vals else 0.0
        
        return jsonify({
            "state": state,
            "year": year,
            "type": data_type,
            "source": overall_source,
            "annual_mean": annual_mean,
            "annual_min": annual_min,
            "annual_max": annual_max,
            "monthly_averages": monthly_values
        })
    
    if not all([data_type, state, month]):
        return jsonify({"error": "Missing required fields."}), 400

    table_map = {
        'PM2.5': {'table': 'Pollution', 'col': 'pm25_mean'},
        'AOD': {'table': 'WeeklySatelliteData', 'col': 'aod_mean'},
        'vegetation': {'table': 'Vegetation', 'col': 'ndvi_mean'},
        'crop_yield': {'table': 'Crop', 'col': 'evi_mean'},
        'water_levels': {'table': 'Water', 'col': 'surface_water_mean'}
    }
    
    type_key = None
    for k in table_map:
        if k.lower() == data_type.lower().replace(" ", "_"):
            type_key = k
            break
    
    conn = get_db_connection()
    cursor = conn.cursor()
    result = {
        "type": data_type,
        "city": city,
        "state": state,
        "month": month,
        "year": year,
        "value": None,
        "source": "Database"
    }

    try:
        query_col = None
        query_table = 'WeeklyEnvironmentalData'

        if type_key == 'AOD':
            query_col = 'aod_mean'
            query_table = 'WeeklySatelliteData'
        elif data_type.lower() == 'pm2.5': query_col = 'pm25'
        elif 'vegetation' in data_type.lower(): query_col = 'ndvi'
        elif 'yield' in data_type.lower(): query_col = 'estimated_yield_index'
        elif 'crop' in data_type.lower(): query_col = 'crop_growth_index' 
        elif 'water' in data_type.lower(): query_col = 'water_stress_index' 

        if query_col:
            if query_col in ['pm25', 'ndvi', 'estimated_yield_index', 'crop_growth_index', 'water_stress_index']:
                query_table = 'WeeklyEnvironmentalData'
            
            week_start = (int(month) - 1) * 4 + 1
            week_end = min(52, int(month) * 4 + 4)
            
            cursor.execute(f"SELECT AVG({query_col}) FROM {query_table} WHERE state_name = ? AND year = ? AND week BETWEEN ? AND ?", 
                           (state, year, week_start, week_end))
            row = cursor.fetchone()
            
            if row and row[0] is not None:
                result['value'] = row[0]
            else:
                result['source'] = "Predicted"
                target_key = query_col
                if query_col == 'aod_mean': target_key = 'aod'
                elif query_col == 'water_stress_index': target_key = 'water_stress'
                elif query_col == 'surface_water_pct': target_key = 'surface_water'
                elif query_col == 'crop_growth_index': target_key = 'crop_growth'
                elif query_col == 'estimated_yield_index': target_key = 'crop_yield'
                elif query_col == 'ndvi_mean': target_key = 'ndvi'
                elif query_col == 'evi_mean': target_key = 'crop_yield'
                
                try:
                    pred_res = predictor.predict_state(state, target_key, int(month))
                    base_val = pred_res.get('predicted_value')
                    year_int = int(year)
                    if base_val is not None and year_int > 2023:
                        year_diff = year_int - 2023
                        trend_factor = 1.0
                        qt_lower = query_col.lower()
                        if 'pm' in qt_lower or 'aod' in qt_lower or 'no2' in qt_lower:
                            trend_factor = 1.0 + (year_diff * 0.015) 
                        elif 'water' in qt_lower or 'stress' in qt_lower:
                            trend_factor = 1.0 + (year_diff * 0.02)
                        elif 'yield' in qt_lower or 'growth' in qt_lower or 'ndvi' in qt_lower or 'evi' in qt_lower:
                            trend_factor = 1.0 + (year_diff * 0.005)
                        result['value'] = float(round(base_val * trend_factor, 3))
                    else:
                        result['value'] = float(base_val) if base_val is not None else 0.0
                except:
                    result['value'] = 0.0

        if result['value'] is not None and ('crop' in str(data_type).lower() or 'yield' in str(data_type).lower()):
            result['value'] = float(round(result['value'] / 3, 3))

            val = result.get('value')
            if val is not None:
                result['mean_value'] = round(val, 3)
                result['max_value'] = round(val * 1.10, 3)
                result['min_value'] = round(val * 0.90, 3)

            aod_week_start = (int(month) - 1) * 4 + 1
            aod_week_end = min(52, int(month) * 4 + 4)
            cursor.execute("SELECT AVG(aod_mean) FROM WeeklySatelliteData WHERE state_name = ? AND year = ? AND week BETWEEN ? AND ?", 
                           (state, year, aod_week_start, aod_week_end))
            aod_row = cursor.fetchone()
            
            if not aod_row or aod_row[0] is None:
                 try:
                     pred_aod = predictor.predict_state(state, 'aod', int(month))
                     result['aod_mean'] = pred_aod.get('predicted_value')
                 except: pass
            else:
                 result['aod_mean'] = round(aod_row[0], 3)

    except Exception as e:
        print(f"Error fetching data: {e}")
        result['error'] = str(e)

    conn.close()
    return jsonify(result)

# --- Service 2: Pollution Level Prediction (PLACEHOLDER) ---
@app.route('/api/predict/pollution', methods=['GET', 'POST'])
def pollution_prediction_service():
    return jsonify({"error": "Service 2 is not yet implemented"}), 501

# --- Service 3: Historical Difference Service (PLACEHOLDER) ---
@app.route('/api/history/diff', methods=['GET', 'POST'])
def historical_diff_service():
    return jsonify({"error": "Service 3 is not yet implemented"}), 501

# --- Service 4: Comparison & Extrapolation Service (PLACEHOLDER) ---
@app.route('/api/compare', methods=['GET', 'POST'])
def comparison_service():
    return jsonify({"error": "Service 4 is not yet implemented"}), 501

# --- Service 5: Notification Service (PLACEHOLDER) ---
@app.route('/api/notification', methods=['GET', 'POST'])
def notification_service():
    return jsonify({"error": "Service 5 is not yet implemented"}), 501

if __name__ == '__main__':
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*60}", file=sys.stderr)
    print(f">>> BASIC SERVER STARTING AT {timestamp} <<<", file=sys.stderr)
    print(f">>> LISTENING ON PORT 5003 <<<", file=sys.stderr)
    print(f"{'='*60}\n", file=sys.stderr, flush=True)
    app.run(host='0.0.0.0', port=5003, debug=True)
