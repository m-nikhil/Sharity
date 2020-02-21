from flask import request
from app.MethodView import SuperView

class NgoDocumentsView(SuperView):
    """ Create NGO service
    """
    method_decorators = []
    _decorators = []

    resource = 'ngo'
    subresource = 'documents'
    mask = []

    def put(self, ngoId):
      req = dict(request.form)
      print(req)
      body = {}
      body[req['filename']] =  "http://to-be-done"
      # TO-DO file storage and update body data
      return self.update_subdocument(ngoId, body)

    def get(self, ngoId):
      return self.retrieve_subdocument(ngoId)