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

    def load(self):
        """ MongoDB connection """
        self.mongo_client = pymongo.MongoClient(self.host_name, self.port)
        self.collection = self.mongo_client[self.db_name][self.collection_name]

    def get_reports_with_sensor(self, sensor):
        """ Get all reports with this sensor """
        reports = list(self.collection.aggregate(
            [
                {'$match': {'sensor': sensor}},
                {'$addFields': {'groups': '$$ROOT'}},
                {'$project': {'_id': 0, 'timestamp': 1, 'sensor': 1,
                              'target': 1, 'groups': 1}},
                {'$project': {'groups': {'_id': 0, 'timestamp': 0,
                                         'sensor': 0, 'target': 0}}}
            ]))

        return reports
