import datetime

from connexion import NoContent
from flask import request, g
from app.MethodView import MethodView
from pymongo import errors

class UserView(MethodView):
    """ Create User service
    """
    method_decorators = []
    _decorators = []

    def post(self):
      body = request.json
      body['_id'] = body['email']
      db = self.getConnection()
      try:
        db.user.insert_one(body)
      except errors.DuplicateKeyError:
        return {"status": 400, "detail": "user already exists"}, 400
      return body, 200

    def put(self, petId):
      body = request.json
      name = body["name"]
      tag = body.get("tag")
      id_ = int(petId)
      pet = self.pets.get(petId, {"id": id_})
      pet["name"] = name
      pet["tag"] = tag
      pet['last_updated'] = datetime.datetime.now()
      self.pets[id_] = pet
      return self.pets[id_], 201

    def delete(self, petId):
      id_ = int(petId)
      if self.pets.get(id_) is None:
          return NoContent, 404
      del self.pets[id_]
      return NoContent, 204

    def get(self, petId):
      id_ = int(petId)
      if self.pets.get(id_) is None:
          return NoContent, 404
      return self.pets[id_]

    def search(self, limit=100):
      # NOTE: we need to wrap it with list for Python 3 as dict_values is not JSON serializable
      return list(self.pets.values())[0:limit]