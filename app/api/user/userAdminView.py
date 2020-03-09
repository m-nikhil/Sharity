from flask import request
from app.MethodView import SuperView

class UserAdminView(SuperView):
    """ Create User Transaction service
    """
    method_decorators = []
    _decorators = []

    resource = 'user'
    mask = 'ALL'

    def post(self, userId):
        body = {"isAdmin": True}
        response = self.update(userId, body)[0]
        _id  = response["_id"]
        return {"id": _id, "detail": "The user is made as Admin"}, 200


    def delete(self, userId):
        body = {"isAdmin": False}
        response = self.update(userId, body)[0]
        _id  = response["_id"]
        return {"id": _id, "detail": "The user is removed from Admin access"}, 200