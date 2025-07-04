# Copyright (c) 2021, Inria
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

from typing import Iterable

from powerapi.database.driver import DatabaseDriver, ReadableWritableDatabase
from powerapi.database.exception import ConnectionFailed, ReadFailed, WriteFailed
from powerapi.report import Report
from .codecs import ReportEncoders, ReportDecoders

try:
    from pymongo import MongoClient
    from pymongo.errors import PyMongoError
except ImportError:
    MongoClient = None
    PyMongoError = None


class MongoDB(DatabaseDriver, ReadableWritableDatabase):
    """
    MongoDB database driver.
    Allow to persist and retrieve reports to/from a MongoDB database.
    """

    def __init__(self, report_type: type[Report], uri: str, db_name: str, collection_name: str):
        """
        :param report_type: Type of the report handled by this database
        :param uri: URI of the MongoDB server
        :param db_name: Database name
        :param collection_name: Collection name
        """
        super().__init__()

        self._client = MongoClient(uri, connect=False)
        self._collection = self._client[db_name][collection_name]

        self._report_encoder = ReportEncoders.get(report_type)
        self._report_decoder = ReportDecoders.get(report_type)

    def connect(self):
        """
        Connect to the MongoDB server.
        :raise: ConnectionFailed if the connection to the MongoDB server fails.
        """
        try:
            # The client will establish a connection on the first operation.
            self._client.admin.command('ping')
        except PyMongoError as exn:
            raise ConnectionFailed(f'Failed to connect to the MongoDB server: {exn}') from exn

    def disconnect(self):
        """
        Disconnect from the MongoDB database.
        """
        self._client.close()

    @staticmethod
    def supported_read_types() -> Iterable[type[Report]]:
        """
        Return the report types that can be retrieved from the MongoDB database.
        :return: Iterable of report types
        """
        return ReportDecoders.supported_types()

    def _reports_generator(self) -> Iterable[Report]:
        """
        Return a generator that yields reports from the database.
        This operation **is not** destructive, the reports are kept in the database.
        :return: Iterable of reports
        """
        cursor = self._collection.find({})
        return (self._report_decoder.decode(report) for report in cursor)

    def _streaming_reports_generator(self) -> Iterable[Report]:
        """
        Return a generator that yields reports from the database.
        This operation **is** destructive, the reports will be removed from the database.
        :return: Iterable of reports
        """
        while True:
            report = self._collection.find_one_and_delete({})
            if report is None:
                break
            yield self._report_decoder.decode(report)

    def read(self, stream_mode: bool = False) -> Iterable[Report]:
        """
        Read reports from the MongoDB database.
        :param stream_mode: If true, handle the reports as a continuous stream of data (**destructive**)
        :return: Iterable of reports
        :raise: ReadFailed if the read operation fails
        """
        try:
            return self._streaming_reports_generator() if stream_mode else self._reports_generator()
        except PyMongoError as exn:
            raise ReadFailed(f'Failed to retrieve reports from the MongoDB database: {exn}') from exn

    @staticmethod
    def supported_write_types() -> Iterable[type[Report]]:
        """
        Return the report types that can be persisted to the MongoDB database.
        :return: Iterable of report types
        """
        return ReportEncoders.supported_types()

    def write(self, reports: Iterable[Report]) -> None:
        """
        Write the reports into the MongoDB database.
        :param reports: Iterable of reports
        :raise: WriteFailed if the write operation fails
        """
        try:
            encoded_reports = [self._report_encoder.encode(report) for report in reports]
            self._collection.insert_many(encoded_reports)
        except PyMongoError as exn:
            raise WriteFailed(f'Failed to write to the MongoDB database: {exn}') from exn
