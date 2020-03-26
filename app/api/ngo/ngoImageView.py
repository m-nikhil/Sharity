from flask import request
from app.MethodView import SuperView

class NgoImageView(SuperView):
    """ Create NGO Image service
    """
    method_decorators = []
    _decorators = []

    resource = 'ngo'
    subresource = 'image'
    mask = []

    def post(self, ngoId):
      req = dict(request.form)
      file = request.files.get('file',None)
      
      meta = {}
      path = self.uploadStatic(file,meta,ngoId,"ngoImage",None,10)

      return self.insert_array(ngoId, path)

    def delete(self, ngoId, imageId):
      fileurl = "/" + "ngoImage" + "/" + imageId

      with self.transaction() as session:
        with session.start_transaction():
          self.remove_array(ngoId, fileurl)
          print("d")
          return self.deleteStatic("ngoImage",imageId)

    def get(self, ngoId):
      return self.retrieve_array(ngoId)