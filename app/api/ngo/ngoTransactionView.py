from flask import request
from app.MethodView import SuperView

class NgoTransactionView(SuperView):
    """ Create NGO Transaction service
    """
    method_decorators = []
    _decorators = []

    resource = 'ngo'
    subresource = 'transaction'
    mask = ['fromId','toId']

    def getAll(self, ngoId):
      return self.retrieve_subdocument(ngoId)