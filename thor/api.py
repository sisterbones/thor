import socket
import ipaddress
from os import environ
from time import time

from flask import Blueprint, current_app, jsonify, request

import thor.db as db
from thor.db import get_db

bp = Blueprint("api", __name__, url_prefix='/api')


@bp.route('/health/')
def health():
    try:
        db = get_db()
    except:
        return jsonify({
            'timestamp': time(),
            'status': 'degraded'
        })

    return jsonify({
        'timestamp': time(),
        'status': 'healthy'
    })


@bp.route('/node/register/<node_id>')
def register_node(node_id):
    # Saves the node id into the database and returns the MQTT key and backup Wi-Fi credentials
    # print(type(node_id))

    db = get_db()
    existing = db.execute('SELECT * FROM nodes WHERE id = ?', [node_id]).fetchone()
    if existing:
        # Update its values
        db.execute('UPDATE nodes SET last_ip = ?, last_contact_time = CURRENT_TIMESTAMP WHERE id = ?', [request.remote_addr, node_id])
    else:
        # Otherwise just make a new one
        db.execute('INSERT INTO nodes (id, last_ip) VALUES (?, ?)', [node_id, request.remote_addr])
    db.commit()

    # Get MQTT IP, not all nodes support hostnames.
    MQTT_HOST_IP = socket.gethostbyname(environ.get('MQTT_BROKER'))
    if environ.get('MQTT_BROKER') == "localhost":
        MQTT_HOST_IP = current_app.config['LOCAL_IP']

    print(MQTT_HOST_IP)

    return jsonify({
        'timestamp': time(),
        'mqtt': {
            'username': 'service',
            'password': environ.get('MQTT_SERVICE_PASSWORD'),
            'port': environ.get('MQTT_PORT', 1883),
            'host': MQTT_HOST_IP
        },
        'wifi': None
    })

@bp.route('/alerts/active')
def get_active_alerts():
    return jsonify(db.get_active_alerts())

@bp.route('/config/<config_id>', methods=['GET', 'POST', 'PATCH'])
def config(config_id):
    db = get_db()
    if request.method == "GET":
        config_value = db.execute('SELECT * FROM config WHERE id = ?', [config_id]).fetchone()
        if config_value is not None:
            config_value = config_value['value']
        return jsonify({
            "id": config_id,
            "config_value": config_value,
            "timestamp": time(),
        })
    if request.method in ["POST", "PATCH"]:
        # Check if the config already exists
        config_value = db.execute('SELECT * FROM config WHERE id = ?', [config_id]).fetchone()

        post_config_value = request.form.get('config_value')
        if post_config_value is None:
            return jsonify({
                "error": "No config value provided"
            })

        if config_value is not None:
            # Update the value
            db.execute(
                "UPDATE config SET value = ?, updated = current_timestamp WHERE id = ?",
                (str(post_config_value), config_id)
            )
            db.commit()
        else:
            # Create a new config entry
            db.execute(
                "INSERT INTO config (id, value) VALUES (?, ?)",
                (config_id, str(post_config_value))
            )
            db.commit()

        return jsonify({
            "id": config_id,
            "config_value": post_config_value,
            "timestamp": time(),
        })
