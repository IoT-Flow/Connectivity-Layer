"""
Integration tests for Control API endpoints
Following TDD principles - tests written before implementation review
"""
import pytest
from src.models import Device, DeviceControl, db
import time


class TestControlCommands:
    """Test sending control commands to devices"""

    def test_send_control_command_success(self, client, test_device):
        """Test successfully sending a control command to a device"""
        headers = {"X-API-Key": test_device.api_key}
        payload = {"command": "SET_THRESHOLD", "parameters": {"temp_max": 30, "temp_min": 10}}

        response = client.post(f"/api/v1/devices/{test_device.id}/control", json=payload, headers=headers)

        assert response.status_code == 201
        data = response.get_json()
        assert data["command"] == "SET_THRESHOLD"
        assert data["status"] == "pending"
        assert data["device_id"] == test_device.id
        assert "id" in data
        assert "created_at" in data

    def test_send_control_command_without_auth(self, client, test_device):
        """Test that control command requires authentication"""
        payload = {"command": "RESTART", "parameters": {}}

        response = client.post(f"/api/v1/devices/{test_device.id}/control", json=payload)

        assert response.status_code == 401

    def test_send_control_command_invalid_device(self, client, test_device):
        """Test sending command to non-existent device"""
        headers = {"X-API-Key": test_device.api_key}
        payload = {"command": "RESTART", "parameters": {}}

        response = client.post("/api/v1/devices/99999/control", json=payload, headers=headers)

        assert response.status_code in [403, 404]

    def test_send_control_command_missing_command(self, client, test_device):
        """Test that command field is required"""
        headers = {"X-API-Key": test_device.api_key}
        payload = {"parameters": {"value": 100}}

        response = client.post(f"/api/v1/devices/{test_device.id}/control", json=payload, headers=headers)

        assert response.status_code == 400

    def test_send_multiple_control_commands(self, client, test_device):
        """Test sending multiple commands to same device"""
        headers = {"X-API-Key": test_device.api_key}

        commands = [
            {"command": "SET_THRESHOLD", "parameters": {"temp_max": 30}},
            {"command": "RESTART", "parameters": {}},
            {"command": "UPDATE_CONFIG", "parameters": {"interval": 60}},
        ]

        for cmd in commands:
            response = client.post(f"/api/v1/devices/{test_device.id}/control", json=cmd, headers=headers)
            assert response.status_code == 201


class TestPendingControls:
    """Test retrieving pending control commands"""

    def test_get_pending_controls_empty(self, client, test_device):
        """Test getting pending controls when none exist"""
        headers = {"X-API-Key": test_device.api_key}

        response = client.get(f"/api/v1/devices/{test_device.id}/control/pending", headers=headers)

        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_pending_controls_with_commands(self, client, test_device, app):
        """Test getting pending control commands"""
        # Create pending commands
        with app.app_context():
            commands = [
                DeviceControl(device_id=test_device.id, command="RESTART", status="pending", parameters={}),
                DeviceControl(
                    device_id=test_device.id, command="SET_THRESHOLD", status="pending", parameters={"temp_max": 30}
                ),
            ]
            for cmd in commands:
                db.session.add(cmd)
            db.session.commit()

        headers = {"X-API-Key": test_device.api_key}
        response = client.get(f"/api/v1/devices/{test_device.id}/control/pending", headers=headers)

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 2
        assert all(cmd["status"] == "pending" for cmd in data)
        assert any(cmd["command"] == "RESTART" for cmd in data)
        assert any(cmd["command"] == "SET_THRESHOLD" for cmd in data)

    def test_get_pending_controls_excludes_completed(self, client, test_device, app):
        """Test that completed commands are not returned"""
        with app.app_context():
            pending = DeviceControl(device_id=test_device.id, command="RESTART", status="pending")
            completed = DeviceControl(device_id=test_device.id, command="UPDATE_CONFIG", status="completed")
            db.session.add(pending)
            db.session.add(completed)
            db.session.commit()

        headers = {"X-API-Key": test_device.api_key}
        response = client.get(f"/api/v1/devices/{test_device.id}/control/pending", headers=headers)

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]["command"] == "RESTART"
        assert data[0]["status"] == "pending"

    def test_get_pending_controls_without_auth(self, client, test_device):
        """Test that authentication is required"""
        response = client.get(f"/api/v1/devices/{test_device.id}/control/pending")

        assert response.status_code == 401

    def test_get_pending_controls_wrong_device(self, client, test_device, test_user, app):
        """Test that device can only see its own pending commands"""
        # Create another device
        with app.app_context():
            other_device = Device(name="Other_Device", user_id=test_user.id, device_type="sensor")
            db.session.add(other_device)
            db.session.commit()
            other_device_id = other_device.id

            # Create command for other device
            cmd = DeviceControl(device_id=other_device_id, command="SECRET_COMMAND", status="pending")
            db.session.add(cmd)
            db.session.commit()

        # Try to access with test_device credentials
        headers = {"X-API-Key": test_device.api_key}
        response = client.get(f"/api/v1/devices/{other_device_id}/control/pending", headers=headers)

        assert response.status_code in [403, 404]


