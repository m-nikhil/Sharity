from flask import request
from app.MethodView import SuperView

class NgoRequirementsView(SuperView):
    """ Create NGO service
    """
    method_decorators = []
    _decorators = []

    resource = 'ngo'
    subresource = 'requirements'
    mask = []

    def post(self, ngoId):
      body = request.json
      return self.insert_subdocument_array(ngoId, body)

    def put(self, ngoId, requirementId):
      body = request.json
      return self.update_subdocument_array(ngoId, body, requirementId)

    def get(self, ngoId, requirementId):
      return self.retrieve_subdocument_array(ngoId, requirementId)

    def delete(self, ngoId, requirementId):
      return self.remove_subdocument_array(ngoId, requirementId)

    def getAll(self, ngoId):
      return self.retrieveAll_subdocument_array(ngoId)