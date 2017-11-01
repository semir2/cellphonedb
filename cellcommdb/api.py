import os

from cellcommdb.api_endpoints.queries import Query0Endpoint
from flask import Flask, abort, request
from flask_restful import Api, Resource

from cellcommdb.config import BaseConfig
from cellcommdb.extensions import db

current_dir = os.path.dirname(os.path.realpath(__file__))


def create_app(config=BaseConfig):
    app = Flask(__name__)
    app.config.from_object(config)
    app.url_map.strict_slashes = False

    with app.app_context():
        db.init_app(app)

    api = Api(app, prefix=config.API_PREFIX)
    # api.add_resource(ProteinResource, '/protein')
    # api.add_resource(ComplexResource, '/complex')

    api.add_resource(Query0Endpoint, '/query0')

    return app
