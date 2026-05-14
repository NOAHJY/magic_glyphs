#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

const char* ssid      = "bukankah ini my WiFi";
const char* password  = "23571113";
const char* serverURL = "https://web-production-f9ef2.up.railway.app/get-command";

const int LED_PIN = 16;

void handleCommand(String command) {
  if (command == "/star") {
    // Blink for 10 seconds
    unsigned long start = millis();
    while (millis() - start < 10000) {
      digitalWrite(LED_PIN, HIGH);
      delay(200);
      digitalWrite(LED_PIN, LOW);
      delay(200);
    }
  }
  else if (command == "/light_beam") {
    // Stay on for 10 seconds
    digitalWrite(LED_PIN, HIGH);
    delay(10000);
    digitalWrite(LED_PIN, LOW);
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("WiFi connected!");
}

void loop() {
  HTTPClient http;
  http.begin(serverURL);
  http.setTimeout(30000);
  int httpCode = http.GET();

  if (httpCode == 200) {
    String payload = http.getString();
    StaticJsonDocument<200> doc;
    deserializeJson(doc, payload);
    String command = doc["command"].as<String>();
    if (command != "null") {
      handleCommand(command);
    }
  }
  http.end();
  delay(2000);
}