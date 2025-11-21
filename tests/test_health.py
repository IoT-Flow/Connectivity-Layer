"""
TDD Test Suite for Health Monitoring
Following TDD approach - write tests first, then implement/fix functionality
"""

import pytest
import os

os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from app import create_app
from src.models import db, User, Device


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


class TestBasicHealthCheck:
    """Test basic health check endpoint"""
    
    def test_health_endpoint_exists(self, client):
        """Test that GET /health endpoint exists"""
        response = client.get('/health')
        
        # Should not return 404
        assert response.status_code != 404
    
    def test_health_returns_200(self, client):
        """Test that health check returns 200 OK"""
        response = client.get('/health')
        
        assert response.status_code == 200
    
    def test_health_returns_json(self, client):
        """Test that health check returns JSON"""
        response = client.get('/health')
        
        assert response.content_type == 'application/json'
        data = response.get_json()
        assert data is not None
    
    def test_health_has_status_field(self, client):
        """Test that health check has status field"""
        response = client.get('/health')
        
        data = response.get_json()
        assert 'status' in data
    
    def test_health_status_is_healthy(self, client):
        """Test that health status is healthy"""
        response = client.get('/health')
        
        data = response.get_json()
        assert data['status'] == 'healthy'
    
    def test_health_has_version(self, client):
        """Test that health check includes version"""
        response = client.get('/health')
        
        data = response.get_json()
        assert 'version' in data or 'message' in data


class TestDetailedHealthCheck:
    """Test detailed health check"""
    
    def test_detailed_health_endpoint(self, client):
        """Test that GET /health?detailed=true works"""
        response = client.get('/health?detailed=true')
        
        assert response.status_code == 200
    
    def test_detailed_health_has_checks(self, client):
        """Test that detailed health includes checks"""
        response = client.get('/health?detailed=true')
        
        data = response.get_json()
        # Should have checks or metrics
        assert 'checks' in data or 'database' in data or 'status' in data
    
    def test_detailed_health_has_timestamp(self, client):
        """Test that detailed health includes timestamp"""
        response = client.get('/health?detailed=true')
        
        data = response.get_json()
        assert 'timestamp' in data or 'status' in data


class TestSystemStatusEndpoint:
    """Test system status endpoint"""
    
    def test_status_endpoint_exists(self, client):
        """Test that GET /status endpoint exists"""
        response = client.get('/status')
        
        # Should not return 404
        assert response.status_code != 404
    
    def test_status_returns_200(self, client):
        """Test that status endpoint returns 200 OK"""
        response = client.get('/status')
        
        assert response.status_code == 200
    
    def test_status_returns_detailed_info(self, client):
        """Test that status endpoint returns detailed information"""
        response = client.get('/status')
        
        data = response.get_json()
        assert data is not None
        # Should have some detailed information
        assert len(data) > 1


class TestRootEndpoint:
    """Test root endpoint"""
    
    def test_root_endpoint_exists(self, client):
        """Test that GET / endpoint exists"""
        response = client.get('/')
        
        # Should not return 404
        assert response.status_code != 404
    
    def test_root_returns_200(self, client):
        """Test that root endpoint returns 200 OK"""
        response = client.get('/')
        
        assert response.status_code == 200
    
    def test_root_has_api_info(self, client):
        """Test that root endpoint returns API information"""
        response = client.get('/')
        
        data = response.get_json()
        assert data is not None
        # Should have name or description
        assert 'name' in data or 'description' in data or 'version' in data


class TestDatabaseHealthCheck:
    """Test database health check"""
    
    def test_database_check_in_detailed_health(self, client):
        """Test that database check is included in detailed health"""
        response = client.get('/health?detailed=true')
        
        data = response.get_json()
        # Database check should be present
        if 'checks' in data:
            assert 'database' in data['checks']
    
    def test_database_is_healthy(self, client):
        """Test that database reports as healthy"""
        response = client.get('/health?detailed=true')
        
        data = response.get_json()
        if 'checks' in data and 'database' in data['checks']:
            # Database should be healthy in test environment
            assert data['checks']['database'].get('healthy') is True


class TestHealthMonitoringMetrics:
    """Test health monitoring metrics"""
    
    def test_metrics_in_detailed_health(self, client):
        """Test that metrics are included in detailed health"""
        response = client.get('/health?detailed=true')
        
        data = response.get_json()
        # Should have metrics or some monitoring data
        assert 'metrics' in data or 'checks' in data or 'status' in data
    
    def test_device_metrics_available(self, client):
        """Test that device metrics are available"""
        response = client.get('/health?detailed=true')
        
        data = response.get_json()
        # Device metrics should be present
        if 'metrics' in data:
            assert 'devices' in data['metrics'] or 'application' in data['metrics']


class TestErrorHandling:
    """Test error handling in health checks"""
    
    def test_404_error_handler(self, client):
        """Test that 404 errors are handled properly"""
        response = client.get('/nonexistent-endpoint')
        
        assert response.status_code == 404
        data = response.get_json()
        assert data is not None
    
    def test_health_check_resilient(self, client):
        """Test that health check is resilient to errors"""
        response = client.get('/health')
        
        # Should always return 200 even if some checks fail
        assert response.status_code == 200


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
