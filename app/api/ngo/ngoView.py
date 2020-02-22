from flask import request
from app.MethodView import SuperView


class NgoView(SuperView):
    """ Create NGO service
    """
    method_decorators = []
    _decorators = []

    resource = 'ngo'
    mask = {'password': False, 'bankdetails' : False, 'requirements': False, 'documents': False, 'transaction': False}

    def post(self):
      body = request.json 
      return self.insert(body)

    def put(self, ngoId):
      body = request.json
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