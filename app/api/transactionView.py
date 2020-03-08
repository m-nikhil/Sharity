from flask import request
from app.MethodView import SuperView
import json
from bson import ObjectId


class TransactionView(SuperView): 
    """ Create transaction service
    """
    method_decorators = []
    _decorators = []

    resource = 'transaction'
    mask = {'fromId' : False, 'toId' : False}

    def post(self):
      body = request.json
      with self.transaction() as session:
        with session.start_transaction():
          user_resp = self.retrieve(body['fromId'],'user', ['firstName','lastName','email'])[0]
          ngo_resp = self.retrieve(body['toId'],'ngo',['name','email'])[0]
          body['from'] = { "name": user_resp['firstName'] + user_resp['lastName'], "email": user_resp['email'] }
          body['to'] = { "name": ngo_resp['name'], "email": ngo_resp['email']}
          objectId = ObjectId()
          self.insert_subdocument_array(body['fromId'],body,'user','transaction',None,objectId)
          self.insert_subdocument_array(body['toId'],body,'ngo','transaction',None,objectId)
          return self.insert(body,objectId=objectId)

    def delete(self, transactionId):
      with self.transaction() as session:
        with session.start_transaction():
          transaction = self.retrieve(transactionId, projection = ['fromId','toId'])[0]
          self.remove_subdocument_array( transaction['fromId'], transactionId, 'user', 'transaction')
          self.remove_subdocument_array( transaction['toId'], transactionId, 'ngo', 'transaction')
          return self.remove(transactionId)

    def get(self, transcationId):
      return self.retrieve(transcationId)

    def getAll(self):
      return self.retrieveAll()