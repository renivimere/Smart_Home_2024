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
thingsboard_connected = False
client_tb = mqtt.Client()
client_tb.username_pw_set("vQ0wcwWsapweTiXfP1dQ")
client_tb.connect("mqtt.thingsboard.cloud", 1883, 60)



import aiocoap

# logging.basicConfig(level=logging.INFO)

class LEDResource(resource.Resource):
    def __init__(self):
        super().__init__()

        # Trạng thái hiện tại của LED
        self.led_status = False

    async def render_put(self, request):
        # Lấy trạng thái mới từ payload của yêu cầu PUT
        payload = request.payload.decode('utf-8')
        new_status = True if payload == "1" else False

        # Cập nhật trạng thái LED
        self.led_status = new_status

        # In trạng thái mới
        print(f"LED Status set to: {self.led_status}")

        # Trả về một response thông báo thành công
        return aiocoap.Message(code=aiocoap.CHANGED, payload=f"LED Status: {self.led_status}".encode('utf-8'))
    async def render_get(self, request):
        # Trả về trạng thái LED hiện tại khi nhận lệnh GET
        return aiocoap.Message(payload=f"LED Status: {self.led_status}".encode('utf-8'))

def send_to_esp8266(led_status):
    async def send_request():
        # Thiết lập thông tin CoAP của ESP8266
        esp8266_ip = "192.168.109.201"
        esp8266_port = 5683
        led_path = "led"

        # Gửi yêu cầu qua CoAP
        uri = f"coap://{esp8266_ip}:{esp8266_port}/{led_path}"

        # Tạo một yêu cầu CoAP PUT với payload là "1" hoặc "0"
        payload = "1" if led_status else "0"
        try:
            # Tạo đối tượng request trực tiếp và gửi yêu cầu
            request = aiocoap.Message(code=aiocoap.PUT, uri=uri, payload=payload.encode('utf-8'), )
            context = await aiocoap.Context.create_client_context()
            response= await context.request(request).response
            print(f"Request sent to ESP8266: LED status {response.payload}")
        except Exception as e:
            print(f"Failed to send request to ESP8266: {e}")
    
    # Chạy coroutine
    asyncio.run(send_request())


def handle_rpc_request(payload):
    method = payload.get("method")
    params = payload.get("params")

    if method == "setValue":
        if params is not None:
            if params:
                print("ON")
                # Gửi yêu cầu bật LED đến ESP8266
                send_to_esp8266(True)
                
            else:
                print("OFF")
                # Gửi yêu cầu tắt LED đến ESP8266
                send_to_esp8266(False)

def on_connect_tb(client, userdata, flags, rc):
    global thingsboard_connected
    if rc == 0:
        thingsboard_connected = True
        print(f"Connected to ThingsBoard with result code {rc}")
        client_tb.subscribe("v1/devices/me/rpc/request/+")
    else:
        thingsboard_connected = False
        

def on_message_tb(client, userdata, msg):
    payload_tb = json.loads(msg.payload)
    #print(f"Received message on ThingsBoard topic {msg.topic}: {payload_tb}")
    if msg.topic.startswith("v1/devices/me/rpc/request/"):
        handle_rpc_request(payload_tb)

client_tb.on_connect = on_connect_tb
client_tb.on_message = on_message_tb




async def get():

    # Resource tree creation
    root = resource.Site()

    # Add resources
    #root.add_resource(['dht11'], DHT11Resource())
    
    led_resource = LEDResource()
    root.add_resource(['led'], led_resource)
    # Create server context
    context = await aiocoap.Context.create_server_context(root)

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
    # Tạo một event loop chung
    second_thread = threading.Thread(target=lambda: asyncio.run(get()))
    second_thread.start()

    # Chạy main trong event loop
    
    second_thread.join()
    
        