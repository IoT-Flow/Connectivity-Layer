# Connectivity-Layer (Flask) — API Reference

This document lists the HTTP endpoints implemented by the Flask `Connectivity-Layer` project (under `src/routes`).
Prefix: `/api/v1` for most blueprints (see each route for full path).

Authentication notes
- `X-API-Key` — Device/API key based authentication used for device endpoints.
- `require_admin_token` / `require_admin_token` — Admin-level access for protected admin endpoints.

---

## Devices (Blueprint: `/api/v1/devices`)

- POST /api/v1/devices/register
  - Register a new device (body: name, device_type, user_id, ...)
  - Auth: user_id-based verification in payload

- GET /api/v1/devices/status
  - Get the authenticated device status (requires X-API-Key)
  - Auth: X-API-Key (authenticate_device)

- POST /api/v1/devices/telemetry
  - Submit telemetry (device-authenticated)
  - Body: { data: {...}, metadata?, timestamp? }
  - Auth: X-API-Key

- GET /api/v1/devices/telemetry
  - Get telemetry for authenticated device (query params supported)
  - Auth: X-API-Key

- PUT /api/v1/devices/config
  - Update device info (status, location, versions)
  - Auth: X-API-Key

- GET /api/v1/devices/credentials
  - Retrieve device credentials (requires X-API-Key header)
  - Auth: X-API-Key

- POST /api/v1/devices/heartbeat
  - Device heartbeat endpoint
  - Auth: X-API-Key

- GET /api/v1/devices/mqtt-credentials
  - Get MQTT broker connection details and topics for the device
  - Auth: X-API-Key

- GET /api/v1/devices/config
  - Retrieve device configuration (active configurations)
  - Auth: X-API-Key

- POST /api/v1/devices/config
  - Create/update device configuration
  - Auth: X-API-Key

- GET /api/v1/devices/statuses
  - Get condensed statuses for all devices (dashboard)
  - Auth: none / optional (security headers applied)

- GET /api/v1/devices/<device_id>/status
  - Get detailed status for a specific device
  - Auth: none / optional (security headers applied)

- GET /api/v1/devices/<device_id>/telemetry (control blueprint endpoints)
  - Various telemetry endpoints available under /api/v1/telemetry (see Telemetry section)

- GET /api/v1/devices/credentials (already listed)


## Device Control (Blueprint mounted under `/api/v1/devices` in control.py)

- POST /api/v1/devices/<device_id>/control
  - Send control/command to device (stores command and publishes via MQTT)
  - Auth: X-API-Key (authenticate_device) — device may only control itself

- POST /api/v1/devices/<device_id>/control/<control_id>/status
  - Update command execution status (pending/completed/failed/acknowledged)
  - Auth: X-API-Key

- GET /api/v1/devices/<device_id>/control/pending
  - Retrieve pending control commands for a device
  - Auth: X-API-Key


## Telemetry (Blueprint: `/api/v1/telemetry`)

- POST /api/v1/telemetry
  - Store telemetry data in IoTDB
  - Auth: X-API-Key in header
  - Body: { data: {...}, metadata?, timestamp? }

- GET /api/v1/telemetry/device/<device_id>
  - Modern query endpoint (migration format) to retrieve paginated telemetry
  - Auth: X-API-Key
  - Query params: data_type, start_date, end_date, limit, page

- GET /api/v1/telemetry/<device_id>
  - Legacy telemetry retrieval (start_time, limit)
  - Auth: X-API-Key

- GET /api/v1/telemetry/<device_id>/latest
  - Get latest telemetry point for device
  - Auth: X-API-Key

- GET /api/v1/telemetry/device/<device_id>/aggregated
  - New aggregated telemetry query (data_type + aggregation required)
  - Auth: X-API-Key
  - Query params: data_type, aggregation, start_date, end_date

- GET /api/v1/telemetry/<device_id>/aggregated
  - Legacy aggregated endpoint (field, aggregation, window)
  - Auth: X-API-Key

- DELETE /api/v1/telemetry/<device_id>
  - Delete telemetry for device within a time range (body: start_time, stop_time)
  - Auth: X-API-Key

- GET /api/v1/telemetry/status
  - Get IoTDB service status and statistics (iotdb availability, host/port)
  - Auth: Public

- GET /api/v1/telemetry/user/<user_id>
  - Get telemetry across all devices for a user (requires device API key belonging to that user)
  - Auth: X-API-Key


