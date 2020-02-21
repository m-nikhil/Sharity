from flask import request
from app.MethodView import SuperView
import json


class NgoTypeView(SuperView): 
    """ Create User service
    """
    method_decorators = []
    _decorators = []

    resource = 'ngoType'
    mask = {}

    def post(self):
      body = request.json
      return self.insert(body)

    def put(self, ngoTypeId):
      body = request.json
      return self.update(ngoTypeId, body)

    def delete(self, ngoTypeId):
      return self.remove(ngoTypeId)

    def get(self, ngoTypeId):
      return self.retrieve(ngoTypeId)

    def getAll(self):
      return self.retrieveAll()