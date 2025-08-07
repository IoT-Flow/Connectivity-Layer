/*
Simple Device Configuration for API Key Only Setup
Only edit the values below - everything else is automatic!
*/

#ifndef DEVICE_CONFIG_SIMPLE_H
#define DEVICE_CONFIG_SIMPLE_H

// ==============================================
// WIFI CONFIGURATION - EDIT THESE VALUES
// ==============================================
const char* WIFI_SSID = "CelluleRech";
const char* WIFI_PASSWORD = "cellrech2023$";

// ==============================================
// SERVER CONFIGURATION - EDIT THESE VALUES
// ==============================================
const char* SERVER_HOST = "10.200.242.133";  // Your IoTFlow server IP
const int HTTP_PORT = 5000;                  // Flask server port
const int MQTT_PORT = 1883;                  // MQTT broker port

// ==============================================
// DEVICE API KEY - GET THIS FROM WEB INTERFACE
// ==============================================
const String DEVICE_API_KEY = "7792e1aa708e6acccb2e4a800464ae5a5c9d5a000b12a2f62dfbab631805a3a3";

// ==============================================
// HARDWARE PINS - CHANGE IF NEEDED
// ==============================================
#define DHT_PIN 23        // DHT sensor pin
#define DHT_TYPE DHT11     // DHT11 or DHT22
#define LED_PIN 2         // Status LED pin

// ==============================================
// TIMING SETTINGS - ADJUST AS NEEDED
// ==============================================
const unsigned long TELEMETRY_INTERVAL = 10000;  // 10 seconds
const unsigned long HEARTBEAT_INTERVAL = 60000;  // 1 minute

#endif // DEVICE_CONFIG_SIMPLE_H
