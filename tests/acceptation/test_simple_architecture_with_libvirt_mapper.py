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
  - litarget name are converted LIBVIRT_TARGET_NAME1 was converted into UUID_1

"""

import logging
from datetime import datetime
from mock import patch

import pytest
import pymongo

from powerapi.cli.tools import CommonCLIParser, PusherGenerator, PullerGenerator, ReportModifierGenerator
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


from powerapi.test_utils.db.mongo import mongo_database, MONGO_URI, MONGO_INPUT_COLLECTION_NAME, MONGO_OUTPUT_COLLECTION_NAME, MONGO_DATABASE_NAME
from powerapi.test_utils.db.mongo import mongo_database
from powerapi.test_utils.libvirt import MockedLibvirt, LIBVIRT_TARGET_NAME1, REGEXP, UUID_1
from powerapi.test_utils.report.hwpc import extract_reports_with_vm_name


@pytest.fixture
def mongodb_content():
    return extract_reports_with_vm_name(20)

@pytest.fixture
def supervisor():
    s = BackendSupervisor(False)
    yield s
    s.kill_actors()


def check_db():
    mongo = pymongo.MongoClient(MONGO_URI)
    c_input = mongo[MONGO_DATABASE_NAME][MONGO_INPUT_COLLECTION_NAME]
    c_output = mongo[MONGO_DATABASE_NAME][MONGO_OUTPUT_COLLECTION_NAME]

    assert c_output.count_documents({}) == c_input.count_documents({}) * 2
    for report in c_input.find({"target": LIBVIRT_TARGET_NAME1}):
        ts = datetime.strptime(report['timestamp'], "%Y-%m-%dT%H:%M:%S.%f")
        assert c_output.count_documents(
            {'timestamp': ts, 'sensor': report['sensor'],
             'target': UUID_1}) == 2

@patch('powerapi.report_modifier.libvirt_mapper.openReadOnly', return_value=MockedLibvirt())
def test_run(mocked_libvirt, mongo_database, supervisor):
    LOG_LEVEL = logging.DEBUG
    config = {'verbose': LOG_LEVEL,
              'stream': False,
              'input': {'puller': {'type': 'mongodb',
                                   'uri': MONGO_URI,
                                   'db': MONGO_DATABASE_NAME,
                                   'collection': MONGO_INPUT_COLLECTION_NAME,
                                   'model': 'HWPCReport',
                                   }},
              'output': {'pusher': {'type': 'mongodb',
                                    'uri': MONGO_URI,
                                    'db': MONGO_DATABASE_NAME,
                                    'collection': MONGO_OUTPUT_COLLECTION_NAME,
                                    'model': 'PowerReport',
                                    'name': 'pusher'}},
    'report_modifier': {'libvirt_mapper': {'uri': '',
                                           'domain_regexp': REGEXP}}}

    # Pusher
    pusher_generator = PusherGenerator()
    pushers = pusher_generator.generate(config)

    # Formula
    formula_factory = (lambda name,
                       verbose: DummyFormulaActor(name, pushers, level_logger=config['verbose']))

    # Dispatcher
    route_table = RouteTable()
    route_table.dispatch_rule(HWPCReport,
                              HWPCDispatchRule(getattr(HWPCDepthLevel, 'SOCKET'), primary=True))

    dispatcher = DispatcherActor('dispatcher', formula_factory, route_table,
                                 level_logger=LOG_LEVEL)

    # Puller
    report_filter = Filter()
    report_filter.filter(lambda msg: True, dispatcher)

    report_modifier_generator = ReportModifierGenerator()
    report_modifier_list = report_modifier_generator.generate(config)

    puller_generator = PullerGenerator(report_filter, report_modifier_list)
    pullers = puller_generator.generate(config)

    for _, pusher in pushers.items():
        supervisor.launch_actor(pusher)

    supervisor.launch_actor(dispatcher)

    for _, puller in pullers.items():
        supervisor.launch_actor(puller)

    supervisor.join()

    check_db()
