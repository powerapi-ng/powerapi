# Copyright (c) 2021, INRIA
# Copyright (c) 2021, University of Lille
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

from powerapi.database.base_db import BaseDB, IterDB
from powerapi.database.exception import ConnectionFailed, WriteFailed
from powerapi.report import Report

try:
    from pymongo import MongoClient
    from pymongo.errors import PyMongoError
except ImportError:
    logging.getLogger().info("PyMongo is not installed.")


class MongoIterDB(IterDB):
    """
    MongoDB Iterator.
    """

    def __init__(self, db, report_type, stream_mode):
        """
        :param db: MongoDB instance
        :param report_type: Report type
        """
        super().__init__(db, report_type, stream_mode)

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
        :raise: StopIteration in stream mode when no report was found. In non stream mode, raise StopIteration if the database is empty
        """
        if not self.stream_mode:
            json = self.cursor.next()
        else:
            json = self.db.collection.find_one_and_delete({})
            if json is None:
                raise StopIteration()

        return self.report_type.from_mongodb(json)


class MongoDB(BaseDB):
    """
    MongoDB class herited from BaseDB

    Allow to handle a MongoDB database in reading or writing.
    """

    def __init__(self, report_type: type[Report], uri: str, db_name: str, collection_name: str):
        """
        :param report_type: Type of the report handled by this database
        :param uri: URI of the MongoDB server
        :param db_name: Database name
        :param collection_name: Collection name
        """
        super().__init__(report_type)

        self.mongo_client = MongoClient(uri, connect=False)
        self.collection = self.mongo_client[db_name][collection_name]

    def connect(self):
        """
        Connect to the MongoDB server.
        :raise: ConnectionFailed if the connection to the MongoDB server fails.
        """
        try:
            # The client will establish a connection on the first operation.
            self.mongo_client.admin.command('ping')
        except PyMongoError as exn:
            raise ConnectionFailed(f'Failed to connect to the MongoDB server: {exn}') from exn

    def disconnect(self):
        """
        Disconnect from the MongoDB database.
        """
        self.mongo_client.close()

    def iter(self, stream_mode: bool = False) -> MongoIterDB:
        """
        Create the iterator for get the data
        """
        return MongoIterDB(self, self.report_type, stream_mode)

    def save(self, report: Report):
        """
        Save the report into the database.
        :param report: Report to save
        """
        try:
            self.collection.insert_one(self.report_type.to_mongodb(report))
        except PyMongoError as exn:
            raise WriteFailed(f'Failed to save report to MongoDB: {exn}') from exn

    def save_many(self, reports: list[Report]):
        """
        Saves multiple reports into the database.
        :param reports: List of Report to save
        """
        try:
            serialized_reports = [self.report_type.to_mongodb(report) for report in reports]
            self.collection.insert_many(serialized_reports)
        except PyMongoError as exn:
            raise WriteFailed(f'Failed to save report to MongoDB: {exn}') from exn
