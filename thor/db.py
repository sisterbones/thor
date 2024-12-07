
import logging
import sqlite3
import time

import click
from flask import current_app, g, Flask

from thor import Alert

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

def add_new_alert(alert: Alert, app):
    """Adds an alert to the database"""
    log.debug("Adding %s to database", alert)
    with app.app_context():
        db = get_db()
        try:
            db.execute(
                "INSERT INTO alerts (timestamp, updated, expiry, type, severity, source, headline, subtitle, icon,"
                "                    nowrap) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (alert.timestamp, alert.updated, alert.expiry, alert.alert_type, alert.severity, alert.source,
                 alert.headline, alert.subtitle, alert.icon, alert.nowrap),
            )
            db.commit()
            log.debug("Committed!")
        except db.IntegrityError as e:
            log.error(e)
        else:
            return True

        return False

def get_active_alerts(app, type:str=None):
    log.debug("Getting active alerts..")
    with app.app_context():
        db = get_db()
        if type is not None:
            alerts = db.execute("SELECT * FROM alerts WHERE expiry >= unixepoch() ORDER BY timestamp",).fetchall()
        else:
            alerts = db.execute("SELECT * FROM alerts WHERE expiry >= unixepoch() AND type = ? ORDER BY timestamp", type).fetchall()
        to_return = []
        for alert in alerts:
            alert_obj = Alert()
            alert_obj.timestamp = alert["timestamp"]
            alert_obj.updated = alert["updated"]
            alert_obj.expiry = alert["expiry"]
            alert_obj.alert_type = alert["type"]
            alert_obj.severity = alert["severity"]
            alert_obj.source = alert["source"]
            alert_obj.headline = alert["headline"]
            alert_obj.subtitle = alert["subtitle"]
            alert_obj.icon = alert["icon"]
            alert_obj.nowrap = alert["nowrap"]
            to_return.append(alert_obj.__dict__)

        log.debug("Got alerts! %s", alerts)

        return to_return

@click.command('reset-db')
def init_db_command():
    """RESET the database"""
    init_db()
    click.echo("Reset the database.")
