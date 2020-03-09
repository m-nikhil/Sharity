from flask import request
from app.MethodView import SuperView
from app.util import exists

class NgoView(SuperView):
    """ Create NGO service
    """
    method_decorators = []
    _decorators = []

    resource = 'ngo'
    mask = ['password', 'bankdetails', 'documents', 'transaction', 'location.cityId', 'ngotypeId']

    def post(self):
      body = request.json
      # fetch city
      if exists(body,['location','cityId']):
        body['location']['city'] = self.retrieve(body['location']['cityId'],'city',['city'])[0]['city']
      # fetch ngotype
      if exists(body,['ngotypeId']):
        body['ngotype'] = self.retrieve(body['ngotypeId'],'ngoType',['ngotype'])[0]['ngotype']
      return self.insert(body)

    def put(self, ngoId):
      body = request.json
      # fetch city
      if exists(body,['location','cityId']):
        body['location']['city'] = self.retrieve(body['location']['cityId'],'city',['city'])[0]['city']
      # fetch ngotype
      if exists(body,['ngotypeId']):
        body['ngotype'] = self.retrieve(body['ngotypeId'],'ngoType',['ngotype'])[0]['ngotype']
      return self.update(ngoId, body)

    def delete(self, ngoId):
      return self.remove(ngoId)

    def get(self, ngoId):
      return self.retrieve(ngoId)

    def getAll(self, city=None, name=None):
      search = {}
      if city:
        search['city'] = city
      if name:
        search['name'] = name
      return self.retrieveAll(search)