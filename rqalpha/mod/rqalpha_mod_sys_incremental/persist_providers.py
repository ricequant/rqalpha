import datetime

from rqalpha.interface import AbstractPersistProvider


class MongodbPersistProvider(AbstractPersistProvider):
    def __init__(self, strategy_id, mongo_url, mongo_db):
        import pymongo
        import gridfs

        persist_db = pymongo.MongoClient(mongo_url)[mongo_db]
        self._strategy_id = strategy_id
        self._fs = gridfs.GridFS(persist_db)

    def store(self, key, value):
        update_time = datetime.datetime.now()
        self._fs.put(value, strategy_id=self._strategy_id, key=key, update_time=update_time)
        for grid_out in self._fs.find({"strategy_id": self._strategy_id, "key": key, "update_time": {"$lt": update_time}}):
            self._fs.delete(grid_out._id)

    def load(self, key, large_file=False):
        import gridfs
        try:
            b = self._fs.get_last_version(strategy_id=self._strategy_id, key=key)
            return b.read()
        except gridfs.errors.NoFile:
            return None
