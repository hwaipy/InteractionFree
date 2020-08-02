import time
from datetime import datetime
from bson.objectid import ObjectId
import pytz
from bson.codec_options import CodecOptions


class Storage:
    Data = 'Data'
    RecordTime = 'RecordTime'
    FetchTime = 'FetchTime'
    Key = 'Key'

    def __init__(self, db):
        self.db = db
        self.tz = pytz.timezone('Asia/Shanghai')

    async def append(self, collection, data, fetchTime=None):
        recordTime = datetime.fromtimestamp(time.time(), tz=self.tz)
        s = {
            Storage.RecordTime: recordTime,
            Storage.Data: data
        }
        if fetchTime:
            s[Storage.FetchTime] = self.__parseFetchTime(fetchTime)
        else:
            s[Storage.FetchTime] = recordTime
        await self.__collection(collection).insert_one(s)

    async def latest(self, collection, by=FetchTime, after=None, filter={}):
        dbFilter = self.__reformFilter(filter)
        r = (await self.__collection(collection).find({}, dbFilter).sort(by, -1).to_list(length=1))
        if len(r) == 0: return None
        r = r[0]
        valid = True
        if after:
            latestEntryTime = r[Storage.FetchTime]
            valid = datetime.fromisoformat(after) < latestEntryTime
        return self.__reformResult(r) if valid else None

    async def first(self, collection, by=FetchTime, after=None, filter={}):
        dbFilter = self.__reformFilter(filter)
        r = (await self.__collection(collection).find({by: {"$gt": datetime.fromisoformat(after)}}, dbFilter).sort(by, 1).to_list(length=1))
        if len(r) == 0: return None
        r = r[0]
        valid = True
        if after:
            latestEntryTime = r[Storage.FetchTime]
            valid = datetime.fromisoformat(after) < latestEntryTime
        return self.__reformResult(r) if valid else None

    async def range(self, collection, begin, end, by=FetchTime, filter={}, limit=1000):
        if by == Storage.RecordTime or by == Storage.FetchTime:
            begin = datetime.fromisoformat(begin)
            end = datetime.fromisoformat(end)
        dbFilter = self.__reformFilter(filter)
        r = await self.__collection(collection).find(
            {"$and": [{by: {"$gt": begin}}, {by: {"$lt": end}}]}
            , dbFilter).to_list(length=limit)
        r.sort(key=lambda e: e[Storage.FetchTime])
        return [self.__reformResult(item) for item in r]

    async def get(self, collection, value, key='_id', filter={}):
        dbFilter = self.__reformFilter(filter)
        if key == '_id':
            value = ObjectId(value)
        if key == 'FetchTime':
            value = datetime.fromisoformat(value)
        r = (await self.__collection(collection).find({key: value}, dbFilter).to_list(length=1))
        if len(r) > 0:
            return self.__reformResult(r[0])
        else:
            return None

    async def delete(self, collection, value, key='_id'):
        if key == '_id':
            value = ObjectId(value)
        if key == 'FetchTime':
            value = datetime.fromisoformat(value)
        await self.__collection(collection).delete_one({key: value})

    async def update(self, collection, id, value):
        await self.__collection(collection).update_one({'_id': ObjectId(id)}, {'$set': value})

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

    def __parseFetchTime(self, fetchTime):
        if isinstance(fetchTime, int):
            return datetime.fromtimestamp(fetchTime / 1000.0, tz=self.tz)
        elif isinstance(fetchTime, float):
            return datetime.fromtimestamp(fetchTime, tz=self.tz)
        elif isinstance(fetchTime, str):
            return datetime.fromisoformat(fetchTime)
        else:
            raise RuntimeError('FetchTime not recognized.')


if __name__ == '__main__':
    from motor import MotorClient


    async def testFunc():
        motor = MotorClient('mongodb://IFDataAdmin:fwaejio8798fwjoiewf@172.16.60.199:27019/IFData')
        storage = Storage(motor.IFData)
        get = await storage.append('DBTest', '2020-07-25T15:37:45.318000+08:00', 'FetchTime', filter={'FetchTime': 1})

        print(get)


    import asyncio

    asyncio.get_event_loop().run_until_complete(testFunc())
