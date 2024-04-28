import pytest
from flask import Flask, jsonify
from app import app 
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv
from datetime import datetime
import time
import os

# Load environment variables
load_dotenv()

# Access variables securely
username = os.getenv('DX_USERNAME')
password = os.getenv('DX_PASS')
server = os.getenv('DX_SERVER')
accountId = os.getenv('DX_ACCOUNT')

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_check_payload_success(client):
    # Test with a valid payload
    response = client.post('/check_payload', data='name,john,age,30')
    assert response.status_code == 200
    assert response.json == {
        "message": "payload check.",
        "details": ["name", "john", "age", "30"]
    }

def test_check_payload_empty(client):
    # Test with an empty payload
    response = client.post('/check_payload', data='')
    assert response.status_code == 200
    assert response.json == {
        "message": "payload check.",
        "details": ['']
    }

def test_check_payload_special_characters(client):
    # Test with special characters
    response = client.post('/check_payload', data='currency,$,rate,3.5%')
    assert response.status_code == 200
    assert response.json == {
        "message": "payload check.",
        "details": ["currency", "$", "rate", "3.5%"]
    }

def test_receive_request_missing_details(client):
    # Test with insufficient data
    insuff_data = f'{username},{password},{server}'
    response = client.post('/receive_request', data=insuff_data)
    assert response.status_code == 200
    assert response.json == {
        "message": "missing key trade details.",
        "details": insuff_data
    }

@patch('app.Identity')  # Replace 'your_flask_app_file' with the actual import name
def test_receive_request_auth_failure(mock_identity, client):
    # Setup the mock
    instance = mock_identity.return_value
    time.sleep(1)
    instance.login.side_effect = Exception("Auth failed")
    
    # Test authentication failure
    response = client.post('/receive_request', data=f'user,pass,server,123,symbol,open,BUY,10,1.0,0.5,abc123')
    time.sleep(1)
    assert response.status_code == 301
    assert response.json == {"message": "Auth unsuccessful", "details": ""}

@patch('app.Identity')
def test_receive_request_open_buy_success(mock_identity, client):
    # Setup the mock
    instance = mock_identity.return_value
    time.sleep(1)
    instance.login.return_value = None
    time.sleep(1)
    instance.buy.return_value = "Buy executed"
    time.sleep(1)

    # Test open buy action
    response = client.post('/receive_request', data='user,pass,server,123,symbol,open,BUY,10,1.0,0.5,abc123')
    time.sleep(1)
    assert response.status_code == 200
    time.sleep(1)
    assert response.json == {"message": "Trade opened successfully", "details": "Buy executed"}

@patch('app.Identity')
def test_receive_request_invalid_action(mock_identity, client):
    # Setup the mock
    instance = mock_identity.return_value
    time.sleep(1)
    instance.login.return_value = None
    time.sleep(1)
    instance.buy.side_effect = ValueError("Invalid action")
    time.sleep(1)
    
    # Test invalid action
    response = client.post('/receive_request', data='user,pass,server,123,symbol,open,NONE,10,1.0,0.5,abc123')
    time.sleep(1)
    assert response.status_code == 400
    time.sleep(1)
    assert "error" in response.json
    assert len(response.json['error']) > 0

# You can add more tests to cover other scenarios like sell success, close success, etc.
