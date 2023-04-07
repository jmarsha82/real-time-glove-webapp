'''
* Cloud ML processing of data sent from glove
'''

####################
# Import Libraries #
####################

# Import utility libs
import json
import os
import time
# Import AWS IoT Core libs
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import logging
# Import Random Forest Classifier lib
from sklearn.ensemble import RandomForestClassifier

############################
# Helper Functions/Classes #
############################

# Custom MQTT message callback
class CallbackContainer(object):

    # Constructor
    def __init__(self, client):
        self._client = client
        self._state = False
        self._glove_data_buffer = []

    # Control topic callback function
    def control_callback(self, client, userdata, message):
        # Contents of topic not important, receipt of topic alone is the trigger
        self._state = True

    # Glove data topic callback function
    def glove_data_callback(self, client, userdata, message):
        topic_contents = json.loads(message.payload.decode('utf-8'))

        glove_data = []
        glove_data.append(topic_contents['state']['reported']['imu_x'])
        glove_data.append(topic_contents['state']['reported']['imu_y'])
        glove_data.append(topic_contents['state']['reported']['imu_z'])
        glove_data.append(topic_contents['state']['reported']['flex_index'])
        glove_data.append(topic_contents['state']['reported']['flex_middle'])
        glove_data.append(topic_contents['state']['reported']['flex_ring'])
        glove_data.append(topic_contents['state']['reported']['flex_pinky'])
        glove_data.append(topic_contents['state']['reported']['flex_thumb'])

        self._glove_data_buffer.append(glove_data)

        print(topic_contents)
        print("\n\n\n")

    # Accessor functions
    def get_control_state(self):
        return self._state

    def get_glove_data_buffer(self):
        return self._glove_data_buffer

    # Mutator functions
    def reset_control_state(self):
        self._state = False

    def clear_glove_data_buffer(self):
        self._glove_data_buffer = []

####################
# Initialize Cloud #
####################

# Initialize Random Forest Classifier
X = []
Y = []

## Get training data files
only_files = [f for f in os.listdir("./training_data") if os.path.isfile(os.path.join("./training_data", f))]

for i in range(0, len(only_files)):
    only_files[i] = os.path.join("./training_data", only_files[i])

## Read training data
for i in range(0, len(only_files)):
    with open(only_files[i]) as data_file:
        for line in data_file:
            line = line.strip("\n")
            x_pt = []
            data_pts = line.split(",")
            result = data_pts[- 1]
            del data_pts[-1]
            for k in range(0, len(data_pts)):
                x_pt.append(float(data_pts[k]))

            X.append(x_pt)
            Y.append(result)

## Create Random Forest Classifier object
rf = RandomForestClassifier(max_depth=15, min_samples_leaf=1, min_samples_split = 4, n_estimators = 1000)

## Build random forest from training data
rf.fit(X, Y)

# Setup AWS IoT
## Configure AWS IoT connection settings
# host = <INSERT_HOST>
# root_CA_path = <INSERT_PATH>
# certificate_path = <INSERT_PATH>
# private_key_path = <INSERT_PATH>
port = 8883
client_id = "cloud_Ec2"
cloud_control_topic = "$aws/things/cloud_control/shadow/update"
result_topic = "$aws/things/processed_data/shadow/update"
glove_control_topic = "$aws/things/glove_control/shadow/update"
glove_data_topic = "$aws/things/sensor_glove/shadow/update"

## Configure AWSIoTMQTTClient connection settings
my_iot_client = AWSIoTMQTTClient(client_id)
my_iot_client.configureEndpoint(host, port)
my_iot_client.configureCredentials(root_CA_path, private_key_path, certificate_path)

## Configure AWS IoT logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.ERROR)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

## Init AWSIoTMQTTClient
my_iot_client.configureAutoReconnectBackoffTime(1, 32, 20)
my_iot_client.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
my_iot_client.configureDrainingFrequency(2)  # Draining: 2 Hz
my_iot_client.configureConnectDisconnectTimeout(10)  # 10 sec
my_iot_client.configureMQTTOperationTimeout(5)  # 5 sec

## Connect to AWS IoT
my_iot_client.connect()

## Subscribe to control topic
my_callback_container = CallbackContainer(my_iot_client)
my_iot_client.subscribe(cloud_control_topic, 1, my_callback_container.control_callback)

## Subscribe to glove data topic
my_iot_client.subscribe(glove_data_topic, 1, my_callback_container.glove_data_callback)

time.sleep(2)

########################
# Main Processing Loop #
########################

while True:

    print(my_callback_container.get_control_state())
    # Get sensor data for prediction once control topic is received
    if (my_callback_container.get_control_state()):
        # Reset control state as request is being processed
        my_callback_container.reset_control_state()

        # Reset glove data buffer
        my_callback_container.clear_glove_data_buffer()

        # Publish glove start command
        message = {}
        message['state'] = {}
        message['state']['reported'] = {}
        message['state']['reported']['command'] = 'start'
        message_json = json.dumps(message)
        my_iot_client.publish(glove_control_topic, message_json, 1)

        # Wait for buffer to fill with glove data
        time.sleep(3)

        # Publish glove stop command
        message = {}
        message['state'] = {}
        message['state']['reported'] = {}
        message['state']['reported']['command'] = 'stop'
        message_json = json.dumps(message)
        my_iot_client.publish(glove_control_topic, message_json, 1)

        # Get random forest classifier's predictions
        predictions = rf.predict(my_callback_container.get_glove_data_buffer())

        # Grabbing majority prediction
        counts = {}
        for pred in predictions:
            if pred in counts.keys():
                counts[pred] = counts[pred] + 1
            else:
                counts[pred] = 1

        max_count = 0
        mode = None
        for key in counts.keys():
            if counts[key] > max_count:
                max_count = counts[key]
                mode = key

        send_result = mode

        # Publish result
        my_iot_client.publish(result_topic, send_result, 1)
        print(send_result)

    time.sleep(1)
