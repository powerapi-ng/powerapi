# Copyright (c) 2021, INRIA
# Copyright (c) 2021, University of Lille
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
Launch an architecture with stream mode on and send it a sigterm signal

Architecture :
  - 1 puller (connected to a database containing 10 hwpc-report, stream mode on)
  - 1 dispatcher (HWPC dispatch rule (dispatch by SOCKET)
  - 1 Dummy Formula
  - 1 pusher (connected to a database)

database content:
  - 10 HWPC Report with two sockets and one RAPL_EVENT

Scenario:
  - Launch the full architecture

Test if:
  - all actors are killed after the signal was sent
"""
import logging
import signal
import os
import subprocess
import time
from datetime import datetime
from multiprocessing import Process

import pytest
import pymongo

from powerapi.database import MongoDB
from powerapi.pusher import PusherActor
from powerapi.formula.dummy import DummyFormulaActor, DummyFormulaValues
from powerapi.supervisor import Supervisor
from powerapi.dispatch_rule import HWPCDispatchRule, HWPCDepthLevel
from powerapi.filter import Filter
from powerapi.puller import PullerActor
from powerapi.report import HWPCReport
from powerapi.dispatcher import DispatcherActor, RouteTable
from powerapi.message import DispatcherStartMessage, FormulaStartMessage
from powerapi.cli.tools import PusherGenerator, PullerGenerator
from powerapi.test_utils.actor import shutdown_system
from powerapi.test_utils.report.hwpc import extract_rapl_reports_with_2_sockets
from powerapi.test_utils.db.mongo import mongo_database
from powerapi.test_utils.db.mongo import MONGO_URI, MONGO_INPUT_COLLECTION_NAME, MONGO_OUTPUT_COLLECTION_NAME, MONGO_DATABASE_NAME

def filter_rule(msg):
    return True

class MainProcess(Process):

    def run(self):
        config = {'verbose': True,
                  'stream': True,
                  'output': {'test_pusher': {'type': 'mongodb',
                                             'model': 'PowerReport',
                                             'uri': MONGO_URI,
                                             'db': MONGO_DATABASE_NAME,
                                             'collection': MONGO_OUTPUT_COLLECTION_NAME}},
                  'input': {'test_puller': {'type': 'mongodb',
                                             'model': 'HWPCReport',
                                             'uri': MONGO_URI,
                                             'db': MONGO_DATABASE_NAME,
                                             'collection': MONGO_INPUT_COLLECTION_NAME}}
                  }
        supervisor = Supervisor(config['verbose'])

        def term_handler(_, __):
            supervisor.shutdown()
            exit(0)

        signal.signal(signal.SIGTERM, term_handler)
        signal.signal(signal.SIGINT, term_handler)
        # Pusher
        pusher_generator = PusherGenerator()
        pusher_info = pusher_generator.generate(config)
        pusher_cls, pusher_start_message = pusher_info['test_pusher']

        pusher = supervisor.launch(pusher_cls, pusher_start_message)
        # Dispatcher
        route_table = RouteTable()
        route_table.dispatch_rule(HWPCReport, HWPCDispatchRule(getattr(HWPCDepthLevel, 'SOCKET'), primary=True))
        dispatcher_start_message = DispatcherStartMessage('system', 'dispatcher', DummyFormulaActor, DummyFormulaValues({'test_pusher': pusher}, 0), route_table, 'cpu')
        
        dispatcher = supervisor.launch(DispatcherActor, dispatcher_start_message)
        # Puller
        report_filter = Filter()
        report_filter.filter(filter_rule, dispatcher)
        puller_generator = PullerGenerator(report_filter, [])
        puller_info = puller_generator.generate(config)
        puller_cls, puller_start_message = puller_info['test_puller']
        puller = supervisor.launch(puller_cls, puller_start_message)
        supervisor.monitor()



@pytest.fixture
def mongodb_content():
    return extract_rapl_reports_with_2_sockets(10)
        
def test_run_mongo(mongo_database, shutdown_system):
    process = MainProcess()
    process.start()
    time.sleep(3)
    os.system('kill ' + str(process.pid))
    time.sleep(3)
    a = subprocess.run(['ps', 'ax'], stdout=subprocess.PIPE)
    b = subprocess.run(['grep', 'Thespian'], input=a.stdout, stdout=subprocess.PIPE)
    assert b.stdout == b''
    
