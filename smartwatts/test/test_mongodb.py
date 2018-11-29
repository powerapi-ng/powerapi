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

"""
Module test db
"""

import pytest

from smartwatts.report_model import HWPCModel
from smartwatts.database import MongoDB, MongoBadDBError
from smartwatts.database import MongoBadDBNameError
from smartwatts.database import MongoBadCollectionNameError


HOSTNAME = "localhost"
PORT = 27017


class TestMongoDB():
    """
    Test class of MongoDB class

    If you want to pass all test, you have to run a mongo server
    with the following configuration:
        @hostname: HOSTNAME
        @port:     PORT
    """

    def test_mongodb_bad_db(self):
        """
        Test if the database doesn't exist (hostname/port error)
        """
        with pytest.raises(MongoBadDBError) as pytest_wrapped:
            MongoDB(HWPCModel(), HOSTNAME, 1, "error", "error").load()
        assert pytest_wrapped.type == MongoBadDBError

    def test_mongodb_bad_db_name(self):
        """
        Test if the database name exist in the Mongodb
        """
        with pytest.raises(MongoBadDBNameError) as pytest_wrapped:
            MongoDB(HWPCModel(), HOSTNAME, PORT, "error", "error").load()
        assert pytest_wrapped.type == MongoBadDBNameError

    def test_mongodb_bad_collection_name(self):
        """
        Test if the collection name exist in the Mongodb
        """
        with pytest.raises(MongoBadCollectionNameError) as pytest_wrapped:
            MongoDB(HWPCModel(), HOSTNAME, PORT, "test_mongodb",
                    "error").load()
        assert pytest_wrapped.type == MongoBadCollectionNameError

    def test_mongodb_read_basic_db(self):
        """
        Test read mongodb collection
        """
        # Load DB
        mongodb = MongoDB(HWPCModel(), HOSTNAME, PORT, "test_mongodb",
                          "test_mongodb1")

        # Check if we can reload after reading
        for _ in range(2):
            mongodb.load()

            for _ in range(10):
                assert mongodb.get_next() is not None

        # Check if there is nothing after
        assert mongodb.get_next() is None

    def test_mongodb_read_capped_db(self):
        """
        Test read mongodb capped collection
        """
        # Load DB
        mongodb = MongoDB(HWPCModel(), HOSTNAME, PORT, "test_mongodb",
                          "test_mongodb2")

        # Check if we can read one time
        mongodb.load()

        for _ in range(mongodb.collection.count_documents({})):
            report = mongodb.get_next()
            assert report is not None

        # Check if there is nothing after
        assert mongodb.get_next() is None

        # Add data in the collection
        for _ in range(2):
            report.pop('_id', None)
            mongodb.collection.insert_one(report)

        # Check if we can read it
        for _ in range(2):
            report = mongodb.get_next()
            assert report is not None

        # Check if there is nothing after
        assert mongodb.get_next() is None

    def test_mongodb_save_basic_db(self):
        """
        Test save mongodb collection
        """
        # Load DB
        mongodb = MongoDB(None, HOSTNAME, PORT, "test_mongodb",
                          "testmongodbsave", save_mode=True)

        mongodb.load()

        # Check if save work
        basic_count = mongodb.collection.count_documents({})
        mongodb.save({'test': 'json'})
        assert mongodb.collection.count_documents({}) == basic_count + 1
