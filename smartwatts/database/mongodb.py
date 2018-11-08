"""
Module MongoDB which handle a mongo database with PyMongo
"""

import pymongo
from smartwatts.database.base_db import BaseDB
from smartwatts.report.hwpc_report import HWPCReport


class MongoDB(BaseDB):
    """
    MongoDB class

    Basic parameters:
        host_name       = "localhost"
        port            = 27017
        db_name         = smartwatts
        collection_name = sensor
    """

    def __init__(self, host_name, port, db_name, collection_name):
        """ Database connection """
        self.host_name = host_name
        self.port = port
        self.db_name = db_name
        self.collection_name = collection_name

        self.mongo_client = None
        self.collection = None
        self.cursor = None

    def load(self):
        """ MongoDB connection """
        self.mongo_client = pymongo.MongoClient(self.host_name, self.port)
        self.collection = self.mongo_client[self.db_name][self.collection_name]
        self.cursor = self.collection.find({})

    def get_next(self):
        """ Return the next report on the db """
        json = self.cursor.next()

        # Re arrange the json before return it
        json.pop('_id', None)
        real_json = {}
        real_json['groups'] = {}
        common_keys = ['timestamp', 'sensor', 'target']

        for key, val in json.items():
            if key in common_keys:
                real_json[key] = val
            else:
                real_json['groups'][key] = val

        return real_json
