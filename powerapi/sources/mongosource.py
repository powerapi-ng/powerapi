# Copyright (c) 2022, INRIA
# Copyright (c) 2022, University of Lille
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

# Author : Lauric Desauw
# Last modified : 11 April 2022

##############################
#
# Imports
#
##############################
import pymongo
from typing import Optional
from rx import Observable
from rx.core.typing import Scheduler, Observer
from powerapi.rx.source import BaseSource, Source
from powerapi.exception import SourceException
import powerapi.rx.report as papi_report


class MongoSource(BaseSource):
    def __init__(self, uri: str, db_name: str, collection_name: str) -> None:
        """Creates a source for Mongodb

        Args:
        :param uri: URL of the database
        :param db_name: Name of the database
        :param collection_name: Collection name in the database

        """
        super().__init__()
        self.__name__ = "MongoSource"
        self.uri = uri
        self.db_name = db_name
        self.collection_name = collection_name
        self.cursor = None
        self.mongo_client = pymongo.MongoClient(self.uri, serverSelectionTimeoutMS=5)
        try:
            self.mongo_client.admin.command("ismaster")
        except pymongo.errors.ServerSelectionTimeoutError as exn:
            raise SourceException(self.__name__, "can't connect to source") from exn

        self.collection = self.mongo_client[self.db_name][self.collection_name]

    def subscribe(self, operator: Observer, scheduler: Optional[Scheduler] = None):
        """Required method for retrieving data from a source by a Formula

        Args:
            operator: The operator (e.g. a formula or log)  that will process the data
            scheduler: Used for parallelism. Not used for the time being

        """
        try:
            self.cursor = self.collection.find({})
        except Exception as exn:
            raise SourceException(self.__name__, "can't subscribe") from exn

        while True:
            report_dic = self.cursor.next()
            report = papi_report.create_report_from_dict(report_dic)

            operator.on_next(report)

    def close(self):
        """Closes the access to the Mongodb"""
        self.mongo_client.close()
