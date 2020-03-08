from flask import request
from app.MethodView import SuperView
import json
from app.ConnectionBusinessException import BussinessException

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
      db = self.getConnection()
      db.ngo.update({"location.cityId" : cityId}, {"$set" : { "location.city" : body['city']}})
      return self.update(cityId, body)

    def delete(self, cityId):
      # though a city is deleted, it lives in document where its foreign key
      return self.remove(cityId)

    def get(self, cityId):
      return self.retrieve(cityId)

    def getAll(self):
      return self.retrieveAll()