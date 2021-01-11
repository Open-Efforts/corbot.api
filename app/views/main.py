import json

from flask import render_template, Blueprint, request, make_response
from flask_cors import cross_origin

from app.controllers.dispatcher import dispatch
from app.controllers.ip_auth import ip_auth
from app.forms import TestingForm
from app.logger import log

main_blueprint = Blueprint("main", __name__)


@main_blueprint.route("/", methods=["GET"])
@ip_auth
def index():
    form = TestingForm()
    return render_template("index.html", form=form)


@main_blueprint.route("/api", methods=["POST"])
@ip_auth
@cross_origin()
def api():
    log(log.INFO, "api")
    if request.json:
        json_data = request.json  # automatically converted to dict
        reg_num = json_data["reg_number"]
        body = json_data["body"]
        method_name = json_data["subject"]
        # dispatch does all work, except converting to json
        res = make_response(
            json.dumps(
                dispatch(method_name, body, reg_num),
                indent=4,
                sort_keys=True,
                default=str,
            ),
            200,
        )
        res.mimetype = "application/json"
        return res
    form = TestingForm()  # form to test from admin dashboard
    if form.validate_on_submit():
        body = form.Body.data
        reg_num = form.RegNumber.data
        method_name = form.Subject.data
        res = make_response(
            json.dumps(
                dispatch(method_name, body, reg_num),
                indent=4,
                sort_keys=True,
                default=str,
            ),
            200,
        )
        res.mimetype = "application/json"
        return res
    return {}
