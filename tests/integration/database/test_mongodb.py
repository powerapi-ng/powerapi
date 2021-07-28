"""
Copyright (c) 2018, INRIA
Copyright (c) 2018, University of Lille
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import pytest

from powerapi.report_model import HWPCModel, PowerModel
from powerapi.report import PowerReport, HWPCReport
from powerapi.database import MongoDB, MongoBadDBError

from powerapi.test_utils.db.mongo import mongo_database, MONGO_URI, MONGO_DATABASE_NAME, MONGO_INPUT_COLLECTION_NAME
from powerapi.test_utils.report.hwpc import gen_HWPCReports, extract_rapl_reports_with_2_sockets

@pytest.fixture
def mongodb_content():
    return extract_rapl_reports_with_2_sockets(10)


###################
#      Tests      #
###################

def test_mongodb_bad_hostname(mongo_database):
    """
    Test if the database doesn't exist (hostname/port error)
    """
    with pytest.raises(MongoBadDBError) as pytest_wrapped:
        MongoDB("mongodb://lel:27017/", "error", "error").connect()
    assert pytest_wrapped.type == MongoBadDBError


def test_mongodb_bad_port(mongo_database):
    """
    Test if the database doesn't exist (hostname/port error)
    """
    with pytest.raises(MongoBadDBError) as pytest_wrapped:
        MongoDB("mongodb://localhost:1", "error", "error").connect()
    assert pytest_wrapped.type == MongoBadDBError


def test_mongodb_read_basic_db(mongo_database):
    """
    Test read mongodb collection
    """
    # Load DB
    mongodb = MongoDB(MONGO_URI, MONGO_DATABASE_NAME, MONGO_INPUT_COLLECTION_NAME)

    # Check if we can reload after reading
    mongodb.connect()

    for _ in range(2):
        mongodb_iter = mongodb.iter(HWPCModel(), False)
        for _ in range(10):
            assert next(mongodb_iter) is not None

        with pytest.raises(StopIteration) as pytest_wrapped:
            next(mongodb_iter)
        assert pytest_wrapped.type == StopIteration


def test_mongodb_read_capped_db(mongo_database):
    """
    Test read mongodb capped collection
    """
    # Load DB
    mongodb = MongoDB(MONGO_URI, MONGO_DATABASE_NAME, MONGO_INPUT_COLLECTION_NAME)

    # Check if we can read one time
    mongodb.connect()
    mongodb_iter = mongodb.iter(HWPCModel(), False)

    report = None
    for _ in range(mongodb.collection.count_documents({})):
        report = next(mongodb_iter)
        assert report is not None

    # Check if there is nothing after
    with pytest.raises(StopIteration) as pytest_wrapped:
        next(mongodb_iter)
    assert pytest_wrapped.type == StopIteration

    # Add data in the collection
    for _ in range(1):
        mongodb.save(report, HWPCModel())

    # Check if there is nothing after
    with pytest.raises(StopIteration) as pytest_wrapped:
        next(mongodb_iter)
    assert pytest_wrapped.type == StopIteration


def test_mongodb_save_basic_db(mongo_database):
    """
    Test save mongodb collection
    """
    # Load DB
    mongodb = MongoDB(MONGO_URI, MONGO_DATABASE_NAME, MONGO_INPUT_COLLECTION_NAME)

    mongodb.connect()

    # Check if save work
    basic_count = mongodb.collection.count_documents({})
    for report in gen_HWPCReports(2):
        mongodb.save(report, HWPCModel())
    assert mongodb.collection.count_documents({}) == basic_count + 2
