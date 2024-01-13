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

THINGSBOARD_HOST = 'thingsboard.hust-2slab.org'
ACCESS_TOKEN = '4qskLfuCoEg08zdFYmqp'
ESP_IP = "192.168.109.202"
ESP_PORT = 5683
HC_PORT = 5684
MAX_RECONNECT_ATTEMPTS = 2
RECONNECT_INTERVAL = 5  # seconds


connect = 0
isInternet = True
max_temp = 29

thingsboard_connected = False

# client_tb.connect(THINGSBOARD_HOST, 1883, 60)


def check_internet():
    global isInternet
    try:
        response = requests.get('http://www.google.com', timeout=5)
        isInternet = True
        return True
    except requests.ConnectionError:
        isInternet = False
        return False

client_tb = mqtt.Client()
client_tb.username_pw_set(ACCESS_TOKEN)
#client_tb.connect(THINGSBOARD_HOST, 1883, 60)

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

def on_connect_tb(client, userdata, flags, rc):
    client_tb.subscribe("v1/devices/me/rpc/request/+")
    #print(f"Connected to ThingsBoard with result code {rc}")    

def on_message_tb(client, userdata, msg):
    payload_tb = json.loads(msg.payload)
    print(f"Received message on ThingsBoard topic {msg.topic}: {payload_tb}")
    if msg.topic.startswith("v1/devices/me/rpc/request/"):
       handle_rpc_request(payload_tb)


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

    async def send_to_thingsboard(self, data):
        
        mqtt_server = THINGSBOARD_HOST
        mqtt_port = 1883
        access_token = ACCESS_TOKEN
        topic = "v1/devices/me/telemetry"

        payload = json.dumps({"3": data.get("state"),"Temperature": data.get("temperature"), "Humidity": data.get("humidity")})

        # Gửi dữ liệu qua MQTT
        publish.single(topic, payload, hostname=mqtt_server, port=mqtt_port, auth={"username": access_token})
        print("Data sent to ThingsBoard:", payload)
    async def on_disconect_internet(self,data):
        temp_now = data.get("temperature")
        if temp_now > max_temp:
            print("Temp too high")
            await send_to_esp8266_state_2(True)
        check_internet()
        await reconnect_to_thingsboard()
    
    async def temp_threshold(self,data):
        temp_now2 = data.get("temperature")
        if temp_now2 > max_temp:
            print("Temp too high")
            await send_to_esp8266_state_2(True)
        
        
async def main():

    # Resource tree creation
    root = resource.Site()

    # Add resources
    root.add_resource(['ledstate'], DHT11Resource())
    led_resource = LEDResource()
    root.add_resource(['led'], led_resource)
    # Create server context
    context = await aiocoap.Context.create_server_context(root,bind=("::", HC_PORT))
    
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
    
    event_loop = asyncio.get_event_loop()

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