/*
ESP32 Ultra-Simple MQTT Client for Pre-Registered IoTFlow Devices
Version: 3.0 - API Key Only

SETUP INSTRUCTIONS:
1. Register your device on the IoTFlow web interface
2. Copy the API key and paste it in device_config_simple.h
3. Set your WiFi credentials in device_config_simple.h
4. Upload to your ESP32
5. The device will automatically get its ID and start sending data

FEATURES:
- Only needs API key - no other credentials required
- Automatic device ID retrieval
- DHT sensor data transmission
- ESP32 system metrics
- Status LED indicators
- Automatic reconnection
- No persistent storage needed
*/

#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <DHT.h>
#include <time.h>
#include "device_config_simple.h"

// Alias for easier access
#define API_KEY DEVICE_API_KEY

// Hardware initialization
DHT dht(DHT_PIN, DHT_TYPE);
WiFiClient espClient;
PubSubClient client(espClient);

// Configure MQTT client with larger buffer
void setupMQTTClient() {
  client.setBufferSize(1024);  // Increase buffer size to 1KB
  client.setKeepAlive(60);     // Keep connection alive
  client.setSocketTimeout(30); // Longer timeout
}

// Simple device tracking (no credentials needed)
int device_id = -1;  // Will be extracted from API responses

// Timing variables
unsigned long lastTelemetry = 0;
unsigned long lastHeartbeat = 0;

// Status tracking
bool mqttConnected = false;

// Function declarations
void setup();
void loop();
void connectToWiFi();
void setupTime();
bool getDeviceIdFromServer();
void connectToMQTT();
void mqttCallback(char* topic, byte* payload, unsigned int length);
void sendTelemetryData();
void sendHeartbeat();
void handleCommand(const String& command);
String getTimestamp();
void blinkLED(int times, int delayMs = 200);
void logStatus(const String& message, bool success = true);

void setup() {
  Serial.begin(115200);
  delay(2000);
  
  logStatus("ESP32 IoTFlow Simple Client v3.0 Starting", true);
  
  // Validate API key
  if (API_KEY == "your_device_api_key_here" || API_KEY.length() < 10) {
    Serial.println("❌ ERROR: Invalid API key!");
    Serial.println("🔧 Please update device_config_simple.h with your device's API key");
    Serial.println("💡 Get your API key from the IoTFlow web interface");
    while(1) {
      blinkLED(5, 100);
      delay(2000);
    }
  }
  
  // Initialize hardware
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  dht.begin();
  
  logStatus("Hardware initialized", true);
  
  // Connect to WiFi
  connectToWiFi();
  
  // Setup time synchronization
  setupTime();
  
  // Get device ID from server using API key
  logStatus("Getting device ID from server...", true);
  if (!getDeviceIdFromServer()) {
    Serial.println("❌ Failed to get device ID");
    Serial.println("💡 Check your API key and server connection");
    while(1) {
      blinkLED(3, 500);
      delay(3000);
    }
  }
  
  // Setup MQTT
  setupMQTTClient();
  client.setServer(SERVER_HOST, MQTT_PORT);
  client.setCallback(mqttCallback);
  
  logStatus("Setup complete - Device ready for telemetry", true);
  blinkLED(3, 100);
}

void loop() {
  // Maintain MQTT connection
  if (!client.connected()) {
    connectToMQTT();
  }
  client.loop();
  
  unsigned long currentTime = millis();
  
  // Send telemetry data
  if (currentTime - lastTelemetry >= TELEMETRY_INTERVAL) {
    sendTelemetryData();
    lastTelemetry = currentTime;
  }
  
  // Send heartbeat
  if (currentTime - lastHeartbeat >= HEARTBEAT_INTERVAL) {
    sendHeartbeat();
    lastHeartbeat = currentTime;
  }
  
  delay(100);
}

void connectToWiFi() {
  Serial.print("🌐 Connecting to WiFi: ");
  Serial.println(WIFI_SSID);
  
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    
    // Blink LED while connecting
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    digitalWrite(LED_PIN, LOW);
    Serial.println("\n✅ WiFi connected successfully");
    Serial.println("📍 IP Address: " + WiFi.localIP().toString());
    Serial.println("📶 Signal Strength: " + String(WiFi.RSSI()) + " dBm");
    blinkLED(2, 200);
  } else {
    Serial.println("\n❌ WiFi connection failed");
    Serial.println("🔄 Restarting in 10 seconds...");
    delay(10000);
    ESP.restart();
  }
}

