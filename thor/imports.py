
"""This file allows blueprints to access socketio."""

from os import environ
from flask_assets import Environment
from flask_socketio import SocketIO

from dotenv import load_dotenv
load_dotenv()


assets = Environment()
if environ.get('REDIS_URL'):
    socketio = SocketIO(message_queue=environ.get('REDIS_URL'))
else:
    socketio = SocketIO()
