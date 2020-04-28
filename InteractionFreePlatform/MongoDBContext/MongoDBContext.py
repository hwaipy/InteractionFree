# from pymongo import MongoClient
from motor.motor_tornado import MotorClient
from MongoDBContext.UserManager import UserManager
from MongoDBContext.IFLocal import IFLocal


class IFConfigContext:
    def __init__(self, db):
        self.db = db
        self.userManager = UserManager(db.Users)

    def getLoginSalt(self, id):
        return self.userManager.getSalt(id)

    def login(self, username, password):
        print('login')


class IFDataContext:
    def __init__(self, db):
        self.db = db
        self.IFLocal = IFLocal(db.IFLocal)


class MongoDBContext:
    def __init__(self, isTest=False):
        self.__IFConfigClient = MotorClient("mongodb://{}:{}@{}:{}/{}".format(
            'IFConfigAdmin', 'jifwa8e923lfwa909iowafe', '172.16.60.199', 27019, 'IFConfig'))
        self.__IFConfig = self.__IFConfigClient.get_database('IFConfig')
        if isTest:
            self.__IFConfig = self.__IFConfigClient.get_database('IFConfigTest')
        self.__IFDataClient = MotorClient("mongodb://{}:{}@{}:{}/{}".format(
            'IFDataAdmin', 'fwaejio8798fwjoiewf', '172.16.60.199', 27019, 'IFData'))
        self.__IFData = self.__IFDataClient.get_database('IFData')
        if isTest:
            self.__IFData = self.__IFDataClient.get_database('IFDataTest')
        self.IFConfig = IFConfigContext(self.__IFConfig)
        self.IFData = IFDataContext(self.__IFData)

        # self.__IFConfig.get_collection('C').update_one({}).upserted_id


MongoDBContextTest = MongoDBContext(True)
MongoDBContext = MongoDBContext()
