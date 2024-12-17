
from flask import Blueprint, jsonify, render_template

bp = Blueprint("testing", __name__, url_prefix="/testing")

@bp.route("/")
def index():
    return render_template("testing.html")
