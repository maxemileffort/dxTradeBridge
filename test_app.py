import pytest
from flask import Flask, jsonify
from app import app 

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
