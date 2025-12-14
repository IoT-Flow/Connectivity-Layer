# MQTT Endpoints Used by Admin Front (Connectivity-Layer)

This file documents the MQTT-related HTTP endpoints provided by the Flask `Connectivity-Layer` backend that are consumed by the admin UI and developer tools.

## Endpoints (admin / monitoring / developer tools)

- GET /api/v1/mqtt/status
  - Purpose: Get MQTT broker and client status (connected, host, port, TLS)
  - Auth: Public
  - Frontend use: Broker status card on admin dashboard

- GET /api/v1/mqtt/monitoring/metrics
  - Purpose: Get MQTT metrics (handlers, subscriptions, topic counts)
  - Auth: Admin token required
  - Frontend use: Monitoring dashboards and metrics panels

- GET /api/v1/mqtt/topics/structure
  - Purpose: Return complete MQTT topic structures and examples
  - Auth: Public
  - Frontend use: Topic builder and topic helper UI

- GET /api/v1/mqtt/topics/device/<device_id>
  - Purpose: Return MQTT topic map for a device
  - Auth: Public
  - Frontend use: Device detail page helpers

- POST /api/v1/mqtt/publish
  - Purpose: Publish messages to MQTT (test/publish tool)
  - Auth: Service-level checks
  - Frontend use: Message inspector / publish tool

- POST /api/v1/mqtt/subscribe
  - Purpose: Ask backend to subscribe to a topic (admin helper)
  - Auth: Admin token required
  - Frontend use: Admin topic subscription helper

- POST /api/v1/mqtt/device/<device_id>/command
  - Purpose: Send a command to a device via MQTT (admin)
  - Auth: Admin token required
  - Frontend use: Device command panel (send control/config/firmware commands)

- POST /api/v1/mqtt/fleet/<group_id>/command
  - Purpose: Send a command to a fleet of devices via MQTT (admin)
  - Auth: Admin token required
  - Frontend use: Fleet command UI

- POST /api/v1/mqtt/telemetry/<device_id>
  - Purpose: Accept telemetry via HTTP proxy from MQTT gateways
  - Auth: X-API-Key required
  - Frontend use: Simulators and test tools

## Quick examples

Publish a message (developer tool):

```bash
curl -X POST http://localhost:5000/api/v1/mqtt/publish \
  -H 'Content-Type: application/json' \
  -d '{"topic":"iotflow/devices/1/telemetry","payload":{"temperature":25.5}}'
```

Send an admin device command:

```bash
curl -X POST http://localhost:5000/api/v1/mqtt/device/1/command \
  -H 'Content-Type: application/json' \
  -H 'X-Admin-Token: <ADMIN_TOKEN>' \
  -d '{"command_type":"control","command":{"action":"reboot"}}'
```

---

If you want, I can:
- Identify the exact frontend files (components/services) that call each endpoint and add file/line references.
- Generate example API client functions for the frontend `apiService`.
