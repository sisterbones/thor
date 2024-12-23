from datetime import datetime
import time
from uuid import uuid4

from thor.constants import *


class Alert:
    def __init__(self, *initial_data, **kwargs):
        self.publisher_id = str(uuid4())
        self.nowrap = False
        self.icon = None
        self.subtitle = None
        self.headline = None
        self.timestamp = time.time()
        self.alert_type = None
        self.severity = 0
        self.source = DATA_SOURCE_UNKNOWN
        self.updated = self.timestamp
        self.expiry = self.timestamp + (60 * 60 * 60)
        self.status = "Warning"

        for dictionary in initial_data:
            for key in dictionary:
                setattr(self, key, dictionary[key])
        for key in kwargs:
            setattr(self, key, kwargs[key])

class InfoAlert(Alert):
    """This alert type doesnt show as an alert to be concerned of, its just informational"""
    def __init__(self, *initial_data, **kwargs):
        super().__init__(*initial_data, **kwargs)
        self.status = "Info"


class MetEireannWeatherWarning(Alert):
    def __init__(self, *initial_data, cap_id: str = "", alert_type: str = "Unknown",
                 regions=None, **kwargs):

        super().__init__(*initial_data, **kwargs)
        # print(self.__dict__)

        if regions is None:
            regions = []
        self.publisher_id = cap_id
        if self.alert_type is None:
            self.alert_type = "Unknown"
        self.alert_type = alert_type.split(" ")[0].casefold()
        if type(self.severity) != int: self.severity = (self.severity.casefold() == "moderate" and 1) or \
                        (self.severity.casefold() == "severe" and 2) or \
                        (self.severity.casefold() == "extreme" and 3) or 0

        # Build headline and description
        self.headline = f"{self.level.capitalize()} {self.alert_type.casefold()} {self.status.casefold()}"
        if type(self.onset) == str: self.subtitle = f"Onset: {datetime.fromisoformat(self.onset).strftime('%H:%M')}"
        else: self.subtitle = f"Onset: {datetime.fromtimestamp(self.onset).strftime('%H:%M')}"
        self.icon = (self.alert_type == "rain" and "cloud-rain") or \
                    (self.alert_type == "wind" and "wind") or \
                    (self.alert_type == "snow-ice" and "snowflake") or \
                    (self.alert_type == "low-temperature" and "temperature-arrow-down") or \
                    (self.alert_type == "high-temperature" and "temperature-arrow-up") or \
                    (self.alert_type == "fog" and GENERIC_WARNING_ICON) or \
                    (self.alert_type == "thunderstorm" and "cloud-bolt") or \
                    (self.alert_type == "advisory" and GENERIC_WARNING_ICON) or \
                    GENERIC_WARNING_ICON
        self.nowrap = True

        if type(self.issued) == str: self.issued = datetime.fromisoformat(self.issued).timestamp()
        if type(self.updated) == str: self.updated = datetime.fromisoformat(self.updated).timestamp()
        if type(self.onset) == str: self.onset = datetime.fromisoformat(self.onset).timestamp()
        if type(self.expiry) == str: self.expiry = datetime.fromisoformat(self.expiry).timestamp()

        self.source = DATA_SOURCE_METEIREANN | DATA_SOURCE_INET


class LightningAlert(Alert):
    def __init__(self, *initial_data, **kwargs):
        super().__init__(*initial_data, **kwargs)
        self.alert_type = "lightning"
        self.source = DATA_SOURCE_MQTT
        self.expiry = self.timestamp + (60 * 10)
        self.icon = "bolt"
        self.headline = "Lightning detected!"
        self.subtitle = f"Distance {self.distance_km}km"
