
import time
from thor.constants import *
from datetime import datetime

class Alert:
    def __init__(self):
        self.nowrap = False
        self.icon = None
        self.subtitle = None
        self.headline = None
        self.timestamp = time.time()
        self.alert_type = None
        self.severity = 0
        self.source = None
        self.updated = self.timestamp
        self.expiry = self.timestamp + (60 * 60 * 60)
        self.status = "Warning"

class MetEireannWeatherWarning(Alert):
    def __init__(self, cap_id: str = "", alert_type: str = "Unknown", severity: str = "Unknown", certainty: str = "Likely",
                 level: str = "Unknown", issued: str = datetime.now().isoformat(), updated: str = datetime.now().isoformat(),
                 onset: str = datetime.now().isoformat(), expiry: str = datetime.now().isoformat(), headline: str = "",
                 description: str = "", regions=None, status: str = "Warning"):
        super().__init__()
        if regions is None:
            regions = []
        self.cap_id = cap_id
        self.alert_type = alert_type.casefold()
        if ";" in self.alert_type:
            self.alert_type = headline.split(" ")[0].casefold()
        self.severity = (severity.casefold() == "moderate" and 1) or \
                        (severity.casefold() == "severe" and 2) or \
                        (severity.casefold() == "extreme" and 3) or 0
        self.certainty = certainty
        self.level = level
        self.issued = issued
        self.updated = updated
        self.onset = onset
        self.expiry = expiry
        self.source_headline = headline
        self.source_description = description
        self.regions = regions
        self.status = status

        # Build headline and description
        self.headline = f"{self.level.capitalize()} {self.alert_type.casefold()} {self.status.casefold()}"
        self.subtitle = f"Onset: {datetime.fromisoformat(self.onset).strftime('%H:%M')}"
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

        self.source = DATA_SOURCE_METEIREANN | DATA_SOURCE_INET


class LightningAlert(Alert):
    def __init__(self):
        super().__init__()
        self.alert_type = "lightning"
        self.distance_km = 0
        self.source = DATA_SOURCE_MQTT
        self.expiry = self.timestamp + (60 * 60 * 60)
        self.icon = "bolt"
        self.headline = "Lightning detected!"
        self.subtitle = f"Last: {datetime.fromtimestamp(self.timestamp).strftime('%H:%M')} • Distance {self.distance_km}km"
