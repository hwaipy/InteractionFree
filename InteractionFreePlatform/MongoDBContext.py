from pymongo import MongoClient
from IFCore import IFException
import random
import string
from hashlib import md5


class IFConfigContext:
    def __init__(self, db):
        self.db = db
        self.userManager = IFConfigContext.UserManager(db.Users)

    def getLoginSalt(self, id):
        return self.userManager.getSalt(id)

    def login(self, username, password):
        print('login')

    class UserManager:
        UserID = 'UserID'
        Name = 'Name'
        SaltA = 'SaltA'
        SaltB = 'SaltB'
        HashedPassword = 'HashedPassword'
        Avatar = 'Avatar'
        Privilege = 'Privilege'

        def __init__(self, collection):
            self.collection = collection
            self.rnd = random.Random()
            self.validCharacters = string.ascii_letters + string.digits + '_-+~'

        def hasUser(self, id):
            return self.collection.find_one({IFConfigContext.UserManager.UserID: id}) != None

        def createUser(self, id, name=None, password=None, privilege=[], avatar=None):
            if self.hasUser(id):
                raise IFException('User [{}] exists.'.format(id))
            if name == None:
                name = id.split('@')[0]
            if password == None:
                password = self.__randomPassword()
            saltA = self.__randomSalt()
            saltB = self.__randomSalt()
            hashedPassword = self.__hashPassword(password, [saltA, saltB])
            privilege = list(set(privilege))
            self.collection.insert_one({
                IFConfigContext.UserManager.UserID: id,
                IFConfigContext.UserManager.Name: name,
                IFConfigContext.UserManager.SaltA: saltA,
                IFConfigContext.UserManager.SaltB: saltB,
                IFConfigContext.UserManager.HashedPassword: hashedPassword,
                IFConfigContext.UserManager.Privilege: privilege,
                IFConfigContext.UserManager.Avatar: avatar,
            })

        def deleteUser(self, id):
            self.collection.delete_one({IFConfigContext.UserManager.UserID: id})

        def getUserInfo(self, id):
            info = self.collection.find_one({
                IFConfigContext.UserManager.UserID: id
            }, {
                IFConfigContext.UserManager.Name: 1,
                IFConfigContext.UserManager.Avatar: 1,
                IFConfigContext.UserManager.Privilege: 1,
                '_id': 0
            })
            if info == None:
                raise IFException('User [{}] not exist.'.format(id))
            return info

        def getUserName(self, id):
            return self.getUserInfo(id)[IFConfigContext.UserManager.Name]

        def getAvatar(self, id):
            return self.getUserInfo(id)[IFConfigContext.UserManager.Avatar]

        def getPrivilege(self, id):
            return self.getUserInfo(id)[IFConfigContext.UserManager.Privilege]

        def updateUserName(self, id, userName):
            r = self.collection.update_one({
                IFConfigContext.UserManager.UserID: id
            }, {'$set': {
                IFConfigContext.UserManager.Name: userName
            }})
            if r.modified_count == 0:
                raise IFException('Failed to update UserName.')

        def updateAvatar(self, id, avatar):
            r = self.collection.update_one({
                IFConfigContext.UserManager.UserID: id
            }, {'$set': {
                IFConfigContext.UserManager.Avatar: avatar
            }})
            if r.modified_count == 0:
                raise IFException('Failed to update Avatar.')

        def verifyPassword(self, id, pwd, salted=False):
            info = self.__getHashedPassword(id)
            saltA = info[IFConfigContext.UserManager.SaltA]
            saltB = info[IFConfigContext.UserManager.SaltB]
            hashedPassword = info[IFConfigContext.UserManager.HashedPassword]
            if salted:
                tobeVerified = self.__hashPassword(pwd, [saltB])
            else:
                tobeVerified = self.__hashPassword(pwd, [saltA, saltB])
            return tobeVerified == hashedPassword

        def updatePassword(self, id, pwd):
            saltA = self.__randomSalt()
            saltB = self.__randomSalt()
            hashedPassword = self.__hashPassword(pwd, [saltA, saltB])
            r = self.collection.update_one({
                IFConfigContext.UserManager.UserID: id
            }, {'$set': {
                IFConfigContext.UserManager.SaltA: saltA,
                IFConfigContext.UserManager.SaltB: saltB,
                IFConfigContext.UserManager.HashedPassword: hashedPassword,
            }})
            if r.modified_count == 0:
                raise IFException('Failed to update Password.')

        def getSalt(self, id):
            return self.__getHashedPassword(id)[IFConfigContext.UserManager.SaltA]

        def resetPassword(self, id):
            newPwd = self.__randomPassword()
            self.updatePassword(id, newPwd)
            return newPwd

        def updatePrivilege(self, id, privilege):
            privilege = list(set(privilege))
            r = self.collection.update_one({
                IFConfigContext.UserManager.UserID: id
            }, {'$set': {
                IFConfigContext.UserManager.Privilege: privilege
            }})
            if r.modified_count == 0:
                raise IFException('Failed to clear Privilege.')

        def clearPrivilege(self, id):
            self.updatePrivilege(id, [])

        def addPrivilege(self, id, onePrivilege):
            oldP = list(self.getPrivilege(id))
            newP = list(oldP) + [onePrivilege]
            self.updatePrivilege(id, newP)

        def removePrivilege(self, id, onePrivilege):
            P = self.getPrivilege(id)
            if P.__contains__(onePrivilege):
                P.remove(onePrivilege)
                self.updatePrivilege(id, P)
            else:
                raise IFException('User [{}] does not has provilege [{}].'.format(id, onePrivilege))

        def __getHashedPassword(self, id):
            info = self.collection.find_one({
                IFConfigContext.UserManager.UserID: id
            }, {
                IFConfigContext.UserManager.SaltA: 1,
                IFConfigContext.UserManager.SaltB: 1,
                IFConfigContext.UserManager.HashedPassword: 1,
                '_id': 0
            })
            if info == None:
                raise IFException('User [{}] not exist.'.format(id))
            return info

        def __hashPassword(self, password, salts):
            for salt in salts:
                password = md5((salt + password).encode('UTF-8')).hexdigest()
            return password

        def __randomPassword(self, length=12):
            return self.__randomString(length)

        def __randomSalt(self, length=1024):
            return self.__randomString(length)

        def __randomString(self, length):
            return ''.join([self.rnd.choice(self.validCharacters) for i in range(length)])


class IFDataContext:
    def __init__(self, db):
        self.db = db


class MongoDBContext:
    def __init__(self, isTest=False):
        self.__client = MongoClient('127.0.0.1', 27017)
        self.__IFConfig = self.__client.get_database('IFConfig')
        self.__IFConfig.authenticate('IFConfigAdmin', 'jifwa8e923lfwa909iowafe')
        if isTest:
            self.__IFConfig = self.__client.get_database('IFConfigTest')
        # self.__IFData = self.__client.get_database('IFData' if not isTest else 'IFDataTest')
        # self.__IFData.authenticate('IFDataAdmin', 'fwaejio8798fwjoiewf')
        self.IFConfig = IFConfigContext(self.__IFConfig)
        # self.IFData = IFDataContext(self.__IFData)

        # self.__IFConfig.get_collection('C').update_one({}).modified_count


MongoDBContextTest = MongoDBContext(True)
MongoDBContext = MongoDBContext()
