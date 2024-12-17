
from os import environ, path, cpu_count
from sys import platform

from dotenv import load_dotenv
load_dotenv()

RUNTIME_DIRECTORY_EXISTS = (path.exists('/run/thor/'))

bind = [
    environ.get('HOST', '0.0.0.0') + ":" + environ.get('PORT', "8467"),
]

if RUNTIME_DIRECTORY_EXISTS: bind.append('unix:/run/thor/thor.sock')

#workers = 1
threads = cpu_count()
