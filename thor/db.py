import json
import logging
import sqlite3

import click
from flask import current_app, g, Flask

from thor import Alert, LightningAlert, MetEireannWeatherWarning
from thor.constants import *

log = logging.getLogger(__name__)


def init_app(app: Flask):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
        if ':memory:' in current_app.config['DATABASE'].casefold():
            init_db()

    log.debug("Database gotten!")

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))


def add_new_alert(alert: Alert):
    """Adds an alert to the database"""
    log.debug("Adding %s to database", alert.__dict__)
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
            log.debug("Failed to add due to an IntegrityError, attempting to update...")
            db.execute("UPDATE alerts SET updated = ?, expiry = ?, data = ? WHERE publisher_id = ?",
                       (alert.updated, alert.expiry, json.dumps(alert.__dict__), alert.publisher_id))
            db.commit()


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


@click.command('reset-db')
def init_db_command():
    """RESET the database"""
    init_db()
    click.echo("Reset the database.")
