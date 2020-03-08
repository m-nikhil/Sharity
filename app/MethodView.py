# 
# overwritten implementaion of MethodView of Flask
# Added capability to docorate middleware to individual route
# Added database getconnection method



from flask import request
from flask import views
from app.database import Database
from pymongo import errors
from bson import ObjectId
from app.ConnectionBusinessException import BussinessException
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
        # if subresource exist
        # print(cls.mask)
        if((not type(cls.subresource) is property) and (not type(cls.subresource) is type(None))):
            subresource_mask = {'_id' : False}
            if not cls.mask:
                subresource_mask[cls.subresource] = True
            else:
                for field in cls.mask:
                    subresource_mask[cls.subresource+'.'+field] = False
            cls.mask = subresource_mask
        elif ((not type(cls.mask) is property) and (not type(cls.mask) is type(None))):
            mask = {}
            for field in cls.mask:
                    mask[field] = False
            cls.mask = mask
            
        
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
        return None

    def __init__(self):
            super().__init__()
            instance = Database.getInstance()
            self.db = instance.getConnection()
            self.transaction = instance.getTansaction
            
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

    def projection_helper(self,projectionList,subresource=None):
        projection = {}
        for field in projectionList:
            if subresource:
                projection[subresource+field] = True
            else: 
                projection[field] = True
        return projection


    # Database operation helper functions
    # TO-DO softdelete, active records
    # TO-Do check if _id is altered
    # TO-DO projection all fields
    # TO-DO projection nothing
    # TO-DO param to avoid the second DB call. No return
    # TO-DO foreign key
    # make a generic builder pattern with customise query
    
    # STANDARDS followed:
    # All the resources and sub resources are operated as a whole, exepect update.
    # insert - resource/sub are inserted as a whole (all fields), not partially.
    # retrive - resource/sub are retrived as a whole (all fields), not partially.
    # delete - resource/sub are deleted as a whole (all fields), not partially.
    # update - partial updates are available for resource/sub.
    # These standards are enough to support any type of requests as of now.
    # -------------  resource APIs ------------------------
    #-------------------------------------------------------

    # objectId can be passed from the application
    def insert(self, data, resource = None, projection = None, objectId = None):
        resource = resource if resource else self.resource
        mask = self.projection_helper(projection) if projection else self.mask
        if objectId:
            data["_id"] = objectId
        try:
            obj_id = self.db[resource].insert_one(data).inserted_id
        except errors.DuplicateKeyError:
            raise BussinessException("error",400,resource + " already exists")
        return self.db[resource].find_one({"_id": obj_id}, mask), 200

    # if the element doesn't exist throw error. Now it inserts new field
    def update(self, obj_id, data, resource = None, projection = None):
        resource = resource if resource else self.resource
        mask = self.projection_helper(projection) if projection else self.mask
        obj_id = convertToObjectId(obj_id)
        if not obj_id:
            raise BussinessException("error",400,"Invalid " + resource + " id")
        result = self.db[resource].update_one({"_id": obj_id}, {'$set': data})
        if not result.matched_count:
            raise BussinessException("error",400,resource + " not found")
        return self.db[resource].find_one({"_id": obj_id}, mask), 200

    def remove(self, obj_id, resource = None, projection = None):
        resource = resource if resource else self.resource
        mask = self.projection_helper(projection) if projection else self.mask
        obj_id = convertToObjectId(obj_id)
        if not obj_id:
            raise BussinessException("error",400, "Invalid " + resource + " id")
        result = self.db[self.resource].delete_one({"_id": obj_id})
        if not result.deleted_count:
            raise BussinessException("error",400,resource + " not found")
        return {"id": obj_id, "detail": resource  + " successfully removed"}, 200

    def retrieve(self, obj_id, resource = None, projection = None):
        resource = resource if resource else self.resource
        mask = self.projection_helper(projection) if projection else self.mask
        obj_id = convertToObjectId(obj_id)
        if not obj_id:
            raise BussinessException("error",400,"Invalid " + resource + " id")
        result = self.db[resource].find_one({"_id": obj_id}, mask)
        if not result:
            raise BussinessException("error",400,resource + " not found")
        return result, 200

    # To-DO add sorting, filtering
    def retrieveAll(self, search=None, resource = None, projection = None):
        resource = resource if resource else self.resource
        mask = self.projection_helper(projection) if projection else self.mask
        result = list(self.db[resource].find(search, mask))
        if not result:
            raise BussinessException("error",400,resource + " list is empty")
        return result, 200

    # -------------  subresource APIs ----------------------
    #-------------------------------------------------------

    # TO-DO Is this really needed? Can it be merged with resource API. 
    # By calling resource API with resouces <resourceName>.<subresouceName>

    # move 'data = {self.subresource : data}' to dot notation format to support sub-subresources
    # insert or update does the same logic. Hence, use update for both apis.

    def subresource_update_data_helper(self, data, subresource):
        subresource = subresource if subresource else self.subresource
        subresource_data = {}
        for key,value in data.items():
            subresource_data[subresource+"."+key] = value
        return subresource_data

    def update_subdocument(self, obj_id, data, resource = None, subresource = None, projection = None):
        resource = resource if resource else self.resource
        subresource = subresource if subresource else self.subresource
        mask = self.projection_helper(projection,subresource) if projection else self.mask
        obj_id = convertToObjectId(obj_id)
        if not obj_id:
            raise BussinessException("error",400,"Invalid " + resource + " id")
        data = self.subresource_update_data_helper(data, subresource)
        result = self.db[resource].update_one({"_id": obj_id}, {'$set': data})
        if not result.matched_count:
            raise BussinessException("error",400,resource + " not found")
        return self.db[resource].find_one({"_id": obj_id}, mask)[subresource], 200

    def remove_subdocument(self, obj_id, resource = None, subresource = None, projection = None):
        resource = resource if resource else self.resource
        subresource = subresource if subresource else self.subresource
        mask = self.projection_helper(projection,subresource) if projection else self.mask
        obj_id = convertToObjectId(obj_id)
        if not obj_id:
            raise BussinessException("error",400, "Invalid " + resource + " id")
        result = self.db[resource].update_one({"_id": obj_id}, {'$unset': { subresource : ""}})
        if not result.matched_count:
            raise BussinessException("error",400,subresource + " not found")
        return {"id": obj_id, "detail": subresource  + " successfully removed"}, 200

    def retrieve_subdocument(self, obj_id, resource = None, subresource = None, projection = None):
        resource = resource if resource else self.resource
        subresource = subresource if subresource else self.subresource
        mask = self.projection_helper(projection,subresource) if projection else self.mask
        obj_id = convertToObjectId(obj_id)
        if not obj_id:
            raise BussinessException("error",400,"Invalid " + resource + " id")
        result = self.db[resource].find_one({"_id": obj_id}, mask)
        if not result:
            raise BussinessException("error",400,subresource + " not found")
        result = result.get(subresource,None)
        if not result:
            raise BussinessException("error",400,subresource + " not found")
        return result, 200

    # -------------  subresource Array APIs ----------------------
    #-------------------------------------------------------------

    # TO-DO mask working. Current implementation is broken and makes no sense.

    def subresource_array_update_data_helper(self,data,subresource):
        subresource_data = {}
        for key,value in data.items():
            subresource_data[subresource+".$."+key] = value
        return subresource_data

    # objectId can be passed from the application
    def insert_subdocument_array(self, obj_id, data, resource = None, subresource = None, projection = None, objectId = None):
        resource = resource if resource else self.resource
        subresource = subresource if subresource else self.subresource
        mask = self.projection_helper(projection) if projection else self.mask
        obj_id = convertToObjectId(obj_id)
        if not obj_id:
            raise BussinessException("error",400,"Invalid " + resource + " id")
        data["_id"] = objectId if objectId else ObjectId() # sub_obj_id
        data = {
            subresource : data
        }
        result = self.db[resource].update_one({"_id": obj_id}, {'$push': data})
        if not result.matched_count:
            raise BussinessException("error",400,subresource + " not found")
        return self.db[resource].find_one({"_id": obj_id}, mask)[subresource][0], 200
        
    # if the element doesn't exist throw error. Now it inserts new field
    def update_subdocument_array(self, obj_id, data, sub_obj_id, resource = None, subresource = None, projection = None):
        resource = resource if resource else self.resource
        subresource = subresource if subresource else self.subresource
        mask = self.projection_helper(projection) if projection else self.mask
        obj_id = convertToObjectId(obj_id)
        if not obj_id:
            raise BussinessException("error",400, "Invalid " + resource + " id")
        sub_obj_id = convertToObjectId(sub_obj_id)
        if not sub_obj_id:
            raise BussinessException("error",400,resource + subresource + " id")
        data = self.subresource_array_update_data_helper(data,subresource)
        result = self.db[resource].update_one({ subresource+"._id" :  sub_obj_id}, {'$set': data })
        if not result.matched_count:
            raise BussinessException("error",400,subresource + " not found")
        result = self.db[resource].find_one({ subresource+"._id" :  sub_obj_id}, mask)
        result = result.get(subresource,None)[0]
        if not result:
            raise BussinessException("error",400,resource + subresource + " not found")
        return result, 200

    # unset on array makes the element null, insead of removing from the array
    def remove_subdocument_array(self, obj_id, sub_obj_id, resource = None, subresource = None, projection = None):
        resource = resource if resource else self.resource
        subresource = subresource if subresource else self.subresource
        mask = self.projection_helper(projection) if projection else self.mask
        obj_id = convertToObjectId(obj_id)
        if not obj_id:
            raise BussinessException("error",400,"Invalid " + resource + " id")
        sub_obj_id = convertToObjectId(sub_obj_id)
        if not sub_obj_id:
            raise BussinessException("error",400,resource + "Invalid " + subresource + " id")
        result = self.db[resource].update_one({ "_id": obj_id}, {'$pull': {subresource : {"_id" : sub_obj_id }}})
        # since we find with obj_id, it always matches and result.matchcount will be 1
        result = self.db[resource].find_one({ subresource+"._id" :  sub_obj_id }, {subresource + ".$" : 1})
        if result:
            raise BussinessException("error",400,resource + subresource + " not found")
        return {"id": sub_obj_id, "detail": subresource  + " successfully removed"}, 200

    def retrieve_subdocument_array(self, obj_id, sub_obj_id, resource = None, subresource = None, projection = None):
        resource = resource if resource else self.resource
        subresource = subresource if subresource else self.subresource
        mask = self.projection_helper(projection) if projection else self.mask
        obj_id = convertToObjectId(obj_id)
        if not obj_id:
            raise BussinessException("error",400,resource + "Invalid " + resource + " id")
        sub_obj_id = convertToObjectId(sub_obj_id)
        if not sub_obj_id:
            raise BussinessException("error",400,resource + "Invalid " + subresource + " id")
        print(subresource)
        result = self.db[resource].find_one({ subresource+"._id" :  sub_obj_id }, {subresource + ".$" : 1})
        # Using non-Index field to query. Use aggregate to improve performace.
        # query with parent index and then with sub index
        if not result:
            raise BussinessException("error",400,resource + " not found")
        result = result.get(subresource,None)[0]
        if not result:
            raise BussinessException("error",400,resource + " not found")
        return result, 200

    # TO-DO filter, sort
    def retrieveAll_subdocument_array(self, obj_id, resource = None, subresource = None, projection = None):
        resource = resource if resource else self.resource
        subresource = subresource if subresource else self.subresource
        mask = self.projection_helper(projection) if projection else self.mask
        obj_id = convertToObjectId(obj_id)
        if not obj_id:
            raise BussinessException("error",400,"Invalid " + resource + " id")
        result = self.db[resource].find_one({"_id": obj_id}, mask)
        if not result:
            raise BussinessException("error",400,resource + " list is empty")
        result = result.get(subresource,None)
        if not result:
            raise BussinessException("error",400,resource + " not found")
        return result, 200