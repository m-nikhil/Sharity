import yaml
from app.ConnectionBusinessException import BussinessException
import sys
import re
import json

class Authz():
        __instance = None
        __rules = None
        __roles = []
        __roles_global = []

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
                                self.processRoles(parsed['roles'])
                        except yaml.YAMLError as exc:
                                print(exc)
                                sys.exit("Error: Couldn't read authz file.")

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


        # Point to consider:
        # 1. if a rule for an url+method does'nt exist. It will raise exception
        # 2. 'all' -> a default rule to allow all loggedin users
        def checkAuthz(self,request,token):
                subject = json.loads(token['sub'])
                role = subject['role']
                id = subject['id']
                if role in self.__roles_global:
                        return True
                rule = self.__rules.get(str(request.url_rule),None)
                if not rule:
                        raise BussinessException("error",500,"Authz error1; Contact Admin")
                authz_list = rule.get(request.method,None)
                if authz_list == None:
                        raise BussinessException("error",500,"Authz error2; Contact Admin")
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
                                                raise BussinessException("error",500,"Authz error3; Contact Admin")
                                        first_param = url_rule[start+1:end]
                                        first_param_value = request.view_args.get(first_param,None)
                                        if id == first_param_value and values[0] == role:
                                                return True
                                else:
                                        # check at application start and do sys.exit
                                        raise BussinessException("error",500,"Authz error4; Contact Admin")
                return False

                
                
                

                

                
