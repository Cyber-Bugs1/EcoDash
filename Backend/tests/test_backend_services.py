import sys
import json
import pytest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src" / "api"))

# Import the app
from src.api.backend_app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_service_1_data_output(client):
    """Test Data Output Service (POST and GET)"""
    # POST
    resp_post = client.post('/api/data', json={
        "type": "PM2.5", "city": "Delhi", "state": "Delhi", "month": 11, "year": 2023
    })
    assert resp_post.status_code == 200
    
    # GET
    resp_get = client.get('/api/data?type=PM2.5&city=Delhi&state=Delhi&month=11&year=2023')
    assert resp_get.status_code == 200
    assert resp_get.get_json()['type'] == 'PM2.5'

def test_service_2_prediction(client):
    """Test Pollution Prediction Service (POST and GET)"""
    # POST
    resp_post = client.post('/api/predict/pollution', json={
        "city": "Mumbai", "state": "Maharashtra", "month": 5
    })
    assert resp_post.status_code == 200
    
    # GET
    resp_get = client.get('/api/predict/pollution?city=Mumbai&state=Maharashtra&month=5')
    assert resp_get.status_code == 200
    assert 'pm2.5' in resp_get.get_json()

def test_service_3_history(client):
    """Test Historical Difference Service (POST and GET)"""
    # POST
    resp_post = client.post('/api/history/diff', json={ "city": "Chennai", "state": "Tamil Nadu" })
    assert resp_post.status_code == 200
    
    # GET
    resp_get = client.get('/api/history/diff?city=Chennai&state=Tamil%20Nadu')
    assert resp_get.status_code == 200
    assert len(resp_get.get_json()['history']) == 5

def test_service_4_compare(client):
    """Test Comparison Service (POST and GET)"""
    # POST
    resp_post = client.post('/api/compare', json={
        "city": "Kolkata", "state": "West Bengal", "month": 12, "start_year": 2022, "end_year": 2025
    })
    assert resp_post.status_code == 200
    
    # GET
    resp_get = client.get('/api/compare?city=Kolkata&state=West%20Bengal&month=12&start_year=2022&end_year=2025')
    assert resp_get.status_code == 200
    assert len(resp_get.get_json()['comparison']) == 4

def test_service_5_notification(client):
    """Test Notification Service (POST and GET)"""
    # POST
    resp_post = client.post('/api/notification', json={ "city": "Delhi", "state": "Delhi" })
    assert resp_post.status_code == 200
    
    # GET
    resp_get = client.get('/api/notification?city=Delhi&state=Delhi')
    assert resp_get.status_code == 200
    assert 'alert' in resp_get.get_json()
