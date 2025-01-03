# Data sources
DATA_SOURCE_INET = 1 << 0  # Internet
DATA_SOURCE_MQTT = 1 << 1  # Arrived via MQTT
DATA_SOURCE_SOCKETIO = 1 << 2  # Arrived via the Socket.IO connection.
DATA_SOURCE_UNKNOWN = 1 << 3
DATA_SOURCE_METEIREANN = 1 << 5  # Met Éireann, Ireland's meteorological service
DATA_SOURCE_METNO = 1 << 6  # Norwegian meteorological service

# Contains constants used in bitwise stuff
DATA_OUTPUT_MQTT = 1 << 0
DATA_OUTPUT_SOCKETIO = 1 << 1

PLACEHOLDER_EPOCH_ISO = "1970-01-01T00:00:00+00:00"
GENERIC_WARNING_ICON = "triangle-exclamation"
GENERIC_ICON = "circle-question"
