"""
TDD Test Suite for Charts API
Following TDD approach - write tests first, then implement functionality
"""

import pytest
import os
from datetime import datetime, timezone

os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from app import create_app
from src.models import db, User, Device, Chart, ChartDevice, ChartMeasurement

@pytest.fixture
def app():
    """Create test app"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Test client"""
    return app.test_client()

@pytest.fixture
def test_user(app):
    """Create test user"""
    with app.app_context():
        user = User(username='testuser', email='test@example.com', password_hash='hash')
        db.session.add(user)
        db.session.commit()
        return {
            'id': user.id,
            'user_id': user.user_id,
            'username': user.username
        }

@pytest.fixture
def test_device(app, test_user):
    """Create test device"""
    with app.app_context():
        device = Device(
            name='Test Sensor',
            device_type='sensor',
            user_id=test_user['id'],
            status='active'
        )
        db.session.add(device)
        db.session.commit()
        return {
            'id': device.id,
            'api_key': device.api_key,
            'name': device.name
        }

class TestCreateChart:
    """Test creating charts"""
    
    def test_create_chart_endpoint_exists(self, client):
        """Test that POST /api/v1/charts endpoint exists"""
        response = client.post('/api/v1/charts')
        # Should not return 404
        assert response.status_code != 404
    
    def test_create_chart_success(self, client, test_user):
        """Test successful chart creation"""
        response = client.post(
            '/api/v1/charts',
            json={
                'name': 'Temperature Chart',
                'title': 'Living Room Temperature',
                'description': 'Temperature monitoring for living room',
                'type': 'line',
                'user_id': test_user['user_id'],
                'time_range': '24h',
                'refresh_interval': 30
            }
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['chart']['name'] == 'Temperature Chart'
        assert data['chart']['type'] == 'line'
    
    def test_create_chart_missing_required_fields(self, client):
        """Test chart creation with missing required fields"""
        response = client.post(
            '/api/v1/charts',
            json={'name': 'Test Chart'}  # Missing required fields
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_create_chart_invalid_type(self, client, test_user):
        """Test chart creation with invalid chart type"""
        response = client.post(
            '/api/v1/charts',
            json={
                'name': 'Test Chart',
                'type': 'invalid_type',
                'user_id': test_user['user_id']
            }
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'type' in data['error'].lower()

class TestListCharts:
    """Test listing charts"""
    
    def test_list_charts_endpoint_exists(self, client):
        """Test that GET /api/v1/charts endpoint exists"""
        response = client.get('/api/v1/charts')
        assert response.status_code != 404
    
    def test_list_charts_empty(self, client):
        """Test listing charts when none exist"""
        response = client.get('/api/v1/charts')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert len(data['charts']) == 0
    
    def test_list_charts_with_data(self, client, test_user):
        """Test listing charts when charts exist"""
        # First create a chart
        client.post(
            '/api/v1/charts',
            json={
                'name': 'Test Chart',
                'type': 'line',
                'user_id': test_user['user_id']
            }
        )
        
        # Then list charts
        response = client.get('/api/v1/charts')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert len(data['charts']) == 1
        assert data['charts'][0]['name'] == 'Test Chart'
    
    def test_list_charts_filter_by_user(self, client, test_user):
        """Test filtering charts by user"""
        # Create chart for test user
        client.post(
            '/api/v1/charts',
            json={
                'name': 'User Chart',
                'type': 'line',
                'user_id': test_user['user_id']
            }
        )
        
        # List charts for specific user
        response = client.get(f'/api/v1/charts?user_id={test_user["user_id"]}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['charts']) == 1
        assert data['charts'][0]['name'] == 'User Chart'

class TestGetChart:
    """Test getting individual chart"""
    
    def test_get_chart_endpoint_exists(self, client):
        """Test that GET /api/v1/charts/{id} endpoint exists"""
        response = client.get('/api/v1/charts/1')
        # Should not return 404 for endpoint (might return 404 for chart not found)
        assert response.status_code in [200, 404, 400]
    
    def test_get_chart_success(self, client, test_user):
        """Test getting chart by ID"""
        # Create chart first
        create_response = client.post(
            '/api/v1/charts',
            json={
                'name': 'Test Chart',
                'type': 'line',
                'user_id': test_user['user_id']
            }
        )
        chart_id = create_response.get_json()['chart']['id']
        
        # Get chart
        response = client.get(f'/api/v1/charts/{chart_id}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['chart']['name'] == 'Test Chart'
    
    def test_get_chart_not_found(self, client):
        """Test getting non-existent chart"""
        response = client.get('/api/v1/charts/999999')
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data

class TestUpdateChart:
    """Test updating charts"""
    
    def test_update_chart_endpoint_exists(self, client):
        """Test that PUT /api/v1/charts/{id} endpoint exists"""
        response = client.put('/api/v1/charts/1')
        assert response.status_code in [200, 404, 400]
    
    def test_update_chart_success(self, client, test_user):
        """Test updating chart"""
        # Create chart first
        create_response = client.post(
            '/api/v1/charts',
            json={
                'name': 'Original Chart',
                'type': 'line',
                'user_id': test_user['user_id']
            }
        )
        chart_id = create_response.get_json()['chart']['id']
        
        # Update chart
        response = client.put(
            f'/api/v1/charts/{chart_id}',
            json={
                'name': 'Updated Chart',
                'description': 'Updated description'
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['chart']['name'] == 'Updated Chart'

class TestDeleteChart:
    """Test deleting charts"""
    
    def test_delete_chart_endpoint_exists(self, client):
        """Test that DELETE /api/v1/charts/{id} endpoint exists"""
        response = client.delete('/api/v1/charts/1')
        assert response.status_code in [200, 404, 400]
    
    def test_delete_chart_success(self, client, test_user):
        """Test deleting chart"""
        # Create chart first
        create_response = client.post(
            '/api/v1/charts',
            json={
                'name': 'Chart to Delete',
                'type': 'line',
                'user_id': test_user['user_id']
            }
        )
        chart_id = create_response.get_json()['chart']['id']
        
        # Delete chart
        response = client.delete(f'/api/v1/charts/{chart_id}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        
        # Verify chart is deleted
        get_response = client.get(f'/api/v1/charts/{chart_id}')
        assert get_response.status_code == 404

class TestChartDevices:
    """Test managing chart-device associations"""
    
    def test_add_device_to_chart(self, client, test_user, test_device):
        """Test adding device to chart"""
        # Create chart
        create_response = client.post(
            '/api/v1/charts',
            json={
                'name': 'Multi-Device Chart',
                'type': 'line',
                'user_id': test_user['user_id']
            }
        )
        chart_id = create_response.get_json()['chart']['id']
        
        # Add device to chart
        response = client.post(
            f'/api/v1/charts/{chart_id}/devices',
            json={'device_id': test_device['id']}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['status'] == 'success'
    
    def test_remove_device_from_chart(self, client, test_user, test_device):
        """Test removing device from chart"""
        # Create chart and add device
        create_response = client.post(
            '/api/v1/charts',
            json={
                'name': 'Test Chart',
                'type': 'line',
                'user_id': test_user['user_id']
            }
        )
        chart_id = create_response.get_json()['chart']['id']
        
        client.post(
            f'/api/v1/charts/{chart_id}/devices',
            json={'device_id': test_device['id']}
        )
        
        # Remove device
        response = client.delete(f'/api/v1/charts/{chart_id}/devices/{test_device["id"]}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'

class TestChartMeasurements:
    """Test managing chart measurements"""
    
    def test_add_measurement_to_chart(self, client, test_user):
        """Test adding measurement to chart"""
        # Create chart
        create_response = client.post(
            '/api/v1/charts',
            json={
                'name': 'Temperature Chart',
                'type': 'line',
                'user_id': test_user['user_id']
            }
        )
        chart_id = create_response.get_json()['chart']['id']
        
        # Add measurement
        response = client.post(
            f'/api/v1/charts/{chart_id}/measurements',
            json={
                'measurement_name': 'temperature',
                'display_name': 'Temperature (°C)',
                'color': '#FF0000'
            }
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['status'] == 'success'
    
    def test_remove_measurement_from_chart(self, client, test_user):
        """Test removing measurement from chart"""
        # Create chart and add measurement
        create_response = client.post(
            '/api/v1/charts',
            json={
                'name': 'Test Chart',
                'type': 'line',
                'user_id': test_user['user_id']
            }
        )
        chart_id = create_response.get_json()['chart']['id']
        
        add_response = client.post(
            f'/api/v1/charts/{chart_id}/measurements',
            json={
                'measurement_name': 'temperature',
                'display_name': 'Temperature',
                'color': '#FF0000'
            }
        )
        measurement_id = add_response.get_json()['measurement']['id']
        
        # Remove measurement
        response = client.delete(f'/api/v1/charts/{chart_id}/measurements/{measurement_id}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'

class TestChartData:
    """Test getting chart data"""
    
    def test_get_chart_data_endpoint_exists(self, client):
        """Test that GET /api/v1/charts/{id}/data endpoint exists"""
        response = client.get('/api/v1/charts/1/data')
        assert response.status_code in [200, 404, 400]
    
    def test_get_chart_data_success(self, client, test_user):
        """Test getting chart data"""
        # Create chart
        create_response = client.post(
            '/api/v1/charts',
            json={
                'name': 'Data Chart',
                'type': 'line',
                'user_id': test_user['user_id']
            }
        )
        chart_id = create_response.get_json()['chart']['id']
        
        # Get chart data
        response = client.get(f'/api/v1/charts/{chart_id}/data')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'data' in data or 'series' in data

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
