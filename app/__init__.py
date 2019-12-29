
import os
import connexion
from connexion.resolver import MethodViewResolver
import app.api
from pymongo import MongoClient
from app.database import *
import prance
from typing import Any, Dict
from pathlib import Path

def get_bundled_specs(main_file: Path) -> Dict[str, Any]:
    parser = prance.ResolvingParser(str(main_file.absolute()),
                                    lazy = True, strict = True)
    parser.parse()
    return parser.specification


def create_app(test_config=None):
    # create and configure the app
    connexionApp = connexion.FlaskApp(__name__, specification_dir='openapi/', debug=True)
    app = connexionApp.app

    app.config.from_mapping(
        SECRET_KEY='dev_secret_3fkj$s',
        DATABASE="mongodb://localhost:27017/",
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('application.cfg')
    else:
        # load the test config if passed in
        app.config.from_pyfile(test_config)

    #swagger
    options = {"swagger_ui": True}
    connexionApp.add_api(get_bundled_specs(Path("app/openapi/sharity-api.yml")),
                options=options,
                arguments={'title': 'Sharity Docs'},
                resolver=MethodViewResolver('app.api'), strict_validation=True, validate_responses=True)

    #database
    client = MongoClient(app.config['DATABASE'])
    with app.app_context():
        init_db(client)

    @app.teardown_appcontext
    def shutdown_session(exception):
        teardown_db()

    # Ping route
    @app.route('/ping')
    def ping():
        return 'Sharity app is up running :)'

    return app

