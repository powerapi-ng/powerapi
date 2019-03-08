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
Test to interrupt the whole architecure after a crash that could hang the system

Architecture :
  - 1 puller (connected to MongoDB1 [collection test_hwrep], stream mode on)
  - 1 dispatcher (HWPC dispatch rule (dispatch by ROOT)
  - 1 RAPL Formula
  - 1 pusher (connected to MongoDB1 [collection test_result]

MongoDB1 content:
  - 1 HWPC Report


Scenario:
  - Launch the full architecture in a sub process
  - send a SIGKILL signal to the dispatcher to crash it
  - send a SIGTERM signal to the architecture process

Test if:
  - if the architecture process was terminated
"""
import logging
import time
import signal
import os
import pytest

from multiprocessing import Process

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
from powerapi.report import create_report_root


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
def main_process():
    p = MainProcess()
    p.start()
    time.sleep(1)
    yield p
    try:
        os.kill(p.pid, signal.SIGKILL)
    except Exception:
        pass

class MainProcess(Process):
    """
    Process that run the global architecture and crash the dispatcher
    """
    def __init__(self):
        Process.__init__(self, name='test_crash_dispatcher')

    def run(self):
        # Setup signal handler
        def term_handler(_, __):
            puller.send_kill()
            dispatcher.send_kill()
            pusher.send_kill()
            exit(0)

        signal.signal(signal.SIGTERM, term_handler)
        signal.signal(signal.SIGINT, term_handler)

        stream_mode = True
        supervisor = BackendSupervisor(stream_mode)

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
            getattr(HWPCDepthLevel, 'ROOT'), primary=True))

        dispatcher = DispatcherActor('dispatcher', formula_factory, route_table,
                                     level_logger=LOG_LEVEL)

        # Puller
        input_mongodb = MongoDB(DB_URI,
                                'MongoDB1', 'test_hwrep',
                                HWPCModel(), stream_mode=stream_mode)
        report_filter = Filter()
        report_filter.filter(lambda msg: True, dispatcher)
        puller = PullerActor("puller_mongodb", input_mongodb,
                             report_filter, level_logger=LOG_LEVEL)

        supervisor.launch_actor(pusher)
        supervisor.launch_actor(dispatcher)
        supervisor.launch_actor(puller)
        time.sleep(1)

        os.kill(dispatcher.pid, signal.SIGKILL)

        supervisor.join()


def test_crash_dispatcher(database, main_process):
    if main_process.is_alive():
        os.kill(main_process.pid, signal.SIGTERM)
        main_process.join(5)
        assert not is_actor_alive(main_process)

    assert True
