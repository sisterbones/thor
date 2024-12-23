from flask import Blueprint, jsonify, current_app, render_template, request
from flask_wtf import FlaskForm
from wtforms import Form, StringField, FloatField, validators

bp = Blueprint("settings", __name__, url_prefix="/settings")

@bp.route("/")
def index():
    return render_template("settings/index.html")

# Forms

class LocationForm(FlaskForm):
    location_lat = FloatField('Latitude', validators=[validators.NumberRange(-90.0, 90, "Invalid latitude")])
    location_long = FloatField('Longitude', validators=[validators.NumberRange(-180.0, 180, "Invalid longitude")])

@bp.route("/location", methods=["GET", "POST"])
def location():
    form = LocationForm(request.form)
    if form.validate_on_submit():
        print("Validated")
    return render_template("settings/location.html", form=form)

