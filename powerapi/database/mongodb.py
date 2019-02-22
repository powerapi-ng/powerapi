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
                 host_name, port, db_name, collection_name, report_model,
                 erase=False):
        """
        :param str host_name:       hostname of the mongodb (ex: "localhost")

        :param int port:            port of the mongodb (ex: 27017)

        :param str db_name:         database name in the mongodb
                                    (ex: "powerapi")

        :param str collection_name: collection name in the mongodb
                                    (ex: "sensor")

        :param report_model:        XXXModel object. Allow to read specific
                                    report with a specific format in a database
        :type report_model:         powerapi.ReportModel

        :param bool erase:          If save_mode is False, erase too. It allows
                                    to erase the collection on setup.
        """
        BaseDB.__init__(self, report_model)

        #: (str): Hostname of the mongodb server
        self.host_name = host_name

        #: (int): Port of the mongodb server
        self.port = port

        #: (str): Database name in the mongodb
        self.db_name = db_name

        #: (str): Collection name in the mongodb
        self.collection_name = collection_name

        #: (bool): If save_mode is False, erase has no effect.
        #: It allows to erase the collection on setup.
        self.erase = False

        #: (pymongo.MongoClient): MongoClient instance of the server
        self.mongo_client = None

        #: (pymongo.MongoClient): MongoClient pointed to the
        #: targeted collection
        self.collection = None

        #: (pymongo.Cursor): Cursor which return data
        self.cursor = None

        # (bool): Define if the mongodb is capped or not
        self.capped = False

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

        self.mongo_client = pymongo.MongoClient(self.host_name, self.port,
                                                serverSelectionTimeoutMS=5)

        self.collection = self.mongo_client[self.db_name][
            self.collection_name]

        # Check if hostname:port work
        try:
            self.mongo_client.admin.command('ismaster')
        except pymongo.errors.ServerSelectionTimeoutError:
            raise MongoBadDBError(self.host_name + ':' + str(self.port))

        # Check if collection is capped or not
        options = self.collection.options()
        self.capped = bool(('capped' in options and
                            options['capped']))

        # If collection exist and erase is True
        if (self.erase and
                self.db_name in self.mongo_client.list_database_names() and
                self.collection_name in self.mongo_client[
                    self.db_name].list_collection_names()):
            self.collection.drop()

    def __iter__(self):
        """
        Create the iterator for get the data
        """
        # Depend if capped or not, create cursor
        if self.capped:
            self.cursor = self.collection.find(
                cursor_type=pymongo.CursorType.TAILABLE_AWAIT)
        else:
            self.cursor = self.collection.find({})
        return self

    def __next__(self):
        """
        Allow to get the next data
        """
        try:
            json = self.cursor.next()
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
