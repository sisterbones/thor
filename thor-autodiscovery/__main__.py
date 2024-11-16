"""
Auto-discovers nodes on the network.
This is heavily based on https://github.com/jholtmann/ip_discovery
"""

import logging
import socket
from os import environ

import requests
from rich.logging import RichHandler

# Set up logging
FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)
log = logging.getLogger("rich")

def discovery_loop():
    log.info('Starting auto-discovery server.')
    log.info(f'Binding to port {environ.get("NODE_DISCOVERY_PORT", 51366)}.')
    response = 'thor_server_response'

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = ('', environ.get('NODE_DISCOVERY_PORT', 51366))
    sock.bind(server_address)

    while True:
        data, address = sock.recvfrom(4096)
        data = str(data.decode('UTF-8'))

        log.debug(f'Received from {address[0]}: {data}')

        if data.startswith('thor_node_broadcast'):
            log.info(f'Sending reply to {address[0]}')
            sent = sock.sendto(response.encode(), address)

if __name__ == '__main__':
    discovery_loop()
