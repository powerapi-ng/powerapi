"""
Module test db
"""

import os
import pytest

from smartwatts.report_model import HWPCModel
from smartwatts.database import MongoDB, MongoBadDBError
from smartwatts.database import MongoBadDBNameError
from smartwatts.database import MongoBadCollectionNameError

PATH_TO_TEST = "/smartwatts/test/"


class TestMongoDB():
    """
    Test class of MongoDB class

    If you want to pass all test, you have to run a mongo server
    with the following configuration:
        @hostname:        localhost
        @port:            27017
        @db-name:         smartwatts
    """

    def test_mongodb_bad_db(self):
        """
        Test if the database doesn't exist (hostname/port error)
        """
        with pytest.raises(MongoBadDBError) as pytest_wrapped:
            MongoDB(HWPCModel(), "localhost", 1, "error", "error").load()
        assert pytest_wrapped.type == MongoBadDBError

    def test_mongodb_bad_db_name(self):
        """
        Test if the database name exist in the Mongodb
        """
        with pytest.raises(MongoBadDBNameError) as pytest_wrapped:
            MongoDB(HWPCModel(), "localhost", 27017, "error", "error").load()
        assert pytest_wrapped.type == MongoBadDBNameError

    def test_mongodb_bad_collection_name(self):
        """
        Test if the collection name exist in the Mongodb
        """
        with pytest.raises(MongoBadCollectionNameError) as pytest_wrapped:
            MongoDB(HWPCModel(), "localhost", 27017, "smartwatts",
                    "error").load()
        assert pytest_wrapped.type == MongoBadCollectionNameError