## MQTT Management (Blueprint: `/api/v1/mqtt`)

- GET /api/v1/mqtt/status
  - Get MQTT broker/client status
  - Auth: Public

- POST /api/v1/mqtt/publish
  - Publish a message to MQTT broker (topic + payload)
  - Auth: none (service-level checks inside)

- POST /api/v1/mqtt/subscribe
  - Subscribe to a topic (admin-only)
  - Auth: admin token required

- GET /api/v1/mqtt/topics/device/<device_id>
  - Get topics for a device
  - Auth: Public

- GET /api/v1/mqtt/topics/structure
  - Get complete MQTT topic structure
  - Auth: Public

- POST /api/v1/mqtt/topics/validate
  - Validate an MQTT topic string
  - Auth: Public

- POST /api/v1/mqtt/device/<device_id>/command
  - Send a command to device via MQTT (admin-only)
  - Auth: Admin token

- POST /api/v1/mqtt/fleet/<group_id>/command
  - Send a fleet-level command via MQTT (admin-only)
  - Auth: Admin token

- GET /api/v1/mqtt/monitoring/metrics
  - Get MQTT monitoring metrics (admin-only)
  - Auth: Admin token

- POST /api/v1/mqtt/telemetry/<device_id>
  - Receive telemetry via MQTT-specific endpoint (accepts HTTP POSTs from gateways)
  - Auth: X-API-Key (checked in endpoint)


## Admin (Blueprint: `/api/v1/admin`)

- GET /api/v1/admin/devices
  - List all devices with complete information (admin)
  - Auth: Admin token

- GET /api/v1/admin/devices/<device_id>
  - Get device details (admin)
  - Auth: Admin token

- PUT /api/v1/admin/devices/<device_id>/status
  - Update device status (active/inactive/maintenance) (admin)
  - Auth: Admin token

- GET /api/v1/admin/stats
  - Get system-level statistics (device counts, telemetry note)
  - Auth: Admin token

- Additional admin endpoints: user/device management exist in `admin.py` (listing users, user devices, etc.) — admin-only.


---

## Endpoints used by the Frontend (IoTFlow Dashboard)

These endpoints are referenced by the dashboard frontend (`IoTFlow_Dashboard/iotflow-frontend`) for UI features, charts and admin pages. This list is derived from the frontend integration docs and code references in the dashboard repository.

- GET /api/v1/admin/stats
  - Used for system statistics on admin dashboard

- GET /api/v1/admin/devices
  - Used to populate device lists and admin device overviews

- GET /api/v1/telemetry/status
  - Health check for telemetry/IoTDB availability shown in UI

- POST /api/v1/telemetry
  - Used by device simulators or gateway integrations to submit telemetry (demo mode/tests)

- GET /api/v1/telemetry/<deviceId>
  - Retrieve device telemetry for charts and timelines

- GET /api/v1/telemetry/<deviceId>/latest
  - Retrieve the latest telemetry point for quick status widgets

- GET /api/v1/telemetry/<deviceId>/aggregated
  - Aggregated queries for charts (legacy and new aggregation endpoints)

- DELETE /api/v1/telemetry/<deviceId>
  - Admin action to delete telemetry in time ranges (used in admin tools)

- GET /api/v1/mqtt/topics/structure
  - Used by UI helpers that display MQTT topic structures or topic builders

- POST /api/v1/mqtt/publish
  - Used by developer/admin tools in the UI to publish test messages

- GET /api/v1/devices/statuses
  - Dashboard device list with online/offline status

- GET /api/v1/devices/<device_id>/status
  - Device detail status panel in dashboard

- GET /api/v1/devices/<device_id>/telemetry and /api/v1/devices/<device_id>/telemetry?limit=...
  - Used by device detail pages and charts

- POST /api/v1/devices/register
  - Device registration flows in demos and simulator integrations

- Endpoints under `/api/v1/admin` for user management (GET /users, PUT /users/:id, GET /users/:id/devices) are used by admin UI (see `USERS_MANAGEMENT_REBUILD_TDD_SUMMARY.md` in the dashboard repo)


---

If you'd like, I can:
- Add example cURL commands for each endpoint (per section).
- Generate an OpenAPI (Swagger) specification from these routes.
- Insert this file into project docs or link it from `README.md`.

Which would you prefer next?