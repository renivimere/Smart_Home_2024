#!/usr/bin/env python3

import asyncio
import json
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt
import aiocoap.resource as resource
import aiocoap
import aiocoap.options
import logging
import threading
import aiocoap
import socket
import requests
import time

# Set the ThingsBoard host
THINGSBOARD_HOST = 'thingsboard.hust-2slab.org' 

# Set the ThingsBoard access token for device authentication
ACCESS_TOKEN = '4qskLfuCoEg08zdFYmqp' # Change the access token based on the device

# Set the ESp8266's IP address
ESP_IP = "192.168.150.71" # Run CoAP on ESP and get the right IP

# Set the Home Center's IP address
HC_IP = "192.168.150.23" #Run ipconfig on shell to get the right IP


ESP_PORT = 5683
HC_PORT = 5684

# Maximum number of attempts to reconnect to the Internet
MAX_RECONNECT_ATTEMPTS = 2

# Time interval (in seconds) between reconnection attempts
RECONNECT_INTERVAL = 5  


connect = 0
isInternet = True

# Threshold temperature value for a specific condition or action
max_temp = 29 # Change this using ThingsBoard Widget

thingsboard_connected = False

# Function to check Internet connection
def check_internet():
    global isInternet
    try:
        response = requests.get('http://www.google.com', timeout=5)
        isInternet = True
        return True
    except requests.ConnectionError:
        isInternet = False
        return False

# MQTT client instances for ThingsBoard
client_tb = mqtt.Client()
client_tb.username_pw_set(ACCESS_TOKEN)

class LEDResource(resource.Resource):
    def __init__(self):
        super().__init__()

        
        self.led_status = False

    async def render_put(self, request):
        
        payload = request.payload.decode('utf-8')
        new_status = True if payload == "1" else False

        
        self.led_status = new_status

        
        print(f"LED Status set to: {self.led_status}")

        
        return aiocoap.Message(code=aiocoap.CHANGED, payload=f"LED Status: {self.led_status}".encode('utf-8'))
    async def render_get(self, request):
        
        return aiocoap.Message(payload=f"LED Status: {self.led_status}".encode('utf-8'))

# Send CoAP request to ESP8266 to update LED status
async def send_to_esp8266_state(led_status):
    
        
    esp8266_ip = ESP_IP
    esp8266_port = ESP_PORT
    led_path = "led"

    
    uri = f"coap://{esp8266_ip}:{esp8266_port}/{led_path}"

    payload = "1" if led_status else "0"
    try:
        
        request = aiocoap.Message(code=aiocoap.PUT, uri=uri, payload=payload.encode('utf-8'), )
        context = await aiocoap.Context.create_client_context()
        response= await context.request(request).response
        print(f"Request sent to ESP8266: LED status {response.payload}")
    except Exception as e:
        print(f"Failed to send request to ESP8266: {e}")

 # Send CoAP request to ESP8266 to update LED status
async def send_to_esp8266_state_2(led_status):
    
    esp8266_ip = ESP_IP
    esp8266_port = ESP_PORT
    led_path = "led"

    
    uri = f"coap://{esp8266_ip}:{esp8266_port}/{led_path}"

    payload = "1" if led_status else "0"
    try:
        
        request = aiocoap.Message(code=aiocoap.PUT, uri=uri, payload=payload.encode('utf-8'), )
        context = await aiocoap.Context.create_client_context()
        response= await context.request(request).response
        print(f"Request sent to ESP8266: LED status {response.payload}")
    except Exception as e:
        print(f"Failed to send request to ESP8266: {e}")
       
    
# Send CoAP request to ESP8266 to update time
async def send_to_esp8266_time(time_send):
    
    esp8266_ip = ESP_IP
    esp8266_port = ESP_PORT
    time_path = "time"
    
    uri = f"coap://{esp8266_ip}:{esp8266_port}/{time_path}"

    payload = str(time_send)
    try:
        
        request = aiocoap.Message(code=aiocoap.PUT, uri=uri, payload=payload.encode('utf-8') )
        context = await aiocoap.Context.create_client_context()
        response= await context.request(request).response
        print(f"Request sent to ESP8266: Time send {response.payload}")
    except Exception as e:
        print(f"Failed to send request to ESP8266: {e}")

# Handle RPC requests received from ThingsBoard
def handle_rpc_request(payload):
    async def send():
        method = payload.get("method")
        params = payload.get("params")

        if method == "setLedState":
            if params is not None:
                if params:
                    print("ON")

                    await send_to_esp8266_state(True)
                else:
                    print("OFF")

                    await send_to_esp8266_state(False)
        if method == 'setTime':
            if params is not None:
                await send_to_esp8266_time(params)
                print("Time send: ", params)
        
        if method == 'setThreshold':
            if params is not None:
                print("Threshold: ", params)
                global max_temp
                max_temp = params
                print("max_temp: ", max_temp)  

    asyncio.run(send())

