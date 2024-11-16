from time import time

from flask import Blueprint, current_app, jsonify, request

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
