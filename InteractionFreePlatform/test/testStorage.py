__author__ = 'Hwaipy'

import unittest
import os

os.chdir('..')
from MongoDBContext.MongoDBContext import MongoDBContextTest, UserManager
from IFCore import IFException
import hashlib
from tornado.ioloop import IOLoop
from MongoDBContext.MongoDBContext import MongoDBContext
from datetime import datetime, timedelta
from functional import seq
from random import Random


class StorageTest(unittest.TestCase):
    storage = MongoDBContextTest.IFData.storage
    collection = 'TestCollection'

    @classmethod
    def setUpClass(cls):
        async def drop():
            await StorageTest.storage.db['Storage_{}'.format('TestCollection')].drop()

        IOLoop.current().run_sync(drop)

    def setUp(self):
        pass

    def testDBFunctions(self):
        async def test():
            rnd = Random()
            iList = [i for i in range(0, 100)]
            rnd.shuffle(iList)
            for i in iList:
                await StorageTest.storage.append(StorageTest.collection, {'Content': i}, (datetime.fromisoformat('2020-07-01T00:00:00+08:00') + timedelta(seconds=i)).isoformat())
            exp = seq(range(0, 100)).map(lambda i: {'FetchTime': (datetime.fromisoformat('2020-07-01T00:00:00+08:00') + timedelta(seconds=i)).isoformat(), 'Data': {'Content': i}})
            self.assertTrue(await StorageTest.storage.latest(StorageTest.collection, 'FetchTime', '2020-07-01T00:01:00+08:00', {'FetchTime': 1, '_id': 0}) == {'FetchTime': '2020-07-01T00:01:39+08:00'})
            self.assertTrue(await StorageTest.storage.latest(StorageTest.collection, 'FetchTime', '2020-07-01T00:01:00+08:00', {'FetchTime': 1, '_id': 0, 'Data.Content': 1}) == exp[99])
            self.assertTrue(await StorageTest.storage.latest(StorageTest.collection, 'FetchTime', '2020-07-01T00:02:00+08:00', {'FetchTime': 1, '_id': 0, 'Data.Content': 1}) == None)
            self.assertTrue(await StorageTest.storage.first(StorageTest.collection, 'FetchTime', '2020-07-01T00:01:00+08:00', {'FetchTime': 1, '_id': 0, 'Data.Content': 1}) == exp[61])
            self.assertTrue(await StorageTest.storage.first(StorageTest.collection, 'FetchTime', '2020-07-01T00:01:50+08:00', {'FetchTime': 1, '_id': 0, 'Data.Content': 1}) == None)
            self.assertTrue(await StorageTest.storage.range(StorageTest.collection, '2020-07-01T00:00:50+08:00', '2020-07-01T00:00:52+08:00', 'FetchTime', {'FetchTime': 1, '_id': 0, 'Data.Content': 1}) == [exp[51]])
            self.assertTrue(await StorageTest.storage.range(StorageTest.collection, '2020-07-01T00:00:40+08:00', '2020-07-01T00:00:48.444+08:00', 'FetchTime', {'FetchTime': 1, '_id': 0, 'Data.Content': 1}) == exp[41:49])
            self.assertTrue(await StorageTest.storage.get(StorageTest.collection, '2020-07-01T00:01:20+08:00', 'FetchTime', {'FetchTime': 1, '_id': 0, 'Data.Content': 1}) == exp[80])
            self.assertTrue(await StorageTest.storage.get(StorageTest.collection, '2020-07-01T00:01:20.121+08:00', 'FetchTime', {'FetchTime': 1, '_id': 0, 'Data.Content': 1}) == None)
            await StorageTest.storage.delete(StorageTest.collection, '2020-07-01T00:00:50+08:00', 'FetchTime')
            await StorageTest.storage.delete(StorageTest.collection, '2020-07-01T00:00:50+08:00', 'FetchTime')
            self.assertTrue(await StorageTest.storage.range(StorageTest.collection, '2020-07-01T00:00:40+08:00', '2020-07-01T00:01:00+08:00', 'FetchTime', {'FetchTime': 1, '_id': 0, 'Data.Content': 1}) == exp[41:50] + exp[51:60])
            self.assertTrue(await StorageTest.storage.get(StorageTest.collection, '2020-07-01T00:00:50+08:00', 'FetchTime', {'FetchTime': 1, '_id': 0, 'Data.Content': 1}) == None)

        IOLoop.current().run_sync(test)

    def tearDown(self):
        pass

    @classmethod
    def tearDownClass(cls):
        pass


if __name__ == '__main__':
    unittest.main()
