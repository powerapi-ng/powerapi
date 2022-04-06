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

# author : Lauric Desauw
# Last modified : 6 April 2022


import pymongo
from powerapi.rx import Destination
from powerapi.exception import DestinationException


class MongoDestination(Destination):
    """Observer Class for storing reports produced by an observable in a mongo database"""

    def __init__(self, uri: str, db_name: str, collection_name: str) -> None:
        """Create a connection to the DB

        Args:
        uri : URI of the mongo server
        db_name : name of the database in mongo
        collection_name : name of the collection in mongo
        """
        super().__init__()
        self.__name__ = "MongoDestination"
        self.uri = uri
        self.db_name = db_name
        self.collection_name = collection_name
        print(uri, db_name, collection_name)
        self.mongo_client = pymongo.MongoClient(self.uri, serverSelectionTimeoutMS=5)

        # Check if hostname:port work
        try:
            self.mongo_client.admin.command("ismaster")
        except pymongo.errors.ServerSelectionTimeoutError as exn:
            raise DestinationException(self.__name__, "can't connect to DB") from exn

        self.collection = self.mongo_client[self.db_name][self.collection_name]

    def store_report(self, report):
        """Required method for storing a report

        Args:
            report: The report that will be stored
        """

        r = report.to_dict()
        self.collection.insert_one(r)

    def on_completed(self) -> None:
        """This method is called when the source finished"""
        self.mongo_client.close()

    def on_error(self, err) -> None:
        """This method is called when the source has an error"""
        self.mongo_client.close()
        raise DestinationException(self.__name__, " : catched exception") from err
