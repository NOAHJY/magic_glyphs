#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

const char* ssid      = "my WiFi 2.4G";
const char* password  = "23571113";
const char* serverURL = "https://web-production-f9ef2.up.railway.app/get-command";

const int LED_PIN = 4;
const int led2 = 2;

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
  else if (command == "/light") {
    // Stay on for 10 seconds
    digitalWrite(LED_PIN, HIGH);
    delay(10000);
    digitalWrite(LED_PIN, LOW);
  }
  else if (command == "/love"){
    // Blinking 2 lights
    digitalWrite(LED_PIN, HIGH);
    digitalWrite(led2, LOW);
    delay(500);
    digitalWrite(LED_PIN, LOW);
    digitalWrite(led2, HIGH);
    delay(500);
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
  // Test LED at startup
  digitalWrite(LED_PIN, HIGH);
  delay(1000);
  digitalWrite(LED_PIN, LOW);
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
      Serial.println("Command received: " + command);
      handleCommand(command);
    }
  }
  http.end();
  delay(2000);
  
}