class TestControlStatus:
    """Test updating control command status"""

    def test_update_control_status_to_completed(self, client, test_device, app):
        """Test updating control status to completed"""
        # Create pending command
        with app.app_context():
            control = DeviceControl(device_id=test_device.id, command="UPDATE_FIRMWARE", status="pending")
            db.session.add(control)
            db.session.commit()
            control_id = control.id

        headers = {"X-API-Key": test_device.api_key}
        payload = {"status": "completed", "result": {"success": True, "message": "Firmware updated"}}

        response = client.post(
            f"/api/v1/devices/{test_device.id}/control/{control_id}/status", json=payload, headers=headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "completed"

        # Verify in database
        with app.app_context():
            updated = DeviceControl.query.get(control_id)
            assert updated.status == "completed"

    def test_update_control_status_to_failed(self, client, test_device, app):
        """Test updating control status to failed"""
        with app.app_context():
            control = DeviceControl(device_id=test_device.id, command="RESTART", status="pending")
            db.session.add(control)
            db.session.commit()
            control_id = control.id

        headers = {"X-API-Key": test_device.api_key}
        payload = {"status": "failed", "result": {"error": "Connection timeout"}}

        response = client.post(
            f"/api/v1/devices/{test_device.id}/control/{control_id}/status", json=payload, headers=headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "failed"

    def test_update_control_status_without_auth(self, client, test_device, app):
        """Test that authentication is required"""
        with app.app_context():
            control = DeviceControl(device_id=test_device.id, command="RESTART", status="pending")
            db.session.add(control)
            db.session.commit()
            control_id = control.id

        payload = {"status": "completed"}

        response = client.post(f"/api/v1/devices/{test_device.id}/control/{control_id}/status", json=payload)

        assert response.status_code == 401

    def test_update_control_status_invalid_control_id(self, client, test_device):
        """Test updating non-existent control command"""
        headers = {"X-API-Key": test_device.api_key}
        payload = {"status": "completed"}

        response = client.post(f"/api/v1/devices/{test_device.id}/control/99999/status", json=payload, headers=headers)

        assert response.status_code == 404

    def test_update_control_status_missing_status(self, client, test_device, app):
        """Test that status field is required"""
        with app.app_context():
            control = DeviceControl(device_id=test_device.id, command="RESTART", status="pending")
            db.session.add(control)
            db.session.commit()
            control_id = control.id

        headers = {"X-API-Key": test_device.api_key}
        payload = {"result": {"message": "Done"}}

        response = client.post(
            f"/api/v1/devices/{test_device.id}/control/{control_id}/status", json=payload, headers=headers
        )

        assert response.status_code == 400

    def test_update_control_status_with_result_data(self, client, test_device, app):
        """Test updating status with detailed result data"""
        with app.app_context():
            control = DeviceControl(device_id=test_device.id, command="CALIBRATE_SENSOR", status="pending")
            db.session.add(control)
            db.session.commit()
            control_id = control.id

        headers = {"X-API-Key": test_device.api_key}
        payload = {
            "status": "completed",
            "result": {"calibration_offset": 0.5, "accuracy": 99.8, "timestamp": "2025-12-09T10:00:00Z"},
        }

        response = client.post(
            f"/api/v1/devices/{test_device.id}/control/{control_id}/status", json=payload, headers=headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "completed"
