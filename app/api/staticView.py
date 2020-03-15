from flask import request
from app.MethodView import SuperView
import json
from app.ConnectionBusinessException import BussinessException

class StaticView(SuperView): 
    """ Create static service
    """
    method_decorators = []
    _decorators = []

    resource = None
    mask = None

    def delete(self,type,id):
      return self.deleteStatic(type,id)

    def get(self,type,id):
      return self.retriveStatic(type,id)