# Function to reconnect to ThingsBoard
async def reconnect_to_thingsboard():
    reconnect_attempts = 0
    reinternet_attempts = 0
    global isInternet
    while isInternet:
        if check_internet():
            
            try:
                client_tb.connect(THINGSBOARD_HOST, 1883, 60)
                client_tb.on_connect = on_connect_tb
                client_tb.on_message = on_message_tb
                
                isInternet = True
                break
            except Exception as e:
                print(f'Error reconnecting to ThingsBoard')
                if reconnect_attempts >= MAX_RECONNECT_ATTEMPTS:
                    print("Max reconnect attempts reached. No connection!!!")
                    isInternet = False
                else:
                    reconnect_attempts += 1
                    print(f"Reconnecting in {RECONNECT_INTERVAL} seconds...")
                    time.sleep(RECONNECT_INTERVAL)
        else:
            if reinternet_attempts >= MAX_RECONNECT_ATTEMPTS:
                print("Max reconnect attempts reached. No connection!!!")
                reinternet_attempts = 0
                isInternet = False
            else:
                reinternet_attempts += 1
                print(f"No Internet connection. Retrying in {RECONNECT_INTERVAL} seconds...")
                time.sleep(RECONNECT_INTERVAL)

# Subscribe to the ThingsBoard RPC topic upon connection
def on_connect_tb(client, userdata, flags, rc):
    client_tb.subscribe("v1/devices/me/rpc/request/+")

# Handle incoming messages on the ThingsBoard RPC topic
def on_message_tb(client, userdata, msg):
    payload_tb = json.loads(msg.payload)
    print(f"Received message on ThingsBoard topic {msg.topic}: {payload_tb}")
    if msg.topic.startswith("v1/devices/me/rpc/request/"):
       handle_rpc_request(payload_tb)

# Handle PUT request for DHT11 sensor data
class DHT11Resource(resource.Resource):
    def __init__(self):
        super().__init__()

    async def render_put(self, request):

        payload = request.payload.decode('utf-8')
        data = json.loads(payload)

        print(data.get("temperature"))
        if isInternet:
            await self.temp_threshold(data)
            await self.send_to_thingsboard(data)
        else:
            print("====")
            await self.on_disconect_internet(data)
        
        return aiocoap.Message(code=aiocoap.CHANGED, payload=b"Data received successfully")
    
    # Send sensor data to ThingsBoard via MQTT
    async def send_to_thingsboard(self, data):
        
        mqtt_server = THINGSBOARD_HOST
        mqtt_port = 1883
        access_token = ACCESS_TOKEN
        topic = "v1/devices/me/telemetry"

        payload = json.dumps({"3": data.get("state"),"Temperature": data.get("temperature"), "Humidity": data.get("humidity")})

        publish.single(topic, payload, hostname=mqtt_server, port=mqtt_port, auth={"username": access_token})
        print("Data sent to ThingsBoard:", payload)
    
    # Handle disconnection from the internet
    async def on_disconect_internet(self,data):
        temp_now = data.get("temperature")
        if temp_now > max_temp:
            print("Temp too high")
            await send_to_esp8266_state_2(True)
        check_internet()
        await reconnect_to_thingsboard()
    
    # Check if temperature exceeds the threshold
    async def temp_threshold(self,data):
        temp_now2 = data.get("temperature")
        if temp_now2 > max_temp:
            print("Temp too high")
            await send_to_esp8266_state_2(True)
        
# Main function to run the CoAP server and handle MQTT communication        
async def main():

    # Resource tree creation
    root = resource.Site()

    # Add resources
    root.add_resource(['ledstate'], DHT11Resource())
    led_resource = LEDResource()
    root.add_resource(['led'], led_resource)
    # Create server context
    context = await aiocoap.Context.create_server_context(root,bind=(HC_IP, HC_PORT))
    
    # Run MQTT client loop
    client_tb.loop_start()

    try:
        # Run the server
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Server stopped by user.")
    finally:
        # Clean up
        client_tb.loop_stop()
        await context.shutdown()

if __name__ == "__main__":
    
    event_loop = asyncio.new_event_loop()

    # Periodically check and reconnect to ThingsBoard if disconnected
    try:
        async def internet_check():
            while True:
                await reconnect_to_thingsboard()
                await asyncio.sleep(RECONNECT_INTERVAL)

        internet_check_task = event_loop.create_task(internet_check())

        event_loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
    finally:
        internet_check_task.cancel()
        event_loop.close()