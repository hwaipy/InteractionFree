__author__ = 'Hwaipy'

import unittest
from MongoDBContext import MongoDBContextTest, IFConfigContext
from IFCore import IFException
import hashlib


class IFConfigContextTest(unittest.TestCase):
    userManager = MongoDBContextTest.IFConfig.userManager

    @classmethod
    def setUpClass(cls):
        IFConfigContextTest.userManager.collection.drop()

    def setUp(self):
        pass

    def testUserManagerCreateAndDeleteUser(self):
        IFConfigContextTest.userManager.createUser('user1@email')
        self.assertTrue(IFConfigContextTest.userManager.hasUser('user1@email'))
        self.assertRaises(IFException, lambda: IFConfigContextTest.userManager.createUser('user1@email'))
        IFConfigContextTest.userManager.deleteUser('user1@email')
        IFConfigContextTest.userManager.deleteUser('user1@email')
        self.assertFalse(IFConfigContextTest.userManager.hasUser('user1@email'))

    def testUserManagerUserInformation(self):
        IFConfigContextTest.userManager.createUser('user2@email', 'DisplayedName', avatar='AVT')
        self.assertEqual(IFConfigContextTest.userManager.getUserInfo('user2@email'),
                         {IFConfigContext.UserManager.Name: 'DisplayedName', IFConfigContext.UserManager.Avatar: 'AVT',
                          IFConfigContext.UserManager.Privilege: []})
        self.assertEqual(IFConfigContextTest.userManager.getUserName('user2@email'), 'DisplayedName')
        self.assertEqual(IFConfigContextTest.userManager.getAvatar('user2@email'), 'AVT')
        IFConfigContextTest.userManager.updateUserName('user2@email', 'NewDisplayName')
        self.assertEqual(IFConfigContextTest.userManager.getUserName('user2@email'), 'NewDisplayName')
        IFConfigContextTest.userManager.updateAvatar('user2@email', 'NewAVT')
        self.assertEqual(IFConfigContextTest.userManager.getAvatar('user2@email'), 'NewAVT')
        self.assertRaises(IFException, lambda: IFConfigContextTest.userManager.updateUserName('user13@email', '1'))
        self.assertRaises(IFException, lambda: IFConfigContextTest.userManager.updateAvatar('user1@email3', '3'))

    def testUserManagerPassword(self):
        IFConfigContextTest.userManager.createUser('user3@email', 'DisplayedName', password='pwd123', avatar='AVT')
        self.assertFalse(IFConfigContextTest.userManager.verifyPassword('user3@email', 'wrong'))
        self.assertTrue(IFConfigContextTest.userManager.verifyPassword('user3@email', 'pwd123'))
        self.assertRaises(IFException,
                          lambda: IFConfigContextTest.userManager.updatePassword('user34@email', 'pwd456'))
        IFConfigContextTest.userManager.updatePassword('user3@email', 'pwd456')
        self.assertFalse(IFConfigContextTest.userManager.verifyPassword('user3@email', 'pwd123'))
        self.assertTrue(IFConfigContextTest.userManager.verifyPassword('user3@email', 'pwd456'))
        newPwd = IFConfigContextTest.userManager.resetPassword('user3@email')
        self.assertFalse(IFConfigContextTest.userManager.verifyPassword('user3@email', 'pwd456'))
        self.assertTrue(IFConfigContextTest.userManager.verifyPassword('user3@email', newPwd))
        saltedPassword = hashlib.md5(
            (IFConfigContextTest.userManager.getSalt('user3@email') + newPwd).encode('UTF-8')).hexdigest()
        self.assertTrue(IFConfigContextTest.userManager.verifyPassword('user3@email', saltedPassword, True))

    def testUserManagerPrivilege(self):
        IFConfigContextTest.userManager.createUser('user4@email', privilege=['a', 'b'])
        self.assertEqual(set(IFConfigContextTest.userManager.getPrivilege('user4@email')), set(['a', 'b']))
        IFConfigContextTest.userManager.addPrivilege('user4@email', 'c')
        self.assertEqual(set(IFConfigContextTest.userManager.getPrivilege('user4@email')), set(['a', 'c', 'b']))
        IFConfigContextTest.userManager.removePrivilege('user4@email', 'b')
        self.assertEqual(set(IFConfigContextTest.userManager.getPrivilege('user4@email')), set(['a', 'c']))
        self.assertRaises(IFException, lambda: IFConfigContextTest.userManager.removePrivilege('user4@email', 'b'))
        IFConfigContextTest.userManager.clearPrivilege('user4@email')
        self.assertEqual(set(IFConfigContextTest.userManager.getPrivilege('user4@email')), set([]))
        IFConfigContextTest.userManager.updatePrivilege('user4@email', ['1', '2', '3'])
        self.assertEqual(set(IFConfigContextTest.userManager.getPrivilege('user4@email')), set(['2', '3', '1']))

    def tearDown(self):
        pass

    @classmethod
    def tearDownClass(cls):
        pass


if __name__ == '__main__':
    unittest.main()
