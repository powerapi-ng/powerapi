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
        self.mongo_client = pymongo.MongoClient(host_name, port)
        self.collection = self.mongo_client[db_name][collection_name]

    def get_last_hwpc_report(self):
        """ Return the last hwpc report """

        """ Get the last datetime value """
        last_datetime = self.collection.find().sort(
                'timestamp',
                pymongo.DESCENDING).limit(1).next()['timestamp']

        """ Find all report with this datetime """
        reports = list(self.collection.find(
            {'timestamp': last_datetime}))

        """ Feed the HWPCReport Object """
        hwpc = HWPCReport()
        for report in reports:
            hwpc.feed_from_mongodb(report)

        return hwpc
