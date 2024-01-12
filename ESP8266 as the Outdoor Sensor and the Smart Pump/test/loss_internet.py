import asyncio
import json
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt
import aiocoap.resource as resource
import aiocoap
import aiocoap.options
import logging
import threading
import socket
import sys
import time
# Global variables
connect = 0
thingsboard_connected = False
temper = 0
maxtemper = 15
client_tb = mqtt.Client()
client_tb.username_pw_set("FMvIjK5alCiIutrTA3JL")

async def check_internet_connection(loop):
    global connect
    while True:
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=5)
            print("Connected to the internet.")
            connect = 1
        except socket.error:
            print("Disconnected: No internet connection.")
            connect = 0
        await asyncio.sleep(5)  


def send_to_esp8266_state(led_status):
    async def send_request():
        esp8266_ip = "192.168.109.202"
        esp8266_port = 5683
        led_path = "led"

        uri = f"coap://{esp8266_ip}:{esp8266_port}/{led_path}"

        payload = "1" if led_status else "0"
        try:
            
            request = aiocoap.Message(code=aiocoap.PUT, uri=uri, payload=payload.encode('utf-8'), )
            context = await aiocoap.Context.create_client_context()
            response = await context.request(request).response
            print(f"Request sent to ESP8266: LED status {response.payload}")
        except Exception as e:
            print(f"Failed to send request to ESP8266: {e}")
    asyncio.run(send_request())
def send_to_esp8266_time(time_send):
    async def send_request():
        # Thiết lập thông tin CoAP của ESP8266
        esp8266_ip = "192.168.109.202"
        esp8266_port = 5683
        time_path = "time"

        # Gửi yêu cầu qua CoAP
        uri = f"coap://{esp8266_ip}:{esp8266_port}/{time_path}"

        payload = str(time_send)
        try:
            # Tạo đối tượng request trực tiếp và gửi yêu cầu
            request = aiocoap.Message(code=aiocoap.PUT, uri=uri, payload=payload.encode('utf-8') )
            context = await aiocoap.Context.create_client_context()
            response= await context.request(request).response
            print(f"Request sent to ESP8266: Time send {response.payload}")
        except Exception as e:
            print(f"Failed to send request to ESP8266: {e}")

    asyncio.run(send_request())

class DHT11Resource(resource.Resource):
    def __init__(self):
        super().__init__()

    async def render_put(self, request):
        
        payload = request.payload.decode('utf-8')
        data = json.loads(payload)
        temper = data.get("temperature")
        
        await self.send_to_thingsboard(data)

        
        return aiocoap.Message(code=aiocoap.CHANGED, payload=b"Data received successfully", mtype=aiocoap.NON)

    async def send_to_thingsboard(self, data):
        
        mqtt_server = "mqtt.thingsboard.cloud"
        mqtt_port = 1883
        access_token = "FMvIjK5alCiIutrTA3JL"
        topic = "v1/devices/me/telemetry"

        # Tạo chuỗi JSON từ dữ liệu nhận được
        payload = json.dumps({"3": data.get("state"),"temperature": data.get("temperature"), "humidity": data.get("humidity")})
        if connect == 1:
            # Gửi dữ liệu qua MQTT
            publish.single(topic, payload, hostname=mqtt_server, port=mqtt_port, auth={"username": access_token})
            print("Data sent to ThingsBoard:", payload)

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


async def handle_rpc_request(payload):
    method = payload.get("method")
    params = payload.get("params")

    if method == "setValue":
        if params is not None:
            if params:
                print("ON")
                
                send_to_esp8266_state(True)
            else:
                print("OFF")
                
                send_to_esp8266_state(False)
    if method == 'setTime':
        if params is not None:
            await send_to_esp8266_time(params)
            print("Time send: ", params)

def on_connect_tb(client, userdata, flags, rc):
        global thingsboard_connected
        if rc == 0:
            thingsboard_connected = True
            print(f"Connected to ThingsBoard with result code {rc}")
            client_tb.subscribe("v1/devices/me/rpc/request/+")
        else:
            thingsboard_connected = False
            print(f"Failed to connect to ThingsBoard with result code {rc}")
def on_message_tb(client, userdata, msg):
        payload_tb = json.loads(msg.payload)
        #print(f"Received message on ThingsBoard topic {msg.topic}: {payload_tb}")
        if msg.topic.startswith("v1/devices/me/rpc/request/"):
         asyncio.run(handle_rpc_request(payload_tb))
    
async def try_connect_to_thingsboard():
    try:
        if connect==1:
                client_tb.on_connect = on_connect_tb
                client_tb.on_message = on_message_tb
                client_tb.connect("mqtt.thingsboard.cloud", 1883, 60)
                client_tb.loop_start()
    except Exception as e:
        print(f"Failed to connect to ThingsBoard: {e}")
        

async def main():
    
    internet_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(internet_loop)

    internet_thread = threading.Thread(target=lambda: asyncio.run(check_internet_connection(internet_loop)))
    internet_thread.start()
    
   
    # Resource tree creation
    root = resource.Site()

    # Add resources
    root.add_resource(['ledstate'], DHT11Resource())
    root.add_resource(['led'],LEDResource())
    
    # Create server context
    context = await aiocoap.Context.create_server_context(root)

    try:
        
        while True:
          if connect==1:
            await try_connect_to_thingsboard() 
            await asyncio.sleep(5)
    except KeyboardInterrupt:
        print("Server stopped by user.")
    finally:
        
        internet_loop.stop()
        internet_thread.join()
        
        await context.shutdown()
        sys.exit() 

if __name__ == "__main__":
    asyncio.run(main())