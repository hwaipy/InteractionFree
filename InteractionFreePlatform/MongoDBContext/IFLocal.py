from IFCore import IFException

class IFLocal:
    LauncherName = 'LauncherName'
    Brief = 'Brief'
    Description = 'Description'
    Commands = 'Commands'

    def __init__(self, collection):
        self.collection = collection

    async def hasLauncher(self, launcherName):
        return await self.collection.find_one({IFLocal.LauncherName: launcherName}) != None

    async def createLauncher(self, launcherName, brief=None, description=None):
        if await self.hasLauncher(launcherName):
            raise IFException('Launcher [{}] exists.'.format(launcherName))
        await self.collection.insert_one({
            IFLocal.LauncherName: launcherName,
            IFLocal.Brief: brief,
            IFLocal.Description: description,
            IFLocal.Commands: {}
        })

    async def getBrief(self, launcherName):
        brief = await self.collection.find_one({
            IFLocal.LauncherName: launcherName
        }, {
            IFLocal.Brief: 1,
            '_id': 0
        })
        if brief == None:
            raise IFException('Launcher [{}] not exist.'.format(launcherName))
        return brief[IFLocal.Brief]

    async def getDescription(self, launcherName):
        description = await self.collection.find_one({
            IFLocal.LauncherName: launcherName
        }, {
            IFLocal.Description: 1,
            '_id': 0
        })
        if description == None:
            raise IFException('Launcher [{}] not exist.'.format(launcherName))
        return description[IFLocal.Description]

    async def getBriefAndDescription(self, launcherName):
        bad = await self.collection.find_one({
            IFLocal.LauncherName: launcherName
        }, {
            IFLocal.Brief: 1,
            IFLocal.Description: 1,
            '_id': 0
        })
        if bad == None:
            raise IFException('Launcher [{}] not exist.'.format(launcherName))
        return [bad[IFLocal.Brief], bad[IFLocal.Description]]

    async def deleteLauncher(self, launcherName):
        await self.collection.delete_one({IFLocal.LauncherName: launcherName})

    async def updateBrief(self, launcherName, brief):
        r = await self.collection.update_one({
            IFLocal.LauncherName: launcherName
        }, {'$set': {
            IFLocal.Brief: brief
        }})
        if r.modified_count == 0:
            raise IFException('Failed to update Brief.')

    async def updateDescription(self, launcherName, description):
        r = await self.collection.update_one({
            IFLocal.LauncherName: launcherName
        }, {'$set': {
            IFLocal.Description: description
        }})
        if r.modified_count == 0:
            raise IFException('Failed to update Description.')

    async def getCommands(self, launcherName):
        commands = await self.collection.find_one({
            IFLocal.LauncherName: launcherName
        }, {
            IFLocal.Commands: 1,
            '_id': 0
        })
        if commands == None:
            raise IFException('Launcher [{}] not exist.'.format(launcherName))
        return commands[IFLocal.Commands]

    # def setCommand(self, launcherName, commandName, commandContent):
    #     # r = self.collection.update_one({
    #     #     IFLocal.LauncherName: launcherName
    #     # }, {'$set': {
    #     #     '{}.{}'.format(IFLocal.Commands, commandName): commandContent
    #     # }}, upsert=True)
    #     # if r.modified_count == 0:
    #     #     raise IFException('Failed to update Command.')
    #
    #     r = self.collection.update_one({
    #         IFLocal.LauncherName: launcherName,
    #     }, {'$set': {
    #         '{}.{}'.format(IFLocal.Commands, commandName): commandContent
    #     }}, upsert=True)
    #     print(r.acknowledged)
    #     print(r.raw_result)
    #     if r.modified_count == 0:
    #         raise IFException('Failed to update Command.')

