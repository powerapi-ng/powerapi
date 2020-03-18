# Copyright (c) 2018, INRIA
# Copyright (c) 2018, University of Lille
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
import logging
import time
import pytest
import pymongo

from powerapi.database import MongoDB
from powerapi.pusher import PusherActor
from powerapi.backendsupervisor import BackendSupervisor
from powerapi.formula import DummyFormulaActor
from powerapi.dispatch_rule import HWPCDispatchRule, HWPCDepthLevel
from powerapi.filter import Filter
from powerapi.puller import PullerActor
from powerapi.report import HWPCReport
from powerapi.report_model import HWPCModel, PowerModel
from powerapi.dispatcher import DispatcherActor, RouteTable


from tests.mongo_utils import gen_base_db_test
from tests.mongo_utils import clean_base_db_test

DB_URI = "mongodb://localhost:27017/"
LOG_LEVEL = logging.NOTSET


@pytest.fixture
def database():
    db = gen_base_db_test(DB_URI, 3000)
    yield db
    clean_base_db_test(DB_URI)

@pytest.fixture
def database2():
    db = gen_base_db_test(DB_URI, 30)
    yield db
    clean_base_db_test(DB_URI)

@pytest.fixture
def supervisor():
    s = BackendSupervisor(False)
    yield s
    s.kill_actors()


def get_number_of_output_reports():
    mongo = pymongo.MongoClient(DB_URI)
    c_output = mongo['MongoDB1']['test_result']

    return c_output.count_documents({})


def test_run(database, supervisor):
    """
    Test the architecture when it has to deal with a lot of data, pulled with a
    hight frequency. Input database contain a lot of data, that will overflow the
    backend. Backend have to handle all of this data and continue to compute data
    and writing them in real time.

    Architecture :
      - 1 puller (connected to MongoDB1 [collection test_hwrep], stream mode off)
      - 1 dispatcher (HWPC dispatch rule (dispatch by SOCKET)
      - 1 Dummy Formula
      - 1 pusher (connected to MongoDB1 [collection test_result]

    MongoDB1 content :
      - 3000 HWPC repport with two socket and one RAPL_EVENT

    Scenario:
      - Launch the full architecture

    Test if:
      - each 50 ms, reports are writen in the output database
    """
    # Pusher
    output_mongodb = MongoDB(DB_URI, 'MongoDB1', 'test_result')
    pusher = PusherActor("pusher_mongodb", PowerModel(), output_mongodb, level_logger=LOG_LEVEL)

    # Formula
    formula_factory = (lambda name, verbose:
                       DummyFormulaActor(name, {'my_pusher': pusher}, level_logger=verbose))

    # Dispatcher
    route_table = RouteTable()
    route_table.dispatch_rule(HWPCReport, HWPCDispatchRule(getattr(HWPCDepthLevel, 'SOCKET'), primary=True))

    dispatcher = DispatcherActor('dispatcher', formula_factory, route_table, level_logger=LOG_LEVEL)

    # Puller
    input_mongodb = MongoDB(DB_URI, 'MongoDB1', 'test_hwrep')
    report_filter = Filter()
    report_filter.filter(lambda msg: True, dispatcher)
    puller = PullerActor("puller_mongodb", input_mongodb, report_filter, HWPCModel(), level_logger=LOG_LEVEL)

    supervisor.launch_actor(pusher)
    supervisor.launch_actor(dispatcher)
    supervisor.launch_actor(puller)


    t = time.time()
    number_of_output_reports = 0
    for i in range(3):
        time.sleep(0.2)
        current = get_number_of_output_reports()
        assert current >= number_of_output_reports
        number_of_output_reports = current

    time.sleep(0.1)
        
    supervisor.join()


def test_with_slow_formula(database2, supervisor):
    """Test the architecture when it has to deal with a lot of data, with a formula
    that is very slow. Input database contain a lot of data, but formula can't
    handle them. The puller will end before formula end to handle data and
    supervisor will begin to send poisonpill message to all actors. Formula and
    pusher must continue to handle report.

    Architecture :
      - 1 puller (connected to MongoDB1 [collection test_hwrep], stream mode off)
      - 1 dispatcher (HWPC dispatch rule (dispatch by SOCKET)
      - 1 Dummy Formula with will wait 0.2 ms when it receive a message
      - 1 pusher (connected to MongoDB1 [collection test_result]

    MongoDB1 content :
      - 30 HWPC repport with two socket and one RAPL_EVENT

    Scenario:
      - Launch the full architecture

    Test if:
      - after powerapi handle all the reports, test if all the reports was handeled
        by the formula and pushed to the mongo database and if no report were lost

    """
    # Pusher
    output_mongodb = MongoDB(DB_URI, 'MongoDB1', 'test_result')
    pusher = PusherActor("pusher_mongodb", PowerModel(), output_mongodb, level_logger=LOG_LEVEL)

    # Formula
    formula_factory = (lambda name, verbose:
                       DummyFormulaActor(name, {'my_pusher': pusher}, level_logger=verbose, sleep_time=0.1))
                       # DummyFormulaActor(name, {'my_pusher': pusher}, level_logger=verbose))

    # Dispatcher
    route_table = RouteTable()
    route_table.dispatch_rule(HWPCReport, HWPCDispatchRule(getattr(HWPCDepthLevel, 'SOCKET'), primary=True))

    dispatcher = DispatcherActor('dispatcher', formula_factory, route_table, level_logger=LOG_LEVEL)

    # Puller
    input_mongodb = MongoDB(DB_URI, 'MongoDB1', 'test_hwrep')
    report_filter = Filter()
    report_filter.filter(lambda msg: True, dispatcher)
    puller = PullerActor("puller_mongodb", input_mongodb, report_filter, HWPCModel(), level_logger=LOG_LEVEL)

    supervisor.launch_actor(pusher)
    supervisor.launch_actor(dispatcher)
    supervisor.launch_actor(puller)

    supervisor.join()

    assert get_number_of_output_reports() == 30 * 2
