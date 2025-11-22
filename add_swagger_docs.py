#!/usr/bin/env python3
"""
Script to add Swagger documentation to all route endpoints
"""

# Swagger documentation templates for each endpoint

DEVICE_REGISTER = '''"""Register a new IoT device
    ---
    tags:
      - Devices
    summary: Register new device
    description: Register a new IoT device with user authentication
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - name
              - device_type
              - user_id
            properties:
              name:
                type: string
                example: Temperature Sensor 1
              device_type:
                type: string
                example: sensor
              user_id:
                type: string
                example: fd596e05-a937-4eea-bbaf-2779686b9f1b
    responses:
      201:
        description: Device registered successfully
      400:
        description: Invalid input
    """'''

DEVICE_LIST = '''"""List all devices
    ---
    tags:
      - Devices
    summary: List devices
    description: Get list of all registered devices
    parameters:
      - name: user_id
        in: query
        schema:
          type: string
        description: Filter by user ID
      - name: status
        in: query
        schema:
          type: string
          enum: [active, inactive, maintenance]
        description: Filter by device status
      - name: limit
        in: query
        schema:
          type: integer
          default: 100
      - name: offset
        in: query
        schema:
          type: integer
          default: 0
    responses:
      200:
        description: List of devices
    """'''

TELEMETRY_POST = '''"""Submit telemetry data
    ---
    tags:
      - Telemetry
    summary: Submit telemetry data
    description: Submit telemetry data from an IoT device
    security:
      - ApiKeyAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - measurements
            properties:
              measurements:
                type: array
                items:
                  type: object
                  properties:
                    name:
                      type: string
                      example: temperature
                    value:
                      type: number
                      example: 25.5
                    unit:
                      type: string
                      example: celsius
    responses:
      201:
        description: Telemetry data stored successfully
      401:
        description: Unauthorized - invalid API key
    """'''

HEALTH_CHECK = '''"""Health check endpoint
    ---
    tags:
      - Health
    summary: Health check
    description: Basic health check endpoint
    parameters:
      - name: detailed
        in: query
        schema:
          type: boolean
          default: false
        description: Return detailed health information
    responses:
      200:
        description: System is healthy
    """'''

print("Swagger documentation templates created!")
print("\nTo add these to your routes:")
print("1. Replace the simple docstring with the full Swagger YAML docstring")
print("2. Restart the Flask server")
print("3. Visit http://localhost:5000/docs")
