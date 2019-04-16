"""
Copyright (c) 2018, INRIA
Copyright (c) 2018, University of Lille
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import pymongo
from powerapi.database.base_db import BaseDB, DBError


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
        BaseDB.__init__(self, report_model, stream_mode)

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
