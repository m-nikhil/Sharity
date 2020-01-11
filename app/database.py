from pymongo import MongoClient
from flask import g

class Database(object):
        __instance = None

        def __init__(self, app):

                if Database.__instance != None:
                        raise Exception("This class is a singleton!")
                else:
                        Database.__instance = self
                
                self.app = app

        def connect(self):
                #use only once in the main thread
                conn = MongoClient(self.app.config['DATABASE_HOST'], maxPoolSize=None, waitQueueTimeoutMS=1000)
                self.conn = conn[self.app.config['DATABASE']]
                return conn

        @staticmethod 
        def getInstance():
                if Database.__instance == None:
                        Database()
                return Database.__instance

        def getConnection(self):
                return self.conn
