#include <SPI.h>
#include <Dhcp.h>
#include <Dns.h>
#include <ESP8266WiFi.h>
#include <WiFiUdp.h>
#include <coap-simple.h>
#include <DHT_U.h>

const char *ssid = "Galaxy";
const char *password = "jfuj5678";
const int coapPort = 5683; // Default CoAP port
const String resourcePath = "dht11";

#define DHTPIN 5 

// DHT parameters
#define DHTTYPE DHT11
DHT_Unified dht(DHTPIN, DHTTYPE);
uint32_t delayMS;

// Parameters for using non-blocking delay
unsigned long previousMillis = 0;
const long interval = 5000;

String msgStr = ""; // MQTT message buffer

float temp, hum;

// CoAP client response callback
void callback_response(CoapPacket &packet, IPAddress ip, int port);

// CoAP server endpoint url callback
void callback_light(CoapPacket &packet, IPAddress ip, int port);

void callback_get_led(CoapPacket &packet, IPAddress ip, int port);

// UDP and CoAP class
WiFiUDP udp;
Coap coap(udp);

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

// CoAP client response callback
void callback_response(CoapPacket &packet, IPAddress ip, int port)
{
  char p[packet.payloadlen + 1];
  memcpy(p, packet.payload, packet.payloadlen);
  p[packet.payloadlen] = NULL;
}

void setup()
{
  Serial.begin(9600);
  // Initialize device.
  dht.begin();
  // get temperature sensor details.
  sensor_t sensor;
  dht.temperature().getSensor(&sensor);
  dht.humidity().getSensor(&sensor);

  setup_wifi();

  Serial.println("Setup Response Callback");
  coap.response(callback_response);

  // Start coap server/client
  coap.start();
}

void loop()
{
  unsigned long currentMillis = millis(); // read current time

  if (currentMillis - previousMillis >= interval)
  { // if current time - last time > 5 sec
    previousMillis = currentMillis;

    // read temp and humidity
    sensors_event_t event;
    dht.temperature().getEvent(&event);

    if (isnan(event.temperature))
    {
      Serial.println(F("Error reading temperature!"));
    }
    else
    {
      Serial.print(F("Temperature: "));
      temp = event.temperature;
      Serial.print(temp);
      Serial.println(F("°C"));
    }
    // Get humidity event and print its value.
    dht.humidity().getEvent(&event);
    if (isnan(event.relative_humidity))
    {
      Serial.println(F("Error reading humidity!"));
    }
    else
    {
      Serial.print(F("Humidity: "));
      hum = event.relative_humidity;
      Serial.print(hum);
      Serial.println(F("%"));
    }
    msgStr = "{\"temperature\":" + String(temp) + ",\"humidity\":" + String(hum) + "}";
    byte arrSize = msgStr.length() + 1;
    char msg[arrSize];

    Serial.print("PUBLISH DATA:");
    Serial.println(msgStr);
    msgStr.toCharArray(msg, arrSize);
    coap.put(IPAddress(192, 168, 109, 254), coapPort, resourcePath.c_str(), msg);
    msgStr = "";
    delay(50);
  }
}