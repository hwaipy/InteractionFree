__author__ = 'Hwaipy'

import unittest
import os

os.chdir('..')
from MongoDBContext.MongoDBContext import MongoDBContextTest, UserManager
from IFCore import IFException
import hashlib
from tornado.ioloop import IOLoop


class IFConfigContextUserManagerTest(unittest.TestCase):
    userManager = MongoDBContextTest.IFConfig.userManager

    @classmethod
    def setUpClass(cls):
        async def drop():
            await IFConfigContextUserManagerTest.userManager.collection.drop()

        IOLoop.current().run_sync(drop)

    def setUp(self):
        pass

    def testUserManagerCreateAndDeleteUser(self):
        async def test():
            self.assertFalse(await IFConfigContextUserManagerTest.userManager.hasUser('user1@email'))
            await IFConfigContextUserManagerTest.userManager.createUser('user1@email')
            self.assertTrue(await IFConfigContextUserManagerTest.userManager.hasUser('user1@email'))
            try:
                await IFConfigContextUserManagerTest.userManager.createUser('user1@email')
                self.fail('No Exception Raised.')
            except IFException as e:
                self.assertEqual(e.__str__(), 'User [{}] exists.'.format('user1@email'))
            await IFConfigContextUserManagerTest.userManager.deleteUser('user1@email')
            await IFConfigContextUserManagerTest.userManager.deleteUser('user1@email')
            self.assertFalse(await IFConfigContextUserManagerTest.userManager.hasUser('user1@email'))

        IOLoop.current().run_sync(test)

    def testUserManagerUserInformation(self):
        async def test():
            await IFConfigContextUserManagerTest.userManager.createUser('user2@email', 'DisplayedName', avatar='AVT')
            self.assertEqual(await IFConfigContextUserManagerTest.userManager.getUserInfo('user2@email'), {UserManager.Name: 'DisplayedName', UserManager.Avatar: 'AVT', UserManager.Privilege: []})
            self.assertEqual(await IFConfigContextUserManagerTest.userManager.getUserName('user2@email'), 'DisplayedName')
            self.assertEqual(await IFConfigContextUserManagerTest.userManager.getAvatar('user2@email'), 'AVT')
            await IFConfigContextUserManagerTest.userManager.updateUserName('user2@email', 'NewDisplayName')
            self.assertEqual(await IFConfigContextUserManagerTest.userManager.getUserName('user2@email'), 'NewDisplayName')
            await IFConfigContextUserManagerTest.userManager.updateAvatar('user2@email', 'NewAVT')
            self.assertEqual(await IFConfigContextUserManagerTest.userManager.getAvatar('user2@email'), 'NewAVT')
            try:
                await IFConfigContextUserManagerTest.userManager.updateUserName('user13@email', '1')
                self.fail('No Exception Raised.')
            except IFException as e:
                self.assertEqual(e.__str__(), 'Failed to update UserName.')
            try:
                await IFConfigContextUserManagerTest.userManager.updateAvatar('user1@email3', '3')
                self.fail('No Exception Raised.')
            except IFException as e:
                self.assertEqual(e.__str__(), 'Failed to update Avatar.')

        IOLoop.current().run_sync(test)

    def testUserManagerPassword(self):
        async def test():
            await IFConfigContextUserManagerTest.userManager.createUser('user3@email', 'DisplayedName', password='pwd123', avatar='AVT')
            self.assertFalse(await IFConfigContextUserManagerTest.userManager.verifyPassword('user3@email', 'wrong'))
            self.assertTrue(await IFConfigContextUserManagerTest.userManager.verifyPassword('user3@email', 'pwd123'))
            try:
                await IFConfigContextUserManagerTest.userManager.updatePassword('user34@email', 'pwd456')
                self.fail('No Exception Raised.')
            except IFException as e:
                self.assertEqual(e.__str__(), 'Failed to update Password.')
            await IFConfigContextUserManagerTest.userManager.updatePassword('user3@email', 'pwd456')
            self.assertFalse(await IFConfigContextUserManagerTest.userManager.verifyPassword('user3@email', 'pwd123'))
            self.assertTrue(await IFConfigContextUserManagerTest.userManager.verifyPassword('user3@email', 'pwd456'))
            newPwd = await IFConfigContextUserManagerTest.userManager.resetPassword('user3@email')
            self.assertFalse(await IFConfigContextUserManagerTest.userManager.verifyPassword('user3@email', 'pwd456'))
            self.assertTrue(await IFConfigContextUserManagerTest.userManager.verifyPassword('user3@email', newPwd))
            saltedPassword = hashlib.md5((await IFConfigContextUserManagerTest.userManager.getSalt('user3@email') + newPwd).encode('UTF-8')).hexdigest()
            self.assertTrue(await IFConfigContextUserManagerTest.userManager.verifyPassword('user3@email', saltedPassword, True))

        IOLoop.current().run_sync(test)

    def testUserManagerPrivilege(self):
        async def test():
            await IFConfigContextUserManagerTest.userManager.createUser('user4@email', privilege=['a', 'b'])
            self.assertEqual(set(await IFConfigContextUserManagerTest.userManager.getPrivilege('user4@email')), set(['a', 'b']))
            await IFConfigContextUserManagerTest.userManager.addPrivilege('user4@email', 'c')
            self.assertEqual(set(await IFConfigContextUserManagerTest.userManager.getPrivilege('user4@email')), set(['a', 'c', 'b']))
            await IFConfigContextUserManagerTest.userManager.removePrivilege('user4@email', 'b')
            self.assertEqual(set(await IFConfigContextUserManagerTest.userManager.getPrivilege('user4@email')), set(['a', 'c']))
            try:
                await IFConfigContextUserManagerTest.userManager.removePrivilege('user4@email', 'b')
                self.fail('No Exception Raised.')
            except IFException as e:
                self.assertEqual(e.__str__(), 'User [user4@email] does not has provilege [b].')
            await IFConfigContextUserManagerTest.userManager.clearPrivilege('user4@email')
            self.assertEqual(set(await IFConfigContextUserManagerTest.userManager.getPrivilege('user4@email')), set([]))
            await IFConfigContextUserManagerTest.userManager.updatePrivilege('user4@email', ['1', '2', '3'])
            self.assertEqual(set(await IFConfigContextUserManagerTest.userManager.getPrivilege('user4@email')), set(['2', '3', '1']))

        IOLoop.current().run_sync(test)

    def tearDown(self):
        pass

    @classmethod
    def tearDownClass(cls):
        pass


if __name__ == '__main__':
    unittest.main()
