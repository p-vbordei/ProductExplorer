#pip install pytest Flask-Testing
# RUN WITH
# pytest tests.py

# tests.py
import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_create_user(client):
    response = client.post('/users', json={"name": "John"})
    assert response.status_code == 201
    assert 'user_id' in response.get_json()

def test_get_user(client):
    # Assuming a user with ID '12345' exists in the database for testing
    response = client.get('/users/12345')
    assert response.status_code == 200
    assert 'name' in response.get_json()

def test_subscribe(client):
    # Assuming a user with ID '12345' exists in the database for testing
    response = client.post('/users/12345/subscribe', json={"package": "premium"})
    assert response.status_code == 200
    assert 'subscription_id' in response.get_json()

def test_start_investigation(client):
    response = client.post('/investigations', json={"title": "New Investigation"})
    assert response.status_code == 201
    assert 'investigation_id' in response.get_json()

def test_get_investigation(client):
    # Assuming an investigation with ID 'inv12345' exists in the database for testing
    response = client.get('/investigations/inv12345')
    assert response.status_code == 200
    assert 'title' in response.get_json()

def test_generate_modeling(client):
    # Assuming an investigation with ID 'inv12345' exists in the database for testing
    response = client.get('/modeling/inv12345')
    assert response.status_code == 200
    assert 'results' in response.get_json()

def test_generate_report(client):
    # Assuming an investigation with ID 'inv12345' exists in the database for testing
    response = client.get('/reports/inv12345')
    assert response.status_code == 200
    assert 'report' in response.get_json()

def test_webhook(client):
    response = client.post('/webhook')
    assert response.status_code == 200
    assert response.get_json()['status'] == 'Webhook received'
