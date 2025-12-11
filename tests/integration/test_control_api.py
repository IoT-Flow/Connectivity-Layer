"""
Integration tests for device control API endpoints.
"""
import pytest
import json
from src.models import Device, DeviceControl, User, db


class TestControlCommands:
    """Test control command endpoints."""

    def test_send_control_command_success(self, client, test_device):
        """Test sending control command to device."""
        headers = {"X-API-Key": test_device.api_key}
        payload = {"command": "SET_THRESHOLD", "parameters": {"temp_max": 30, "humidity_max": 80}}

        response = client.post(f"/api/v1/control/{test_device.id}/control", json=payload, headers=headers)

        assert response.status_code == 201
        data = response.get_json()
        assert data["command"] == "SET_THRESHOLD"
        assert data["status"] == "pending"
        assert data["device_id"] == test_device.id
        assert "control_id" in data

    def test_send_control_command_without_auth(self, client, test_device):
        """Test sending control command without authentication."""
        payload = {"command": "RESTART", "parameters": {}}

        response = client.post(f"/api/v1/control/{test_device.id}/control", json=payload)

        assert response.status_code == 401

    def test_send_control_command_invalid_device(self, client, test_device):
        """Test sending control command to invalid device."""
        headers = {"X-API-Key": test_device.api_key}
        payload = {"command": "UPDATE_CONFIG", "parameters": {"setting": "value"}}

        response = client.post("/api/v1/control/999999/control", json=payload, headers=headers)

        assert response.status_code == 404

    def test_send_control_command_missing_command(self, client, test_device):
        """Test sending control command without command field."""
        headers = {"X-API-Key": test_device.api_key}
        payload = {"parameters": {"setting": "value"}}

        response = client.post(f"/api/v1/control/{test_device.id}/control", json=payload, headers=headers)

        assert response.status_code == 400

    def test_send_multiple_control_commands(self, client, test_device):
        """Test sending multiple control commands."""
        headers = {"X-API-Key": test_device.api_key}

        commands = [
            {"command": "RESTART", "parameters": {}},
            {"command": "UPDATE_FIRMWARE", "parameters": {"version": "1.2.3"}},
            {"command": "SET_MODE", "parameters": {"mode": "eco"}},
        ]

        control_ids = []
        for cmd in commands:
            response = client.post(f"/api/v1/control/{test_device.id}/control", json=cmd, headers=headers)
            assert response.status_code == 201
            data = response.get_json()
            control_ids.append(data["control_id"])

        # Verify all commands were created
        assert len(control_ids) == 3
        assert len(set(control_ids)) == 3  # All unique


class TestPendingControls:
    """Test pending control commands endpoints."""

    def test_get_pending_controls_empty(self, client, test_device):
        """Test getting pending controls when none exist."""
        headers = {"X-API-Key": test_device.api_key}

        response = client.get(f"/api/v1/control/{test_device.id}/control/pending", headers=headers)

        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_pending_controls_with_commands(self, client, test_device, app):
        """Test getting pending control commands."""
        # Create pending commands
        with app.app_context():
            controls = [
                DeviceControl(device_id=test_device.id, command="RESTART", status="pending", parameters={}),
                DeviceControl(
                    device_id=test_device.id, command="UPDATE_CONFIG", status="pending", parameters={"setting": "value"}
                ),
            ]
            for control in controls:
                db.session.add(control)
            db.session.commit()

        headers = {"X-API-Key": test_device.api_key}
        response = client.get(f"/api/v1/control/{test_device.id}/control/pending", headers=headers)

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 2

        commands = [item["command"] for item in data]
        assert "RESTART" in commands
        assert "UPDATE_CONFIG" in commands

    def test_get_pending_controls_excludes_completed(self, client, test_device, app):
        """Test that completed controls are not returned."""
        with app.app_context():
            controls = [
                DeviceControl(device_id=test_device.id, command="PENDING_CMD", status="pending"),
                DeviceControl(device_id=test_device.id, command="COMPLETED_CMD", status="completed"),
                DeviceControl(device_id=test_device.id, command="FAILED_CMD", status="failed"),
            ]
            for control in controls:
                db.session.add(control)
            db.session.commit()

        headers = {"X-API-Key": test_device.api_key}
        response = client.get(f"/api/v1/control/{test_device.id}/control/pending", headers=headers)

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]["command"] == "PENDING_CMD"

    def test_get_pending_controls_without_auth(self, client, test_device):
        """Test getting pending controls without authentication."""
        response = client.get(f"/api/v1/control/{test_device.id}/control/pending")

        assert response.status_code == 401

    def test_get_pending_controls_wrong_device(self, client, test_device, app):
        """Test getting pending controls for wrong device."""
        # Create another device
        with app.app_context():
            other_user = User(username="other_user", email="other@test.com")
            db.session.add(other_user)
            db.session.commit()

            other_device = Device(name="other_device", user_id=other_user.id, device_type="sensor")
            db.session.add(other_device)
            db.session.commit()
            other_device_api_key = other_device.api_key

        headers = {"X-API-Key": other_device_api_key}
        response = client.get(f"/api/v1/control/{test_device.id}/control/pending", headers=headers)

        assert response.status_code == 403


