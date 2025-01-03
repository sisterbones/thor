import logging

from flask import Blueprint, jsonify, current_app, render_template, request, flash, redirect, url_for
from wtforms import Form, StringField, FloatField, validators, BooleanField, SubmitField, SelectField

from thor import db
from thor.misc import truthy

bp = Blueprint("settings", __name__, url_prefix="/settings")

log = logging.getLogger(__name__)

@bp.route("/")
def index():
    return render_template("settings/index.html")


# Forms
class LocationForm(Form):
    location_lat = FloatField('Latitude', validators=[validators.NumberRange(-90.0, 90, "Invalid latitude")])
    location_long = FloatField('Longitude', validators=[validators.NumberRange(-180.0, 180, "Invalid longitude")])


class MetNoConfigForm(Form):
    metenable = BooleanField('Enable')
    metnosubmit = SubmitField('Save')


class MetEireannWWConfigForm(Form):
    mewwenable = BooleanField('Enable')
    mewwsubmit = SubmitField("Save")
    choices = [
        ("IRELAND", "Ireland"),
        ("EI01", "Carlow"),
        ("EI02", "Canvan"),
        ("EI03", "Clare"),
        ("EI04", "Cork"),
        ("EI06", "Donegal"),
        ("EI07", "Dublin"),
        ("EI10", "Galway"),
        ("EI11", "Kerry"),
        ("EI12", "Kildare"),
        ("EI13", "Kilkenny"),
        ("EI14", "Leitrim"),
        ("EI15", "Laois"),
        ("EI16", "Limerick"),
        ("EI18", "Longford"),
        ("EI19", "Louth"),
        ("EI20", "Mayo"),
        ("EI21", "Meath"),
        ("EI22", "Monaghan"),
        ("EI23", "Offaly"),
        ("EI24", "Roscommon"),
        ("EI25", "Sligo"),
        ("EI26", "Tipperary"),
        ("EI27", "Waterford"),
        ("EI29", "Westmeath"),
        ("EI30", "Wexford"),
        ("EI31", "Wicklow"),
    ]

    county = SelectField("Region", choices=choices)


# Routes
@bp.route("/providers", methods=["GET", "POST"])
def providers():
    met_form = MetNoConfigForm()
    metie_form = MetEireannWWConfigForm()
    met_form.metenable.data = truthy(db.get_config("MET_NO_ENABLE", False))

    metie_form.mewwenable.data = truthy(db.get_config("METIE_WW_ENABLE", False))
    metie_form.county.data = db.get_config("METIE_WW_COUNTY", "IRELAND")

    return render_template("settings/providers.html", met_form=met_form, metie_form=metie_form)

# TODO: Investigate why these don't get saved to the database.
@bp.route("/providers/metieww", methods=["POST"])
def providers_metieww():
    form = MetEireannWWConfigForm()

    log.debug("metie_form.mewwenable: %s", form.mewwenable.data)
    log.debug("metie_form.county: %s", form.county.data)

    if form.validate():
        log.debug("met_ie form validated.")

        db.set_config("METIE_WW_ENABLE", form.mewwenable.data)
        if form.mewwenable.data:
            db.set_config("METIE_WW_COUNTY", form.county.data)
        flash("Your changes for Met Éireann have been saved.")
    else:
        flash(form.errors)

    return redirect(url_for("settings.providers"))


@bp.route("/providers/metno", methods=["POST"])
def providers_metno():
    form = MetNoConfigForm()

    if form.validate():
        log.debug("Enable is set to %s", form.metenable.data)
        db.set_config("MET_NO_ENABLE", truthy(form.metenable.data))
        flash("Your changes for met.no have been saved.")
    else:
        flash(form.errors)

    return redirect(url_for("settings.providers"))


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
