# Copyright (c) 2018, INRIA
# Copyright (c) 2018, University of Lille
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import logging
try:
    import pymongo
except ImportError:
    logging.getLogger().info("PyMongo is not installed.")

from typing import List
from powerapi.database.base_db import BaseDB, DBError, IterDB
from powerapi.report import Report
from powerapi.report_model import ReportModel


class MongoBadDBError(DBError):
    """
    Error raised when hostname/port fail
    """
    def __init__(self, hostname):
        DBError.__init__(self, 'Mongo DB error : can\'t connect to ' + hostname)


class MongoIterDB(IterDB):
    """
    MongoIterDB class

    Class for iterating in a MongoDB class
    """

    def __init__(self, db, report_model, stream_mode):
        """
        """
        super().__init__(db, report_model, stream_mode)

        #: (pymongo.Cursor): Cursor which return data
        self.cursor = None

        self.__iter__()

    def __iter__(self):
        """
        Create the iterator for get the data
        """
        if not self.stream_mode:
            self.cursor = self.db.collection.find({})
        return self

    def __next__(self) -> Report:
        """
        Allow to get the next data
        """
        if not self.stream_mode:
            json = self.cursor.next()
        else:
            json = self.db.collection.find_one_and_delete({})
            if json is None:
                raise StopIteration()


        return self.report_model.get_type().deserialize(self.report_model.from_mongodb(json))


class MongoDB(BaseDB):
    """
    MongoDB class herited from BaseDB

    Allow to handle a MongoDB database in reading or writing.
    """

    def __init__(self, uri: str, db_name: str, collection_name: str):
        """
        :param uri:             URI of the MongoDB server

        :param db_name:         database name in the mongodb
                                (ex: "powerapi")

        :param collection_name: collection name in the mongodb
                                    (ex: "sensor")
        """
        BaseDB.__init__(self)

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

        self.mongo_client = pymongo.MongoClient(self.uri, serverSelectionTimeoutMS=5)

        # Check if hostname:port work
        try:
            self.mongo_client.admin.command('ismaster')
        except pymongo.errors.ServerSelectionTimeoutError:
            raise MongoBadDBError(self.uri)

        self.collection = self.mongo_client[self.db_name][self.collection_name]

    def iter(self, report_model: ReportModel, stream_mode: bool) -> MongoIterDB:
        """
        Create the iterator for get the data
        """
        return MongoIterDB(self, report_model, stream_mode)

    def save(self, report: Report, report_model: ReportModel):
        """
        Override from BaseDB

        :param report: Report to save
        :param report_model: ReportModel
        """
        self.collection.insert_one(report_model.to_mongodb(report.serialize()))

    def save_many(self, reports: List[Report], report_model: ReportModel):
        """
        Allow to save a batch of data

        :param reports: Batch of data.
        :param report_model: ReportModel
        """
        serialized_reports = list(map(lambda r: report_model.to_mongodb(r.serialize()), reports))
        self.collection.insert_many(serialized_reports)
