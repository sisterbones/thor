import json
from datetime import datetime
import logging
from os import environ
from secrets import token_hex

import werkzeug.exceptions
from dotenv import load_dotenv
load_dotenv()
from flask import Flask, render_template
# from flask_apscheduler import APScheduler
from flask_assets import Environment, Bundle
from flask_socketio import SocketIO
from rich.logging import RichHandler

from thor.alert import *
from thor.constants import *
from thor.providers import MetNoWeatherProvider, MetEireannWeatherWarningProvider


# Set up logging
FORMAT = "%(message)s"
logging.basicConfig(
    level="INFO", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)

log = logging.getLogger("rich")

assets = Environment()
# mqtt = Mqtt()
# scheduler = APScheduler()
socketio = SocketIO()

def get_time(strftime="%H:%M"):
    # Returns the current time as a string in the format "HH:MM"
    return datetime.now().strftime(strftime)

def create_app(use_mqtt=False):
    app = Flask(__name__,
                static_url_path = '')

    # Template configs
    if environ.get('FLASK_ENV') == 'development':
        app.config['TEMPLATES_AUTO_RELOAD'] = True

    app.config['SECRET_KEY'] = environ.get('SECRET_KEY', token_hex(32))

    # Database URI
    app.config["DATABASE"] = environ.get('DATABASE', ":memory:")

    # Python RQ stuff
    # app.config['REDIS_URL'] = environ.get('REDIS_URL', 'redis://localhost')

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

    from thor import db
    db.init_app(app)
    assets.init_app(app)
    socketio.init_app(app)
    # if use_mqtt: mqtt.init_app(app)

    scss = Bundle('styles/style.scss', filters="scss", output="styles/style.css")
    assets.register('scss_all', scss)

    @app.route('/')
    def index():
        return render_template('dashboard.html')

    @app.errorhandler(werkzeug.exceptions.NotFound)
    def not_found(error):
        return render_template('not-found.html'), 404

    # @scheduler.task('cron', id='publish_weather', minute="*/10")
    def publish_weather(methods=3):
        log.info('Serving weather')

        weather = MetNoWeatherProvider(lat=app.config.get('HOME_LAT', 0), long=app.config.get('HOME_LONG', 0)).fetch()

        if methods & DATA_OUTPUT_MQTT:
            mqtt.publish('thor/weather', json.dumps(weather).encode('utf-8'))
        if methods & DATA_OUTPUT_SOCKETIO:
            socketio.emit('weather', weather)

    def publish_alert(alert: Alert, methods=3):
        topic = f'thor/alerts/{alert.alert_type}'
        # Add the alert to the alerts database
        db.add_new_alert(alert, app)
        # if methods & DATA_OUTPUT_MQTT:
        #     mqtt.publish('thor/alerts', json.dumps(alert.__dict__).encode('utf-8')) # for nodes subscribed to all alerts
        #     mqtt.publish(topic, json.dumps(alert.__dict__).encode('utf-8'))
        if methods & DATA_OUTPUT_SOCKETIO:
            socketio.emit(f'alerts#{alert.alert_type}', alert.__dict__)

    # @mqtt.on_message()
    # def handle_mqtt_message(client, userdata, message):
    #     data = dict(
    #         topic=message.topic,
    #         payload=message.payload.decode()
    #     )
    #     log.debug(data)
    #     if data['topic'] == 'thor/ask':
    #         # Send weather information over 'thor/weather'
    #         publish_weather(DATA_OUTPUT_MQTT)
    #     if data['topic'].startswith('thor/update/lightning'):
    #         # Send a lightning alert to every device
    #         alert = LightningAlert()
    #         log.debug("Alerting of lightning.")
    #         alert.distance_km = 15
    #         publish_alert(alert)

    @socketio.on('ask')
    def sio_ask(message):
        if 'weather' in message:
            # Calls publish_weather
            publish_weather(DATA_OUTPUT_SOCKETIO)

    # @mqtt.on_connect()
    # def mqtt_on_connect(client, userdata, flags, rc):
    #     mqtt.publish('thor/status', f'{get_time()}: Hub online'.encode('utf-8'))
    #     publish_weather(DATA_OUTPUT_MQTT)
    #     mqtt.subscribe('thor/ask')
    #     mqtt.subscribe('thor/status/#')
    #     mqtt.subscribe('thor/update/#')

    # import thor.testing_endpoints
    # app.register_blueprint(thor.testing_endpoints.bp)

    import thor.api
    app.register_blueprint(thor.api.bp)

    # scheduler.start()

    return app


if __name__ == '__main__':
    debug_app = create_app()
    debug_app.run(use_reloader=False, debug=True)
