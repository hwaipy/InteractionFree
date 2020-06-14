import time
from datetime import datetime, tzinfo
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
        r = (await self.__collection(collection).find({}, dbFilter).sort("_id", -1).to_list(length=1))[0]
        if not r: return r
        valid = True
        if after:
            latestEntryTime = r[Storage.RecordTime]
            valid = datetime.fromisoformat(after) < latestEntryTime
        return self.__reformResult(r) if valid else None

    async def range(self, collection, begin, end, by=RecordTime, filter={}):
        if by == Storage.RecordTime or by == Storage.FetchTime:
            begin = datetime.fromisoformat(begin)
            end = datetime.fromisoformat(end)
        dbFilter = self.__reformFilter(filter)
        r = await self.__collection(collection).find(
            {"$and": [{by: {"$gt": begin}}, {by: {"$lt": end}}]}
            , dbFilter).sort('_id', 1).to_list(10000)
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
            dbFilter = {Storage.RecordTime: 1, '_id': 1}
            dbFilter.update(filter)
        return dbFilter
