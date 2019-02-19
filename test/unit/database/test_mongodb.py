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

from powerapi.report_model import HWPCModel
from powerapi.database import MongoDB, MongoBadDBError

from test.unit.database.mongo_utils import gen_base_test_unit_mongo
from test.unit.database.mongo_utils import clean_base_test_unit_mongo

HOSTNAME = "localhost"
PORT = 27017


@pytest.fixture
def database():
    """
    setup : init and fill the database with data
    teardown : drop collection loaded in database
    """
    gen_base_test_unit_mongo(HOSTNAME, PORT)
    yield
    clean_base_test_unit_mongo(HOSTNAME, PORT)


def test_mongodb_bad_hostname(database):
    """
    Test if the database doesn't exist (hostname/port error)
    """
    with pytest.raises(MongoBadDBError) as pytest_wrapped:
        MongoDB("lel", PORT, "error", "error",
                HWPCModel()).load()
    assert pytest_wrapped.type == MongoBadDBError


def test_mongodb_bad_port(database):
    """
    Test if the database doesn't exist (hostname/port error)
    """
    with pytest.raises(MongoBadDBError) as pytest_wrapped:
        MongoDB(HOSTNAME, 1, "error", "error",
                HWPCModel()).load()
    assert pytest_wrapped.type == MongoBadDBError


def test_mongodb_read_basic_db(database):
    """
    Test read mongodb collection
    """
    # Load DB
    mongodb = MongoDB(HOSTNAME, PORT, "test_mongodb",
                      "test_mongodb1", HWPCModel())

    # Check if we can reload after reading
    for _ in range(2):
        mongodb.load()

        for _ in range(10):
            assert mongodb.get_next() is not None

    # Check if there is nothing after
    assert mongodb.get_next() is None


def test_mongodb_read_capped_db(database):
    """
    Test read mongodb capped collection
    """
    # Load DB
    mongodb = MongoDB(HOSTNAME, PORT, "test_mongodb",
                      "test_mongodb2", HWPCModel())

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


def test_mongodb_save_basic_db(database):
    """
    Test save mongodb collection
    """
    # Load DB
    mongodb = MongoDB(HOSTNAME, PORT, "test_mongodb",
                      "test_mongodb3", HWPCModel())

    mongodb.load()

    # Check if save work
    basic_count = mongodb.collection.count_documents({})
    for _ in range(2):
        mongodb.save({'test': 'json'})
    assert mongodb.collection.count_documents({}) == basic_count + 2
