import datetime

from connexion import NoContent
from flask import request, g
from app.MethodView import SuperView

class UserView(SuperView):
    """ Create User service
    """
    method_decorators = []
    _decorators = []

    resource = 'user'
    projection = {'active': False, 'isAdmin': False, 'transations': False, 'password': False}

    def post(self):
      body = request.json
      return self.insert(body)

    def put(self, userId):
      body = request.json
      return self.update(userId, body)

    def delete(self, userId):
      return self.remove(userId)

    def get(self, userId):
      return self.retrieve(userId)

    def search(self):
      return self.retrieveAll()