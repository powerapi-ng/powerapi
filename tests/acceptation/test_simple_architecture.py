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

"""
Test the behaviour of the most simple architecture

Architecture :
  - 1 puller (connected to MongoDB1 [collection test_hwrep], stream mode off)
  - 1 dispatcher (HWPC dispatch rule (dispatch by SOCKET)
  - 1 Dummy Formula
  - 1 pusher (connected to MongoDB1 [collection test_result]

MongoDB1 content:
  - 10 HWPC Report with two sockets and one RAPL_EVENT


Scenario:
  - Launch the full architecture

Test if: 
  - each HWPCReport in the intput database was converted in one PowerReport per
    socket in the output database
"""
import logging
import pytest
import pymongo

from powerapi.database import MongoDB
from powerapi.pusher import PusherActor
from powerapi.backendsupervisor import BackendSupervisor
from powerapi.formula import DummyFormulaActor
from powerapi.dispatch_rule import HWPCDispatchRule, HWPCDepthLevel
from powerapi.filter import Filter
from powerapi.puller import PullerActor
from powerapi.report import HWPCReport, PowerReport
from powerapi.report_model import HWPCModel
from powerapi.dispatcher import DispatcherActor, RouteTable


from tests.mongo_utils import gen_base_db_test
from tests.mongo_utils import clean_base_db_test

DB_URI = "mongodb://localhost:27017/"
LOG_LEVEL = logging.NOTSET


@pytest.fixture
def database():
    db = gen_base_db_test(DB_URI, 10)
    yield db
    clean_base_db_test(DB_URI)

@pytest.fixture
def supervisor():
    s = BackendSupervisor(False)
    yield s
    s.kill_actors()


def check_db():
    mongo = pymongo.MongoClient(DB_URI)
    c_input = mongo['MongoDB1']['test_hwrep']
    c_output = mongo['MongoDB1']['test_result']

    assert c_output.count_documents({}) == c_input.count_documents({}) * 2

    for report in c_input.find():

        assert c_output.count_documents(
            {'timestamp': report['timestamp'], 'sensor': report['sensor'],
             'target': report['target']}) == 2

def test_run(database, supervisor):
    # Pusher
    output_mongodb = MongoDB(DB_URI,
                             'MongoDB1', 'test_result',
                             HWPCModel())
    pusher = PusherActor("pusher_mongodb", PowerReport, output_mongodb,
                         level_logger=LOG_LEVEL)

    # Formula
    formula_factory = (lambda name, verbose:
                       DummyFormulaActor(name, [pusher], level_logger=verbose))

    # Dispatcher
    route_table = RouteTable()
    route_table.dispatch_rule(HWPCReport, HWPCDispatchRule(
        getattr(HWPCDepthLevel, 'SOCKET'), primary=True))

    dispatcher = DispatcherActor('dispatcher', formula_factory, route_table,
                                 level_logger=LOG_LEVEL)

    # Puller
    input_mongodb = MongoDB(DB_URI,
                            'MongoDB1', 'test_hwrep',
                            HWPCModel())
    report_filter = Filter()
    report_filter.filter(lambda msg: True, dispatcher)
    puller = PullerActor("puller_mongodb", input_mongodb,
                         report_filter, level_logger=LOG_LEVEL)

    supervisor.launch_actor(pusher)
    supervisor.launch_actor(dispatcher)
    supervisor.launch_actor(puller)

    supervisor.join()

    check_db()
