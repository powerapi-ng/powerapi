# Copyright (C) 2018  University of Lille
# Copyright (C) 2018  INRIA
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import pymongo
from powerapi.database.base_db import BaseDB, DBError
from powerapi.utils import Error


class MongoBadDBError(DBError):
    """
    Error raised when hostname/port fail
    """
    def __init__(self, hostname):
        DBError.__init__(self, 'Mongo DB error : can\'t connect to ' +
                         hostname)


class MongoDB(BaseDB):
    """
    MongoDB class herited from BaseDB

    Allow to handle a MongoDB database in reading or writing.
    """

    def __init__(self,
                 uri, db_name, collection_name, report_model, stream_mode=False):
        """
        :param str uri:             URI of the MongoDB server

        :param str db_name:         database name in the mongodb
                                    (ex: "powerapi")

        :param str collection_name: collection name in the mongodb
                                    (ex: "sensor")

        :param report_model:        XXXModel object. Allow to read specific
                                    report with a specific format in a database
        :type report_model:         powerapi.ReportModel

        """
        BaseDB.__init__(self, report_model)

        #: (str): URI of the mongodb server
        self.uri = uri

        #: (str): Database name in the mongodb
        self.db_name = db_name

        #: (str): Collection name in the mongodb
        self.collection_name = collection_name

        #: (pymongo.MongoClient): MongoClient instance of the server
        self.mongo_client = None

        #: (pymongo.MongoClient): MongoClient pointed to the
        #: targeted collection
        self.collection = None

        #: (bool): Stream mode
        self.stream_mode = stream_mode

        #: (pymongo.Cursor): Cursor which return data
        self.cursor = None

    def connect(self):
        """
        Override from BaseDB.

        It create the connection to the mongodb database with the current
        configuration (hostname/port/db_name/collection_name), then check
        if the connection has been created without failure.
        """

        # close connection if reload
        if self.mongo_client is not None:
            self.mongo_client.close()

        self.mongo_client = pymongo.MongoClient(self.uri,
                                                serverSelectionTimeoutMS=5)

        self.collection = self.mongo_client[self.db_name][
            self.collection_name]

        # Check if hostname:port work
        try:
            self.mongo_client.admin.command('ismaster')
        except pymongo.errors.ServerSelectionTimeoutError:
            raise MongoBadDBError(self.uri)

    def __iter__(self):
        """
        Create the iterator for get the data
        """
        if not self.stream_mode:
            self.cursor = self.collection.find({})
        return self

    def __next__(self):
        """
        Allow to get the next data
        """
        try:
            if not self.stream_mode:
                json = self.cursor.next()
            else:
                json = self.collection.find_one_and_delete({})
                if json is None:
                    raise StopIteration()
        except StopIteration:
            raise StopIteration()

        # Re arrange the json before return it by removing '_id' field
        json.pop('_id', None)

        return self.report_model.from_mongodb(json)

    def save(self, json):
        """
        Override from BaseDB

        :param dict json: data JSON to save
        """
        # TODO: Check if json is valid with the report_model
        self.collection.insert_one(json)

    def save_many(self, tab_json):
        """
        Allow to save a batch of data

        :param [Dict] tab_json: Batch of data.
        """
        self.collection.insert_many(tab_json)
