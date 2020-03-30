from flask import request
from app.MethodView import SuperView
import json


class ProfileView(SuperView): 
    """ Create Profile view service
    """
    method_decorators = []
    _decorators = []

    resource = 'user'
    
    def get(self, token_info):
        print(token_info)
        return json.loads(token_info['sub'])