void setupTime() {
  Serial.print("🕐 Synchronizing time with NTP servers...");
  configTime(0, 0, "pool.ntp.org", "time.nist.gov");
  
  int timeout = 15;
  while (!time(nullptr) && timeout > 0) {
    delay(1000);
    Serial.print(".");
    timeout--;
  }
  
  if (timeout > 0) {
    Serial.println(" ✅ Time synchronized");
    time_t now = time(nullptr);
    Serial.println("📅 Current time: " + String(ctime(&now)));
  } else {
    Serial.println(" ⚠️ Time sync failed (using local time)");
  }
}

bool getDeviceIdFromServer() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("❌ WiFi not connected");
    return false;
  }
  
  HTTPClient http;
  String url = "http://" + String(SERVER_HOST) + ":" + String(HTTP_PORT) + "/api/v1/devices/credentials";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-API-Key", API_KEY);
  
  Serial.println("📡 Getting device ID from server...");
  Serial.println("🔗 URL: " + url);
  Serial.println("🔑 API Key: " + API_KEY.substring(0, 8) + "...");
  
  int httpCode = http.GET();
  String response = http.getString();
  
  Serial.println("📡 HTTP Response Code: " + String(httpCode));
  
  bool success = false;
  
  if (httpCode == 200) {
    DynamicJsonDocument doc(1024);
    DeserializationError error = deserializeJson(doc, response);
    
    if (!error && doc.containsKey("device")) {
      JsonObject deviceObj = doc["device"];
      device_id = deviceObj["id"];
      
      if (device_id > 0) {
        Serial.println("✅ Device ID retrieved: " + String(device_id));
        String device_name = deviceObj["name"].as<String>();
        String device_type = deviceObj["device_type"].as<String>();
        Serial.println("📝 Device Name: " + device_name);
        Serial.println("🏷️ Device Type: " + device_type);
        success = true;
      }
    } else {
      Serial.println("❌ Invalid response format");
      Serial.println("📄 Response: " + response);
    }
  } else if (httpCode == 401) {
    Serial.println("❌ Authentication failed - Invalid API key");
    Serial.println("💡 Please check your API key in the IoTFlow web interface");
  } else if (httpCode == 404) {
    Serial.println("❌ Device not found");
    Serial.println("💡 Please ensure the device is registered in IoTFlow");
  } else {
    Serial.println("❌ HTTP request failed: " + String(httpCode));
    Serial.println("📄 Response: " + response);
  }
  
  http.end();
  return success;
}

