
from os import environ, path
from sys import platform

from dotenv import load_dotenv
load_dotenv()

RUNTIME_DIRECTORY_EXISTS = (platform.startswith('linux') and path.exists('/run/thor/'))

bind = [
    environ.get('HOST', '0.0.0.0') + ":" + environ.get('PORT', "8467"),
]

if RUNTIME_DIRECTORY_EXISTS: bind.append('unix:/run/thor/thor.sock')
