from flask import request
from app.MethodView import SuperView

class UserTransactionView(SuperView):
    """ Create User Transaction service
    """
    method_decorators = []
    _decorators = []

    resource = 'user'
    subresource = 'transaction'
    mask = ['fromId','toId']

    def getAll(self, userId):
      return self.retrieve_subdocument(userId)