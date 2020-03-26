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

    def post(self, ngoId):
      req = dict(request.form)
      filename = req['filename']

      file = request.files.get('file',None)
      
      unique = ngoId + "_" + filename

      meta = {}
      path = self.uploadStatic(file,meta,ngoId,"ngoDocuments",unique,None)

      unset_data = None
      body = {filename: path}


      return self.update_subdocument(ngoId, body, unset_data)

    def delete(self, ngoId, fileId):
      unique = ngoId + "_" + filename

      unset_data = {filename: ""}
      body = None
      with self.transaction() as session:
        with session.start_transaction():
          self.update_subdocument(ngoId, body, unset_data)
          return self.deleteStaticUsingUnique(unique)
      

    def get(self, ngoId):
      return self.retrieve_subdocument(ngoId)