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
Test the behaviour of the most simple architecture

Architecture :
  - 1 puller (connected to MongoDB1 [collection test_hwrep], stream mode off)
  - 1 dispatcher (HWPC dispatch rule (dispatch by SOCKET)
  - 1 RAPL Formula
  - 1 pusher (connected to MongoDB1 [collection test_result]

MongoDB1 content:
  - 10 HWPC Report with two sockets and one RAPL_EVENT


Scenario:
  - Launch the full architecture

Test if: 
  - each HWPCReport in the intput database was converted in one PowerReport per
    socket in the output database
  - if the energy consumption was computed correctly using the following
    formula : math.ldexp(RAPL_EVENT, -32)

"""
import logging
import math
import pytest
import pymongo

from powerapi.database import MongoDB
from powerapi.pusher import PusherActor
from powerapi.backendsupervisor import BackendSupervisor
from powerapi.formula import RAPLFormulaActor
from powerapi.dispatch_rule import HWPCDispatchRule, HWPCDepthLevel
from powerapi.filter import Filter
from powerapi.puller import PullerActor
from powerapi.report import HWPCReport, PowerReport
from powerapi.report_model import HWPCModel
from powerapi.dispatcher import DispatcherActor, RouteTable


from test.mongo_utils import gen_base_db_test
from test.mongo_utils import clean_base_db_test
from test.utils import is_actor_alive

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

        for power_report in c_output.find({'timestamp': report['timestamp'],
                                          'sensor': report['sensor'],
                                          'target': report['target']}):

            rapl_event = report['groups']['rapl']['0']['0']['RAPL_EVENT']
            assert power_report['power'] == math.ldexp(rapl_event, -32)


def test_crash_dispatcher(database, supervisor):
    # Pusher
    output_mongodb = MongoDB(DB_URI,
                             'MongoDB1', 'test_result',
                             HWPCModel())
    pusher = PusherActor("pusher_mongodb", PowerReport, output_mongodb,
                         level_logger=LOG_LEVEL)

    # Formula
    formula_factory = (lambda name, verbose:
                       RAPLFormulaActor(name, pusher, level_logger=verbose))

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