#     def getUserInfo(self, id):
#         info = self.collection.find_one({
#             UserManager.UserID: id
#         }, {
#             UserManager.Name: 1,
#             UserManager.Avatar: 1,
#             UserManager.Privilege: 1,
#             '_id': 0
#         })
#         if info == None:
#             raise IFException('User [{}] not exist.'.format(id))
#         return info
#
#     def getUserName(self, id):
#         return self.getUserInfo(id)[UserManager.Name]
#
#     def getAvatar(self, id):
#         return self.getUserInfo(id)[UserManager.Avatar]
#
#     def getPrivilege(self, id):
#         return self.getUserInfo(id)[UserManager.Privilege]
#
#     def updateUserName(self, id, userName):
#         r = self.collection.update_one({
#             UserManager.UserID: id
#         }, {'$set': {
#             UserManager.Name: userName
#         }})
#         if r.modified_count == 0:
#             raise IFException('Failed to update UserName.')
#
#     def updateAvatar(self, id, avatar):
#         r = self.collection.update_one({
#             UserManager.UserID: id
#         }, {'$set': {
#             UserManager.Avatar: avatar
#         }})
#         if r.modified_count == 0:
#             raise IFException('Failed to update Avatar.')
#
#     def verifyPassword(self, id, pwd, salted=False):
#         info = self.__getHashedPassword(id)
#         saltA = info[UserManager.SaltA]
#         saltB = info[UserManager.SaltB]
#         hashedPassword = info[UserManager.HashedPassword]
#         if salted:
#             tobeVerified = self.__hashPassword(pwd, [saltB])
#         else:
#             tobeVerified = self.__hashPassword(pwd, [saltA, saltB])
#         return tobeVerified == hashedPassword
#
#     def updatePassword(self, id, pwd):
#         saltA = self.__randomSalt()
#         saltB = self.__randomSalt()
#         hashedPassword = self.__hashPassword(pwd, [saltA, saltB])
#         r = self.collection.update_one({
#             UserManager.UserID: id
#         }, {'$set': {
#             UserManager.SaltA: saltA,
#             UserManager.SaltB: saltB,
#             UserManager.HashedPassword: hashedPassword,
#         }})
#         if r.modified_count == 0:
#             raise IFException('Failed to update Password.')
#
#     def getSalt(self, id):
#         return self.__getHashedPassword(id)[UserManager.SaltA]
#
#     def resetPassword(self, id):
#         newPwd = self.__randomPassword()
#         self.updatePassword(id, newPwd)
#         return newPwd
#
#     def updatePrivilege(self, id, privilege):
#         privilege = list(set(privilege))
#         r = self.collection.update_one({
#             UserManager.UserID: id
#         }, {'$set': {
#             UserManager.Privilege: privilege
#         }})
#         if r.modified_count == 0:
#             raise IFException('Failed to clear Privilege.')
#
#     def clearPrivilege(self, id):
#         self.updatePrivilege(id, [])
#
#     def addPrivilege(self, id, onePrivilege):
#         oldP = list(self.getPrivilege(id))
#         newP = list(oldP) + [onePrivilege]
#         self.updatePrivilege(id, newP)
#
#     def removePrivilege(self, id, onePrivilege):
#         P = self.getPrivilege(id)
#         if P.__contains__(onePrivilege):
#             P.remove(onePrivilege)
#             self.updatePrivilege(id, P)
#         else:
#             raise IFException('User [{}] does not has provilege [{}].'.format(id, onePrivilege))
#
#     def __getHashedPassword(self, id):
#         info = self.collection.find_one({
#             UserManager.UserID: id
#         }, {
#             UserManager.SaltA: 1,
#             UserManager.SaltB: 1,
#             UserManager.HashedPassword: 1,
#             '_id': 0
#         })
#         if info == None:
#             raise IFException('User [{}] not exist.'.format(id))
#         return info
#
#     def __hashPassword(self, password, salts):
#         for salt in salts:
#             password = md5((salt + password).encode('UTF-8')).hexdigest()
#         return password
#
#     def __randomPassword(self, length=12):
#         return self.__randomString(length)
#
#     def __randomSalt(self, length=1024):
#         return self.__randomString(length)
#
#     def __randomString(self, length):
#         return ''.join([self.rnd.choice(self.validCharacters) for i in range(length)])
