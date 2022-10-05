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
Launch a simple architecture with and with a formula that will handle a minor error

Architecture :
  - 1 puller (connected to a mongo database containing 10 hwpc-report, stream mode off)
  - 1 dispatcher (HWPC dispatch rule (dispatch by SOCKET)
  - 1 Formula that crash when it handle a report with ts = (2021-07-12T11:33:16.521)
  - 1 pusher (connected to a mongo database)


database content:
  - 10 HWPC reports

Test if:
 - each HWPCReport (except the report with ts = ts = (2021-07-12T11:33:16.521)) was converted in one PowerReport per
    socket in the output database
"""
import time
from datetime import datetime

import pytest

import pymongo

from thespian.actors import ActorAddress

from powerapi.formula.dummy import DummyFormulaActor, DummyFormulasState
from powerapi.report import Report, PowerReport, HWPCReport
from powerapi.cli.generator import PusherGenerator, PullerGenerator
from powerapi.dispatcher import DispatcherActor, RouteTable
from powerapi.dispatch_rule import HWPCDispatchRule, HWPCDepthLevel
from powerapi.message import DispatcherStartMessage
from powerapi.filter import Filter
from powerapi.supervisor import Supervisor, SIMPLE_SYSTEM_IMP

from powerapi.test_utils.db.mongo import mongo_database
from powerapi.test_utils.db.mongo import MONGO_URI, MONGO_INPUT_COLLECTION_NAME, MONGO_OUTPUT_COLLECTION_NAME, MONGO_DATABASE_NAME
from powerapi.test_utils.actor import shutdown_system
from powerapi.test_utils.report.hwpc import extract_rapl_reports_with_2_sockets

class CrashDummyFormulaActor(DummyFormulaActor):
    def __init__(self):
        DummyFormulaActor.__init__(self)

    def receiveMsg_Report(self, message: Report, sender: ActorAddress):
        print((self.name, message))
        if message.timestamp == datetime.strptime("2021-07-12T11:33:16.521", "%Y-%m-%dT%H:%M:%S.%f"):
            raise Exception()

        time.sleep(self.sleeping_time)
        power_report = PowerReport(message.timestamp, message.sensor, message.target, 42, {'socket': self.socket})
        for _, pusher in self.pushers.items():
            self.send(pusher, power_report)


def filter_rule(msg):
    return True

def launch_simple_architecture(config, supervisor):
    # Pusher
    pusher_generator = PusherGenerator()
    pusher_info = pusher_generator.generate(config)
    pusher_cls, pusher_start_message = pusher_info['test_pusher']
    
    pusher = supervisor.launch(pusher_cls, pusher_start_message)

    # Dispatcher
    route_table = RouteTable()
    route_table.dispatch_rule(HWPCReport, HWPCDispatchRule(getattr(HWPCDepthLevel, 'ROOT'), primary=True))
    dispatcher_start_message = DispatcherStartMessage('system', 'dispatcher', CrashDummyFormulaActor, DummyFormulasState({'test_pusher': pusher}, 0), route_table, 'cpu')

    dispatcher = supervisor.launch(DispatcherActor, dispatcher_start_message)

    # Puller
    report_filter = Filter()
    report_filter.filter(filter_rule, dispatcher)
    puller_generator = PullerGenerator(report_filter, [])
    puller_info = puller_generator.generate(config)
    puller_cls, puller_start_message = puller_info['test_puller']
    puller = supervisor.launch(puller_cls, puller_start_message)

##################
# MONGO to MONGO #
##################
def check_mongo_db():
    mongo = pymongo.MongoClient(MONGO_URI)
    c_input = mongo[MONGO_DATABASE_NAME][MONGO_INPUT_COLLECTION_NAME]
    c_output = mongo[MONGO_DATABASE_NAME][MONGO_OUTPUT_COLLECTION_NAME]

    assert c_output.count_documents({}) == c_input.count_documents({}) - 1

    report_number = 0
    for report in c_input.find():
        report_number += 1
        ts = datetime.strptime(report['timestamp'], "%Y-%m-%dT%H:%M:%S.%f")
        if ts == datetime.strptime("2021-07-12T11:33:16.521", "%Y-%m-%dT%H:%M:%S.%f"):
            pass
        else:
            assert c_output.count_documents(
                {'timestamp': ts, 'sensor': report['sensor'],
                 'target': report['target']}) == 1


@pytest.fixture
def mongodb_content():
    return extract_rapl_reports_with_2_sockets(10)


def test_run_mongo(mongo_database, shutdown_system):
    config = {'verbose': True,
              'stream': False,
              'actor_system': SIMPLE_SYSTEM_IMP,
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
    supervisor = Supervisor(verbose_mode=config['verbose'], system_imp=config['actor_system'])
    launch_simple_architecture(config, supervisor)
    supervisor.monitor()

    check_mongo_db()