class TestControlStatus:
    """Test control status update endpoints."""

    def test_update_control_status_to_completed(self, client, test_device, app):
        """Test updating control status to completed."""
        # Create a pending control
        with app.app_context():
            control = DeviceControl(
                device_id=test_device.id, command="UPDATE_FIRMWARE", status="pending", parameters={"version": "1.2.3"}
            )
            db.session.add(control)
            db.session.commit()
            control_id = control.id

        headers = {"X-API-Key": test_device.api_key}
        payload = {"status": "completed", "result": {"success": True, "message": "Firmware updated successfully"}}

        response = client.post(
            f"/api/v1/control/{test_device.id}/control/{control_id}/status", json=payload, headers=headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "completed"

        # Verify in database
        with app.app_context():
            updated_control = DeviceControl.query.get(control_id)
            assert updated_control.status == "completed"
            assert updated_control.result is not None

    def test_update_control_status_to_failed(self, client, test_device, app):
        """Test updating control status to failed."""
        with app.app_context():
            control = DeviceControl(device_id=test_device.id, command="RESTART", status="pending")
            db.session.add(control)
            db.session.commit()
            control_id = control.id

        headers = {"X-API-Key": test_device.api_key}
        payload = {"status": "failed", "result": {"error": "Device not responding"}}

        response = client.post(
            f"/api/v1/control/{test_device.id}/control/{control_id}/status", json=payload, headers=headers
        )

        assert response.status_code == 200

        # Verify in database
        with app.app_context():
            updated_control = DeviceControl.query.get(control_id)
            assert updated_control.status == "failed"

    def test_update_control_status_without_auth(self, client, test_device, app):
        """Test updating control status without authentication."""
        with app.app_context():
            control = DeviceControl(device_id=test_device.id, command="TEST_CMD", status="pending")
            db.session.add(control)
            db.session.commit()
            control_id = control.id

        payload = {"status": "completed"}

        response = client.post(f"/api/v1/control/{test_device.id}/control/{control_id}/status", json=payload)

        assert response.status_code == 401

    def test_update_control_status_invalid_control_id(self, client, test_device):
        """Test updating status for invalid control ID."""
        headers = {"X-API-Key": test_device.api_key}
        payload = {"status": "completed"}

        response = client.post(f"/api/v1/control/{test_device.id}/control/999999/status", json=payload, headers=headers)

        assert response.status_code == 404

    def test_update_control_status_missing_status(self, client, test_device, app):
        """Test updating control status without status field."""
        with app.app_context():
            control = DeviceControl(device_id=test_device.id, command="TEST_CMD", status="pending")
            db.session.add(control)
            db.session.commit()
            control_id = control.id

        headers = {"X-API-Key": test_device.api_key}
        payload = {"result": {"message": "No status provided"}}

        response = client.post(
            f"/api/v1/control/{test_device.id}/control/{control_id}/status", json=payload, headers=headers
        )

        assert response.status_code == 400

    def test_update_control_status_with_result_data(self, client, test_device, app):
        """Test updating control status with detailed result data."""
        with app.app_context():
            control = DeviceControl(device_id=test_device.id, command="DIAGNOSTIC", status="pending")
            db.session.add(control)
            db.session.commit()
            control_id = control.id

        headers = {"X-API-Key": test_device.api_key}
        payload = {
            "status": "completed",
            "result": {
                "cpu_usage": 45.2,
                "memory_usage": 67.8,
                "temperature": 42.5,
                "uptime": 86400,
                "diagnostics": {"sensors": "ok", "connectivity": "ok", "storage": "warning"},
            },
        }

        response = client.post(
            f"/api/v1/control/{test_device.id}/control/{control_id}/status", json=payload, headers=headers
        )

        assert response.status_code == 200

        # Verify complex result data is stored
        with app.app_context():
            updated_control = DeviceControl.query.get(control_id)
            assert updated_control.result["cpu_usage"] == 45.2
            assert updated_control.result["diagnostics"]["storage"] == "warning"
