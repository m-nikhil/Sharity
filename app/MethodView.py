# 
# overwritten implementaion of MethodView of Flask
# Added capability to docorate middleware to individual route
# Added database getconnection method



from flask import request, send_file, views
from app.database import Database
from pymongo import errors
from bson import ObjectId
from app.ConnectionBusinessException import BussinessException
import json
from werkzeug.utils import secure_filename
import io

# move to util
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
            if cls.mask == 'ALL': #to mask all the fields
                cls.mask = {'_id' : True}
            else:
                mask = {}
                for field in cls.mask:
                        mask[field] = False
                cls.mask = mask

    # Mongo Collection used for static files
    # primary key is _id
    # unique key is unique field and partial key. All rows don't have unique key.
    __static_collection = "static"
            
        
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
    # TO-DO unset data in update. Make it generic with body
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
        result = self.db[resource].delete_one({"_id": obj_id})
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

    def update_subdocument(self, obj_id, data, unset_data = None, resource = None, subresource = None, projection = None):
        resource = resource if resource else self.resource
        subresource = subresource if subresource else self.subresource
        mask = self.projection_helper(projection,subresource) if projection else self.mask
        obj_id = convertToObjectId(obj_id)
        if not obj_id:
            raise BussinessException("error",400,"Invalid " + resource + " id")
        # optimse this using only data and removing unset_data
        update = {}
        if data:
            update['$set'] = self.subresource_update_data_helper(data, subresource)
        if unset_data:
            update['$unset'] = self.subresource_update_data_helper(unset_data, subresource)
        result = self.db[resource].update_one({"_id": obj_id}, update)
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
        sub_obj_id = data["_id"] = objectId if objectId else ObjectId() # sub_obj_id
        data = {
            subresource : data
        }
        result = self.db[resource].update_one({"_id": obj_id}, {'$push': data})
        if not result.matched_count:
            raise BussinessException("error",400,subresource + " not found")
        return self.db[resource].find_one({ subresource+"._id" :  sub_obj_id }, {subresource + ".$" : 1}).get(subresource)[0]

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
        result = self.db[resource].find_one({ subresource+"._id" :  sub_obj_id }, {subresource + ".$" : 1})
        if not result:
            raise BussinessException("error",400,resource + subresource + " not found")
        result = self.db[resource].update_one({ "_id": obj_id}, {'$pull': {subresource : {"_id" : sub_obj_id }}})
        # since we find with obj_id, it always matches and result.matchcount will be 1
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

    # -------------  Array APIs ----------------------
    #-------------------------------------------------------

    # Different from subresource
    # primitive objs like int, string...
    # Don't have _id
    # to delete need the exact obj to be the operation
    # no update operation
    # no retrive one element. Only retrive all the elements.
    # no mask as primitive data
    # support only 1st depth
    # maintain at max 50 elements; due to performance. Value is just a guess.
    # return value will be updated array for each operation, as each are considered as 
        # updation to existing entity/field.


    def insert_array(self, obj_id, data, resource = None, subresource = None):
        resource = resource if resource else self.resource
        subresource = subresource if subresource else self.subresource
        obj_id = convertToObjectId(obj_id)
        if not obj_id:
            raise BussinessException("error",400,"Invalid " + resource + " id")
        data = {
            subresource : data
        }
        result = self.db[resource].update_one({"_id": obj_id}, {'$push': data})
        if not result.matched_count:
            raise BussinessException("error",400,subresource + " not found")
        return self.db[resource].find_one({"_id": obj_id})[subresource], 200

    def retrieve_array(self, obj_id, resource = None, subresource = None):
        resource = resource if resource else self.resource
        subresource = subresource if subresource else self.subresource
        obj_id = convertToObjectId(obj_id)
        if not obj_id:
            raise BussinessException("error",400,"Invalid " + resource + " id")
        result = self.db[resource].find_one({"_id": obj_id})
        if not result:
            raise BussinessException("error",400,resource + " list is empty")
        result = result.get(subresource,None)
        if not result:
            raise BussinessException("error",400,resource + " not found")
        return result, 200

    # if the element to be removed is not already present, nothing will happen.
    def remove_array(self, obj_id, value, resource = None, subresource = None):
        resource = resource if resource else self.resource
        subresource = subresource if subresource else self.subresource
        obj_id = convertToObjectId(obj_id)
        if not obj_id:
            raise BussinessException("error",400,"Invalid " + resource + " id")
        print(value)
        self.db[resource].update_one({ "_id": obj_id}, {'$pull': {subresource : { '$in': [value] }}})
        return self.db[resource].find_one({"_id": obj_id})[subresource], 200    

    #---------------------------- Static -------------------------------------
    # add gzip protocol

    ALLOWED_EXTENSIONS = {'doc', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

    def allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS

    # Structure of static collection
    # binary - the file itself
    # meta - meta data about file - like date of upload, user id
    # owner - owner of document; used for authz
    # owerType - to be added
    # unique - used to identify uniqly which can be build from known fields; used for deleting old file

    # Structure of static collection return url
    # doc_prefix - know which type of doc used for authz
    # id - unique identifier of the file

    # if a resouce is an array of files dont use unique field
    # Use unique only when you have an object (key: unique field, value: image)
    # Setting unique param enables updation of the file with the same unique value, instead of
    # insection.

    # max param is set to denote the maximum number of files that can be uploaded in the case of 
    # unlimited / non-named files. It is not considered in the case where unique is set
    def uploadStatic(self,file,meta,owner,doc_prefix,unique,max):

        if file is None:
            raise BussinessException("error",400, "No file attached.")

        if owner is None:
            raise BussinessException("error",500,"Authz error; Contact Admin")

        if doc_prefix is None:
            raise BussinessException("error",500,"Authz error; Contact Admin")

        resource = self.__static_collection
        data = {}

        if file.filename == '':
            raise BussinessException("error",400, "No file selected")
        if not self.allowed_file(file.filename):
            raise BussinessException("error",400, "File format not allowed")

        # filenames can be dangerous, so use secure_filename
        meta['filename'] = secure_filename(file.filename)
        data['binary'] = file.read()
        data['meta'] = meta
        data['owner'] = owner

        if unique:     
            data['unique'] = unique

            try:
                # replace_one doc - https://api.mongodb.com/python/current/api/pymongo/collection.html#pymongo.collection.Collection.replace_one
                result = self.db[resource].replace_one({"unique": unique},data, True)
                if result.matched_count > 1:
                    pass # TODO log this part; dont throw error.
            except:
                raise BussinessException("error",500, "Upload document failed")

            obj_id = self.db[resource].find_one({"unique": unique}, {"_id": True})["_id"]
        
        else: 
             obj_id = self.db[resource].insert_one(data,{"_id": True}).inserted_id

        return "/"+doc_prefix+"/"+str(obj_id)

    # Dont expose it as rest api. Only internal api should call to maintain sync with the resouce and the static image.
    # used only by Admin as Rest api and incase of urgent.
    def deleteStatic(self,type,id):
        resource = self.__static_collection
        obj_id = convertToObjectId(id)
        if not obj_id:
            raise BussinessException("error",400, "Invalid file url")
        result = self.db[resource].delete_one({"_id": obj_id})
        if not result.deleted_count:
            raise BussinessException("error",400, "File not found")
        return {"url": type+"/"+id, "detail": "File successfully removed"}, 200

    def deleteStaticUsingUnique(self,unique):
        resource = self.__static_collection
        if not unique:
            raise BussinessException("error",400, "Invalid file name")
        result = self.db[resource].delete_one({"unique": unique})
        if not result.deleted_count:
            raise BussinessException("error",400, "File not found")
        return {"file": unique, "detail": "File successfully removed"}, 200

    # url format host+authz_type+fileId
    # authz_type to perform authz before database read
    # incase of authz of curr, database meta is read
    def retriveStatic(self,type,id):
        resource = self.__static_collection
        obj_id = convertToObjectId(id)
        if not obj_id:
            raise BussinessException("error",400, "Invalid file url")
        result = self.db[resource].find_one({"_id": obj_id},{"_id": False,"binary": True})
        if not result:
            raise BussinessException("error",400, "File not found")
        response =  send_file(io.BytesIO(result['binary']), attachment_filename="download.pdf", as_attachment=True)
        response.headers["Content-Type"] = 'application/pdf'
        response.direct_passthrough = False
        return response, 200
        
        
