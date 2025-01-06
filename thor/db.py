import logging
import os
import sqlite3
import time

import click
from flask import current_app, g, Flask

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


def get_config(key, fallback=None):
    with current_app.app_context():
        db = get_db()
        log.debug("Getting %s...", key)
        try:
            result = db.execute("SELECT * FROM config WHERE id = ? LIMIT 1", [key]).fetchone()
            log.debug("%s's value is %s", key, result['value'])
            return result['value']
        except Exception as e:
            log.critical(e)
            if fallback is None:
                log.debug("Falling back to %s", os.environ.get(key, fallback))
                return os.environ.get(key, fallback)
            else:
                log.debug("Falling back to %s", fallback)
                return fallback


def set_config(key, value):
    with current_app.app_context():
        db = get_db()
        try:
            log.debug("Setting config value %s to %s", key, value)
            db.execute(
                "INSERT INTO config (id, value)"
                "                    VALUES (?, ?)",
                [key, value])
            db.commit()
        except db.IntegrityError as e:
            log.debug("Failed to add due to an IntegrityError, attempting to update...")
            db.execute("UPDATE config SET value = ?, updated = ? WHERE id = ?", [value, time.time(), key])
            db.commit()
            log.debug("Updated %s to %s", key, value)


@click.command('reset-db')
def init_db_command():
    """RESET the database"""
    init_db()
    click.echo("Reset the database.")
