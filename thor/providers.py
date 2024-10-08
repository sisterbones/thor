import time
import requests

# Constants
SOURCE_INTERNET = 0<<1

class WeatherProvider:
    def __init__(self, lat: float, long: float):
        self.lat = lat
        self.long = long

    def fetch(self) -> dict:
        """Fetches the latest data from the weather provider"""
        return {
            "timestamp": time.time(),
            "location": {
                "lat": self.lat,
                "long": self.long
            },
            "icon": 'circle-question', # Font Awesome icon
            "weather": {
                "temperature": 0.0,
                "conditions": "unknown"
            }
        }

def met_no_symbol_to_font_awesome(icon):
    """Converts a MET Norway symbol name to a similar Font Awesome icon and summary of icon."""
    mapping = {
        "clearsky_day": ("sun", "Sunny"),
        "fair_day": ("cloud-sun", "Fair skies"),
        "cloudy": ("cloud", "Cloudy"),
        "rain": ("cloud-rain", "Raining"),
        "partlycloudy_night": ("cloud-moon", "Partly cloudy")
    }

    print(icon)

    if icon in mapping:
        print(mapping.get(icon))
        return mapping.get(icon, ("circle-question", "Unknown"))

    return "circle-question", "Unknown"

class CachingWeatherProvider(WeatherProvider):
    def __init__(self, lat: float, long: float):
        super().__init__(lat, long)

        self.last_fetched_time = 0
        self.seconds_to_live = 6000 # 10 minutes
        self.cached_response = {}

    def fetch(self) -> dict:
        if (time.time() > last_fetched_time + seconds_to_live):
            return cached_response

class MetNoWeatherProvider(CachingWeatherProvider):
    """Weather provider using the MET Norway's Location Forcast API. (Requires an internet connection)"""

    def __init__(self, lat: float, long: float):
        super().__init__(lat, long)

        self.user_agent = "Thor Lightning Alert System (in development) https://github.com/sisterbones/thor"
        self.base_url = 'https://api.met.no/weatherapi/locationforecast/2.0/compact'

    def fetch(self) -> dict:
        """Fetches data from the MET Norway Location Forcast API"""

        cache = super().fetch()

        if not cache:
            data_request = requests.get(
                self.base_url,
                {
                    "lat": self.lat,
                    "lon": self.long
                },
                headers={
                    "User-Agent": self.user_agent
                }
            )
            data = data_request.json()
            self.cache = data
        else:
            data = cache

        icon = met_no_symbol_to_font_awesome(data['properties']['timeseries'][0]['data']['next_12_hours']['summary']['symbol_code'])

        return {
            "timestamp": time.time(),
            "location": {
                "lat": self.lat,
                "long": self.long
            },
            "icon": icon[0], # Font Awesome icon
            "weather": {
                "temperature": data['properties']['timeseries'][0]['data']['instant']['details']['air_temperature'],
                "conditions": data['properties']['timeseries'][0]['data']['next_1_hours']['summary']['symbol_code'],
                "headline": icon[1]
            }
        }
