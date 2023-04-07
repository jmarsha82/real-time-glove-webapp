'''
* UI Backend subscription service
*
* Used by backend.py when user clicks button to start subscription service
'''

# Import utility libs
import time
import os
# Import AWS IoT Core libs
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import logging
import json

# Custom MQTT message callback
class CallbackContainer(object):

    # Constructor
    def __init__(self, client):
        self._client = client

    # Processed_Data topic callback function
    def processed_data_callback(self, client, userdata, message):
        # Write received data to file
        with open ("../public/hand_data.txt", 'w') as data_file:
            write_line = str(message.payload)
            write_line = write_line.strip("b")
            data_file.write(write_line)
            data_file.write("\n")
        print('Backend Sub Received: ' + str(message.payload))

def start_sub():
    # Setup AWS IoT
    ## Configure AWS IoT connection settings
    # host = <INSERT_HOST>
    # root_CA_path = <INSERT_PATH>
    # certificate_path = <INSERT_PATH>
    # private_key_path = <INSERT_PATH>
    port = 8883
    client_id = "back_end_sub"
    data_topic = "$aws/things/processed_data/shadow/update"

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
    my_iot_client.subscribe(data_topic, 1, my_callback_container.processed_data_callback)

    time.sleep(2)

    print('\nBackend subscriber started\n')

    # Infinitely sleep to keep subscribing
    while True:
        time.sleep(0.1)

if __name__ == '__main__':
    start_sub()
