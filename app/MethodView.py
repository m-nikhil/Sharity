# 
# overwritten implementaion of MethodView of Flask
# Added capability to docorate middleware to individual route
# Added database getconnection method
#

from flask.views import MethodView
from app.database import Database
from pymongo import errors
from bson import ObjectId


def convertToObjectId(obj_id):
    try:
        obj_id = ObjectId(obj_id)
        return obj_id
    except:
        return None


class SuperView(MethodView):

    _decorators = {}

    # abstract member; needs to be overridden
    # datatype - string
    @property
    def resource(self):
        raise NotImplementedError

    # abstract member; needs to be overridden
    # datatype - dict
    @property
    def projection(self):
        raise NotImplementedError

    def __init__(self):
            super().__init__()
            instance = Database.getInstance()
            self.db = instance.getConnection()
            
    def dispatch_request(self, *args, **kwargs):
        """Derived MethodView dispatch to allow for decorators to be
            applied to specific individual request methods - in addition
            to the standard decorator assignment.
            
            Example decorator use:
            decorators = [user_required] # applies to all methods
            _decorators = {
                'post': [admin_required, format_results]
            }    
        """

        view = super(MethodView, self).dispatch_request
        decorators = self._decorators.get(request.method.lower())
        if decorators:
            for decorator in decorators:
                view = decorator(view)

        return view(*args, **kwargs)

    # Get database
    def getConnection(self):
        return self.db

    # Database operation helper functions
    # TO-DO softdelete, active records
    def insert(self, data):
        try:
            obj_id = self.db[self.resource].insert_one(data).inserted_id
        except errors.DuplicateKeyError:
            return {"status": 400, "detail": self.resource + " already exists"}, 400
        return self.db.user.find_one({"_id": obj_id}, self.projection), 200

    def update(self, obj_id, data):
        obj_id = convertToObjectId(obj_id)
        if not obj_id:
            return {"status": 400, "detail": "Invalid " + self.resource + " id"}, 400
        result = self.db[self.resource].update_one({"_id": obj_id}, {'$set': data})
        if not result.matched_count:
            return {"status": 400, "detail": self.resource + " not found"}, 400
        return self.db.user.find_one({"_id": obj_id}, self.projection), 200

    def remove(self, obj_id):
        obj_id = convertToObjectId(obj_id)
        if not obj_id:
            return {"status": 400, "detail": "Invalid " + self.resource + " id"}, 400
        result = self.db[self.resource].delete_one({"_id": obj_id})
        print(result.raw_result)
        if not result.deleted_count:
            return {"status": 400, "detail": self.resource + " not found"}, 400
        return {"id": obj_id, "detail": self.resource + " successfully removed"}, 200

    def retrieve(self, obj_id):
        obj_id = convertToObjectId(obj_id)
        if not obj_id:
            return {"status": 400, "detail": "Invalid " + self.resource + " id"}, 400
        result = self.db[self.resource].find_one({"_id": obj_id}, self.projection)
        if not result:
            return {"status": 400, "detail": self.resource + " not found"}, 400
        return result, 200

    # To-DO add sorting, filtering
    def retrieveAll(self):
        result = list(self.db[self.resource].find(None, self.projection))
        if not result:
            return {"status": 400, "detail": self.resource + " not found"}, 400
        return result, 200

