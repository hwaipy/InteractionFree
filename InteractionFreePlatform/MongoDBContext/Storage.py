import time
from datetime import datetime
from bson.objectid import ObjectId


class Storage:
    Data = 'Data'
    RecordTime = 'RecordTime'

    def __init__(self, db):
        self.db = db

    async def append(self, collection, data):
        await self.db['Storage_{}'.format(collection)].insert_one({
            Storage.RecordTime: datetime.fromtimestamp(time.time()),
            Storage.Data: data
        })

    async def latest(self, collection, after=None, filter={}):
        dbFilter = self.__reformFilter(filter)
        r = (await self.db['Storage_{}'.format(collection)].find({}, dbFilter).sort("_id", -1).to_list(length=1))[0]
        if not r: return r
        valid = True
        if after:
            latestEntryTime = r[Storage.RecordTime]
            valid = datetime.fromisoformat(after) < latestEntryTime
        r[Storage.RecordTime] = str(r[Storage.RecordTime])
        r['_id'] = str(r['_id'])
        return self.__reformResult(r) if valid else None

    async def range(self, collection, begin, end, filter={}):
        dbFilter = self.__reformFilter(filter)
        r = await self.db['Storage_{}'.format(collection)].find(
            {"$and": [{Storage.RecordTime: {"$gt": datetime.fromisoformat(begin)}}, {Storage.RecordTime: {"$lt": datetime.fromisoformat(end)}}]}
            , dbFilter).sort('_id', 1).to_list(10000)
        return [self.__reformResult(item) for item in r]

    async def get(self, collection, id, filter={}):
        dbFilter = self.__reformFilter(filter)
        r = (await self.db['Storage_{}'.format(collection)].find({'_id': ObjectId(id)}, dbFilter).to_list(length=1))[0]
        return self.__reformResult(r)

    def __reformResult(self, result):
        if result.__contains__(Storage.RecordTime):
            result[Storage.RecordTime] = str(result[Storage.RecordTime])
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
