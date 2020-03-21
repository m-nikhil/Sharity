from flask import request
from app.MethodView import SuperView

class NgoDocumentsView(SuperView):
    """ Create NGO Documents service
    """
    method_decorators = []
    _decorators = []

    resource = 'ngo'
    subresource = 'documents'
    mask = []

    def put(self, ngoId):
      req = dict(request.form)
      filename = req['filename']
      delete =  True if req['delete'] == 'true' else False

      file = request.files.get('file',None)
      
      unique = ngoId + "_" + filename

      meta = {}
      path = self.uploadStatic(file,delete,meta,ngoId,"ngoDocuments",unique)

      if not delete:
        unset_data = None
        body = {filename: path}
      else:
        unset_data = {filename: ""}
        body = None

      return self.update_subdocument(ngoId, body, unset_data)

    def get(self, ngoId):
      return self.retrieve_subdocument(ngoId)