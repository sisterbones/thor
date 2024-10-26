
from flask import Blueprint, jsonify

bp = Blueprint("testing", __name__)

@bp.get('/meteireann/weatherwarning/<region>.json')
def me_weather_warning_sample(region="IRELAND"):
    return jsonify([{"id": 1,
                "capId": "2.49.0.1.372.0.200610184826.N_Norm001_Weather",
                "type": "Rain",
                "severity": "Moderate",
                "certainty": "Likely",
                "level": "yellow",
                "issued": "2020-06-10T19:48:26+01:00",
                "updated": "2020-06-10T19:48:26+01:00",
                "onset": "2020-06-10T22:00:00+01:00",
                "expiry": "2020-06-11T14:00:00+01:00",
                "headline": "Rain warning for Ireland",
                "description": "Heavy showers will affect all areas overnight and tomorrow. Expect local flooding",
                "regions": ["EI30", "EI21", "EI31", "EI23", "EI19", "EI18", "EI01", "EI15", "EI29", "EI13", "EI12",
                            "EI07", "EI02", "EI22", "EI06", "EI26", "EI27", "EI16", "EI03", "EI04", "EI11", "EI25",
                            "EI24", "EI14",  "EI20", "EI10"],
                "status": "Warning"}])
