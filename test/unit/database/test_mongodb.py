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

from test.mongo_utils import gen_base_test_unit_mongo
from test.mongo_utils import clean_base_test_unit_mongo

URI = "mongodb://localhost:27017/"

@pytest.fixture
def database():
    """
    setup : init and fill the database with data
    teardown : drop collection loaded in database
    """
    gen_base_test_unit_mongo(URI)
    yield
    clean_base_test_unit_mongo(URI)


def test_mongodb_bad_hostname(database):
    """
    Test if the database doesn't exist (hostname/port error)
    """
    with pytest.raises(MongoBadDBError) as pytest_wrapped:
        MongoDB("mongodb://lel:27017/", "error", "error",
                HWPCModel()).connect()
    assert pytest_wrapped.type == MongoBadDBError


def test_mongodb_bad_port(database):
    """
    Test if the database doesn't exist (hostname/port error)
    """
    with pytest.raises(MongoBadDBError) as pytest_wrapped:
        MongoDB("mongodb://localhost:1", "error", "error",
                HWPCModel()).connect()
    assert pytest_wrapped.type == MongoBadDBError


def test_mongodb_read_basic_db(database):
    """
    Test read mongodb collection
    """
    # Load DB
    mongodb = MongoDB(URI, "test_mongodb",
                      "test_mongodb1", HWPCModel())

    # Check if we can reload after reading
    mongodb.connect()

    for _ in range(2):
        mongodb_iter = iter(mongodb)
        for _ in range(10):
            assert next(mongodb_iter) is not None

        with pytest.raises(StopIteration) as pytest_wrapped:
            next(mongodb_iter)
        assert pytest_wrapped.type == StopIteration


def test_mongodb_read_capped_db(database):
    """
    Test read mongodb capped collection
    """
    # Load DB
    mongodb = MongoDB(URI, "test_mongodb",
                      "test_mongodb2", HWPCModel())

    # Check if we can read one time
    mongodb.connect()
    mongodb_iter = iter(mongodb)

    for _ in range(mongodb.collection.count_documents({})):
        report = next(mongodb_iter)
        assert report is not None

    # Check if there is nothing after
    with pytest.raises(StopIteration) as pytest_wrapped:
        next(mongodb_iter)
    assert pytest_wrapped.type == StopIteration

    # Add data in the collection
    for _ in range(2):
        report.pop('_id', None)
        mongodb.collection.insert_one(report)

    # Check if there is nothing after
    with pytest.raises(StopIteration) as pytest_wrapped:
        next(mongodb_iter)
    assert pytest_wrapped.type == StopIteration


def test_mongodb_save_basic_db(database):
    """
    Test save mongodb collection
    """
    # Load DB
    mongodb = MongoDB(URI, "test_mongodb",
                      "test_mongodb3", HWPCModel())

    mongodb.connect()

    # Check if save work
    basic_count = mongodb.collection.count_documents({})
    for _ in range(2):
        mongodb.save({'test': 'json'})
    assert mongodb.collection.count_documents({}) == basic_count + 2
