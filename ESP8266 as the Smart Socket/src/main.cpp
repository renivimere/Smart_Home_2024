#include <ESP8266WiFi.h>  // Library for using ESP8266 WiFi
#include <PubSubClient.h> // Library for MQTT
#include <ArduinoJson.h>  // Library for Parsing JSON

// Defining Pins
//#define LED 2 for ESP8266 v3
#define LED D0 //for ESP8266 v2
// MQTT Credentials
const char *ssid = "Galaxy"; // Setting your AP SSID
const char *password = "8910jqka";       // Setting your AP password
const char *mqttServer = "192.168.109.23";   // MQTT URL
const char *mqttUserName = "";            // MQTT username
const char *mqttPwd = "";                 // MQTT password
const char *clientID = "";                // Client ID
const char *topic = "indoor/status";      // Publish Topic

// Parameters for using non-blocking delay
unsigned long previousMillis = 0;
const long interval = 5000;

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
      client.subscribe("indoor/command");
      Serial.println("Topic Subscribed");
    }
    else
    {
      Serial.print("failed, rc = ");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000); // Wait 5sec and retry
    }
  }
}

// Subscribe call back
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

  StaticJsonDocument<256> doc; // Read JSON data
  DeserializationError error = deserializeJson(doc, payload, length);

  if (error)
  {
    Serial.print("Failed to deserialize JSON: ");
    Serial.println(error.c_str());
    return;
  }

  bool command_parameters_led = doc["params"];

  Serial.print("LED Command: ");
  Serial.println(command_parameters_led);

  digitalWrite(LED, command_parameters_led ? LOW : HIGH);
}

void setup()
{
  Serial.begin(9600);
  pinMode(LED, OUTPUT);
  digitalWrite(LED, HIGH);

  setup_wifi();

  client.setServer(mqttServer, 1883); // Setting MQTT server
  client.setCallback(callback);       // Defining function which will be called when message is recieved.
}

bool readLedState()
{
  return digitalRead(LED) == LOW;
}

String createJsonString()
{
  DynamicJsonDocument doc(256);
  doc["3"] = readLedState(); // Change ledstate to 3
  String jsonString;
  serializeJson(doc, jsonString);
  return jsonString;
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
    msgStr = createJsonString();
    byte arrSize = msgStr.length() + 1;
    char msg[arrSize];

    Serial.print("PUBLISH STATUS:");
    Serial.println(msgStr);
    msgStr.toCharArray(msg, arrSize);
    client.publish(topic, msg);
    msgStr = "";
    delay(50);
  }
}
