#include <SPI.h>
#include <Dhcp.h>
#include <Dns.h>
#include <ESP8266WiFi.h>
#include <WiFiUdp.h>
#include <coap-simple.h>
#include <DHT.h>
#define LEDP 2
#define DHTPIN D5

const char *ssid = "Galaxy";
const char *password = "8910jqka";
const int coapPort = 5684; // Default CoAP port
const String resourcePath = "ledstate";
unsigned long interval = 5000;
const int interval2 = 10000;
unsigned long previousMillis = 0;
unsigned long previousMillis2 = 0;
unsigned long currentMillis2 = 0;

DHT dht(DHTPIN, DHT11);
float temperature;
float humidity;
int count = 1;
// CoAP client response callback
void callback_response(CoapPacket &packet, IPAddress ip, int port);

// CoAP server endpoint url callback
void callback_light(CoapPacket &packet, IPAddress ip, int port);

void callback_time(CoapPacket &packet, IPAddress ip, int port);

// UDP and CoAP class
WiFiUDP udp;
Coap coap(udp);

// LED STATE
bool LEDSTATE;

// CoAP server endpoint URL
void callback_light(CoapPacket &packet, IPAddress ip, int port)
{
  Serial.println("[led] ON/OFF");

  // send response
  char p[packet.payloadlen + 1];
  memcpy(p, packet.payload, packet.payloadlen);
  p[packet.payloadlen] = NULL;

  String message(p);
  Serial.println(message);

  if (message.equals("0"))
    LEDSTATE = false;
  else if (message.equals("1"))
    LEDSTATE = true;

  if (LEDSTATE)
  {
    digitalWrite(LEDP, LOW);
    Serial.println("ON");
    coap.sendResponse(ip, port, packet.messageid, "1", 1, COAP_CONTENT, COAP_TEXT_PLAIN, packet.token, packet.tokenlen);
  }
  else
  {
    digitalWrite(LEDP, HIGH);
    Serial.println("OFF");
    coap.sendResponse(ip, port, packet.messageid, "0", 1, COAP_CONTENT, COAP_TEXT_PLAIN, packet.token, packet.tokenlen);
  }
}

void callback_time(CoapPacket &packet, IPAddress ip, int port)
{
  Serial.println("Time");

  // send response
  char p[packet.payloadlen + 1];
  memcpy(p, packet.payload, packet.payloadlen);
  p[packet.payloadlen] = NULL;

  String message(p);
  Serial.println(message);

  float time_in_sec = message.toFloat();
  interval = time_in_sec * 1000;

  coap.sendResponse(ip, port, packet.messageid, message.c_str(), message.length(), COAP_CONTENT, COAP_TEXT_PLAIN, packet.token, packet.tokenlen);
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

  // LED State
  pinMode(LEDP, OUTPUT);
  digitalWrite(LEDP, HIGH);
  LEDSTATE = false;

  Serial.println("Setup Callback Light");
  coap.server(callback_light, "led");

  Serial.println("Setup Callback Time");
  coap.server(callback_time, "time");

  Serial.println("Setup Response Callback");
  coap.response(callback_response);

  // start coap server/client
  coap.start();
}

void loop()
{
  bool LED_STATE = digitalRead(LEDP);
  String responsePayload = LED_STATE ? "false" : "true";
  humidity = random(20, 100);
  temperature = random(10, 40);

  if (LED_STATE == false)
  {
    if (count == 1)
    {
      currentMillis2 = millis();
      previousMillis2 = currentMillis2;
      count++;
    }
    if (currentMillis2 - previousMillis2 >= interval2)
    {
      digitalWrite(LEDP, HIGH);
      Serial.println("Pump OFF");
      count = 1;  
    }
    else
    {
      currentMillis2 = millis();
      Serial.println("Pump is running");
    }
  }

  if (isnan(humidity) || isnan(temperature))
  {
    Serial.println("Failed to read from DHT sensor");
    return;
  }
  unsigned long currentMillis = millis(); // Read current time

  if (currentMillis - previousMillis >= interval)
  {
    previousMillis = currentMillis;
    char msg[100];
    snprintf(msg, sizeof(msg), "{\"state\": %s,\"temperature\": %.1f,\"humidity\": %.1f}", responsePayload.c_str(), temperature, humidity);
    Serial.println(msg);
    coap.put(IPAddress(192, 168, 109, 23), coapPort, resourcePath.c_str(), msg);
    Serial.println("Send to HC");
    delay(50);
  }
  // delay(interval2);
  coap.loop();
}
