import datetime
import json
import logging
import time

import requests
import requests.exceptions
from flask import current_app
from rich.logging import RichHandler

from thor.constants import *
from thor.alert import MetEireannWeatherWarning, InfoAlert, add_new_alert, Alert, publish_alert, remove_alert
from thor.db import get_config, set_config
from thor.misc import has_internet_connection

log = logging.getLogger("rich")


class WeatherProvider:
    def fetch(self) -> dict:
        """Fetches the latest data from the weather provider"""
        return {
            "timestamp": time.time(),
            "icon": 'circle-question',  # Font Awesome icon
            "source": {"label": None, "href": None},
            "weather": {
                "temperature": 0.0,
                "conditions": "unknown",
                "headline": "Unknown"
            }
        }


def met_no_symbol_to_font_awesome(icon):
    """Converts a MET Norway symbol name to a similar Font Awesome icon and summary of icon."""
    mapping = {
        "clearsky_day": ("sun", "Clear sky"),
        "clearsky_night": ("moon", "Clear sky"),
        "clearsky_polartwilight": ("sun", "Clear sky"),

        "fair_day": ("cloud-sun", "Fair"),
        "fair_night": ("cloud-moon", "Fair"),
        "fair_polartwilight": ("cloud-sun", "Fair"),

        "cloudy": ("cloud", "Cloudy"),

        "partlycloudy_day": ("cloud-sun", "Partly cloudy"),
        "partlycloudy_night": ("cloud-moon", "Partly cloudy"),
        "partlycloudy_polartwilight": ("cloud-sun", "Partly cloudy"),

        "rainshowers_day": ("cloud-sun-rain", "Rain showers"),
        "rainshowers_night": ("cloud-moon-rain", "Rain showers"),
        "rainshowers_polartwilight": ("cloud-sun-rain", "Rain showers"),

        "rainshowersandthunder_day": ("cloud-bolt", "Rain showers and thunder"),
        "rainshowersandthunder_night": ("cloud-bolt", "Rain showers and thunder"),
        "rainshowersandthunder_polartwilight": ("cloud-bolt", "Rain showers and thunder"),

        "sleetshowers_day": ("cloud-showers-heavy", "Sleet showers"),
        "sleetshowers_night": ("cloud-showers-heavy", "Sleet showers"),
        "sleetshowers_polartwilight": ("cloud-showers-heavy", "Sleet showers"),

        "snowshowers_day": ("cloud-showers-heavy", "Snow showers"),
        "snowshowers_night": ("cloud-showers-heavy", "Snow showers"),
        "snowshowers_polartwilight": ("cloud-showers-heavy", "Snow showers"),

        "rain": ("cloud-rain", "Rain"),

        "heavyrain": ("cloud-showers-heavy", "Heavy rain"),

        "heavyrainandthunder": ("cloud-bolt", "Heavy rain and thunder"),

        "sleet": ("cloud-showers-heavy", "Sleet"),

        "snow": ("cloud-showers-heavy", "Snow"),

        "snowandthunder": ("cloud-bolt", "Snow and thunder"),

        "sleetshowersandthunder_day": ("cloud-bolt", "Sleet showers and thunder"),
        "sleetshowersandthunder_night": ("cloud-bolt", "Sleet showers and thunder"),
        "sleetshowersandthunder_polartwilight": ("cloud-bolt", "Sleet showers and thunder"),

        "snowshowersandthunder_day": ("cloud-bolt", "Snow showers and thunder"),
        "snowshowersandthunder_night": ("cloud-bolt", "Snow showers and thunder"),
        "snowshowersandthunder_polartwilight": ("cloud-bolt", "Snow showers and thunder"),

        "rainandthunder": ("cloud-bolt", "Rain and thunder"),

        "sleetandthunder": ("cloud-bolt", "Sleet and thunder"),

        "lightrain": ("cloud-rain", "Light rain"),
    }

    if icon in mapping:
        return mapping.get(icon, ("circle-question", "Unknown"))

    return "circle-question", "Unknown"