void connectToMQTT() {
  if (device_id <= 0) {
    Serial.println("⚠️ Cannot connect to MQTT - invalid device ID");
    return;
  }
  
  while (!client.connected()) {
    Serial.print("🔌 Connecting to MQTT broker...");
    
    String clientId = "esp32_simple_" + String(device_id);
    String lwt_topic = "iotflow/devices/" + String(device_id) + "/status/offline";
    
    if (client.connect(clientId.c_str(), NULL, NULL, lwt_topic.c_str(), 1, true, "offline")) {
      Serial.println(" ✅ Connected!");
      
      // Publish online status
      String online_topic = "iotflow/devices/" + String(device_id) + "/status/online";
      DynamicJsonDocument onlineDoc(256);
      onlineDoc["api_key"] = API_KEY;
      onlineDoc["timestamp"] = getTimestamp();
      onlineDoc["status"] = "online";
      onlineDoc["device_id"] = device_id;
      
      String onlinePayload;
      serializeJson(onlineDoc, onlinePayload);
      client.publish(online_topic.c_str(), onlinePayload.c_str(), true);
      
      // Subscribe to commands
      String command_topic = "iotflow/devices/" + String(device_id) + "/commands/control";
      client.subscribe(command_topic.c_str());
      
      Serial.println("📡 Online status published");
      Serial.println("👂 Subscribed to commands: " + command_topic);
      
      mqttConnected = true;
      blinkLED(2, 100);
      
    } else {
      Serial.print(" ❌ Failed, rc=");
      Serial.print(client.state());
      Serial.println(" retrying in 5 seconds");
      
      blinkLED(5, 100);
      delay(5000);
    }
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  
  Serial.println("📨 Command received: [" + String(topic) + "] " + message);
  
  // Parse JSON command
  DynamicJsonDocument doc(512);
  DeserializationError error = deserializeJson(doc, message);
  
  if (!error && doc.containsKey("command")) {
    handleCommand(doc["command"].as<String>());
  } else {
    // Simple string commands for testing
    if (message.indexOf("led_on") >= 0) {
      handleCommand("led_on");
    } else if (message.indexOf("led_off") >= 0) {
      handleCommand("led_off");
    } else if (message.indexOf("restart") >= 0) {
      handleCommand("restart");
    }
  }
}

void handleCommand(const String& command) {
  Serial.println("🎮 Processing command: " + command);
  
  if (command == "led_on") {
    digitalWrite(LED_PIN, HIGH);
    Serial.println("💡 LED turned ON");
  }
  else if (command == "led_off") {
    digitalWrite(LED_PIN, LOW);
    Serial.println("💡 LED turned OFF");
  }
  else if (command == "restart") {
    Serial.println("🔄 Restarting device...");
    delay(1000);
    ESP.restart();
  }
  else if (command == "status") {
    sendTelemetryData();
    Serial.println("📊 Status sent");
  }
  else {
    Serial.println("❓ Unknown command: " + command);
  }
}

void sendTelemetryData() {
  if (!mqttConnected || device_id <= 0) return;
  
  // Read DHT sensor
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  bool dht_valid = !isnan(temperature) && !isnan(humidity);
  
  // Get system metrics
  float cpu_temp = temperatureRead();
  uint32_t free_heap = ESP.getFreeHeap();
  int32_t wifi_rssi = WiFi.RSSI();
  uint32_t uptime = millis() / 1000;
  
  // Create smaller telemetry payload to avoid memory issues
  DynamicJsonDocument doc(256);  // Reduced size
  doc["api_key"] = API_KEY;
  doc["device_id"] = device_id;
  
  // Environmental data (only if valid)
  if (dht_valid) {
    doc["temperature"] = round(temperature * 10) / 10.0;
    doc["humidity"] = round(humidity);
  }
  
  // Essential system metrics only
  doc["cpu_temp"] = round(cpu_temp * 10) / 10.0;
  doc["free_heap"] = free_heap;
  doc["uptime"] = uptime;
  
  String payload;
  serializeJson(doc, payload);
  
  // Debug the payload
  Serial.println("📤 Telemetry payload (" + String(payload.length()) + " bytes): " + payload);
  
  String topic = "iotflow/devices/" + String(device_id) + "/telemetry/sensors";
  Serial.println("📡 Publishing to: " + topic);
  
  if (client.publish(topic.c_str(), payload.c_str())) {
    // Quick LED blink to indicate telemetry sent
    digitalWrite(LED_PIN, HIGH);
    delay(50);
    digitalWrite(LED_PIN, LOW);
    
    if (dht_valid) {
      Serial.println("✅ Telemetry sent - T:" + String(temperature, 1) + "°C H:" + String(humidity, 0) + "%");
    } else {
      Serial.println("✅ System telemetry sent - CPU:" + String(cpu_temp, 1) + "°C Heap:" + String(free_heap/1024) + "KB");
    }
  } else {
    Serial.println("❌ Failed to send telemetry");
    Serial.println("📊 MQTT state: " + String(client.state()));
    Serial.println("📶 WiFi status: " + String(WiFi.status()));
    Serial.println("💾 Free heap: " + String(ESP.getFreeHeap()));
    blinkLED(2, 200);
  }
}

void sendHeartbeat() {
  if (!mqttConnected || device_id <= 0) return;
  
  DynamicJsonDocument doc(256);
  doc["api_key"] = API_KEY;
  doc["timestamp"] = getTimestamp();
  doc["status"] = "alive";
  doc["device_id"] = device_id;
  doc["uptime"] = millis() / 1000;
  doc["free_heap"] = ESP.getFreeHeap();
  doc["wifi_rssi"] = WiFi.RSSI();
  
  String payload;
  serializeJson(doc, payload);
  
  String topic = "iotflow/devices/" + String(device_id) + "/status/heartbeat";
  
  if (client.publish(topic.c_str(), payload.c_str())) {
    Serial.println("💓 Heartbeat sent (uptime: " + String(millis()/1000) + "s)");
  } else {
    Serial.println("❌ Heartbeat failed");
  }
}

String getTimestamp() {
  time_t now = time(nullptr);
  if (now < 1000000000) {
    return String(millis() / 1000);
  }
  
  struct tm *timeinfo = gmtime(&now);
  char buffer[25];
  strftime(buffer, sizeof(buffer), "%Y-%m-%dT%H:%M:%SZ", timeinfo);
  return String(buffer);
}

void blinkLED(int times, int delayMs) {
  for (int i = 0; i < times; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(delayMs);
    digitalWrite(LED_PIN, LOW);
    delay(delayMs);
  }
}

void logStatus(const String& message, bool success) {
  if (success) {
    Serial.println("✅ " + message);
  } else {
    Serial.println("❌ " + message);
  }
}
