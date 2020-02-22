from flask import request
from app.MethodView import SuperView
import json


class TransactionView(SuperView): 
    """ Create transaction service
    """
    method_decorators = []
    _decorators = []

    resource = 'transaction'
    mask = None

    def post(self):
      body = request.json
      return self.insert(body)

    def delete(self, transcationId):
      return self.remove(transcationId)

    def get(self, transcationId):
      return self.retrieve(transcationId)

    def getAll(self):
      return self.retrieveAll()