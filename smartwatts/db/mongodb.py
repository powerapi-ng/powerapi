"""
Module MongoDB which handle a mongo database with PyMongo
"""

import pymongo
import smartwatts.utils
from smartwatts.db.base_db import BaseDB, MissConfigParamError
from smartwatts.model import HWPCReport


class MongoDB(BaseDB):
    """ MongoDB class """

    def __init__(self, config):
        self.config = config

        """ Check if config contain the necessary fields """
        for needed in ['host', 'port', 'db', 'collection']:
            if needed not in self.config:
                raise MissConfigParamError

        """ Database connection """
        self.mongo_client = pymongo.MongoClient(self.config['host'],
                                                self.config['port'])
        self.collection = self.mongo_client[
            self.config['db']][self.config['collection']]

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
