"""
Module test db
"""

import os
import pytest

from smartwatts.report_model import HWPCModel
from smartwatts.report import HWPCReport
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
        Test read mongodb collection without unstack the db and
        without reload data
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
        Test read mongodb collection and unstack each data
        without reload data
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
