
import os, sys
import connexion
from app.ConnectionBusinessException import BussinessException
from app.CustomViewResolver import CustomViewResolver
from connexion.apps.flask_app import FlaskJSONEncoder
import app.api
from app.database import Database
import prance
from typing import Any, Dict
from pathlib import Path
from bson import ObjectId
from swagger_ui_bundle import swagger_ui_3_path
from flask import Response, send_from_directory
import json
from app.AuthzModule import Authz
from app.CustomResponseValidator import CustomResponseValidator

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
        DATABASE="sharity",
        HOST="http:localhost:5000"
    )

    # The code above will limit the maximum allowed payload to 16 megabytes.
    # If a larger file is transmitted, Flask will raise a RequestEntityTooLarge exception.
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

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

    #Authz Module (needs to be before connexion)
    authzfile = Path("app/authzApiRules.yml")
    authz = Authz()
    authz.initializeAuthz(authzfile)

    validator_map = {
        'response': CustomResponseValidator
    }

    #swagger
    def return_response(exeception):
        return Response(response= json.dumps({"title" : exeception.title, "status" : exeception.status, "detail" : exeception.detail}), status = exeception.status, mimetype="application/json")

    options = {'swagger_path': swagger_ui_3_path}
    connexionApp.add_api(get_bundled_specs(Path("app/openapi/sharity-api.yml")),
                options=options,
                arguments={'title': 'Sharity Docs'},
                resolver=CustomViewResolver('app.api'), validate_responses=True, validator_map=validator_map )
    connexionApp.add_error_handler(BussinessException, return_response)

    @app.route('/static/<path:path>')
    def staticfile(path):
        return send_from_directory('static', path)

    # Ping route
    @app.route('/ping')
    def ping():
        return 'Sharity app is up running :)'

    return app