# 
# overwritten implementaion of MethodView of Flask
# Added capability to docorate middleware to individual route
# Added database getconnection method



from flask import request
from flask import views
from app.database import Database
from pymongo import errors
from bson import ObjectId
import json

# views.MethodViewType.__init__ = MethodViewType.__init__


def convertToObjectId(obj_id):
    try:
        obj_id = ObjectId(obj_id)
        return obj_id
    except:
        return None


class SuperView(views.MethodView):

    # subresource mask is not efficient
    # now, application fetch all the parent fields from database and
    # exludes in the application. Unnessary data flows from database to 
    # application. Fix using mongo aggregations
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if((not type(cls.subresource) is property) and (not type(cls.subresource) is type(None))):
            subresource_mask = {'_id' : False}
            if not cls.mask:
                subresource_mask[cls.subresource] = True
            else:
                for field in cls.mask:
                    subresource_mask[cls.subresource+'.'+field] = False
            cls.mask = subresource_mask
            
        
    _decorators = {}

    # abstract member; needs to be overridden
    # datatype - string
    @property
    def resource(self):
        raise NotImplementedError

    @property
    def subresource(self):
        return  None

    # subresource of non array type don't have mongo _id
    @property
    def is_subresource_array(self):
        return False

    # abstract member; needs to be overridden
    # datatype - dict
    # Projection must have only 'Flase' values
    @property
    def mask(self):
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
        view = super(views.MethodView, self).dispatch_request
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
    # TO-Do check if _id is altered
    
    # STANDARDS followed:
    # All the resources and sub resources are operated as a whole, exepect update.
    # insert - resource/sub are inserted as a whole (all fields), not partially.
    # retrive - resource/sub are retrived as a whole (all fields), not partially.
    # delete - resource/sub are deleted as a whole (all fields), not partially.
    # update - partial updates are available for resource/sub.
    # These standards are enough to support any type of requests as of now.
    # -------------  resource APIs ------------------------
    #-------------------------------------------------------

    def insert(self, data):
        try:
            obj_id = self.db[self.resource].insert_one(data).inserted_id
        except errors.DuplicateKeyError:
            return {"status": 400, "detail": self.resource + " already exists"}, 400
        return self.db[self.resource].find_one({"_id": obj_id}, self.mask), 200

    # if the element doesn't exist throw error. Now it inserts new field
    def update(self, obj_id, data):
        obj_id = convertToObjectId(obj_id)
        if not obj_id:
            return {"status": 400, "detail": "Invalid " + self.resource + " id"}, 400
        result = self.db[self.resource].update_one({"_id": obj_id}, {'$set': data})
        if not result.matched_count:
            return {"status": 400, "detail": self.resource + " not found"}, 400
        return self.db[self.resource].find_one({"_id": obj_id}, self.mask), 200

    def remove(self, obj_id):
        obj_id = convertToObjectId(obj_id)
        if not obj_id:
            return {"status": 400, "detail": "Invalid " + self.resource + " id"}, 400
        result = self.db[self.resource].delete_one({"_id": obj_id})
        if not result.deleted_count:
            return {"status": 400, "detail": self.resource + " not found"}, 400
        return {"id": obj_id, "detail": self.resource  + " successfully removed"}, 200

    def retrieve(self, obj_id):
        obj_id = convertToObjectId(obj_id)
        if not obj_id:
            return {"status": 400, "detail": "Invalid " + self.resource + " id"}, 400
        result = self.db[self.resource].find_one({"_id": obj_id}, self.mask)
        if not result:
            return {"status": 400, "detail": self.resource + " not found"}, 400
        return result, 200

    # To-DO add sorting, filtering
    def retrieveAll(self, search=None):
        result = list(self.db[self.resource].find(search, self.mask))
        if not result:
            return {"status": 400, "detail": self.resource + " list is empty"}, 400
        return result, 200

    # -------------  subresource APIs ----------------------
    #-------------------------------------------------------

    # move 'data = {self.subresource : data}' to dot notation format to support sub-subresources
    # insert or update does the same logic. Hence, use update for both apis.

    def subresource_update_data_helper(self,data):
        subresource_data = {}
        for key,value in data.items():
            subresource_data[self.subresource+"."+key] = value
        return subresource_data

    def update_subdocument(self, obj_id, data):
        obj_id = convertToObjectId(obj_id)
        if not obj_id:
            return {"status": 400, "detail": "Invalid " + self.resource + " id"}, 400
        data = self.subresource_update_data_helper(data)
        result = self.db[self.resource].update_one({"_id": obj_id}, {'$set': data})
        if not result.matched_count:
            return {"status": 400, "detail": self.resource + " not found"}, 400
        return self.db[self.resource].find_one({"_id": obj_id}, self.mask)[self.subresource], 200

    def remove_subdocument(self, obj_id):
        obj_id = convertToObjectId(obj_id)
        if not obj_id:
            return {"status": 400, "detail": "Invalid " + self.resource + " id"}, 400
        result = self.db[self.resource].update_one({"_id": obj_id}, {'$unset': { self.subresource : ""}})
        if not result.matched_count:
            return {"status": 400, "detail": self.subresource + " not found"}, 400 
        return {"id": obj_id, "detail": self.subresource  + " successfully removed"}, 200

    def retrieve_subdocument(self, obj_id):
        obj_id = convertToObjectId(obj_id)
        if not obj_id:
            return {"status": 400, "detail": "Invalid " + self.resource + " id"}, 400
        result = self.db[self.resource].find_one({"_id": obj_id}, self.mask)
        if not result:
            return {"status": 400, "detail": self.subresource + " not found"}, 400
        result = result.get(self.subresource,None)
        if not result:
            return {"status": 400, "detail": self.subresource + " not found"}, 400
        return result, 200

    # -------------  subresource Array APIs ----------------------
    #-------------------------------------------------------------

    def subresource_array_update_data_helper(self,data):
        subresource_data = {}
        for key,value in data.items():
            subresource_data[self.subresource+".$."+key] = value
        return subresource_data

    def insert_subdocument_array(self, obj_id, data):
        obj_id = convertToObjectId(obj_id)
        if not obj_id:
            return {"status": 400, "detail": "Invalid " + self.resource + " id"}, 400
        sub_obj_id = ObjectId()
        data["_id"] = sub_obj_id
        data = {
            self.subresource : data
        }
        result = self.db[self.resource].update_one({"_id": obj_id}, {'$push': data})
        if not result.matched_count:
            return {"status": 400, "detail": self.subresource + " not found"}, 400
        return self.db[self.resource].find_one({"_id": obj_id}, self.mask)[self.subresource][0], 200
        
    # if the element doesn't exist throw error. Now it inserts new field
    def update_subdocument_array(self, obj_id, data, sub_obj_id):
        obj_id = convertToObjectId(obj_id)
        if not obj_id:
            return {"status": 400, "detail": "Invalid " + self.resource + " id"}, 400
        sub_obj_id = convertToObjectId(sub_obj_id)
        if not sub_obj_id:
            return {"status": 400, "detail": "Invalid " + self.subresource + " id"}, 400
        data = self.subresource_array_update_data_helper(data)
        result = self.db[self.resource].update_one({ "requirements._id" :  sub_obj_id}, {'$set': data })
        if not result.matched_count:
            return {"status": 400, "detail": self.subresource + " not found"}, 400
        result = self.db[self.resource].find_one({ "requirements._id" :  sub_obj_id}, self.mask)
        result = result.get(self.subresource,None)[0]
        if not result:
            return {"status": 400, "detail": self.subresource + " not found"}, 400
        return result, 200

    # unset on array makes the element null, insead of removing from the array
    def remove_subdocument_array(self, obj_id, sub_obj_id):
        obj_id = convertToObjectId(obj_id)
        if not obj_id:
            return {"status": 400, "detail": "Invalid " + self.resource + " id"}, 400
        sub_obj_id = convertToObjectId(sub_obj_id)
        if not sub_obj_id:
            return {"status": 400, "detail": "Invalid " + self.subresource + " id"}, 400
        result = self.db[self.resource].update_one({ "_id": obj_id}, {'$pull': {self.subresource : {"_id" : sub_obj_id }}})
        # since we find with obj_id, it always matches and result.matchcount will be 1
        result = self.db[self.resource].find_one({ "requirements._id" :  sub_obj_id }, {self.subresource + ".$" : 1})
        if result:
            return {"status": 400, "detail": self.subresource + " not found"}, 400
        return {"id": sub_obj_id, "detail": self.subresource  + " successfully removed"}, 200

    def retrieve_subdocument_array(self, obj_id, sub_obj_id):
        obj_id = convertToObjectId(obj_id)
        if not obj_id:
            return {"status": 400, "detail": "Invalid " + self.resource + " id"}, 400
        sub_obj_id = convertToObjectId(sub_obj_id)
        if not sub_obj_id:
            return {"status": 400, "detail": "Invalid " + self.subresource + " id"}, 400
        result = self.db[self.resource].find_one({ "requirements._id" :  sub_obj_id }, {self.subresource + ".$" : 1})
        # Using non-Index field to query. Use aggregate to improve performace.
        # query with parent index and then with sub index
        if not result:
            return {"status": 400, "detail": self.subresource + " not found"}, 400
        result = result.get(self.subresource,None)[0]
        if not result:
            return {"status": 400, "detail": self.subresource + " not found"}, 400
        return result, 200

    # TO-DO filter, sort
    def retrieveAll_subdocument_array(self, obj_id):
        obj_id = convertToObjectId(obj_id)
        if not obj_id:
            return {"status": 400, "detail": "Invalid " + self.resource + " id"}, 400
        result = self.db[self.resource].find_one({"_id": obj_id}, self.mask)
        if not result:
            return {"status": 400, "detail": self.resource + " list is empty"}, 400
        result = result.get(self.subresource,None)
        if not result:
            return {"status": 400, "detail": self.subresource + " not found"}, 400
        return result, 200