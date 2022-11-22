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
  - 1 Formula that crash when it handles a report with ts = (2021-07-12T11:33:16.521)
  - 1 pusher (connected to a mongo database)


database content:
  - 10 HWPC reports

Test if:
 - each HWPCReport (except the report with ts = ts = (2021-07-12T11:33:16.521)) was converted in one PowerReport per
    socket in the output database
"""
import logging
import time
from datetime import datetime

import pytest

import pymongo

from powerapi.actor import Supervisor
from powerapi.formula import FormulaPoisonPillMessageHandler, AbstractCpuDramFormula
from powerapi.formula.dummy.dummy_handlers import ReportHandler
from powerapi.handler import StartHandler
from powerapi.report import Report, PowerReport
from powerapi.message import PoisonPillMessage, StartMessage
from powerapi.test_utils.acceptation import launch_simple_architecture, ROOT_DEPTH_LEVEL, BASIC_CONFIG

from powerapi.test_utils.db.mongo import mongo_database
from powerapi.test_utils.db.mongo import MONGO_URI, MONGO_INPUT_COLLECTION_NAME, MONGO_OUTPUT_COLLECTION_NAME, \
    MONGO_DATABASE_NAME
from powerapi.test_utils.report.hwpc import extract_rapl_reports_with_2_sockets

CRASH_DATE = "2021-07-12T11:33:22.529000"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"


class CrashDummyReportHandlerMinorError(ReportHandler):

    def handle(self, message: Report):
        """
        Process a report and raise an exception when a report having a given date is received.
        Otherwise, send report to the pushers
        :param powerapi.Report message:  Received message
        """
        if message.timestamp == datetime.strptime(CRASH_DATE, DATE_FORMAT):
            raise Exception()

        time.sleep(self.state.actor.sleep_time)
        power_report = PowerReport(message.timestamp, message.sensor, message.target, 42, {'socket': self.state.socket})
        for _, pusher in self.state.pushers.items():
            pusher.send_data(power_report)


class CrashDummyFormulaActorMinorError(AbstractCpuDramFormula):
    def __init__(self, name, pushers, socket, core, level_logger=logging.WARNING, sleep_time=0, timeout=None):
        AbstractCpuDramFormula.__init__(self, name=name, pushers=pushers, socket=socket, core=core,
                                        level_logger=level_logger, timeout=timeout)
        self.sleep_time = sleep_time

    def setup(self):
        """
        Initialize Handler
        """
        AbstractCpuDramFormula.setup(self)
        self.add_handler(PoisonPillMessage, FormulaPoisonPillMessageHandler(self.state))
        self.add_handler(StartMessage, StartHandler(self.state))
        self.add_handler(Report, CrashDummyReportHandlerMinorError(self.state))


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
        ts = datetime.strptime(report['timestamp'], DATE_FORMAT)
        if ts == datetime.strptime(CRASH_DATE, DATE_FORMAT):
            pass
        else:
            assert c_output.count_documents(
                {'timestamp': ts, 'sensor': report['sensor'],
                 'target': report['target']}) == 1


@pytest.fixture
def mongodb_content():
    return extract_rapl_reports_with_2_sockets(10)


def test_run_mongo(mongo_database):
    supervisor = Supervisor()
    launch_simple_architecture(config=BASIC_CONFIG, supervisor=supervisor, hwpc_depth_level=ROOT_DEPTH_LEVEL,
                               formula_class=CrashDummyFormulaActorMinorError)

    time.sleep(2)

    check_mongo_db()

    supervisor.kill_actors()
