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

from powerapi.actor import Supervisor
from powerapi.formula.dummy import DummyFormulaActor
from powerapi.dispatch_rule import HWPCDispatchRule, HWPCDepthLevel
from powerapi.filter import Filter
from powerapi.report import HWPCReport
from powerapi.dispatcher import DispatcherActor, RouteTable
from powerapi.cli.generator import PusherGenerator, PullerGenerator
from powerapi.test_utils.report.hwpc import extract_rapl_reports_with_2_sockets
from powerapi.test_utils.db.mongo import mongo_database
from powerapi.test_utils.db.mongo import MONGO_URI, MONGO_INPUT_COLLECTION_NAME, MONGO_OUTPUT_COLLECTION_NAME, \
    MONGO_DATABASE_NAME


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
        supervisor = Supervisor()

        def term_handler(_, __):
            supervisor.kill_actors()
            exit(0)

        signal.signal(signal.SIGTERM, term_handler)
        signal.signal(signal.SIGINT, term_handler)
        # Pusher
        pusher_generator = PusherGenerator()
        pusher_info = pusher_generator.generate(config)
        pusher = pusher_info['test_pusher']

        supervisor.launch_actor(actor=pusher, start_message=True)
        # Dispatcher
        route_table = RouteTable()
        route_table.dispatch_rule(HWPCReport, HWPCDispatchRule(getattr(HWPCDepthLevel, 'SOCKET'), primary=True))

        dispatcher = DispatcherActor(name='dispatcher',
                                     formula_init_function=lambda name, pushers: DummyFormulaActor(name=name,
                                                                                                   pushers=pushers,
                                                                                                   socket=0,
                                                                                                   core=0),
                                     route_table=route_table,
                                     pushers={'test_pusher': pusher})

        supervisor.launch_actor(actor=dispatcher, start_message=True)
        # Puller
        report_filter = Filter()
        report_filter.filter(filter_rule, dispatcher)
        puller_generator = PullerGenerator(report_filter, [])
        puller_info = puller_generator.generate(config)
        puller = puller_info['test_puller']
        supervisor.launch_actor(actor=puller, start_message=True)


@pytest.fixture
def mongodb_content():
    return extract_rapl_reports_with_2_sockets(10)


def test_run_mongo(mongo_database):
    process = MainProcess()
    process.start()
    time.sleep(3)
    os.system('kill ' + str(process.pid))
    time.sleep(3)
    a = subprocess.run(['ps', 'ax'], stdout=subprocess.PIPE)
    b = subprocess.run(['grep', 'Thespian'], input=a.stdout, stdout=subprocess.PIPE)
    assert b.stdout == b''
