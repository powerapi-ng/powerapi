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
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=unused-import
import time
from datetime import datetime
from mock import patch

import pytest
import pymongo

from powerapi.actor import Supervisor
from powerapi.formula.dummy import DummyFormulaActor
from powerapi.test_utils.acceptation import launch_simple_architecture, SOCKET_DEPTH_LEVEL, LIBVIRT_CONFIG
from powerapi.test_utils.db.mongo import mongo_database
from powerapi.test_utils.db.mongo import MONGO_URI, MONGO_INPUT_COLLECTION_NAME, MONGO_OUTPUT_COLLECTION_NAME, \
    MONGO_DATABASE_NAME
from powerapi.test_utils.report.hwpc import extract_all_events_reports_with_vm_name
from powerapi.test_utils.libvirt import MockedLibvirt, LIBVIRT_TARGET_NAME1, UUID_1
from tests.unit.actor.abstract_test_actor import shutdown_system


@pytest.fixture
def mongodb_content():
    """
        Get reports from a file for testing purposes
    """
    return extract_all_events_reports_with_vm_name(20)


def check_db():
    """
        Verify that output DB has correct information
    """
    mongo = pymongo.MongoClient(MONGO_URI)
    c_input = mongo[MONGO_DATABASE_NAME][MONGO_INPUT_COLLECTION_NAME]
    c_output = mongo[MONGO_DATABASE_NAME][MONGO_OUTPUT_COLLECTION_NAME]

    assert c_output.count_documents({}) == c_input.count_documents({}) * 2
    for report in c_input.find({"target": LIBVIRT_TARGET_NAME1}):
        ts = datetime.strptime(report['timestamp'], "%Y-%m-%dT%H:%M:%S.%f")
        cursor = c_output.find(
            {'timestamp': ts, 'sensor': report['sensor']})
        print('metadata: ' + str(cursor.__getitem__(0)["metadata"]))
        assert cursor.__getitem__(0)["metadata"]["domain_id"] == UUID_1
        assert cursor.__getitem__(1)["metadata"]["domain_id"] == UUID_1


@patch('powerapi.report_modifier.libvirt_mapper.openReadOnly', return_value=MockedLibvirt())
def test_run(mocked_libvirt, mongo_database, shutdown_system):
    """
        Check that the actor system behave correctly with libvirt mapper
    """
    supervisor = Supervisor()
    launch_simple_architecture(config=LIBVIRT_CONFIG, supervisor=supervisor, hwpc_depth_level=SOCKET_DEPTH_LEVEL,
                               formula_class=DummyFormulaActor, generate_report_modifier_list=True)
    time.sleep(2)

    check_db()

    supervisor.kill_actors()
