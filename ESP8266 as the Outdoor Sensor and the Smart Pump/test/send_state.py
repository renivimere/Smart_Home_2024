#!/usr/bin/env python3

import asyncio
import json
import logging
import paho.mqtt.client as mqtt
import aiocoap
from aiocoap import resource, Context, Message, CHANGED
import threading

THINGSBOARD_HOST = 'mqtt.thingsboard.cloud'


#logging.basicConfig(level=logging.INFO)

thingsboard_connected = False
client_tb = mqtt.Client()  # Initialize client_tb as None
client_tb.username_pw_set("KDUmMReN8EFb58UQwI97")
client_tb.connect(THINGSBOARD_HOST, 1883, 60)

def on_connect(client, userdata, flags, rc):
    print('Connected with result code ' + str(rc))


def send_to_thingsboard(data):
    


    topic = "v1/devices/me/telemetry"

    # Tạo chuỗi JSON từ dữ liệu nhận được
    payload = json.dumps({"temperature": data.get("temperature"), "humidity": data.get("humidity")})
    #payload2 = json.dumps({"3": data.get("state")})

    # Gửi dữ liệu qua MQTT
    # client_tb.publish("v1/devices/me/attributes", payload2, qos=1)
    client_tb.publish(topic, payload, qos=1)
    #publish.single(topic, payload, hostname=mqtt_server, port=mqtt_port, auth={"username": access_token})
    #publish.single("v1/devices/me/attributes", payload2, hostname=mqtt_server, port=mqtt_port, auth={"username": access_token})


# async def send_to_thingsboard2(data):
#     global client_tb
#     try:
#         # Thiết lập thông tin MQTT của ThingsBoard
#         mqtt_server = "mqtt.thingsboard.cloud"
#         mqtt_port = 1883
#         access_token = "vQ0wcwWsapweTiXfP1dQ"
#         topic = "v1/devices/me/telemetry"

#         # Tạo chuỗi JSON từ dữ liệu nhận được
#         #payload = json.dumps({"temperature": data.get("temperature"), "humidity": data.get("humidity")})
#         payload2 = json.dumps({"3": data.get("state")})

#         # Gửi dữ liệu qua MQTT
#         client_tb.publish("v1/devices/me/attributes", payload2, qos=1)
#         # client_tb.publish(topic, payload, qos=1)
#         #publish.single(topic, payload, hostname=mqtt_server, port=mqtt_port, auth={"username": access_token})
#         #publish.single("v1/devices/me/attributes", payload2, hostname=mqtt_server, port=mqtt_port, auth={"username": access_token})
        
#         print("Dữ liệu đã được gửi đến ThingsBoard:", payload2)
#     except MqttError as e:
#         print(f"Lỗi khi gửi dữ liệu đến ThingsBoard: {e}")

class DHT11Resource(resource.Resource):
    def __init__(self):
        super().__init__()

    async def render_put(self, request):
        # Lấy dữ liệu từ payload của yêu cầu PUT
        payload = request.payload.decode('utf-8')
        data = json.loads(payload)

        print("temperature:", data.get("temperature"))
        print("humidity:", data.get("humidity"))
        # print("state:", data.get("state"))
        # self.led_status = data.get("state")

        send_to_thingsboard(data)


        return Message(code=CHANGED, payload=b"Data received!")
    async def render_get(self, request):
        # Trả về trạng thái LED hiện tại khi nhận lệnh GET
        return aiocoap.Message(payload=f"LED Status: {self.led_status}".encode('utf-8'))

def start_mqtt_client():
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    client_tb.on_connect = on_connect
    # loop.run_until_complete(client_tb.username_pw_set("Ct0YTI3Bnwf94e1sqJIz"))
    # loop.run_until_complete(client_tb.connect("mqtt.thingsboard.cloud", 1883, 60))
    
    loop.run_forever()

async def send():
    

    # Tạo một thread mới cho MQTT client
    mqtt_thread = threading.Thread(target=start_mqtt_client)
    mqtt_thread.start()

    # Tạo cây tài nguyên
    root = resource.Site()

    # Thêm tài nguyên
    root.add_resource(['dht11'], DHT11Resource())
    # Tạo ngữ cảnh máy chủ CoAP
    context = await Context.create_server_context(root)

    try:
        # Chạy vòng lặp sự kiện cho máy chủ CoAP
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        # Dọn dẹp khi thoát
        client_tb.loop_stop()
        client_tb.disconnect()
        await context.shutdown()

if __name__ == "__main__":
    # Tạo một vòng lặp sự kiện chung cho cả hai
    first_thread = threading.Thread(target=lambda: asyncio.run(send()))
    first_thread.start()

    # Chạy hàm chính trong vòng lặp sự kiện
    try:
        first_thread.join()
    except KeyboardInterrupt:
        first_thread.terminate()
        
        # Đảm bảo rằng vòng lặp sự kiện được đóng sau khi kết thúc
        
