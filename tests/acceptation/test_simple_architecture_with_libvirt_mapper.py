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
Test the behaviour of the most simple architecture with a libvirt mapper

Architecture :
  - 1 puller (connected to MongoDB1 [collection test_hwrep], stream mode off, with a report_modifier (LibvirtMapper))
  - 1 dispatcher (HWPC dispatch rule (dispatch by SOCKET)
  - 1 Dummy Formula
  - 1 pusher (connected to MongoDB1 [collection test_result]

MongoDB1 content:
- 10 HWPCReports with 2 socket for target LIBVIRT_TARGET_NAME1
- 10 HWPCReports with 2 socket for target LIBVIRT_TARGET_NAME2

Scenario:
  - Launch the full architecture with a libvirt mapper connected to a fake libvirt daemon which only know LIBVIRT_INSTANCE_NAME1
Test if:
  - each HWPCReport in the intput database was converted in one PowerReport per
    socket in the output database
  - only target name LIBVIRT_TARGET_NAME1 was converted into UUID_1
"""
import logging
import time
from datetime import datetime
from mock import patch

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
from powerapi.cli.generator import PusherGenerator, PullerGenerator, ReportModifierGenerator
from powerapi.test_utils.actor import shutdown_system
from powerapi.test_utils.db.mongo import mongo_database
from powerapi.test_utils.db.mongo import MONGO_URI, MONGO_INPUT_COLLECTION_NAME, MONGO_OUTPUT_COLLECTION_NAME, MONGO_DATABASE_NAME
from powerapi.test_utils.report.hwpc import extract_all_events_reports_with_vm_name
from powerapi.test_utils.libvirt import MockedLibvirt, LIBVIRT_TARGET_NAME1, REGEXP, UUID_1

@pytest.fixture
def mongodb_content():
    return extract_all_events_reports_with_vm_name(20)


def check_db():
    mongo = pymongo.MongoClient(MONGO_URI)
    c_input = mongo[MONGO_DATABASE_NAME][MONGO_INPUT_COLLECTION_NAME]
    c_output = mongo[MONGO_DATABASE_NAME][MONGO_OUTPUT_COLLECTION_NAME]

    assert c_output.count_documents({}) == c_input.count_documents({}) * 2
    for report in c_input.find({"target": LIBVIRT_TARGET_NAME1}):
        ts = datetime.strptime(report['timestamp'], "%Y-%m-%dT%H:%M:%S.%f")
        assert c_output.count_documents(
            {'timestamp': ts, 'sensor': report['sensor'],
             'domain_id': UUID_1}) == 2

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
    route_table.dispatch_rule(HWPCReport, HWPCDispatchRule(getattr(HWPCDepthLevel, 'SOCKET'), primary=True))
    dispatcher_start_message = DispatcherStartMessage('system', 'dispatcher', DummyFormulaActor, DummyFormulaValues({'test_pusher': pusher}, 0), route_table, 'cpu')

    dispatcher = supervisor.launch(DispatcherActor, dispatcher_start_message)

    # Puller
    report_filter = Filter()
    report_filter.filter(filter_rule, dispatcher)
    report_modifier_generator = ReportModifierGenerator()
    report_modifier_list = report_modifier_generator.generate(config)
    puller_generator = PullerGenerator(report_filter, report_modifier_list)
    puller_info = puller_generator.generate(config)
    puller_cls, puller_start_message = puller_info['test_puller']
    puller = supervisor.launch(puller_cls, puller_start_message)


@patch('powerapi.report_modifier.libvirt_mapper.openReadOnly', return_value=MockedLibvirt())
def test_run(mocked_libvirt, mongo_database, shutdown_system):
    config = {'verbose': True,
              'stream': False,
              'input': {'test_puller': {'type': 'mongodb',
                                   'uri': MONGO_URI,
                                   'db': MONGO_DATABASE_NAME,
                                   'collection': MONGO_INPUT_COLLECTION_NAME,
                                   'model': 'HWPCReport',
                                    }},
              'output': {'test_pusher': {'type': 'mongodb',
                                    'uri': MONGO_URI,
                                    'db': MONGO_DATABASE_NAME,
                                    'collection': MONGO_OUTPUT_COLLECTION_NAME,
                                    'model': 'PowerReport'}},
              'report_modifier': {'libvirt_mapper': {'uri': '',
                                                     'domain_regexp': REGEXP}}
              }

    supervisor = Supervisor(config['verbose'])
    launch_simple_architecture(config, supervisor)
    supervisor.monitor()

    check_db()
