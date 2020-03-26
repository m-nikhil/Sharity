import yaml
from app.ConnectionBusinessException import BussinessException
from app.database import Database
from bson import ObjectId
import sys
import re
import json

# move to util
def convertToObjectId(obj_id):
    try:
        obj_id = ObjectId(obj_id)
        return obj_id
    except:
        return None

class Authz():
        __instance = None
        __rules = None
        __static_rules = None
        __roles = []
        __roles_global = []

        # Similar variable exists in MethodView
        __static_collection = "static"

        def __init__(self):

                if Authz.__instance != None:
                        raise Exception("This class is a singleton!")
                else:
                        Authz.__instance = self
                
        @staticmethod 
        def getInstance():
                if Authz.__instance == None:
                        raise Exception("This class not initialized!")
                return Authz.__instance

        def initializeAuthz(self,file):
                with open(file, 'r') as stream:
                        try:
                                parsed = yaml.safe_load(stream)
                                self.__rules = parsed['rules']
                                self.__static_rules = parsed['static_rules']
                                self.processRoles(parsed['roles'])
                        except yaml.YAMLError as exc:
                                print(exc)
                                sys.exit("Error: Couldn't read authz file.")

                # get db instance
                instance = Database.getInstance()
                self.db = instance.getConnection()

        def processRoles(self,roles):
                for role in roles:
                        if role.find(":") == -1:
                                self.__roles.append(role)
                        else:
                                # check for global attr
                                values = role.split(":")
                                if values[1] == "global":
                                        self.__roles_global.append(values[0])
                                else:
                                        sys.exit("Error: Couldn't parse roles of authz file.")

        # Add logging...

        # Point to consider:
        # 1. if a rule for an url, method doesn't exist. It will raise exception
        # 2. 'all' -> a default rule to allow all loggedin users
        def checkAuthz(self,request,token):
                
                #check if the url is static 
                if str(request.url_rule) == "/static/<type>/<id>":
                        return self.checkStaticAuthz(request,token)

                if self.__rules == None:
                        raise BussinessException("error",500,"No rules defined; Contact Admin")

                subject = json.loads(token['sub'])
                role = subject['role']
                id = subject['id']
                if role in self.__roles_global:
                        return True
                rule = self.__rules.get(str(request.url_rule),None)
                if not rule:
                        raise BussinessException("error",500,"Authz error; Contact Admin")
                authz_list = rule.get(request.method,None)
                if authz_list == None:
                        raise BussinessException("error",500,"Authz error; Contact Admin")
                for authz in authz_list:
                        if authz == "all":
                                return True
                        elif authz.find(":") == -1:
                                if role == authz:
                                        return True
                        else:
                                # check for curr attr
                                values = authz.split(":")
                                if values[1] == "curr":
                                        # get first path param name
                                        url_rule = str(request.url_rule)
                                        start = url_rule.find("<")
                                        end = url_rule.find(">")
                                        if start == -1 and end == -1:
                                                raise BussinessException("error",500,"Authz error; Contact Admin")
                                        first_param = url_rule[start+1:end]
                                        first_param_value = request.view_args.get(first_param,None)
                                        if id == first_param_value and values[0] == role:
                                                return True
                                else:
                                        # check at application start and do sys.exit
                                        raise BussinessException("error",500,"Authz error; Contact Admin")
                return False


        # Point to consider:
        # 2. if url doesn't exist or its method doesn't exist, authz will return true
        def checkStaticAuthz(self, request, token):

                if self.__static_rules == None:
                        raise BussinessException("error",500,"No rules defined; Contact Admin")

                # the static rest api must be static/{type}/{id}
                auth_type = request.view_args.get("type",None)
                obj_id = request.view_args.get("id",None)
              
                if auth_type is None or obj_id is None:
                        raise BussinessException("error",500,"Authz error; Contact Admin")

                subject = json.loads(token['sub'])
                role = subject['role']
                user_id = subject['id']
                if role in self.__roles_global:
                        return True

                required_type = self.__static_rules.get(auth_type, None)
                if not required_type:
                        return True  # if url don't exist, return true
                authz_list = required_type.get(request.method,None)
                if authz_list == None:
                        return True  # if method don't exist, return true

                for authz in authz_list:
                        if authz == "all":
                                return True
                        elif authz.find(":") == -1:
                                if role == authz:
                                        return True
                        else:
                                # check for curr attr
                                values = authz.split(":")
                                if values[1] == "curr":
                                        obj_id = convertToObjectId(obj_id)
                                        if not obj_id:
                                                raise BussinessException("error",400,"Invalid File id")
                                        result = self.db[self.__static_collection].find_one({"_id": obj_id},{"_id": False, "owner": True})
                                        if not result:
                                                raise BussinessException("error",400, "File not found") 
                                        if user_id == result["owner"] and values[0] == role:
                                                return True
                                else:
                                        # check at application start and do sys.exit
                                        raise BussinessException("error",500,"Authz error; Contact Admin")
                return False

