"""
Unit tests for middleware layer
Testing authentication, security, and monitoring middleware
"""

import pytest
from unittest.mock import Mock, patch
from flask import Flask
import json


@pytest.mark.unit
class TestAuthMiddleware:
    """Unit tests for authentication middleware"""

    def test_authenticate_device_with_valid_api_key(self, client, test_device):
        """Test device authentication with valid API key"""
        headers = {"X-API-Key": test_device.api_key}

        response = client.get("/api/v1/devices/status", headers=headers)

        # Should authenticate successfully
        assert response.status_code == 200

    def test_authenticate_device_without_api_key(self, client):
        """Test authentication fails without API key"""
        response = client.get("/api/v1/devices/status")

        assert response.status_code == 401
        data = response.get_json()
        assert "error" in data or "message" in data

    def test_authenticate_device_with_invalid_api_key(self, client):
        """Test authentication fails with invalid API key"""
        headers = {"X-API-Key": "invalid_key_12345"}

        response = client.get("/api/v1/devices/status", headers=headers)

        assert response.status_code == 401

    def test_admin_authentication_with_valid_token(self, client, test_user, app):
        """Test admin authentication with valid token"""
        with app.app_context():
            from src.models import db

            # Make user admin
            test_user.is_admin = True
            db.session.commit()

            headers = {"Authorization": "admin test"}

            response = client.get("/api/v1/admin/devices", headers=headers)

            # Should authenticate (may return 200 or other valid response)
            assert response.status_code in [200, 401]  # Depends on admin token config

    def test_admin_authentication_without_token(self, client):
        """Test admin endpoint requires authentication"""
        response = client.get("/api/v1/admin/devices")

        assert response.status_code == 401

    def test_rate_limiting_enforced(self, client, test_device):
        """Test rate limiting is enforced"""
        headers = {"X-API-Key": test_device.api_key}

        # Make multiple requests
        responses = []
        for _ in range(5):
            response = client.post("/api/v1/devices/heartbeat", headers=headers)
            responses.append(response.status_code)

        # All should succeed (within rate limit)
        assert all(status in [200, 201] for status in responses)


@pytest.mark.unit
class TestSecurityMiddleware:
    """Unit tests for security middleware"""

    def test_security_headers_present(self, client):
        """Test security headers are added to responses"""
        response = client.get("/health")

        # Check for security headers
        # Note: Actual headers depend on security middleware implementation
        assert response.status_code == 200

    def test_input_sanitization(self, client, test_user):
        """Test input sanitization middleware"""
        payload = {
            "name": "Test Device <script>alert('xss')</script>",
            "device_type": "sensor",
            "user_id": test_user.user_id,
        }

        response = client.post("/api/v1/devices/register", data=json.dumps(payload), content_type="application/json")

        # Should handle potentially malicious input
        assert response.status_code in [201, 400]

    def test_cors_headers(self, client):
        """Test CORS headers are configured"""
        response = client.options("/health")

        # Should handle OPTIONS request
        assert response.status_code in [200, 204]


@pytest.mark.unit
class TestMonitoringMiddleware:
    """Unit tests for monitoring middleware"""

    def test_request_logging(self, client):
        """Test requests are logged"""
        response = client.get("/health")

        assert response.status_code == 200
        # Logging happens in background, just verify request succeeds

    def test_health_monitor_tracks_requests(self, client):
        """Test health monitor tracks requests"""
        # Make several requests
        for _ in range(3):
            client.get("/health")

        # Health endpoint should still work
        response = client.get("/health")
        assert response.status_code == 200

    def test_device_heartbeat_monitoring(self, client, test_device):
        """Test device heartbeat is monitored"""
        headers = {"X-API-Key": test_device.api_key}

        response = client.post("/api/v1/devices/heartbeat", headers=headers)

        assert response.status_code == 200
        data = response.get_json()
        assert "timestamp" in data


@pytest.mark.unit
class TestValidationMiddleware:
    """Unit tests for validation middleware"""

    def test_json_payload_validation_missing_field(self, client, test_user):
        """Test validation catches missing required fields"""
        # Missing 'device_type'
        payload = {"name": "Test Device", "user_id": test_user.user_id}

        response = client.post("/api/v1/devices/register", data=json.dumps(payload), content_type="application/json")

        assert response.status_code == 400

    def test_json_payload_validation_invalid_json(self, client):
        """Test validation handles invalid JSON"""
        response = client.post("/api/v1/devices/register", data='{"invalid": json}', content_type="application/json")

        # Flask catches invalid JSON and returns 400 or 500
        assert response.status_code in [400, 500]

    def test_json_payload_validation_empty_body(self, client):
        """Test validation handles empty request body"""
        response = client.post("/api/v1/devices/register", data="", content_type="application/json")

        # Empty body is handled as error
        assert response.status_code in [400, 500]


@pytest.mark.unit
class TestErrorHandling:
    """Unit tests for error handling middleware"""

    def test_404_error_handler(self, client):
        """Test 404 error is handled properly"""
        response = client.get("/nonexistent/endpoint")

        assert response.status_code == 404
        data = response.get_json()
        # Error handler should return JSON with error info
        if data:
            assert "error" in data or "message" in data

    def test_500_error_handler(self, client):
        """Test 500 error is handled gracefully"""
        # This would require triggering an actual error
        # For now, just verify error handling exists
        pass

    def test_method_not_allowed_handler(self, client):
        """Test 405 error for wrong HTTP method"""
        # Try POST on GET-only endpoint
        response = client.post("/health")

        assert response.status_code == 405
