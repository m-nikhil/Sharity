from flask import request
from app.MethodView import SuperView
import json


class CityView(SuperView): 
    """ Create City service
    """
    method_decorators = []
    _decorators = []

    resource = 'city'
    mask = None

    def post(self):
      body = request.json
      return self.insert(body)

    def put(self, cityId):
      body = request.json
      return self.update(cityId, body)

    def delete(self, cityId):
      return self.remove(cityId)

    def get(self, cityId):
      return self.retrieve(cityId)

    def getAll(self):
      return self.retrieveAll()