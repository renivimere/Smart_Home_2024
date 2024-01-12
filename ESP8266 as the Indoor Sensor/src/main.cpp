#include <Adafruit_Sensor.h> // Library for Adafruit sensors, using for DHT
#include <DHT_U.h>           // DHT library which uses some func from Adafruit Sensor library
#include <ESP8266WiFi.h>     // Library for using ESP8266 WiFi
#include <PubSubClient.h>    // Library for MQTT
#include <ArduinoJson.h>     // Library for Parsing JSON

// Defining Pins
#define DHTPIN 5
#define LED D2

// DHT parameters
#define DHTTYPE DHT11
DHT_Unified dht(DHTPIN, DHTTYPE);
uint32_t delayMS;

// MQTT Credentials
const char *ssid = "Galaxy"; // Setting your AP SSID
const char *password = "8910jqka";       // Setting your AP password
const char *mqttServer = "192.168.109.23";   // MQTT URL
const char *mqttUserName = "";            // MQTT Username
const char *mqttPwd = "";                 // MQTT Password
const char *clientID = "";                // Client ID
const char *topic = "indoor/sensor";      // Publish Topic

// Parameters for using non-blocking delay
unsigned long previousMillis = 0;
unsigned long interval = 5000;

String msgStr = ""; // MQTT message buffer

float temp, hum;

// Setting up wifi and mqtt client
WiFiClient espClient;
PubSubClient client(espClient);

void setup_wifi()
{
  delay(10);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

void reconnect()
{
  while (!client.connected())
  {
    if (client.connect(clientID, mqttUserName, mqttPwd))
    {
      Serial.println("MQTT connected");
      client.subscribe("indoor/interval");
      Serial.println("Topic Subscribed");
    }
    else
    {
      Serial.print("failed, rc = ");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000); // wait 5sec and retry
    }
  }
}

// subscribe call back
void callback(char *topic, byte *payload, int length)
{
  Serial.print("Message arrived in topic: ");
  Serial.println(topic);
  Serial.print("Message:");
  for (int i = 0; i < length; i++)
  {
    Serial.print((char)payload[i]);
  }
  Serial.println();
  Serial.print("Message size :");
  Serial.println(length);
  Serial.println();
  Serial.println("-----------------------");

  StaticJsonDocument<256> doc; // read JSON data
  DeserializationError error = deserializeJson(doc, payload, length);

  if (error)
  {
    Serial.print("Failed to deserialize JSON: ");
    Serial.println(error.c_str());
    return;
  }

  interval = doc["params"];

  Serial.print("Interval: ");
  Serial.print(interval);
  Serial.println("s");
  interval = interval * 1000;
}

void setup()
{
  Serial.begin(9600);
  // Initialize device.
  dht.begin();
  // Get temperature sensor details.
  sensor_t sensor;
  dht.temperature().getSensor(&sensor);
  dht.humidity().getSensor(&sensor);

  setup_wifi();

  client.setServer(mqttServer, 1883); // Setting MQTT server
  client.setCallback(callback);       // Defining function which will be called when message is recieved.
}

void loop()
{
  if (!client.connected())
  {
    reconnect();
  }
  client.loop();

  unsigned long currentMillis = millis(); // Read current time

  if (currentMillis - previousMillis >= interval)
  {
    previousMillis = currentMillis;

    Serial.print(F("Temperature: "));
    temp = random(10, 40);
    Serial.print(temp);
    Serial.println(F("°C"));

    Serial.print(F("Humidity: "));
    hum = random(20, 100);
    Serial.print(hum);
    Serial.println(F("%"));

    msgStr = "{\"Temperature\":" + String(temp) + ",\"Humidity\":" + String(hum) + "}";
    byte arrSize = msgStr.length() + 1;
    char msg[arrSize];

    Serial.print("PUBLISH DATA:");
    Serial.println(msgStr);
    msgStr.toCharArray(msg, arrSize);
    client.publish(topic, msg);
    msgStr = "";
    delay(50);
  }
}
