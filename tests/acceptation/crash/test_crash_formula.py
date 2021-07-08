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
from powerapi.formula import FormulaValues
from powerapi.supervisor import Supervisor
from powerapi.dispatch_rule import HWPCDispatchRule, HWPCDepthLevel
from powerapi.filter import Filter
from powerapi.puller import PullerActor
from powerapi.report import HWPCReport
from powerapi.report_model import HWPCModel, PowerModel
from powerapi.dispatcher import DispatcherActor, RouteTable
from powerapi.message import DispatcherStartMessage, FormulaStartMessage
from powerapi.cli.tools import PusherGenerator, PullerGenerator
from powerapi.test_utils.actor import shutdown_system, CrashFormula
from powerapi.test_utils.report.hwpc import extract_json_report
from powerapi.test_utils.db.mongo import mongo_database
from powerapi.test_utils.db.mongo import MONGO_URI, MONGO_HWPC_COLLECTION_NAME, MONGO_POWER_COLLECTION_NAME, MONGO_DATABASE_NAME


def filter_rule(msg):
    return True

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
        supervisor = Supervisor()

        # Setup signal handler
        def term_handler(_, __):
            supervisor.kill_actors()

        signal.signal(signal.SIGTERM, term_handler)
        signal.signal(signal.SIGINT, term_handler)

        config = {'verbose': True, 'stream': True,
                  'output': {'mongodb': {'test_pusher': {'model': 'PowerReport', 'name': 'test_pusher', 'uri': MONGO_URI, 'db': MONGO_DATABASE_NAME, 'collection': MONGO_POWER_COLLECTION_NAME}}},
                  'input': {'mongodb': {'test_puller': {'model': 'HWPCReport', 'name': 'test_puller', 'uri': MONGO_URI, 'db': MONGO_DATABASE_NAME, 'collection': MONGO_HWPC_COLLECTION_NAME}}}
                  }

        # Pusher
        pusher_generator = PusherGenerator()
        pusher_info = pusher_generator.generate(config)
        pusher_cls, pusher_start_message = pusher_info['test_pusher']
    
        pusher = supervisor.launch(pusher_cls, pusher_start_message)

        # Dispatcher
        route_table = RouteTable()
        route_table.dispatch_rule(HWPCReport, HWPCDispatchRule(getattr(HWPCDepthLevel, 'SOCKET'), primary=True))
        dispatcher_start_message = DispatcherStartMessage('system', 'dispatcher', CrashFormula, FormulaValues({'test_pusher': pusher}), route_table, 'cpu')
            
        dispatcher = supervisor.launch(DispatcherActor, dispatcher_start_message)

        # Puller
        report_filter = Filter()
        report_filter.filter(filter_rule, dispatcher)
        puller_generator = PullerGenerator(report_filter)
        puller_info = puller_generator.generate(config)
        puller_cls, puller_start_message = puller_info['test_puller']
        puller = supervisor.launch(puller_cls, puller_start_message)


        supervisor.monitor()


def test_crash_dispatcher(main_process, mongo_database, shutdown_system):
    if main_process.is_alive():
        print('toto')
        main_process.join(10)
        assert not main_process.is_alive()

    assert True
