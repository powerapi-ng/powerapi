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
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=unused-import
import signal
import os

import sys
import time
from multiprocessing import Process

import pytest

from powerapi.actor import Supervisor
from tests.utils.formula.dummy import DummyFormulaActor

from tests.utils.acceptation import launch_simple_architecture, SOCKET_DEPTH_LEVEL, \
    get_basic_config_with_stream
from tests.utils.report.hwpc import extract_rapl_reports_with_2_sockets
# noinspection PyUnresolvedReferences
from tests.utils.db.mongo import mongo_database


class MainProcess(Process):
    """
        Process executing the actor system for testing
    """

    def __init__(self):
        Process.__init__(self)
        self.supervisor = Supervisor()

    def run(self):
        def term_handler(_, __):
            self.supervisor.kill_actors()
            time.sleep(3)
            for actor in self.supervisor.supervised_actors:
                assert not actor.is_alive()
            sys.exit(0)

        signal.signal(signal.SIGTERM, term_handler)
        signal.signal(signal.SIGINT, term_handler)

        launch_simple_architecture(config=get_basic_config_with_stream(), supervisor=self.supervisor,
                                   hwpc_depth_level=SOCKET_DEPTH_LEVEL,
                                   formula_class=DummyFormulaActor)


@pytest.fixture
def mongodb_content():
    """
        Retrieve 10 RAPL reports from a mongo database
    """
    return extract_rapl_reports_with_2_sockets(10)


def test_system_stop(mongo_database):
    """
        Check via term_handler that all actors (pusher, puller and dispatcher) are stopped
    """

    process = MainProcess()
    process.start()
    time.sleep(3)
    os.system('kill ' + str(process.pid))
    time.sleep(3)
