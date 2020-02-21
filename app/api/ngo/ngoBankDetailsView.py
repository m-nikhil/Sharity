from flask import request
from app.MethodView import SuperView

class NgoBankDetailsView(SuperView):
    """ Create NGO service
    """
    method_decorators = []
    _decorators = []

    resource = 'ngo'
    subresource = 'bankdetails'
    mask = []

    def put(self, ngoId):
      body = request.json
      return self.update_subdocument(ngoId, body)

    def get(self, ngoId):
      return self.retrieve_subdocument(ngoId)

    def delete(self, ngoId):
      return self.remove_subdocument(ngoId)