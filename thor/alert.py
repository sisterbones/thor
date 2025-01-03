import json
from datetime import datetime
import time
import logging
from uuid import uuid4

import requests
from flask import current_app
from rich.logging import RichHandler

from thor.constants import *
import thor.db as db
from thor.db import log, get_db
from thor.imports import socketio

FORMAT = "%(message)s"
logging.basicConfig(
    level="DEBUG", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)

log = logging.getLogger("rich")

class Alert:
    def __init__(self, *initial_data, **kwargs):
        self.publisher_id = str(uuid4())
        self.nowrap = False
        self.icon = None
        self.subtitle = None
        self.headline = None
        self.timestamp = time.time()
        self.alert_type = None
        self.severity = 0
        self.source = DATA_SOURCE_UNKNOWN
        self.updated = self.timestamp
        self.expiry = self.timestamp + (60 * 60 * 60)
        self.status = "Warning"

        for dictionary in initial_data:
            for key in dictionary:
                setattr(self, key, dictionary[key])
        for key in kwargs:
            setattr(self, key, kwargs[key])

class InfoAlert(Alert):
    """This alert type doesnt show as an alert to be concerned of, its just informational"""
    def __init__(self, *initial_data, **kwargs):
        super().__init__(*initial_data, **kwargs)
        self.status = "Info"


class MetEireannWeatherWarning(Alert):
    def __init__(self, *initial_data, cap_id: str = "", alert_type: str = "Unknown",
                 regions=None, **kwargs):

        super().__init__(*initial_data, **kwargs)
        # print(self.__dict__)

        if regions is None:
            regions = []
        self.publisher_id = cap_id
        if self.alert_type is None:
            self.alert_type = "Unknown"
        self.alert_type = alert_type.split(" ")[0].casefold()
        if type(self.severity) != int: self.severity = (self.severity.casefold() == "moderate" and 1) or \
                        (self.severity.casefold() == "severe" and 2) or \
                        (self.severity.casefold() == "extreme" and 3) or 0

        # Build headline and description
        self.headline = f"{self.level.capitalize()} {self.alert_type.casefold()} {self.status.casefold()}"
        if type(self.onset) == str: self.subtitle = f"Onset: {datetime.fromisoformat(self.onset).strftime('%H:%M')}"
        else: self.subtitle = f"Onset: {datetime.fromtimestamp(self.onset).strftime('%H:%M')}"
        self.icon = (self.alert_type == "rain" and "cloud-rain") or \
                    (self.alert_type == "wind" and "wind") or \
                    (self.alert_type == "snow-ice" and "snowflake") or \
                    (self.alert_type == "low-temperature" and "temperature-arrow-down") or \
                    (self.alert_type == "high-temperature" and "temperature-arrow-up") or \
                    (self.alert_type == "fog" and GENERIC_WARNING_ICON) or \
                    (self.alert_type == "thunderstorm" and "cloud-bolt") or \
                    (self.alert_type == "advisory" and GENERIC_WARNING_ICON) or \
                    GENERIC_WARNING_ICON
        self.nowrap = True

        if type(self.issued) == str: self.issued = datetime.fromisoformat(self.issued).timestamp()
        if type(self.updated) == str: self.updated = datetime.fromisoformat(self.updated).timestamp()
        if type(self.onset) == str: self.onset = datetime.fromisoformat(self.onset).timestamp()
        if type(self.expiry) == str: self.expiry = datetime.fromisoformat(self.expiry).timestamp()

        self.source = DATA_SOURCE_METEIREANN | DATA_SOURCE_INET


class LightningAlert(Alert):
    def __init__(self, *initial_data, **kwargs):
        super().__init__(*initial_data, **kwargs)
        self.alert_type = "lightning"
        self.source = DATA_SOURCE_MQTT
        self.expiry = self.timestamp + (60 * 10)
        self.icon = "bolt"
        self.headline = "Lightning detected!"
        self.subtitle = f"About {self.distance_km}km away."

def fetch_weather() -> dict:
    return current_app.config['METNO_LOCATIONFORECAST'].fetch()

def fetch_alerts() -> None:
    """Updates alerts from external providers."""
    try:
        current_app.config['METIE_WEATHERWARNING'].fetch()
    except requests.exceptions.JSONDecodeError:
        add_new_alert(InfoAlert(headline="Failed to fetch data from Met Éireann. (WW_FAIL)", publisher_id="metie_ww_fail"))

def publish_current_alerts(methods=3):
    log.info('Serving current alerts')

    fetch_alerts()

    current_alerts = get_active_alerts()
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
        socketio.emit(f'alerts/{alert.alert_type}', alert.__dict__,
                      namespace="/mqtt")  # For nodes only looking at specific alerts
    if methods & DATA_OUTPUT_SOCKETIO:
        socketio.emit(f'alerts', alert.__dict__)  # For nodes looking for all alerts
        socketio.emit(f'alerts/{alert.alert_type}', alert.__dict__)  # For nodes only looking at specific alerts


def add_new_alert(alert: Alert, callback = None):
    """Adds an alert to the database. `callback` is a function that takes a boolean as its first parameter."""
    log.debug("Adding %s to database", alert.__dict__)
    updated = False
    with current_app.app_context():
        db = get_db()
        try:
            db.execute(
                "INSERT INTO alerts (publisher_id, timestamp, updated, expiry, type, data)"
                "                    VALUES (?, ?, ?, ?, ?, ?)",
                (alert.publisher_id, alert.timestamp, alert.updated, alert.expiry, alert.alert_type,
                 json.dumps(alert.__dict__)),
            )
            db.commit()
            log.debug("Committed!")
        except db.IntegrityError as e:
            # log.debug("Failed to add due to an IntegrityError, attempting to update...")
            db.execute("UPDATE alerts SET updated = ?, expiry = ?, data = ? WHERE publisher_id = ?",
                       (alert.updated, alert.expiry, json.dumps(alert.__dict__), alert.publisher_id))
            updated = True
            db.commit()

        if callback:
            callback(updated)


def get_active_alerts(type: str = None, output_type: str = "dict"):
    log.info("Getting active alerts..")
    with current_app.app_context():
        db = get_db()
        if type is None:
            alerts = db.execute("SELECT * FROM alerts WHERE expiry >= unixepoch() ORDER BY timestamp", ).fetchall()
        else:
            alerts = db.execute("SELECT * FROM alerts WHERE expiry >= unixepoch() AND type = ? ORDER BY timestamp",
                                [type]).fetchall()

        to_return = []
        for alert in alerts:
            data = json.loads(alert['data'])

            if alert["type"] == "lightning":
                alert_obj = LightningAlert(data)
            elif data.get("source") & DATA_SOURCE_METEIREANN:
                alert_obj = MetEireannWeatherWarning(data)
            elif alert['type'] == 'info':
                alert_obj = InfoAlert(data)
            else:
                alert_obj = Alert(json.loads(alert['data']))

            alert_obj.updated = alert['updated']
            alert_obj.expiry = alert['expiry']
            alert_obj.timestamp = alert['timestamp']

            if output_type.casefold() == "alert":
                to_return.append(alert_obj)
            else:
                to_return.append(alert_obj.__dict__)

        log.debug("Returning! %s", to_return)

        return to_return
