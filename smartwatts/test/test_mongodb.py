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
from smartwatts.database import MongoNeedReportModelError
from smartwatts.database import MongoSaveInReadModeError
from smartwatts.database import MongoGetNextInSaveModeError


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

    def test_mongodb_without_report_model(self):
        """
        Test if we can create mongodb without report_model
        """
        with pytest.raises(MongoNeedReportModelError) as pytest_wrapped:
            MongoDB(HOSTNAME, 1, "error", "error")
        assert pytest_wrapped.type == MongoNeedReportModelError

    def test_mongodb_bad_db(self):
        """
        Test if the database doesn't exist (hostname/port error)
        """
        with pytest.raises(MongoBadDBError) as pytest_wrapped:
            MongoDB(HOSTNAME, 1, "error", "error",
                    report_model=HWPCModel()).load()
        assert pytest_wrapped.type == MongoBadDBError

    def test_mongodb_bad_db_name(self):
        """
        Test if the database name exist in the Mongodb
        """
        with pytest.raises(MongoBadDBNameError) as pytest_wrapped:
            MongoDB(HOSTNAME, PORT, "error", "error",
                    report_model=HWPCModel()).load()
        assert pytest_wrapped.type == MongoBadDBNameError

    def test_mongodb_bad_collection_name(self):
        """
        Test if the collection name exist in the Mongodb
        """
        with pytest.raises(MongoBadCollectionNameError) as pytest_wrapped:
            MongoDB(HOSTNAME, PORT, "test_mongodb",
                    "error", report_model=HWPCModel()).load()
        assert pytest_wrapped.type == MongoBadCollectionNameError

    def test_mongodb_read_basic_db(self):
        """
        Test read mongodb collection
        """
        # Load DB
        mongodb = MongoDB(HOSTNAME, PORT, "test_mongodb",
                          "test_mongodb1", report_model=HWPCModel())

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
        mongodb = MongoDB(HOSTNAME, PORT, "test_mongodb",
                          "test_mongodb2", report_model=HWPCModel())

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

    def test_mongodb_save_mode_and_erase(self):
        """
        Test save_mode and erase

        save_mode   erase   behaviour
        False       False   can't call save()
        False       True    can't call save(), erase == False
        True        False   can't call get_next(), count_doc > 0
        True        True    can't call get_next(), count_doc == 0
        """
        # basic read mode
        mongodb_ff = MongoDB(HOSTNAME, PORT, "test_mongodb",
                             "test_mongodb3", report_model=HWPCModel())
        mongodb_ff.load()

        with pytest.raises(MongoSaveInReadModeError) as pytest_wrapped:
            mongodb_ff.save(None)
        assert pytest_wrapped.type == MongoSaveInReadModeError

        # basic read mode and try to force erase
        mongodb_ft = MongoDB(HOSTNAME, PORT, "test_mongodb",
                             "test_mongodb3", report_model=HWPCModel(),
                             erase=True)
        mongodb_ft.load()

        with pytest.raises(MongoSaveInReadModeError) as pytest_wrapped:
            mongodb_ft.save(None)
        assert pytest_wrapped.type == MongoSaveInReadModeError
        assert mongodb_ft.erase is False

        # save mode with no erase
        mongodb_tf = MongoDB(HOSTNAME, PORT, "test_mongodb",
                             "test_mongodb3", save_mode=True)
        mongodb_tf.load()
        with pytest.raises(MongoGetNextInSaveModeError) as pytest_wrapped:
            mongodb_tf.get_next()
        assert pytest_wrapped.type == MongoGetNextInSaveModeError
        assert mongodb_tf.collection.count_documents({}) > 0

        # save mode with erase mode
        mongodb_tt = MongoDB(HOSTNAME, PORT, "test_mongodb",
                             "test_mongodb3", save_mode=True, erase=True)
        mongodb_tt.load()
        with pytest.raises(MongoGetNextInSaveModeError) as pytest_wrapped:
            mongodb_tt.get_next()
        assert pytest_wrapped.type == MongoGetNextInSaveModeError
        assert mongodb_tt.collection.count_documents({}) == 0

    def test_mongodb_save_basic_db(self):
        """
        Test save mongodb collection
        """
        # Load DB
        mongodb = MongoDB(HOSTNAME, PORT, "test_mongodb",
                          "test_mongodb3", save_mode=True)

        mongodb.load()

        # Check if save work
        basic_count = mongodb.collection.count_documents({})
        for _ in range(2):
            mongodb.save({'test': 'json'})
        assert mongodb.collection.count_documents({}) == basic_count + 2
