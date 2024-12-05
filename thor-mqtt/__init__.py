
from os import environ

import paho.mqtt.client as mqtt

from dotenv import load_dotenv
load_dotenv()

def on_connect(client, metadata, flags, reason_code, properties):
    print(f"Connected with result code {reason_code}")

    client.subscribe("$SYS/#")

def on_message(client, userdata, message):
    print(message)

mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_message = on_message

mqttc.connect(environ.get('MQTT_BROKER', "localhost"), environ.get('MQTT_BROKER_PORT', 1883))
mqttc.username_pw_set(environ.get('MQTT_USERNAME', 'thor'), environ.get('MQTT_PASSWORD', ''))
mqttc.loop_forever()
