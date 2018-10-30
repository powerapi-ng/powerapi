"""
Module db which define an extensive class that handle
different kind of database (mongodb, csv, ...)
"""

import json
import sys

import smartwatts.db.mongodb as mongodb
import smartwatts.db.csvdb as csvdb
from smartwatts.db.base_db import BaseDB, MissConfigParamError


class UnknownDatabaseTypeError(Exception):
    """ Exception when we don't know the database type  """
    pass


class Database(BaseDB):
    """
    Database class.
    """

    def __init__(self, config_file='config_db.json'):

        """ Load config file """
        try:
            with open(config_file) as json_file:
                self.config = json.load(json_file)
        except FileNotFoundError:
            sys.exit("Database: config file not found.")

        """ Check if there is db_type """
        if 'db_type' not in self.config['database']:
            raise MissConfigParamError

        """
        Load database
        """
        self.database_type = self.config['database']['db_type']
        if self.database_type == 'mongodb':
            self.database = mongodb.MongoDB(self.config['database'])
        elif self.database_type == 'csvdb':
            self.database = csvdb.CsvDB(self.config['database'])
        else:
            raise UnknownDatabaseTypeError

    def get_last_hwpc_report(self):
        """ Get the last hwpc sensor save in the database """
        return self.database.get_last_hwpc_report()
