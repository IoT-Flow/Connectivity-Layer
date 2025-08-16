from locust import HttpUser, task, between
import os
import random
import uuid
from datetime import datetime, timezone


class IoTFlowUser(HttpUser):
    """Simulated users exercising all IoTFlow endpoints.

    - Uses LOCUST_API_KEY and LOCUST_DEVICE_ID env vars when provided.
    - Falls back to attempting registration to obtain an API key.
    - Tasks cover devices, telemetry, admin, mqtt, control, and core endpoints.
    """

    wait_time = between(0.5, 2)

    def on_start(self):
        self.api_key = os.environ.get("LOCUST_API_KEY")
        self.device_id = os.environ.get("LOCUST_DEVICE_ID")
        self.admin_token = os.environ.get("IOTFLOW_ADMIN_TOKEN")
        self.user_id = os.environ.get("LOCUST_USER_ID", "test_user")

        # If no API key/device provided, try to register a device to obtain one.
        # if not self.api_key or not self.device_id:
        #     name = f"locust-device-{uuid.uuid4().hex[:8]}"
        #     payload = {
        #         "name": name,
        #         "device_type": "simulated_sensor",
        #         "user_id": self.user_id,
        #     }
        #     for _ in range(3):
        #         try:
        #             r = self.client.post("/api/v1/devices/register", json=payload, timeout=10)
        #             if r.status_code in (200, 201):
        #                 body = r.json()
        #                 device = body.get("device") or {}
        #                 self.api_key = self.api_key or device.get("api_key") or body.get("api_key")
        #                 self.device_id = self.device_id or str(device.get("id") or device.get("device_id"))
        #                 break
        #         except Exception:
        #             pass

    def _headers(self, include_api_key=True):
        headers = {"Content-Type": "application/json"}
        if include_api_key and self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    def _admin_headers(self):
        headers = {"Content-Type": "application/json"}
        if self.admin_token:
            headers["Authorization"] = f"admin {self.admin_token}"
        return headers

    def _telemetry_payload(self):
        return {
            "data": {
                "temperature": round(20 + random.random() * 10, 2),
                "humidity": round(30 + random.random() * 40, 2),
                "battery": round(50 + random.random() * 50, 1),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # Core endpoints
    @task(1)
    def root(self):
        self.client.get("/")

    @task(2)
    def health(self):
        self.client.get("/health")

    @task(1)
    def metrics(self):
        self.client.get("/metrics")

    @task(1)
    def status(self):
        self.client.get("/status")

    # # Device endpoints
    # @task(2)
    # def register_device(self):
    #     payload = {"name": f"locust-{uuid.uuid4().hex[:6]}", "device_type": "locust", "user_id": self.user_id}
    #     self.client.post("/api/v1/devices/register", json=payload, timeout=10)

    @task(2)
    def get_device_status(self):
        if not self.api_key:
            return
        headers = self._headers()
        self.client.get("/api/v1/devices/status", headers=headers, timeout=10)

    @task(1)
    def post_device_telemetry(self):
        payload = self._telemetry_payload()
        headers = self._headers()
        # device-specific endpoint expects API key auth; generic endpoint also supported
        endpoint = "/api/v1/devices/telemetry" if self.device_id else "/api/v1/telemetry"
        if not self.api_key:
            return
        self.client.post(endpoint, json=payload, headers=headers, timeout=10)

    @task(2)
    def list_device_telemetry(self):
        headers = self._headers()
        if not self.api_key or not self.device_id:
            return
        self.client.get(f"/api/v1/telemetry/{self.device_id}", headers=headers, timeout=10)

    @task(1)
    def get_device_telemetry_latest(self):
        headers = self._headers()
        if not self.api_key or not self.device_id:
            return
        self.client.get(f"/api/v1/telemetry/{self.device_id}/latest", headers=headers, timeout=10)

    @task(1)
    def get_telemetry_status(self):
        self.client.get("/api/v1/telemetry/status")

    @task(1)
    def delete_telemetry(self):
        # safe no-op: request may be rejected without proper auth
        headers = self._headers()
        if not self.api_key or not self.device_id:
            return
        payload = {"start_time": "-1h", "stop_time": "now"}
        self.client.request("DELETE", f"/api/v1/telemetry/{self.device_id}", headers=headers, json=payload, timeout=10)

    # Device config/credentials
    @task(1)
    def put_config(self):
        headers = self._headers()
        if not self.api_key:
            return
        payload = {"config_key": "sample", "config_value": "value"}
        self.client.put("/api/v1/devices/config", headers=headers, json=payload, timeout=10)

    @task(1)
    def get_config(self):
        headers = self._headers()
        if not self.api_key:
            return
        self.client.get("/api/v1/devices/config", headers=headers, timeout=10)

    @task(1)
    def post_config(self):
        headers = self._headers()
        if not self.api_key:
            return
        payload = {"config_key": "k", "config_value": "v"}
        self.client.post("/api/v1/devices/config", headers=headers, json=payload, timeout=10)

    @task(1)
    def get_credentials(self):
        headers = self._headers()
        if not self.api_key:
            return
        self.client.get("/api/v1/devices/credentials", timeout=10)

    @task(2)
    def heartbeat(self):
        headers = self._headers()
        payload = {"status": "alive"}
        if not self.api_key:
            return
        self.client.post("/api/v1/devices/heartbeat", headers=headers, json=payload, timeout=10)

    # Control routes
    @task(1)
    def post_control(self):
        if not self.device_id:
            return
        headers = self._headers()
        payload = {"command": "reboot"}
        if not self.api_key:
            return
        self.client.post(f"/api/v1/devices/{self.device_id}/control", headers=headers, json=payload, timeout=10)

    @task(1)
    def post_control_status(self):
        if not self.device_id:
            return
        headers = self._headers()
        payload = {"status": "acknowledged"}
        if not self.api_key:
            return
        self.client.post(f"/api/v1/devices/{self.device_id}/control/1/status", headers=headers, json=payload, timeout=10)

    @task(1)
    def get_pending_controls(self):
        if not self.device_id:
            return
        headers = self._headers()
        if not self.api_key:
            return
        self.client.get(f"/api/v1/devices/{self.device_id}/control/pending", timeout=10)

    # MQTT routes
    @task(1)
    def mqtt_status(self):
        self.client.get("/api/v1/mqtt/status", timeout=10)

    @task(2)
    def mqtt_publish(self):
        headers = self._headers()
        payload = {"topic": f"devices/{self.device_id or 'unknown'}/cmd", "payload": {"value": "on"}}
        if not self.api_key:
            return
        self.client.post("/api/v1/mqtt/publish", headers=headers, json=payload, timeout=10)

    @task(1)
    def mqtt_subscribe(self):
        payload = {"topic": "devices/+/telemetry"}
        self.client.post("/api/v1/mqtt/subscribe", json=payload, timeout=10)

    @task(1)
    def mqtt_topics_device(self):
        if self.device_id:
            self.client.get(f"/api/v1/mqtt/topics/device/{self.device_id}", timeout=10)

    @task(1)
    def mqtt_topics_structure(self):
        self.client.get("/api/v1/mqtt/topics/structure", timeout=10)

    @task(1)
    def mqtt_topics_validate(self):
        payload = {"topic": "devices/+/telemetry"}
        self.client.post("/api/v1/mqtt/topics/validate", json=payload, timeout=10)

    @task(1)
    def mqtt_device_command(self):
        if self.device_id:
            payload = {"command": "set", "parameters": {"value": 1}}
            self.client.post(f"/api/v1/mqtt/device/{self.device_id}/command", json=payload, timeout=10)

    @task(1)
    def mqtt_fleet_command(self):
        payload = {"command": "set"}
        self.client.post(f"/api/v1/mqtt/fleet/1/command", json=payload, timeout=10)

    @task(1)
    def mqtt_monitoring_metrics(self):
        # This endpoint requires admin token on the server; skip if not configured to avoid 401s
        if not self.admin_token:
            return
        headers = self._admin_headers()
        self.client.get("/api/v1/mqtt/monitoring/metrics", headers=headers, timeout=10)

    @task(1)
    def mqtt_telemetry_post(self):
        if self.device_id:
            payload = {"data": {"temp": 22}}
            if not self.api_key:
                return
            self.client.post(f"/api/v1/mqtt/telemetry/{self.device_id}", json=payload, timeout=10)

    # Admin routes
    @task(1)
    def admin_list_devices(self):
        # Skip admin calls if no admin token configured to avoid 401s
        if not self.admin_token:
            return
        headers = self._admin_headers()
        self.client.get("/api/v1/admin/devices", headers=headers, timeout=10)

    @task(1)
    def admin_get_device(self):
        if not self.admin_token or not self.device_id:
            return
        headers = self._admin_headers()
        self.client.get(f"/api/v1/admin/devices/{self.device_id}", headers=headers, timeout=10)

    @task(1)
    def admin_update_status(self):
        if not self.admin_token or not self.device_id:
            return
        headers = self._admin_headers()
        payload = {"status": "maintenance"}
        self.client.put(f"/api/v1/admin/devices/{self.device_id}/status", headers=headers, json=payload, timeout=10)

    @task(1)
    def admin_stats(self):
        if not self.admin_token:
            return
        headers = self._admin_headers()
        self.client.get("/api/v1/admin/stats", headers=headers, timeout=10)
