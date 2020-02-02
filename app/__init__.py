
import os, sys
import connexion
from connexion.resolver import MethodViewResolver
from connexion.apps.flask_app import FlaskJSONEncoder
import app.api
from app.database import Database
import prance
from typing import Any, Dict
from pathlib import Path
from bson import ObjectId

class CustomJSONEncoder(FlaskJSONEncoder):
        def default(self, obj):
            if isinstance(obj, ObjectId):
                return str(obj)
            return FlaskJSONEncoder.default(self, obj)

def get_bundled_specs(main_file: Path) -> Dict[str, Any]:
    parser = prance.ResolvingParser(str(main_file.absolute()),
                                    lazy = True, strict = True)
    parser.parse()
    return parser.specification


def create_app(test_config=None):
    # create and configure the app
    connexionApp = connexion.FlaskApp(__name__, specification_dir='openapi/', debug=True)
    app = connexionApp.app

    app.json_encoder = CustomJSONEncoder  # custom json decoder
                                          # added to decode mongoDB id

    app.config.from_mapping(
        SECRET_KEY='dev_secret_3fkj$s',
        DATABASE_HOST="mongodb://localhost:27017/",
        DATABASE="sharity"
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('application.cfg')
    else:
        # load the test config if passed in
        app.config.from_pyfile(test_config)

    #database
    instance = Database(app)
    db = instance.connect()
    try:
        res = db.admin.command('ping') # ping database; to check if it's up and running
    except:
        sys.exit("Error: Couldn't reach the database.")
    if(not res['ok']):
        sys.exit("Error: Couldn't reach the database.")

    #swagger
    options = {"swagger_ui": True}
    connexionApp.add_api(get_bundled_specs(Path("app/openapi/sharity-api.yml")),
                options=options,
                arguments={'title': 'Sharity Docs'},
                resolver=MethodViewResolver('app.api'), strict_validation=True, validate_responses=True )

    # Ping route
    @app.route('/ping')
    def ping():
        return 'Sharity app is up running :)'

    return app

