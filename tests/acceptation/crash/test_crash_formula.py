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
"""
Launch the whole architecture, crash the formula with a fatal error and test if the whole architecture is interupted

Architecture :
  - 1 puller (connected to MongoDB1 [collection test_hwrep], stream mode on)
  - 1 dispatcher (HWPC dispatch rule (dispatch by ROOT)
  - 1 Crash Formula
  - 1 pusher (connected to MongoDB1 [collection test_result]

MongoDB1 content:
  - 1 HWPC Report

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
from powerapi.formula import DummyFormulaActor
from powerapi.dispatch_rule import HWPCDispatchRule, HWPCDepthLevel
from powerapi.filter import Filter
from powerapi.puller import PullerActor
from powerapi.report import HWPCReport
from powerapi.report_model import HWPCModel, PowerModel
from powerapi.dispatcher import DispatcherActor, RouteTable


from tests.mongo_utils import gen_base_db_test
from tests.mongo_utils import clean_base_db_test
from tests.utils import is_actor_alive
from tests.utils import CrashFormulaActor

DB_URI = "mongodb://localhost:27017/"
LOG_LEVEL = logging.NOTSET


@pytest.fixture
def database():
    db = gen_base_db_test(DB_URI, 200)
    yield db
    clean_base_db_test(DB_URI)

@pytest.fixture
def main_process():
    p = MainProcess()
    p.start()
    time.sleep(1)
    yield p
    try:
        os.kill(p.pid, signal.SIGTERM)
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
            puller.hard_kill()
            dispatcher.hard_kill()
            pusher.hard_kill()
            exit(0)

        signal.signal(signal.SIGTERM, term_handler)
        signal.signal(signal.SIGINT, term_handler)

        stream_mode = True
        supervisor = BackendSupervisor(stream_mode)

        # Pusher
        output_mongodb = MongoDB(DB_URI, 'MongoDB1', 'test_result')
        pusher = PusherActor("pusher_mongodb", PowerModel(), output_mongodb, level_logger=LOG_LEVEL)


        # Formula
        formula_factory = (lambda name, verbose:
                           CrashFormulaActor(name, {'my_pusher': pusher}, 0, RuntimeError, level_logger=verbose))

        # Dispatcher
        route_table = RouteTable()
        route_table.dispatch_rule(HWPCReport, HWPCDispatchRule(getattr(HWPCDepthLevel, 'ROOT'), primary=True))

        dispatcher = DispatcherActor('dispatcher', formula_factory, route_table,
                                     level_logger=LOG_LEVEL)

        # Puller
        input_mongodb = MongoDB(DB_URI, 'MongoDB1', 'test_hwrep')
        report_filter = Filter()
        report_filter.filter(lambda msg: True, dispatcher)
        puller = PullerActor("puller_mongodb", input_mongodb,
                             report_filter, HWPCModel(), stream_mode=stream_mode, level_logger=LOG_LEVEL)

        time.sleep(2)
        supervisor.launch_actor(pusher)
        supervisor.launch_actor(dispatcher)
        supervisor.launch_actor(puller)
        supervisor.join()


def test_crash_dispatcher(database, main_process):
    if main_process.is_alive():
        main_process.join(100)
        assert not is_actor_alive(main_process)

    assert True
