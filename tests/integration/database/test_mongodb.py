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
from powerapi.report import create_socket_report, create_report_root, create_group_report, create_core_report
from powerapi.database import MongoDB, MongoBadDBError

from tests.mongo_utils import gen_base_test_unit_mongo
from tests.mongo_utils import clean_base_test_unit_mongo

URI = "mongodb://localhost:27017/"
CPT = 1

###################
# Report Creation #
###################


def gen_power_report():
    global CPT
    CPT += 1
    return PowerReport(CPT, "sensor", "target", 0, 0.11, {"metadata1": "truc", "metadata2": "oui"})


def gen_hwpc_report():
    """
    Return a well formated HWPCReport
    """
    cpua = create_core_report('1', 'e0', '0')
    cpub = create_core_report('2', 'e0', '1')
    cpuc = create_core_report('1', 'e0', '2')
    cpud = create_core_report('2', 'e0', '3')
    cpue = create_core_report('1', 'e1', '0')
    cpuf = create_core_report('2', 'e1', '1')
    cpug = create_core_report('1', 'e1', '2')
    cpuh = create_core_report('2', 'e1', '3')

    socketa = create_socket_report('1', [cpua, cpub])
    socketb = create_socket_report('2', [cpuc, cpud])
    socketc = create_socket_report('1', [cpue, cpuf])
    socketd = create_socket_report('2', [cpug, cpuh])

    groupa = create_group_report('1', [socketa, socketb])
    groupb = create_group_report('2', [socketc, socketd])

    return create_report_root([groupa, groupb])


###################
#     Fixture     #
###################

@pytest.fixture
def database():
    """
    setup : init and fill the database with data
    teardown : drop collection loaded in database
    """
    gen_base_test_unit_mongo(URI)
    yield
    clean_base_test_unit_mongo(URI)

###################
#      Tests      #
###################

def test_mongodb_bad_hostname(database):
    """
    Test if the database doesn't exist (hostname/port error)
    """
    with pytest.raises(MongoBadDBError) as pytest_wrapped:
        MongoDB("mongodb://lel:27017/", "error", "error").connect()
    assert pytest_wrapped.type == MongoBadDBError


def test_mongodb_bad_port(database):
    """
    Test if the database doesn't exist (hostname/port error)
    """
    with pytest.raises(MongoBadDBError) as pytest_wrapped:
        MongoDB("mongodb://localhost:1", "error", "error").connect()
    assert pytest_wrapped.type == MongoBadDBError


def test_mongodb_read_basic_db(database):
    """
    Test read mongodb collection
    """
    # Load DB
    mongodb = MongoDB(URI, "test_mongodb", "test_mongodb1")

    # Check if we can reload after reading
    mongodb.connect()

    for _ in range(2):
        mongodb_iter = mongodb.iter(HWPCModel(), False)
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
    mongodb = MongoDB(URI, "test_mongodb", "test_mongodb2")

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


def test_mongodb_save_basic_db(database):
    """
    Test save mongodb collection
    """
    # Load DB
    mongodb = MongoDB(URI, "test_mongodb", "test_mongodb3")

    mongodb.connect()

    # Check if save work
    basic_count = mongodb.collection.count_documents({})
    for _ in range(2):
        mongodb.save(gen_hwpc_report(), HWPCModel())
    assert mongodb.collection.count_documents({}) == basic_count + 2


def test_mongodb_all_reports(database):
    """
    Test create/save/read all kind of reports
    """
    all_reports = [(HWPCModel(), gen_hwpc_report),
                   (PowerModel(), gen_power_report)]

    for model, generator in all_reports:
        # Load DB
        mongodb = MongoDB(URI, "test_reports"+model.get_type().__name__,
                          "test_reports"+model.get_type().__name__)
        mongodb.connect()

        # Create report
        report = generator()

        # Save report
        mongodb.save(report, model)

        # Read report
        mongodb_iter = mongodb.iter(model, False)
        read_report = next(mongodb_iter)

        # Compare
        assert read_report == report
