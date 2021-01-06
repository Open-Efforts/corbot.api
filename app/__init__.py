import os
import json

from app.controllers.db_handler import DB1, DB_TEST
from app.models.vps import VPS

from flask import Flask, make_response, current_app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc
from pymysql import err
from app.logger import log


# instantiate extensions
db = SQLAlchemy()
db1 = DB1()
if current_app and (current_app.config["TESTING"]):
    db1 = DB_TEST()
session = db1.session
metadata = db1.metadata


def create_app(environment="development"):

    from config import config
    from app.views import (
        main_blueprint,
    )

    # Instantiate app.
    app = Flask(__name__)
    # Set app config.
    env = os.environ.get("FLASK_ENV", environment)
    app.config.from_object(config[env])
    config[env].configure(app)
    log.set_level(app.config["LOG_LEVEL"])

    # Set up extensions.
    db.init_app(app)

    # Register blueprints.
    app.register_blueprint(main_blueprint)

    # Error handlers.
    @app.errorhandler(Exception)
    def handle_error(ex):
        if isinstance(ex, exc.SQLAlchemyError):
            log(log.ERROR, "Handled exc.SQLAlchemyError and throw out")
            raise ex
        if isinstance(ex, err.Error):
            log(log.ERROR, "Handled err.Error and throw out")
            raise ex
        log(log.ERROR, "Return error responce")
        error_dict = {
            'error': ex,
            "doc": ex.__doc__
        }
        res = make_response(json.dumps(error_dict, indent=4, sort_keys=True, default=str), 400)
        res.mimetype = 'application/json'
        return res

    return app
