from flask import request
from app.MethodView import SuperView

class NgoTransactionView(SuperView):
    """ Create NGO Transaction service
    """
    method_decorators = []
    _decorators = []

    resource = 'ngo'
    subresource = 'transaction'
    mask = None

    def getAll(self, ngoId):
      return self.retrieveAll_subdocument(ngoId)