class CachingWeatherProvider(WeatherProvider):
    def __init__(self):
        self.last_fetched_time = 0
        self.seconds_to_live = 6000  # 10 minutes
        self.cached_response = None
        self.user_agent = "Thor Lightning Detection & Alert System (in development) https://github.com/sisterbones/thor"
        self.query = {}

    def fetch(self) -> dict:
        if not has_internet_connection():
            return self.cached_response
        if time.time() <= self.last_fetched_time + self.seconds_to_live and self.cached_response:
            log.debug("Serving cache")
            return self.cached_response
        try:
            data_request = requests.get(
                self.base_url,
                self.query,
                timeout=(1, 10),
                headers={
                    "User-Agent": self.user_agent
                }
            )
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
            log.critical(f"Couldnt connect to {self.base_url}.")
            return self.cached_response
        self.cached_response = data_request
        self.last_fetched_time = time.time()
        return data_request


class MetNoWeatherProvider(CachingWeatherProvider):
    """Weather provider using the MET Norway's Location Forcast API. (Requires an internet connection)"""

    def __init__(self, lat: float, long: float):
        super().__init__()

        self.lat = lat
        self.long = long

        self.base_url = 'https://api.met.no/weatherapi/locationforecast/2.0/compact'
        self.query = {"lat": self.lat, "lon": self.long}

    def fetch(self) -> dict:
        """Fetches data from the MET Norway Location Forcast API"""

        try:
            data = super().fetch()
            data = data.json()
        except (json.JSONDecodeError, TypeError):
            return {"timestamp": time.time(), "error": "no_internet", "icon": "circle-exclamation",
                    "source": {"label": "Norwegian Meteorological Institute", "href": "https://met.no"}, "weather": {
                    "temperature": 0.0,
                    "conditions": "unknown",
                    "headline": "No Internet"
                }
                    }

        icon = met_no_symbol_to_font_awesome(
            data['properties']['timeseries'][0]['data']['next_12_hours']['summary']['symbol_code'])

        response = {
            "timestamp": time.time(),
            "location": {
                "lat": self.lat,
                "long": self.long
            },
            "icon": icon[0],  # Font Awesome icon
            "source": {"label": "Norwegian Meteorological Institute", "href": "https://met.no"},
            "weather": {
                "temperature": data['properties']['timeseries'][0]['data']['instant']['details']['air_temperature'],
                "conditions": data['properties']['timeseries'][0]['data']['next_1_hours']['summary']['symbol_code'],
                "headline": icon[1]
            }
        }

        return response


class MetEireannWeatherWarningProvider(CachingWeatherProvider):
    def __init__(self, region="IRELAND"):
        super().__init__()
        self.region = region
        self.base_url = f'https://www.met.ie/Open_Data/json/warning_{self.region}.json'

    def fetch(self) -> dict:
        cache = super().fetch()

        def callback(updated=True, alert=Alert()):
            log.debug("%s: updated=%s", alert.headline, updated)
            if updated:
                return
            else:
                publish_alert(alert)

        try:
            data = super().fetch().json()
        except:
            alert = InfoAlert(publisher_id="metie_ww_fail",
                              headline="Can't get weather warnings from Met Éireann. (WW_FAIL)",
                              icon="globe")
            add_new_alert(alert, callback)

            return {"timestamp": time.time(), "error": "no_internet", "warnings": [
                alert
            ]}

        remove_alert(publisher_id="metie_ww_fail")

        warnings = []

        # Process warnings
        for warning in data:
            alert = MetEireannWeatherWarning(
                cap_id=warning.get("capId", ""), alert_type=warning.get("type", "Unknown"),
                severity=warning.get("severity", "Unknown"),
                certainty=warning.get("certainty"), level=warning.get("level", "Unknown"),
                issued=warning.get("issued", PLACEHOLDER_EPOCH_ISO),
                updated=warning.get("updated", PLACEHOLDER_EPOCH_ISO),
                onset=warning.get("onset", PLACEHOLDER_EPOCH_ISO),
                expiry=warning.get("expiry", PLACEHOLDER_EPOCH_ISO), source_headline=warning.get("headline", ""),
                source_description=warning.get("description", ""),
                regions=warning.get("regions", [self.region]), status=warning.get("status", "warning")
            )
            add_new_alert(alert)

            warnings.append(alert.__dict__)

        response = {
            "timestamp": time.time(),
            "warnings": warnings,
        }

        return response
