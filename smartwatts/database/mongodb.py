"""
Module MongoDB
"""

import pymongo
from smartwatts.database.base_db import BaseDB


class MongoDB(BaseDB):
    """
    MongoDB class
    """

    def __init__(self, host_name, port, db_name, collection_name):
        """
        Parameters:
            @host_name:       hostname of the mongodb (ex: "localhost")
            @port:            port of the mongodb (ex: 27017)
            @db_name:         database name in the mongodb (ex: "smartwatts")
            @collection_name: collection name in the mongodb (ex: "sensor")
        """
        self.host_name = host_name
        self.port = port
        self.db_name = db_name
        self.collection_name = collection_name

        self.mongo_client = None
        self.collection = None
        self.cursor = None

    def load(self):
        """ Override """
        self.mongo_client = pymongo.MongoClient(self.host_name, self.port)
        self.collection = self.mongo_client[self.db_name][self.collection_name]
        self.cursor = self.collection.find({})

    def get_next(self):
        """ Override """
        json = self.cursor.next()

        # Re arrange the json before return it by removing '_id' field
        # and add "groups"
        json.pop('_id', None)
        final_json = {}
        final_json['groups'] = {}
        common_keys = ['timestamp', 'sensor', 'target']

        for key, val in json.items():
            if key in common_keys:
                final_json[key] = val
            else:
                final_json['groups'][key] = val

        return final_json

    def save(self, json):
        """ Override """
        raise NotImplementedError
