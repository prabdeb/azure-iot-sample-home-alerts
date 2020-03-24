#!/usr/bin/env python3

import grovepi
import math
import time

from azure.iot.device import IoTHubDeviceClient, Message

# Global Variables
DHT_SENSOR_DOGITAL_PIN = 2
SOUND_SENSON_ANALOG_PIN = 0
MQ135_SENSOR_ANALOG_PIN = 1
MQ2_SENSOR_ANALOG_PIN = 2
AZURE_IOTHUB_CONNECTION_STRING = "<connection string>"

# Output Message
MSG_TXT = '{{"temperature": {temperature},"humidity": {humidity},"air": {air},"sound": {sound},"lpg": {lpg},"deviceid": {deviceid}}}'

def getGrovePlusData():
    try:
        [temperature,humidity] = grovepi.dht(DHT_SENSOR_DOGITAL_PIN,0)
        air_quality = grovepi.analogRead(MQ135_SENSOR_ANALOG_PIN)
        sound = int( (grovepi.analogRead(SOUND_SENSON_ANALOG_PIN) / 1024.0) * 54 * 1.664)
        lpg_value = grovepi.analogRead(MQ2_SENSOR_ANALOG_PIN)
    except IOError:
        print ("IO Error")
    return([temperature,humidity,air_quality,sound,lpg_value])

def iothub_client_init():
    # Create an IoT Hub client
    client = IoTHubDeviceClient.create_from_connection_string(AZURE_IOTHUB_CONNECTION_STRING)
    return client

def iothub_client_telemetry_sample_run():
    try:
        client = iothub_client_init()
        print ( "IoT Hub device sending periodic messages, press Ctrl-C to exit" )

        while True:
            [temperature,humidity,air_quality,sound,lpg_value] = getGrovePlusData()
            # Device ID
            deviceId = 1
            # Build the message with simulated telemetry values.
            msg_txt_formatted = MSG_TXT.format(temperature=temperature, humidity=humidity, air=air_quality, sound=sound, lpg=lpg_value, deviceid=deviceId)
            message = Message(msg_txt_formatted)

            # Add a custom application property to the message.
            # An IoT hub can filter on these properties without access to the message body.
            if temperature > 30:
              message.custom_properties["temperatureAlert"] = "true"
            else:
              message.custom_properties["temperatureAlert"] = "false"
            
            if 400 <= sound:
              message.custom_properties["soundAlert"] = "true"
            else:
              message.custom_properties["soundAlert"] = "false"

            if 200 <= air_quality:
              message.custom_properties["airQualityAlert"] = "true"
            else:
              message.custom_properties["airQualityAlert"] = "false"
            
            if 200 <= lpg_value:
              message.custom_properties["LpgAlert"] = "true"
            else:
              message.custom_properties["LpgAlert"] = "false"

            # Send the message.
            print( "Sending message: {}".format(message) )
            client.send_message(message)
            print ( "Message successfully sent" )
            time.sleep(15)

    except KeyboardInterrupt:
        print ( "IoTHubClient sample stopped" )

if __name__ == '__main__':
    print ( "IoT Hub Quickstart #1 - Simulated device" )
    print ( "Press Ctrl-C to exit" )
    iothub_client_telemetry_sample_run()