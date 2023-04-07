'''
* Glove Sensor Data Collection Stop Command Utility Script
*
* usage: python3 glove_stop.py
'''

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import logging
import time
import json

# Setup AWS IoT
## Connection settings
# host = <INSERT_HOST>
# root_CA_path = <INSERT_PATH>
# certificate_path = <INSERT_PATH>
# private_key_path = <INSERT_PATH>
port = 8883
clientId = "test_controller"
controlTopic = "$aws/things/glove_control/shadow/update"

## Configure logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

## Init AWSIoTMQTTClient object
myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
myAWSIoTMQTTClient.configureEndpoint(host, port)
myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

## AWSIoTMQTTClient connection configuration
myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connect to AWS IoT
myAWSIoTMQTTClient.connect()
time.sleep(2)

# Build and publish control topic telling glove to stop
message = {}
message['state'] = {}
message['state']['reported'] = {}
message['state']['reported']['command'] = 'stop'
messageJson = json.dumps(message)
myAWSIoTMQTTClient.publish(controlTopic, messageJson, 1)
