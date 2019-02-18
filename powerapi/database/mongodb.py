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


class MongoBadDBNameError(DBError):
    """
    Error raised when database doesn't exist
    """
    def __init__(self, db_name):
        DBError.__init__(self, 'Mongo DB error : DB ' + db_name +
                         ' doesn\'t exist')


class MongoBadCollectionNameError(DBError):
    """
    Error raised when collection doesn't exist
    """
    def __init__(self, collection_name):
        DBError.__init__(self, 'Mongo DB error : collection ' +
                         collection_name + ' doesn\'t exist')


class MongoNeedReportModelError(Error):
    """
    Error raised when MongoDB is define without report model
    """


class MongoSaveInReadModeError(Error):
    """
    Error raised when save() is called in read mode
    """


class MongoGetNextInSaveModeError(Error):
    """
    Error raised when get_next() is called in save_mode
    """


class MongoDB(BaseDB):
    """
    MongoDB class herited from BaseDB

    Allow to handle a MongoDB database in reading or writing.
    """

    def __init__(self,
                 host_name, port, db_name, collection_name,
                 report_model=None, save_mode=False, erase=False):
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

        :param bool save_mode:      put save_mode to True if you want to use it
                                    with a Pusher

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

        #: (bool): True if you want to save data,
        #: False if you want to read data
        self.save_mode = save_mode

        #: (bool): If save_mode is False, erase has no effect.
        #: It allows to erase the collection on setup.
        self.erase = erase

        # If save_mode is False, erase too.
        if not self.save_mode:
            self.erase = False
            if report_model is None:
                raise MongoNeedReportModelError("Mongo need a report model.")

        #: (pymongo.MongoClient): MongoClient instance of the server
        self.mongo_client = None

        #: (pymongo.MongoClient): MongoClient pointed to the
        #: targeted collection
        self.collection = None

        #: (pymongo.Cursor): Cursor which return data
        self.cursor = None

        # (bool): Define if the mongodb is capped or not
        self.capped = False

    def load(self):
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

        if not self.save_mode:
            # Check if database exist
            if self.db_name not in self.mongo_client.list_database_names():
                raise MongoBadDBNameError(self.db_name)

            # Check if collection exist
            if self.collection_name not in self.mongo_client[
                    self.db_name].list_collection_names():
                raise MongoBadCollectionNameError(self.collection_name)

            # Check if collection is capped or not
            options = self.collection.options()
            self.capped = bool(('capped' in options and
                                options['capped']))

            # Depend if capped or not, create cursor
            if self.capped:
                self.cursor = self.collection.find(
                    cursor_type=pymongo.CursorType.TAILABLE_AWAIT)
            else:
                self.cursor = self.collection.find({})
        # Else if collection exist and erase is True
        elif (self.erase and
              self.db_name in self.mongo_client.list_database_names() and
              self.collection_name in self.mongo_client[
                  self.db_name].list_collection_names()):
            self.collection.drop()

    def get_next(self):
        """
        Override from BaseDB.

        Make one iteration on the cursor, remove the '_id' field and
        return the data JSON.

        :return: The next report
        :rtype: formatted JSON
        """
        if self.save_mode:
            raise MongoGetNextInSaveModeError("get_next can't be used.")

        try:
            json = self.cursor.next()
        except StopIteration:
            return None

        # Re arrange the json before return it by removing '_id' field
        json.pop('_id', None)

        return self.report_model.from_mongodb(json)

    def save(self, json):
        """
        Override from BaseDB

        :param dict json: data JSON to save
        """
        if not self.save_mode:
            raise MongoSaveInReadModeError("save can't be used.")

        # TODO: Check if json is valid with the report_model
        self.collection.insert_one(json)
