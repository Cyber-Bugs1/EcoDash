"""
Environmental AI API Server - Flask-based API for testing AI models.

Endpoints:
- /api/predict/pm25 - Predict PM2.5 from environmental factors
- /api/predict/health - Classify environmental health
- /api/predict/spike - Predict future pollution spikes
- /api/forecast/<state>/<year> - Forecast for specific state and year
- /api/national/<year> - National forecast for a year
- /api/states - List available states
"""

import sys
from pathlib import Path
from flask import Flask, request, jsonify, render_template_string

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai import EnvironmentalAISystem
from ai.spike_predictor import PollutionSpikePredictor

app = Flask(__name__)

# Initialize AI systems
db_path = str(Path(__file__).parent.parent / "processed_data.db")
ai_system = None
spike_predictor = None

def init_models():
    """Initialize AI models on first request."""
    global ai_system, spike_predictor
    
    if ai_system is None:
        print("Initializing AI models...")
        ai_system = EnvironmentalAISystem(db_path)
        ai_system.train_all_models()
        
        spike_predictor = PollutionSpikePredictor(db_path)
        spike_predictor.train()
        print("Models ready!")

# HTML template for testing interface
TEST_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Environmental AI Testing</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: 'Segoe UI', Arial, sans-serif; 
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh; color: #e0e0e0; padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { 
            text-align: center; margin-bottom: 30px; 
            color: #00d4ff; text-shadow: 0 0 20px rgba(0,212,255,0.5);
        }
        .card { 
            background: rgba(255,255,255,0.1); border-radius: 15px; 
            padding: 25px; margin-bottom: 20px;
            backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1);
        }
        h2 { color: #00d4ff; margin-bottom: 15px; font-size: 1.3em; }
        label { display: block; margin: 10px 0 5px; color: #aaa; }
        input, select { 
            width: 100%; padding: 12px; border: none; border-radius: 8px;
            background: rgba(0,0,0,0.3); color: white; font-size: 14px;
        }
        button { 
            background: linear-gradient(135deg, #00d4ff, #0099cc);
            color: white; border: none; padding: 15px 30px; 
            border-radius: 8px; cursor: pointer; font-size: 16px;
            margin-top: 15px; width: 100%; transition: all 0.3s;
        }
        button:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(0,212,255,0.4); }
        .result { 
            background: rgba(0,0,0,0.3); padding: 20px; border-radius: 10px;
            margin-top: 15px; white-space: pre-wrap; font-family: monospace;
        }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; }
        .risk-critical { color: #ff4444; font-weight: bold; }
        .risk-high { color: #ff8844; font-weight: bold; }
        .risk-moderate { color: #ffcc00; }
        .risk-low { color: #44ff44; }
        .loading { opacity: 0.5; }
        .endpoints { font-size: 12px; color: #888; margin-top: 20px; }
        .endpoints a { color: #00d4ff; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Environmental AI Testing Interface</h1>
        
        <div class="grid">
            <!-- PM2.5 Prediction -->
            <div class="card">
                <h2>PM2.5 Prediction</h2>
                <form id="pm25Form">
                    <label>NDVI (0-1):</label>
                    <input type="number" name="ndvi" step="0.01" value="0.5" min="0" max="1">
                    
                    <label>Annual Rainfall (mm):</label>
                    <input type="number" name="rainfall" value="1500" min="0" max="5000">
                    
                    <label>Dry Months (0-12):</label>
                    <input type="number" name="dry_months" value="5" min="0" max="12">
                    
                    <label>Cropland (%):</label>
                    <input type="number" name="cropland" value="50" min="0" max="100">
                    
                    <label>EVI (0-1):</label>
                    <input type="number" name="evi" step="0.01" value="0.35" min="0" max="1">
                    
                    <label>Surface Water (%):</label>
                    <input type="number" name="surface_water" step="0.1" value="2.0" min="0" max="100">
                    
                    <button type="submit">Predict PM2.5</button>
                </form>
                <div id="pm25Result" class="result"></div>
            </div>
            
            <!-- Spike Prediction -->
            <div class="card">
                <h2>Future Pollution Spike Prediction</h2>
                <form id="spikeForm">
                    <label>State:</label>
                    <select name="state" id="stateSelect">
                        <option value="Delhi">Delhi</option>
                        <option value="Bihar">Bihar</option>
                        <option value="Punjab">Punjab</option>
                        <option value="Kerala">Kerala</option>
                        <option value="Maharashtra">Maharashtra</option>
                        <option value="West Bengal">West Bengal</option>
                        <option value="Uttar Pradesh">Uttar Pradesh</option>
                        <option value="Rajasthan">Rajasthan</option>
                        <option value="Tamil Nadu">Tamil Nadu</option>
                        <option value="Karnataka">Karnataka</option>
                    </select>
                    
                    <label>Target Year:</label>
                    <input type="number" name="year" value="2025" min="2024" max="2030">
                    
                    <button type="submit">Predict Spike Risk</button>
                </form>
                <div id="spikeResult" class="result"></div>
            </div>
            
            <!-- National Forecast -->
            <div class="card">
                <h2>National Forecast</h2>
                <form id="nationalForm">
                    <label>Forecast Year:</label>
                    <input type="number" name="year" value="2025" min="2024" max="2030">
                    
                    <button type="submit">Get National Forecast</button>
                </form>
                <div id="nationalResult" class="result"></div>
            </div>
            
            <!-- State Analysis -->
            <div class="card">
                <h2>State Analysis (Current + Prediction)</h2>
                <form id="analysisForm">
                    <label>State:</label>
                    <select name="state">
                        <option value="Delhi">Delhi</option>
                        <option value="Bihar">Bihar</option>
                        <option value="Punjab">Punjab</option>
                        <option value="Kerala">Kerala</option>
                        <option value="Mizoram">Mizoram</option>
                        <option value="Maharashtra">Maharashtra</option>
                    </select>
                    
                    <button type="submit">Analyze State</button>
                </form>
                <div id="analysisResult" class="result"></div>
            </div>
        </div>
        
        <div class="endpoints card">
            <h2>API Endpoints</h2>
            <p>
                <a href="/api/states">/api/states</a> - List all states<br>
                <a href="/api/forecast/Delhi/2025">/api/forecast/{state}/{year}</a> - State forecast<br>
                <a href="/api/national/2025">/api/national/{year}</a> - National forecast<br>
                POST /api/predict/pm25 - PM2.5 prediction<br>
                POST /api/predict/spike - Spike prediction
            </p>
        </div>
    </div>
    
    <script>
        // PM2.5 Prediction
        document.getElementById('pm25Form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const form = e.target;
            const result = document.getElementById('pm25Result');
            result.innerHTML = 'Loading...';
            result.className = 'result loading';
            
            const data = {
                ndvi: parseFloat(form.ndvi.value),
                rainfall: parseFloat(form.rainfall.value),
                dry_months: parseInt(form.dry_months.value),
                cropland: parseFloat(form.cropland.value),
                evi: parseFloat(form.evi.value),
                surface_water: parseFloat(form.surface_water.value)
            };
            
            const res = await fetch('/api/predict/pm25', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
            const json = await res.json();
            result.className = 'result';
            result.innerHTML = JSON.stringify(json, null, 2);
        });
        
        // Spike Prediction
        document.getElementById('spikeForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const form = e.target;
            const result = document.getElementById('spikeResult');
            result.innerHTML = 'Loading...';
            
            const state = form.state.value;
            const year = form.year.value;
            
            const res = await fetch(`/api/forecast/${state}/${year}`);
            const json = await res.json();
            
            let html = `Year: ${json.year}
Predicted PM2.5: ${json.predicted_pm25} ug/m3
Spike Probability: ${(json.spike_probability * 100).toFixed(0)}%
Risk Level: <span class="risk-${json.risk_level.toLowerCase()}">${json.risk_level}</span>
Trend: ${json.trend_direction}
Confidence: ${(json.confidence * 100).toFixed(0)}%

Contributing Factors:
${json.contributing_factors.map(f => '  - ' + f).join('\\n')}`;
            
            result.innerHTML = html;
        });
        
        // National Forecast
        document.getElementById('nationalForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const form = e.target;
            const result = document.getElementById('nationalResult');
            result.innerHTML = 'Loading...';
            
            const res = await fetch(`/api/national/${form.year.value}`);
            const json = await res.json();
            
            let html = `Year: ${json.year}
National Avg PM2.5: ${json.national_avg_pm25} ug/m3
Avg Spike Probability: ${(json.national_spike_probability * 100).toFixed(0)}%
States at High Risk: ${json.states_at_risk} / ${json.total_states}

High Risk States:
${json.high_risk_states.slice(0, 5).map(s => 
    `  - ${s.state}: ${s.predicted_pm25} ug/m3 (${s.risk_level})`
).join('\\n')}`;
            
            result.innerHTML = html;
        });
        
        // State Analysis
        document.getElementById('analysisForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const form = e.target;
            const result = document.getElementById('analysisResult');
            result.innerHTML = 'Loading...';
            
            const res = await fetch(`/api/analyze/${form.state.value}`);
            const json = await res.json();
            
            result.innerHTML = JSON.stringify(json, null, 2);
        });
    </script>
</body>
</html>
"""


@app.route('/')
def home():
    """Serve the testing interface."""
    init_models()
    return render_template_string(TEST_PAGE)


@app.route('/api/states')
def get_states():
    """Get list of available states."""
    init_models()
    states = list(spike_predictor.historical_data.keys())
    return jsonify({'states': sorted(states), 'count': len(states)})


@app.route('/api/predict/pm25', methods=['POST'])
def predict_pm25():
    """Predict PM2.5 from environmental factors."""
    init_models()
    
    data = request.get_json()
    
    result = ai_system.predict_pm25(
        ndvi=data.get('ndvi', 0.5),
        rainfall=data.get('rainfall', 1500),
        dry_months=data.get('dry_months', 6),
        cropland=data.get('cropland', 50),
        evi=data.get('evi', 0.35),
        surface_water=data.get('surface_water', 2.0)
    )
    
    return jsonify(result)


@app.route('/api/forecast/<state>/<int:year>')
def forecast_state(state, year):
    """Get pollution forecast for a specific state and year."""
    init_models()
    
    try:
        prediction = spike_predictor.predict_for_year(state, year)
        return jsonify({
            'state': state,
            'year': prediction.year,
            'predicted_pm25': prediction.predicted_pm25,
            'spike_probability': prediction.spike_probability,
            'trend_direction': prediction.trend_direction,
            'confidence': prediction.confidence,
            'risk_level': prediction.risk_level,
            'contributing_factors': prediction.contributing_factors
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 404


@app.route('/api/national/<int:year>')
def national_forecast(year):
    """Get national-level pollution forecast."""
    init_models()
    
    forecast = spike_predictor.get_national_forecast(year)
    return jsonify(forecast)


@app.route('/api/analyze/<state>')
def analyze_state(state):
    """Get comprehensive analysis for a state."""
    init_models()
    
    analysis = ai_system.analyze_state(state, 2023)
    
    # Add 2025 prediction
    try:
        prediction_2025 = spike_predictor.predict_for_year(state, 2025)
        analysis['forecast_2025'] = {
            'predicted_pm25': prediction_2025.predicted_pm25,
            'spike_probability': prediction_2025.spike_probability,
            'risk_level': prediction_2025.risk_level,
            'trend': prediction_2025.trend_direction
        }
    except:
        pass
    
    return jsonify(analysis)


@app.route('/api/predict/multi-year', methods=['POST'])
def predict_multi_year():
    """Predict pollution for multiple years."""
    init_models()
    
    data = request.get_json()
    state = data.get('state', 'Delhi')
    start_year = data.get('start_year', 2024)
    end_year = data.get('end_year', 2030)
    
    predictions = spike_predictor.predict_multi_year(state, start_year, end_year)
    
    return jsonify({
        'state': state,
        'predictions': [
            {
                'year': p.year,
                'predicted_pm25': p.predicted_pm25,
                'spike_probability': p.spike_probability,
                'risk_level': p.risk_level
            }
            for p in predictions
        ]
    })


if __name__ == '__main__':
    print("=" * 60)
    print("Environmental AI API Server")
    print("=" * 60)
    print("\nStarting server at http://localhost:5000")
    print("Open in browser to test the AI models")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=False)
