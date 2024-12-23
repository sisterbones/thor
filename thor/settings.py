from flask import Blueprint, jsonify, current_app, render_template, request, flash
from wtforms import Form, StringField, FloatField, validators

from thor import db

bp = Blueprint("settings", __name__, url_prefix="/settings")

@bp.route("/")
def index():
    return render_template("settings/index.html")

# Forms

class LocationForm(Form):
    location_lat = FloatField('Latitude', validators=[validators.NumberRange(-90.0, 90, "Invalid latitude")])
    location_long = FloatField('Longitude', validators=[validators.NumberRange(-180.0, 180, "Invalid longitude")])

@bp.route("/location", methods=["GET", "POST"])
def location():
    # Get current values
    with current_app.app_context():
        loc = {
            "location_lat": db.get_config("HOME_LAT", 0),
            "location_long": db.get_config("HOME_LONG", 0)
        }

    form = LocationForm(request.form, loc)

    if request.method == "POST" and form.validate():
        loc['location_lat'] = form.location_lat.data
        loc['location_long'] = form.location_long.data
        db.set_config("HOME_LAT", form.location_lat.data)
        db.set_config("HOME_LONG", form.location_long.data)

        flash("Your changes were saved.")


    return render_template("settings/location.html", form=form, loc=loc)

