from flask import request
from app.MethodView import SuperView
import json


class TransactionView(SuperView): 
    """ Create transaction service
    """
    method_decorators = []
    _decorators = []

    resource = 'transaction'
    mask = None

    def post(self):
      body = request.json
      fromId = body.pop('fromId')
      toId = body.pop('toId')
      with self.transaction() as session:
        with session.start_transaction():
          user_resp = self.retrieve(fromId,'user')[0]
          ngo_resp = self.retrieve(toId,'ngo')[0]
          body['from'] = { "name": user_resp['firstName'] + user_resp['lastName'], "email": user_resp['email'] }
          body['to'] = { "name": ngo_resp['name'], "email": ngo_resp['email']}
          self.insert_subdocument_array(fromId,body,'user','transaction')
          self.insert_subdocument_array(toId,body,'ngo','transaction')
          return self.insert(body)

    def delete(self, transcationId):
      with self.getTransaction() as session:
        with session.start_transaction():
          self.remove_subdocument_array(transcationId, 'user')
          self.insert_subdocument_array(transcationId, 'ngo')
          return self.remove(transcationId)

    def get(self, transcationId):
      return self.retrieve(transcationId)

    def getAll(self):
      return self.retrieveAll()