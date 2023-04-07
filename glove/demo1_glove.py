'''
*  Glove Sensor Data Collection Service
*
* Created with help from sample code from AWS and Adafruit
'''

# Import utility libs
import time
# Import AWS IoT Core libs
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import logging
import json
# Import Adafruit base libs
import board
import busio
import digitalio
# Import BNO055 lib
import adafruit_bno055
# Import MCP3008 libs
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

class CallbackContainer(object):

    def __init__(self, client):
        self._client = client
        self._state = False

    # Custom MQTT message callback
    def customCallback(self, client, userdata, message):
        topicContents = json.loads(message.payload.decode('utf-8'))
        if(topicContents['state']['reported']['command'] == 'start'):
            self._state = True
        elif(topicContents['state']['reported']['command'] == 'stop'):
            self._state = False

    def getState(self):
        return self._state

# Connection settings
# host = <INSERT_HOST>
# rootCAPath = <INSERT_PATH>
# certificatePath = <INSERT_PATH>
# privateKeyPath = <INSERT_PATH>
port = 8883
clientId = "glove"
sensorDataTopic = "$aws/things/sensor_glove/shadow/update"
controlTopic = "$aws/things/glove_control/shadow/update"

# Configure logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# Init AWSIoTMQTTClient
myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
myAWSIoTMQTTClient.configureEndpoint(host, port)
myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTClient connection configuration
myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connect to AWS IoT
myAWSIoTMQTTClient.connect()

# Subscribe to control sensorDataTopic
myCallbackContainer = CallbackContainer(myAWSIoTMQTTClient)
myAWSIoTMQTTClient.subscribe(controlTopic, 1, myCallbackContainer.customCallback)
time.sleep(2)

# Create BNO055 device
i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_bno055.BNO055(i2c)

# Setup MCP3008
## Create the spi bus
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
## Create the cs (chip select)
cs = digitalio.DigitalInOut(board.D5)
## Create the mcp object
mcp = MCP.MCP3008(spi, cs)
## Create an analog input channels
chan0 = AnalogIn(mcp, MCP.P0)
chan1 = AnalogIn(mcp, MCP.P1)
chan2 = AnalogIn(mcp, MCP.P2)
chan3 = AnalogIn(mcp, MCP.P3)
chan4 = AnalogIn(mcp, MCP.P4)

# Publish to sensor data sensorDataTopic when start sensorDataTopic is received until control sensorDataTopic says stop
while True:
    if(myCallbackContainer.getState()):
        imu_orient = sensor.euler
        imu_accel = sensor.acceleration

        message = {}
        message['state'] = {}
        message['state']['reported'] = {}
        message['state']['reported']['flex_index'] = chan0.value
        message['state']['reported']['flex_middle'] = chan1.value
        message['state']['reported']['flex_ring'] = chan2.value
        message['state']['reported']['flex_pinky'] = chan3.value
        message['state']['reported']['flex_thumb'] = chan4.value
        message['state']['reported']['imu_x'] = imu_orient[0]
        message['state']['reported']['imu_y'] = imu_orient[1]
        message['state']['reported']['imu_z'] = imu_orient[2]
        message['state']['reported']['imu_accel_x'] = imu_accel[0]
        message['state']['reported']['imu_accel_y'] = imu_accel[1]
        message['state']['reported']['imu_accel_z'] = imu_accel[2]
        messageJson = json.dumps(message)

        myAWSIoTMQTTClient.publish(sensorDataTopic, messageJson, 1)

    time.sleep(1)
