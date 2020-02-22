from flask import request
from app.MethodView import SuperView
import json


class UserView(SuperView): 
    """ Create User service
    """
    method_decorators = []
    _decorators = []

    resource = 'user'
    mask = {'active': False, 'isAdmin': False, 'transations': False, 'password': False, 'transaction': False}

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

    def getAll(self):
      return self.retrieveAll()