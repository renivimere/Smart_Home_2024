# Smart_Home_2024
EE4348 HUST   
Architectures and communication protocols in IOT   
Group 07  
Agent 007  
## Overview
This Smart Home Project aims to create an intelligent home automation system using a combination of MQTT (Message Queuing Telemetry Transport), CoAP (Constrained Application Protocol), and ThingsBoard platform. The project facilitates communication between various devices, such as sensors and controllers, allowing seamless control and monitoring of the smart home environment.

## Features
- **MQTT Communication:** Utilizes MQTT for communication between devices like ESP8266 within the home network. MQTT allows for real-time data exchange and control commands.
- **CoAP Protocol:** Implements CoAP for efficient communication between the Home Center and IoT devices like ESP8266. CoAP is designed for resource-constrained devices and ensures low overhead communication.
- **ThingsBoard Integration:** Connects to the ThingsBoard platform for centralized data storage, visualization, and remote device control. The platform provides a dashboard for monitoring and managing the smart home system.
- **Temperature Monitoring:** Monitors temperature using a DHT11 sensor (optional), providing real-time updates to ThingsBoard. High-temperature alerts trigger actions such as controlling the LED state.
- **LED Control:** Enables remote control of the LED a.k.a the Smart Socket and the Smart Pump state via the ThingsBoard platform, allowing users to turn the LED on or off.
- **Interval Configuration:** Allows users to remotely set the data reporting interval for temperature and humidity updates.

## Components
- **MQTT_Windows_HC.py:** Python script implementing MQTT communication for Windows-based Home Center.
- **CoAP_Windows_HC.py:** Python script implementing CoAP communication for Windows-based Home Center.
- **ESP8266 Code:** Arduino sketch for ESP8266, providing CoAP services for LED control and time configuration.
- **README.md:** Project documentation providing an overview, features, and instructions for usage.

## Requirements
- Python 3.x
- Paho MQTT library
- Aiocoap library
- DHT11 sensor (optional): (Here, the project randomly generates values for temperature (between 10 to 40 degrees Celsius) and humidity (between 20 to 100%) for demonstration purposes)
- ThingsBoard account, devices and access tokens
- ESP8266 board with PlatformIO and Visual Studio Code

## Setup Instructions
1. Clone the repository to your local machine.
2. Install required Python libraries.  
3. Connect the DHT11 sensor and ESP8266 to your Home Center.
4. Update the SSID and password, change the IP, and configure other network settings as needed.  
5. Update the `THINGSBOARD_HOST` and `ACCESS_TOKEN` variables in the scripts with your ThingsBoard details.
6. Execute `MQTT_Windows_HC.py` and `CoAP_Windows_HC.py` scripts on your Home Center using `HC_Running.py`.
7. Flash all ESP8266 code to your ESP8266 board using the Arduino IDE.
8. Monitor and control your smart home through the ThingsBoard platform.


## Notes
- Make sure all scripts are in the same directory.
- Adjust the file names in the `scripts` list if necessary.
- Customize the project according to your specific device configurations and preferences.

Feel free to explore and enhance the Smart Home Project for a more personalized and efficient home automation experience!
Thank you!!!
