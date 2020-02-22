from flask import request
from app.MethodView import SuperView

class UserTransactionView(SuperView):
    """ Create User Transaction service
    """
    method_decorators = []
    _decorators = []

    resource = 'user'
    subresource = 'transaction'
    mask = None

    def getAll(self, ngoId):
      return self.retrieveAll_subdocument(ngoId)