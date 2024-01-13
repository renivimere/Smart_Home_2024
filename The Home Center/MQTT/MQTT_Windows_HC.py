import threading
import time
import paho.mqtt.client as mqtt
import json
import requests

# Set the ThingsBoard host
THINGSBOARD_HOST = 'thingsboard.hust-2slab.org'

# Set the ThingsBoard access token for device authentication
ACCESS_TOKEN = 'zXQJfHshl3GQxUZrN2rv' # Change the access token based on the device

# Define the ThingsBoard telemetry topic for sending data
THINGSBOARD_TOPIC = 'v1/devices/me/telemetry' 

# Set the Mosquitto broker's IP address
MOSQUITTO_BROKER = '192.168.150.23' # Run ipconfig on the shell to get the correct IP

# Subscribe to this topic to receive Temperature and Humidity data
MOSQUITTO_TOPIC = 'indoor/sensor'  

# Subscribe to this topic to get the LED state
MOSQUITTO_TOPIC_2 = 'indoor/status' 

# Publish to this topic to control the LED
MOSQUITTO_LED = 'indoor/command'    

# Publish to this topic to change the data reporting interval
MOSQUITTO_TIME = 'indoor/interval' 

# Maximum number of attempts to reconnect to the Internet
MAX_RECONNECT_ATTEMPTS = 2

# Time interval (in seconds) between reconnection attempts
RECONNECT_INTERVAL = 5  

# Threshold temperature value for a specific condition or action
THRESHOLD_TEMPERATURE = 29.0 # Change this using ThingsBoard Widget

isInternet = True

# MQTT client instances for Mosquitto and ThingsBoard
client_mosquitto = mqtt.Client()
client_thingsboard = mqtt.Client()
client_thingsboard.username_pw_set(ACCESS_TOKEN)

# Function to check Internet connection
def check_internet():
    global isInternet
    try:
        response = requests.get('http://www.google.com', timeout=5)
        return True
    except requests.ConnectionError:
        return False

# Callback function for ThingsBoard disconnection event
def on_disconnect_thingsboard(client, userdata, rc):
    if rc != 0 :  
        print(f"Disconnected from ThingsBoard with result code {rc}")  
        reconnect_to_thingsboard()

# Callback function for ThingsBoard connection event
def on_connect_thingsboard(client, userdata, rc, *extra_params):
    print('Connected with result code ' + str(rc))
    # Subscribing to receive RPC requests
    client.subscribe('v1/devices/me/rpc/request/+')

# Function to reconnect to ThingsBoard
def reconnect_to_thingsboard():
    reconnect_attempts = 1
    reinternet_attempts = 1
    global isInternet
    while True:
        if check_internet():
            try:
                client_thingsboard.connect(THINGSBOARD_HOST, 1883, 60)
                client_thingsboard.on_connect = on_connect_thingsboard
                client_thingsboard.subscribe('v1/devices/me/rpc/request/+')
                client_thingsboard.loop_start()
                print("Reconnected to ThingsBoard")
                isInternet = True
                break 
            except Exception as e:
                print(f'Error reconnecting to ThingsBoard: {e}')
                if reconnect_attempts >= MAX_RECONNECT_ATTEMPTS:
                    print("Max reconnect attempts reached. No connection!!!")
                    reconnect_attempts = 1
                    isInternet = False
                else:
                    reconnect_attempts += 1
                    print(f"Reconnecting in {RECONNECT_INTERVAL} seconds...")
                    time.sleep(RECONNECT_INTERVAL)
        else:
            if reinternet_attempts >= MAX_RECONNECT_ATTEMPTS:
                print("Max reconnect attempts reached. No connection!!!")
                reinternet_attempts = 1
                isInternet = False
            else:
                reinternet_attempts += 1
                print(f"No Internet connection. Retrying in {RECONNECT_INTERVAL} seconds...")
                time.sleep(RECONNECT_INTERVAL)

