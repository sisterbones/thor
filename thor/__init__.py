from datetime import datetime
from io import BytesIO
from os import environ
import json
import time

import werkzeug.exceptions
from flask import Flask, render_template
from flask_apscheduler import APScheduler
from flask_assets import Environment, Bundle
from flask_mqtt import Mqtt
from flask_socketio import SocketIO

from thor.providers import MetNoWeatherProvider

assets = Environment()
mqtt = Mqtt()
scheduler = APScheduler()
socketio = SocketIO()
weather = MetNoWeatherProvider(environ.get('HOME_LAT', 0.0), environ.get('HOME_LONG', 0.0))

def get_time(strftime="%H:%M"):
    # Returns the current time as a string in the format "HH:MM"
    return datetime.now().strftime(strftime)

def create_app():
    app = Flask(__name__,
                static_url_path = '')

    # Template configs
    if environ.get('FLASK_ENV') == 'development':
        app.config['TEMPLATES_AUTO_RELOAD'] = True

    app.config['SECRET_KEY'] = environ.get('SECRET_KEY', '') # TODO: make this random

    # MQTT configuration
    app.config['MQTT_BROKER_URL'] = environ.get('MQTT_BROKER', 'localhost')
    app.config['MQTT_BROKER_PORT'] = environ.get('MQTT_BROKER_PORT', 1883)
    app.config['MQTT_USERNAME'] = environ.get('MQTT_USERNAME', 'thor')
    app.config['MQTT_PASSWORD'] = environ.get('MQTT_PASSWORD', '')
    app.config['MQTT_REFRESH_TIME'] = 1.0

    # Scheduler config
    # app.config['SCHEDULER_API_ENABLED'] = True

    # Configure GPS location
    app.config['HOME_LAT'] = environ.get('HOME_LAT', 0.0)
    app.config['HOME_LONG'] = environ.get('HOME_LONG', 0.0)

    # SASS configuration
    app.config['SASS_LOAD_PATHS'] = ['vendor/']

    assets.init_app(app)
    socketio.init_app(app)
    mqtt.init_app(app)

    scss = Bundle('styles/style.scss', filters="scss", output="styles/style.css")
    assets.register('scss_all', scss)

    @app.errorhandler(werkzeug.exceptions.NotFound)
    def not_found(error):
        return render_template('not-found.html')

    @scheduler.task('cron', id='publish_weather', minute="*/10")
    def publish_weather():
        print('Serving weather')
        weather_data = weather.fetch()
        mqtt.publish('thor/weather', json.dumps(weather_data).encode('utf-8'))
        socketio.emit('weather', weather_data)

    @mqtt.on_message()
    def handle_mqtt_message(client, userdata, message):
        data = dict(
            topic=message.topic,
            payload=message.payload.decode()
        )
        if data['topic'] == 'thor/ask':
            # Send weather information over 'thor/weather'
            publish_weather()

    @socketio.on('ask')
    def sio_ask(message):
        if 'weather' in message:
            print(2)
            # Calls publish_weather
            publish_weather()

    @mqtt.on_connect()
    def mqtt_on_connect(client, userdata, flags, rc):
        mqtt.publish('thor/status', f'{get_time()}: Hub online'.encode('utf-8'))
        publish_weather()
        mqtt.subscribe('thor/ask')

    @app.route('/')
    def index():
        return render_template('base.html')

    scheduler.start()

    return app


if __name__ == '__main__':
    debug_app = create_app()
    debug_app.run(use_reloader=False, debug=True)
