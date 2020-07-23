import time
from datetime import datetime
from bson.objectid import ObjectId
import pytz
from bson.codec_options import CodecOptions
from IFCore import IFException
from motor.motor_tornado import MotorClient


class Storage:
    Data = 'Data'
    RecordTime = 'RecordTime'
    FetchTime = 'FetchTime'
    Key = 'Key'

    def __init__(self, db):
        self.db = db
        self.tz = pytz.timezone('Asia/Shanghai')

    async def append(self, collection, data, fetchTime=None, key=None):
        recordTime = datetime.fromtimestamp(time.time(), tz=self.tz)
        s = {
            Storage.RecordTime: recordTime,
            Storage.Data: data
        }
        if fetchTime:
            if isinstance(fetchTime, int):
                fetchTime = datetime.fromtimestamp(fetchTime / 1000.0, tz=self.tz)
            elif isinstance(fetchTime, float):
                fetchTime = datetime.fromtimestamp(fetchTime, tz=self.tz)
            elif isinstance(fetchTime, str):
                fetchTime = datetime.fromisoformat(fetchTime)
            else:
                raise RuntimeError('FetchTime not recognized.')
            s[Storage.FetchTime] = fetchTime
        if key:
            s[Storage.Key] = key
        await self.__collection(collection).insert_one(s)

    async def latest(self, collection, after=None, filter={}):
        dbFilter = self.__reformFilter(filter)
        r = (await self.__collection(collection).find({}, dbFilter).sort("_id", -1).to_list(length=1))
        if len(r) == 0: raise IFException('No record.')
        r = r[0]
        valid = True
        if after:
            latestEntryTime = r[Storage.FetchTime]
            valid = datetime.fromisoformat(after) < latestEntryTime
        return self.__reformResult(r) if valid else None

    async def range(self, collection, begin, end, by=RecordTime, filter={}, limit=1000):
        if by == Storage.RecordTime or by == Storage.FetchTime:
            begin = datetime.fromisoformat(begin)
            end = datetime.fromisoformat(end)
        dbFilter = self.__reformFilter(filter)
        r = await self.__collection(collection).find(
            {"$and": [{by: {"$gt": begin}}, {by: {"$lt": end}}]}
            , dbFilter).sort('_id', 1).to_list(length=limit)
        return [self.__reformResult(item) for item in r]

    async def get(self, collection, id, filter={}):
        dbFilter = self.__reformFilter(filter)
        r = (await self.__collection(collection).find({'_id': ObjectId(id)}, dbFilter).to_list(length=1))[0]
        return self.__reformResult(r)

    def __collection(self, collection):
        return self.db['Storage_{}'.format(collection)].with_options(codec_options=CodecOptions(tz_aware=True, tzinfo=self.tz))

    def __reformResult(self, result):
        if result.__contains__(Storage.RecordTime):
            result[Storage.RecordTime] = result[Storage.RecordTime].isoformat()
        if result.__contains__(Storage.FetchTime):
            result[Storage.FetchTime] = result[Storage.FetchTime].isoformat()
        if result.__contains__('_id'):
            result['_id'] = str(result['_id'])
        return result

    def __reformFilter(self, filter):
        if filter == {}:
            dbFilter = {}
        else:
            dbFilter = {Storage.FetchTime: 1, '_id': 1}
            dbFilter.update(filter)
        return dbFilter


if __name__ == '__main__':
    # print('test db')
    # db = MotorClient('mongodb://IFDataAdmin:fwaejio8798fwjoiewf@172.16.60.199:27019/IFData').get_database('IFData')
    #
    # collection = db['Storage_MDIQKD_GroundTDC'].with_options(codec_options=CodecOptions(tz_aware=True, tzinfo=pytz.timezone('Asia/Shanghai')))
    # r = collection.find({"$and": [{'FetchTime': {"$gt": '2020-07-22T16:03:00+08:00'}}, {'FetchTime': {"$lt": '2020-07-22T16:03:00+08:00'}}]}, {})  # .sort('_id', 1).to_list()
    #
    import asyncio


    async def testFunc():
        db = MotorClient('mongodb://IFDataAdmin:fwaejio8798fwjoiewf@172.16.60.199:27019/IFData').get_database('IFData')

        collection = db.Storage_MDIQKD_GroundTDC.with_options(codec_options=CodecOptions(tz_aware=True, tzinfo=pytz.timezone('Asia/Shanghai')))
        # r = await collection.count_documents({}) #.sort('_id', 1).to_list(1000)
        r = await collection.find({"$and": [{'FetchTime': {"$gt": datetime.fromisoformat('2020-07-22T16:03:00+08:00')}}, {'FetchTime': {"$lt": datetime.fromisoformat('2020-07-22T16:13:00+08:00')}}]}, {'_id': 1, 'FetchTime': 1}).to_list(1)

        for i in r:
            print(i)


    asyncio.get_event_loop().run_until_complete(testFunc())

    # from pymongo import MongoClient
    #
    # client = MongoClient('mongodb://IFDataAdmin:fwaejio8798fwjoiewf@172.16.60.199:27019/IFData')
    # db = client.IFData
    # collection = db.Storage_MDIQKD_GroundTDC  # .with_options(codec_options=CodecOptions(tz_aware=True, tzinfo=pytz.timezone('Asia/Shanghai')))
    #
    # t1 = time.time()
    # r = collection.find({"$and": [{'FetchTime': {"$gt": datetime.fromisoformat('2020-07-22T16:03:00+08:00')}}, {'FetchTime': {"$lt": datetime.fromisoformat('2020-07-22T16:13:00+08:00')}}]}, {'_id': 1, 'FetchTime': 1})  # .sort('_id', 1).to_list(1000)
    # c = 0
    # for i in r:
    #     c += 1
    # t2 = time.time()
    #
    # print('finished in {} s.'.format(t2 - t1))
    # print(c)
