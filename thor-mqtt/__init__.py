
import json
import logging
import os
from os import environ

from rich.logging import RichHandler
import socketio
import paho.mqtt.client as mqtt

from dotenv import load_dotenv
load_dotenv()

# Set up logging
FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)
log = logging.getLogger("rich")

sio = socketio.Client()
sio.connect(f"http://0.0.0.0:{environ.get('PORT', '8467')}", namespaces=["/mqtt"])

def on_connect(client, metadata, flags, reason_code, properties):
    log.info(f"Connected with result code {reason_code}")
    if reason_code == "Not authorized":
        log.error("MQTT reported not authorised")
    client.subscribe("thor/#")
    # client.subscribe("$SYS/broker/uptime")

def on_message(client, userdata, message):
    log.debug(f"[dim][bold]{message.topic}[/bold]: {message.payload}[/dim]", extra={"markup": True})
    if not message.topic.startswith('thor/'):
        return
    topic = message.topic.split('thor/')[1]
    log.info(f"[bold]{topic}[/bold]: {message.payload}", extra={"markup": True})
    sio.emit(topic, message.payload.decode(), namespace="/mqtt")

mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_message = on_message

@sio.on('*', namespace="/mqtt")
def message(topic, data):
    log.info("%s: %s", topic, data)
    if type(data) == dict:
        data = json.dumps(data)
    mqttc.publish(f'thor/{topic}', data)

@sio.on('connect')
def sio_on_connect(data=""):
    log.info("Connected to THOR.")

mqttc.connect(environ.get('MQTT_BROKER', "localhost"), environ.get('MQTT_BROKER_PORT', 1883))
mqttc.username_pw_set(environ.get('MQTT_USERNAME', 'thor'), environ.get('MQTT_PASSWORD', ''))
mqttc.loop_forever()
