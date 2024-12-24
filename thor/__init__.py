import json
from datetime import datetime
import logging
from os import environ
from secrets import token_hex

import werkzeug.exceptions
from dotenv import load_dotenv

load_dotenv()
from flask import Flask, render_template
from flask_assets import Environment, Bundle
from flask_socketio import SocketIO
from rich.logging import RichHandler

import thor.misc as misc
from thor.alert import *
from thor.constants import *
from thor.providers import MetNoWeatherProvider, MetEireannWeatherWarningProvider

# Set up logging
FORMAT = "%(message)s"
logging.basicConfig(
    level="DEBUG", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)

log = logging.getLogger("rich")

assets = Environment()
if environ.get('REDIS_URL'):
    socketio = SocketIO(message_queue=environ.get('REDIS_URL'))
else:
    socketio = SocketIO()

def get_time(strftime="%H:%M"):
    # Returns the current time as a string in the format "HH:MM"
    return datetime.now().strftime(strftime)

def create_app(use_mqtt=False):
    app = Flask(__name__,
                static_url_path = '')

    # Template configs
    if environ.get('FLASK_ENV') == 'development':
        app.config['DEBUG'] = True
        app.config['TEMPLATES_AUTO_RELOAD'] = True

    app.secret_key = environ.get('SECRET_KEY', token_hex(32))

    # Database URI
    app.config["DATABASE"] = environ.get('DATABASE', ":memory:")

    # Might be useful to keep track of this in the app config idk
    app.config['REDIS_URL'] = environ.get('REDIS_URL', 'redis://localhost')

    # MQTT configuration
    app.config['MQTT_BROKER_URL'] = environ.get('MQTT_BROKER', 'localhost')
    app.config['MQTT_BROKER_PORT'] = environ.get('MQTT_BROKER_PORT', 1883)
    app.config['MQTT_USERNAME'] = environ.get('MQTT_USERNAME', 'thor')
    app.config['MQTT_PASSWORD'] = environ.get('MQTT_PASSWORD', '')
    app.config['MQTT_REFRESH_TIME'] = 1.0

    app.config['LOCAL_IP'] = misc.get_ip()

    # SASS configuration
    app.config['SASS_LOAD_PATHS'] = ['vendor/']

    from thor import db
    db.init_app(app)
    assets.init_app(app)
    socketio.init_app(app)

    scss = Bundle('styles/style.scss', filters="scss", output="styles/style.css")
    assets.register('scss_all', scss)

    @app.route('/')
    def index():
        return render_template('dashboard.html')

    @app.errorhandler(werkzeug.exceptions.NotFound)
    def not_found(error):
        return render_template('not-found.html'), 404

    def publish_weather(methods=3):
        log.info('Serving weather')

        weather = MetNoWeatherProvider(lat=app.config.get('HOME_LAT', 0), long=app.config.get('HOME_LONG', 0)).fetch()

        if methods & DATA_OUTPUT_MQTT:
            socketio.emit('weather', weather, namespace="/mqtt")
        if methods & DATA_OUTPUT_SOCKETIO:
            socketio.emit('weather', weather)

    def publish_current_alerts(methods=3):
        log.info('Serving current alerts')

        current_alerts = db.get_active_alerts()
        payload = {
            "alerts": current_alerts,
            "timestamp": time.time(),
            "refresh": True
        }

        if methods & DATA_OUTPUT_MQTT:
            socketio.emit('alerts', payload, namespace="/mqtt")
        if methods & DATA_OUTPUT_SOCKETIO:
            socketio.emit('alerts', payload)

    def publish_alert(alert: Alert, methods=3):
        log.info(f"Publishing {alert.alert_type} alert...")
        if methods & DATA_OUTPUT_MQTT:
            socketio.emit(f'alerts', alert.__dict__, namespace="/mqtt")  # For nodes looking for all alerts
            socketio.emit(f'alerts/{alert.alert_type}', alert.__dict__, namespace="/mqtt")  # For nodes only looking at specific alerts
        if methods & DATA_OUTPUT_SOCKETIO:
            socketio.emit(f'alerts', alert.__dict__)  # For nodes looking for all alerts
            socketio.emit(f'alerts/{alert.alert_type}', alert.__dict__)  # For nodes only looking at specific alerts

    def ask_common(message, output=3):
        if 'weather' in message:
            publish_weather(output)
        if 'alerts' in message:
            publish_current_alerts(output)

    @socketio.on('ask')
    def sio_ask(message):
        ask_common(message, DATA_OUTPUT_SOCKETIO)

    @socketio.on('ask', namespace="/mqtt")
    def mqtt_ask(message):
        ask_common(message, DATA_OUTPUT_MQTT)

    @socketio.on('update/lightning')
    @socketio.on('update/lightning', namespace="/mqtt")
    def sio_update(message):
        try:
            message = json.loads(message)
        except:
            pass

        if db.get_config("LOG_LIGHTNING_EVENTS", False):
            if not message.get("error"):
                dbc = db.get_db()
                dbc.execute("INSERT INTO lightning_events (distance, energy) VALUES (?, ?)", [message.get("distance", 0.0), message.get("energy", 0.0)])
                dbc.commit()

        if message.get("error") == "noisy":
            alert = InfoAlert()
            alert.alert_type = "info"
            alert.icon = "warning"
            alert.severity = 2
            alert.publisher_id = "lightning_noisy"
            alert.headline = "Lightning sensor is detecting too much noise"
            db.add_new_alert(alert)
            publish_alert(alert)
            return

        alert = LightningAlert(distance_km=int(message.get("distance")))

        # If there was lighting detected in the last ten minutes, bundle it in with that alert.
        alerts = db.get_active_alerts("lightning", output_type="alert")
        if not alerts:
            db.add_new_alert(alert)
            publish_alert(alert)

        # Check if there's any lighting strikes that are closer
        closer_strikes = [x for x in alerts if x.distance_km <= alert.distance_km]
        if not closer_strikes:
            if alerts:
                alerts[0].distance_km = alert.distance_km
                alerts[0].subtitle = f"Distance {alert.distance_km}km"
                alerts[0].updated = time.time()
                alerts[0].expiry = time.time() + (60 * 10)
                alert = alerts[0]

            db.add_new_alert(alert)
            publish_alert(alert)

    import thor.testing
    app.register_blueprint(thor.testing.bp)

    import thor.api
    app.register_blueprint(thor.api.bp)

    import thor.settings
    app.register_blueprint(thor.settings.bp)

    return app


if __name__ == '__main__':
    debug_app = create_app()
    debug_app.run(debug=True, host=environ.get("HOST", "0.0.0.0"), port=environ.get("PORT", 5000))
