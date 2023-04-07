#! /usr/bin/env python3
'''
* Demo 3 Glove Sensor Data Collection Service
*
* usage: python3 demo3_glove.py
'''

#######################
# Import ###Libraries #
#######################

# Import utility libs
import time
import os
# Import AWS IoT Core libs
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import logging
import json
# Import LED lib
from gpiozero import LED
# Import Adafruit base libs
import board
import busio
import digitalio
# Import MCP3008 libs
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
# Import BNO055 lib
from Adafruit_BNO055 import BNO055

############################
# Helper Functions/Classes #
############################

# Custom MQTT message callback
class CallbackContainer(object):

    # Constructor
    def __init__(self, client):
        self._client = client
        self._state = False

    # Glove control topic callback function
    def glove_control_callback(self, client, userdata, message):
        topic_contents = json.loads(message.payload.decode('utf-8'))
        if(topic_contents['state']['reported']['command'] == 'start'):
            self._state = True
        elif(topic_contents['state']['reported']['command'] == 'stop'):
            self._state = False

    # Accessor function
    def get_state(self):
        return self._state

# Function to convert received analog voltage to percentage flex
def map_flex_to_percent(x, in_min, in_max):
    out_min = 0
    out_max = 100

    mapped_val = (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    # Bounding
    if (mapped_val < out_min):
        mapped_val = out_min
    elif (mapped_val > out_max):
        mapped_val = out_max

    # Flip percent (was 100=no flex, now 100=max flex)
    return (mapped_val-100) * -1

####################
# Initialize Glove #
####################

# Create Status LED
led = LED(12)

# Setup MCP3008
## Create the spi bus
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
## Create the cs (chip select)
cs = digitalio.DigitalInOut(board.D5)
## Create the mcp object
mcp = MCP.MCP3008(spi, cs)
## Create an analog input channels
chan_0 = AnalogIn(mcp, MCP.P0)
chan_1 = AnalogIn(mcp, MCP.P1)
chan_2 = AnalogIn(mcp, MCP.P2)
chan_3 = AnalogIn(mcp, MCP.P3)
chan_4 = AnalogIn(mcp, MCP.P4)

# Setup BNO055
## Create BNO055 device
bno = BNO055.BNO055(serial_port='/dev/serial0', rst=13)
## Init connection to BNO055
bno_started = False
while not bno_started:
    try:
        bno_started = bno.begin()
    except RuntimeError:
        print('Error starting BNO! Retrying...')
        led.blink(0.1, 0.1, 5)
        time.sleep(1)
## Calibrate BNO055
script_path = os.path.dirname(os.path.realpath(__file__))
cal_data_path = os.path.join(script_path, 'bno055_cal.dat')
cal_data = open(cal_data_path, 'rb')
bno.set_calibration(cal_data.read())

# Setup AWS IoT
## Configure AWS IoT connection settings
# host = <INSERT_HOST>
# root_CA_path = <INSERT_PATH>
# certificate_path = <INSERT_PATH>
# private_key_path = <INSERT_PATH>
port = 8883
client_id = "glove"
sensor_data_topic = "$aws/things/sensor_glove/shadow/update"
control_topic = "$aws/things/glove_control/shadow/update"

## Configure AWS IoT logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.ERROR)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

## Init AWSIoTMQTTClient
my_iot_client = AWSIoTMQTTClient(client_id)
my_iot_client.configureEndpoint(host, port)
my_iot_client.configureCredentials(root_CA_path, private_key_path, certificate_path)

## Configure AWSIoTMQTTClient connection settings
my_iot_client.configureAutoReconnectBackoffTime(1, 32, 20)
my_iot_client.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
my_iot_client.configureDrainingFrequency(2)  # Draining: 2 Hz
my_iot_client.configureConnectDisconnectTimeout(10)  # 10 sec
my_iot_client.configureMQTTOperationTimeout(5)  # 5 sec

## Connect to AWS IoT
my_iot_client.connect()

## Subscribe to control topic
my_callback_container = CallbackContainer(my_iot_client)
my_iot_client.subscribe(control_topic, 1, my_callback_container.glove_control_callback)

time.sleep(2)
led.on()
print('System initialization complete.')

########################
# Main Processing Loop #
########################

while True:
    # Publish glove data topic when control topic says start until control topic says stop
    if(my_callback_container.get_state()):
        # Get glove orientation
        imu_orient = bno.read_euler()

        # Get finger flexion
        flex_index = map_flex_to_percent(chan_0.voltage, 1.87, 2.57)
        flex_mid = map_flex_to_percent(chan_1.voltage, 2.02, 2.65)
        flex_ring = map_flex_to_percent(chan_2.voltage, 2.18, 2.76)
        flex_pinky = map_flex_to_percent(chan_3.voltage, 1.71, 2.54)
        flex_thumb = map_flex_to_percent(chan_4.voltage, 1.35, 2.07)

        # Build data topic
        message = {}
        message['state'] = {}
        message['state']['reported'] = {}
        message['state']['reported']['flex_index'] = flex_index
        message['state']['reported']['flex_middle'] = flex_mid
        message['state']['reported']['flex_ring'] = flex_ring
        message['state']['reported']['flex_pinky'] = flex_pinky
        message['state']['reported']['flex_thumb'] = flex_thumb
        message['state']['reported']['imu_x'] = imu_orient[0]
        message['state']['reported']['imu_y'] = imu_orient[1]
        message['state']['reported']['imu_z'] = imu_orient[2]
        message_json = json.dumps(message)

        # Publish data topic
        my_iot_client.publish(sensor_data_topic, message_json, 1)

    # Loop at 10Hz
    time.sleep(0.1)
