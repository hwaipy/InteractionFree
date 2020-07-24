from IFCore import IFException
import random
import string
from hashlib import md5


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

    async def hasUser(self, id):
        return await self.collection.find_one({UserManager.UserID: id}) != None

    async def createUser(self, id, name=None, password=None, privilege=[], avatar=None):
        if await self.hasUser(id):
            raise IFException('User [{}] exists.'.format(id))
        if name == None:
            name = id.split('@')[0]
        if password == None:
            password = self.__randomPassword()
        saltA = self.__randomSalt()
        saltB = self.__randomSalt()
        hashedPassword = self.__hashPassword(password, [saltA, saltB])
        privilege = list(set(privilege))
        await self.collection.insert_one({
            UserManager.UserID: id,
            UserManager.Name: name,
            UserManager.SaltA: saltA,
            UserManager.SaltB: saltB,
            UserManager.HashedPassword: hashedPassword,
            UserManager.Privilege: privilege,
            UserManager.Avatar: avatar,
        })

    async def deleteUser(self, id):
        await self.collection.delete_one({UserManager.UserID: id})

    async def getUserInfo(self, id):
        info = await self.collection.find_one({
            UserManager.UserID: id
        }, {
            UserManager.Name: 1,
            UserManager.Avatar: 1,
            UserManager.Privilege: 1,
            '_id': 0
        })
        if info == None:
            raise IFException('User [{}] not exist.'.format(id))
        return info

    async def getUserName(self, id):
        return (await self.getUserInfo(id))[UserManager.Name]

    async def getAvatar(self, id):
        return (await self.getUserInfo(id))[UserManager.Avatar]

    async def getPrivilege(self, id):
        return (await self.getUserInfo(id))[UserManager.Privilege]

    async def updateUserName(self, id, userName):
        r = await self.collection.update_one({
            UserManager.UserID: id
        }, {'$set': {
            UserManager.Name: userName
        }})
        if r.modified_count == 0:
            raise IFException('Failed to update UserName.')

    async def updateAvatar(self, id, avatar):
        r = await self.collection.update_one({
            UserManager.UserID: id
        }, {'$set': {
            UserManager.Avatar: avatar
        }})
        if r.modified_count == 0:
            raise IFException('Failed to update Avatar.')

    async def verifyPassword(self, id, pwd, salted=False):
        info = await self.__getHashedPassword(id)
        saltA = info[UserManager.SaltA]
        saltB = info[UserManager.SaltB]
        hashedPassword = info[UserManager.HashedPassword]
        if salted:
            tobeVerified = self.__hashPassword(pwd, [saltB])
        else:
            tobeVerified = self.__hashPassword(pwd, [saltA, saltB])
        return tobeVerified == hashedPassword

    async def updatePassword(self, id, pwd):
        saltA = self.__randomSalt()
        saltB = self.__randomSalt()
        hashedPassword = self.__hashPassword(pwd, [saltA, saltB])
        r = await self.collection.update_one({
            UserManager.UserID: id
        }, {'$set': {
            UserManager.SaltA: saltA,
            UserManager.SaltB: saltB,
            UserManager.HashedPassword: hashedPassword,
        }})
        if r.modified_count == 0:
            raise IFException('Failed to update Password.')

    async def getSalt(self, id):
        return (await self.__getHashedPassword(id))[UserManager.SaltA]

    async def resetPassword(self, id):
        newPwd = self.__randomPassword()
        await self.updatePassword(id, newPwd)
        return newPwd

    async def updatePrivilege(self, id, privilege):
        privilege = list(set(privilege))
        r = await self.collection.update_one({
            UserManager.UserID: id
        }, {'$set': {
            UserManager.Privilege: privilege
        }})
        if r.modified_count == 0:
            raise IFException('Failed to clear Privilege.')

    async def clearPrivilege(self, id):
        await self.updatePrivilege(id, [])

    async def addPrivilege(self, id, onePrivilege):
        oldP = list(await self.getPrivilege(id))
        newP = list(oldP) + [onePrivilege]
        await self.updatePrivilege(id, newP)

    async def removePrivilege(self, id, onePrivilege):
        P = await self.getPrivilege(id)
        if P.__contains__(onePrivilege):
            P.remove(onePrivilege)
            await self.updatePrivilege(id, P)
        else:
            raise IFException('User [{}] does not has provilege [{}].'.format(id, onePrivilege))

    async def __getHashedPassword(self, id):
        info = await self.collection.find_one({
            UserManager.UserID: id
        }, {
            UserManager.SaltA: 1,
            UserManager.SaltB: 1,
            UserManager.HashedPassword: 1,
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