# Callback function for Mosquitto sensor message reception
def on_message_mosquitto(client, userdata, msg):
    message = msg.payload.decode("utf-8")
    print(f"Received message from Mosquitto: {message}")

    # Sending the received message to ThingsBoard
    client_thingsboard.publish(THINGSBOARD_TOPIC, message, 1)

    # Handling the temperature event, determining if it exceeds a specified threshold
    try:
        data = json.loads(message)
        if 'Temperature' in data:
            temperature = float(data['Temperature'])
            if temperature >= THRESHOLD_TEMPERATURE:
                print(f"High temperature alert! Temperature: {temperature}")
                payload_str = '{"params":false}'
                client_mosquitto.publish(MOSQUITTO_LED, payload_str, 1)
            else:
                print("Received a message with normal temperature.")
        else:
            print("Received a message, but it does not contain temperature information.")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")

# Callback function for Mosquitto state message reception
def on_message_mosquitto_2(client, userdata, msg):
    message = msg.payload.decode("utf-8")
    print(f"Received message from Mosquitto: {message}")

    # Sending the received message to ThingsBoard
    client_thingsboard.publish(THINGSBOARD_TOPIC, message, 1)

# Function to set the temperature threshold
def set_temperature_threshold(new_threshold):
    global THRESHOLD_TEMPERATURE
    THRESHOLD_TEMPERATURE = new_threshold
    print(f"Temperature threshold set to: {THRESHOLD_TEMPERATURE}")

# Callback function for ThingsBoard message reception
def on_message_thingsboard(client, userdata, msg):
    message = msg.payload.decode("utf-8")
    print(f"Received message from ThingsBoard: {message}")
    try:
        data = json.loads(message)
        # Check the request method
        if data['method'] == 'setThreshold':
            params_value = data.get('params')
            if params_value is not None:
                new_threshold = float(params_value)
                set_temperature_threshold(new_threshold)
            else:
                print("Received a message, but no Threshold.")
        elif data['method'] == 'setTime':
            time_value = data.get('params')
            if time_value is not None:
                client_mosquitto.publish(MOSQUITTO_TIME, message, 1)
                print(f"Time interval is set to: {time_value}")
            else:
                print("Received a message, but no Interval.")
        elif data['method'] == 'setLedState':
            led_value = data.get('params')
            if led_value is not None:
                client_mosquitto.publish(MOSQUITTO_LED, message, 1)
                print(f"LED is set to: {led_value}")
            else:
                print("Received a message, but no LED control.")
        else:
            print("Received a message, but it does not contain useful information.")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")       

# Function to handle Mosquitto operations on sensor topic
def mqtt_worker(mosquitto_broker, mosquitto_topic):
    client_mosquitto.on_message = on_message_mosquitto
    client_mosquitto.connect(mosquitto_broker, 1883, 60)
    client_mosquitto.subscribe(mosquitto_topic)
    client_mosquitto.loop_start()

    try:
        while True:
           pass
    except KeyboardInterrupt:
        pass

    client_mosquitto.loop_stop()
    client_mosquitto.disconnect()

# Function to handle MQTT operations on state topic
def mqtt_worker_2(mosquitto_broker, mosquitto_topic):
    client_mosquitto_2 = mqtt.Client()
    client_mosquitto_2.on_message = on_message_mosquitto_2
    client_mosquitto_2.connect(mosquitto_broker, 1883, 60)
    client_mosquitto_2.subscribe(mosquitto_topic)
    client_mosquitto_2.loop_start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        pass

    client_mosquitto_2.loop_stop()
    client_mosquitto_2.disconnect()

# Function to handle ThingsBoard operations
def thingsboard_worker():
    client_thingsboard.on_message = on_message_thingsboard
    client_thingsboard.on_disconnect = on_disconnect_thingsboard
    try:
        while True:
            pass
    except KeyboardInterrupt:
        pass

# Main entry point
if __name__ == '__main__':

    # Initialize the connection to ThingsBoard
    reconnect_to_thingsboard() 

    # Create threads for MQTT operations on two different topics
    mqtt_thread = threading.Thread(target=mqtt_worker, args=(MOSQUITTO_BROKER, MOSQUITTO_TOPIC, ))
    mqtt_thread_2 = threading.Thread(target=mqtt_worker_2, args=(MOSQUITTO_BROKER, MOSQUITTO_TOPIC_2, ))

    # Create a thread for ThingsBoard operations
    thingsboard_thread = threading.Thread(target=thingsboard_worker)

    # Start all threads
    mqtt_thread.start()
    mqtt_thread_2.start()
    thingsboard_thread.start()

    # Wait for all threads to finish
    mqtt_thread.join()
    mqtt_thread_2.join()
    thingsboard_thread.join()
