__author__ = 'Hwaipy'

import unittest
import os

os.chdir('..')
from MongoDBContext.MongoDBContext import MongoDBContextTest
from IFCore import IFException, IFLoop
from tornado.ioloop import IOLoop


class IFDataContextIFLocalTest(unittest.TestCase):
    IFLocal = MongoDBContextTest.IFData.IFLocal

    @classmethod
    def setUpClass(cls):
        IFDataContextIFLocalTest.IFLocal.collection.drop()

        async def drop():
            await IFDataContextIFLocalTest.IFLocal.collection.drop()

        IOLoop.current().run_sync(drop)

    def setUp(self):
        pass

    def testLauncherBasic(self):
        async def test():
            self.assertFalse(await IFDataContextIFLocalTest.IFLocal.hasLauncher('testLauncher 1'))
            await IFDataContextIFLocalTest.IFLocal.createLauncher('testLauncher 1', 'This is TL1', 'Long des')
            try:
                await IFDataContextIFLocalTest.IFLocal.createLauncher('testLauncher 1', 'This is TL1', 'Long des')
                self.fail('No Exception Raised.')
            except IFException as e:
                self.assertEqual(e.__str__(), 'Launcher [{}] exists.'.format('testLauncher 1'))
            try:
                await IFDataContextIFLocalTest.IFLocal.getBrief('testLauncher 2')
                self.fail('No Exception Raised.')
            except IFException as e:
                self.assertEqual(e.__str__(), 'Launcher [{}] not exist.'.format('testLauncher 2'))
            await IFDataContextIFLocalTest.IFLocal.createLauncher('testLauncher 2', None, None)
            self.assertIsNone(await IFDataContextIFLocalTest.IFLocal.getBrief('testLauncher 2'))
            self.assertEqual(await IFDataContextIFLocalTest.IFLocal.getBrief('testLauncher 1'), 'This is TL1')
            self.assertEqual(await IFDataContextIFLocalTest.IFLocal.getDescription('testLauncher 1'), 'Long des')
            self.assertEqual(await IFDataContextIFLocalTest.IFLocal.getBriefAndDescription('testLauncher 1'), ['This is TL1', 'Long des'])
            await IFDataContextIFLocalTest.IFLocal.updateBrief('testLauncher 2', 'New TL2')
            try:
                await IFDataContextIFLocalTest.IFLocal.updateBrief('TL 3', 'New TL2')
                self.fail('No Exception Raised.')
            except IFException as e:
                self.assertEqual(e.__str__(), 'Failed to update Brief.')
            self.assertEqual(await IFDataContextIFLocalTest.IFLocal.getBrief('testLauncher 2'), 'New TL2')
            await IFDataContextIFLocalTest.IFLocal.updateDescription('testLauncher 2', 'des 2')
            try:
                await IFDataContextIFLocalTest.IFLocal.updateDescription('TL 3', 'New TL2')
                self.fail('No Exception Raised.')
            except IFException as e:
                self.assertEqual(e.__str__(), 'Failed to update Description.')
            self.assertEqual(await IFDataContextIFLocalTest.IFLocal.getDescription('testLauncher 2'), 'des 2')
            self.assertTrue(await IFDataContextIFLocalTest.IFLocal.hasLauncher('testLauncher 2'))
            await IFDataContextIFLocalTest.IFLocal.deleteLauncher('testLauncher 2')
            self.assertFalse(await IFDataContextIFLocalTest.IFLocal.hasLauncher('testLauncher 2'))

        IOLoop.current().run_sync(test)

    def testCommands(self):
        async def test():
            await IFDataContextIFLocalTest.IFLocal.createLauncher('TL')
            self.assertEqual(await IFDataContextIFLocalTest.IFLocal.getCommands('TL'), {})

        #
        #     IFDataContextIFLocalTest.IFLocal.setCommand('TL', 'CMD1', {})
        #     IFDataContextIFLocalTest.IFLocal.setCommand('TL', 'CMD1', {})

        #     self.assertTrue(IFConfigContextTest.userManager.hasUser('user1@email'))
        #     self.assertRaises(IFException, lambda: IFConfigContextTest.userManager.createUser('user1@email'))
        #     IFConfigContextTest.userManager.deleteUser('user1@email')
        #     IFConfigContextTest.userManager.deleteUser('user1@email')
        #

        IOLoop.current().run_sync(test)

    # def testUserManagerUserInformation(self):
    #     IFConfigContextTest.userManager.createUser('user2@email', 'DisplayedName', avatar='AVT')
    #     self.assertEqual(IFConfigContextTest.userManager.getUserInfo('user2@email'),
    #                      {IFConfigContext.UserManager.Name: 'DisplayedName', IFConfigContext.UserManager.Avatar: 'AVT',
    #                       IFConfigContext.UserManager.Privilege: []})
    #     self.assertEqual(IFConfigContextTest.userManager.getUserName('user2@email'), 'DisplayedName')
    #     self.assertEqual(IFConfigContextTest.userManager.getAvatar('user2@email'), 'AVT')
    #     IFConfigContextTest.userManager.updateUserName('user2@email', 'NewDisplayName')
    #     self.assertEqual(IFConfigContextTest.userManager.getUserName('user2@email'), 'NewDisplayName')
    #     IFConfigContextTest.userManager.updateAvatar('user2@email', 'NewAVT')
    #     self.assertEqual(IFConfigContextTest.userManager.getAvatar('user2@email'), 'NewAVT')
    #     self.assertRaises(IFException, lambda: IFConfigContextTest.userManager.updateUserName('user13@email', '1'))
    #     self.assertRaises(IFException, lambda: IFConfigContextTest.userManager.updateAvatar('user1@email3', '3'))
    #
    # def testUserManagerPassword(self):
    #     IFConfigContextTest.userManager.createUser('user3@email', 'DisplayedName', password='pwd123', avatar='AVT')
    #     self.assertFalse(IFConfigContextTest.userManager.verifyPassword('user3@email', 'wrong'))
    #     self.assertTrue(IFConfigContextTest.userManager.verifyPassword('user3@email', 'pwd123'))
    #     self.assertRaises(IFException,
    #                       lambda: IFConfigContextTest.userManager.updatePassword('user34@email', 'pwd456'))
    #     IFConfigContextTest.userManager.updatePassword('user3@email', 'pwd456')
    #     self.assertFalse(IFConfigContextTest.userManager.verifyPassword('user3@email', 'pwd123'))
    #     self.assertTrue(IFConfigContextTest.userManager.verifyPassword('user3@email', 'pwd456'))
    #     newPwd = IFConfigContextTest.userManager.resetPassword('user3@email')
    #     self.assertFalse(IFConfigContextTest.userManager.verifyPassword('user3@email', 'pwd456'))
    #     self.assertTrue(IFConfigContextTest.userManager.verifyPassword('user3@email', newPwd))
    #     saltedPassword = hashlib.md5(
    #         (IFConfigContextTest.userManager.getSalt('user3@email') + newPwd).encode('UTF-8')).hexdigest()
    #     self.assertTrue(IFConfigContextTest.userManager.verifyPassword('user3@email', saltedPassword, True))
    #
    # def testUserManagerPrivilege(self):
    #     IFConfigContextTest.userManager.createUser('user4@email', privilege=['a', 'b'])
    #     self.assertEqual(set(IFConfigContextTest.userManager.getPrivilege('user4@email')), set(['a', 'b']))
    #     IFConfigContextTest.userManager.addPrivilege('user4@email', 'c')
    #     self.assertEqual(set(IFConfigContextTest.userManager.getPrivilege('user4@email')), set(['a', 'c', 'b']))
    #     IFConfigContextTest.userManager.removePrivilege('user4@email', 'b')
    #     self.assertEqual(set(IFConfigContextTest.userManager.getPrivilege('user4@email')), set(['a', 'c']))
    #     self.assertRaises(IFException, lambda: IFConfigContextTest.userManager.removePrivilege('user4@email', 'b'))
    #     IFConfigContextTest.userManager.clearPrivilege('user4@email')
    #     self.assertEqual(set(IFConfigContextTest.userManager.getPrivilege('user4@email')), set([]))
    #     IFConfigContextTest.userManager.updatePrivilege('user4@email', ['1', '2', '3'])
    #     self.assertEqual(set(IFConfigContextTest.userManager.getPrivilege('user4@email')), set(['2', '3', '1']))

    def tearDown(self):
        pass

    @classmethod
    def tearDownClass(cls):
        pass


if __name__ == '__main__':
    unittest.main()
