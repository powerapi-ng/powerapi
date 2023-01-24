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
from multiprocessing import Pipe

import pytest

from powerapi.dispatcher import RouteTable, DispatcherActor
from powerapi.formula import DummyFormulaActor
from powerapi.message import StartMessage
from powerapi.report import HWPCReport, PowerReport
from powerapi.dispatch_rule import HWPCDispatchRule, HWPCDepthLevel
from powerapi.test_utils.dummy_actor import DummyActor
from powerapi.test_utils.report.hwpc import gen_HWPCReports
from tests.unit.actor.abstract_test_actor import recv_from_pipe
from powerapi.test_utils.unit import shutdown_system

PUSHER_NAME_POWER_REPORT = 'fake_pusher_power'
REPORT_TYPE_TO_BE_SENT = PowerReport


@pytest.fixture
def pipe():
    return Pipe()


@pytest.fixture
def dummy_pipe_in(pipe):
    return pipe[0]


@pytest.fixture
def dummy_pipe_out(pipe):
    return pipe[1]


@pytest.fixture
def formula_class():
    return DummyFormulaActor


@pytest.fixture
def route_table():
    route_table = RouteTable()
    route_table.dispatch_rule(HWPCReport, HWPCDispatchRule(getattr(HWPCDepthLevel, 'ROOT'), primary=True))
    return route_table


@pytest.fixture
def started_fake_pusher_power_report(dummy_pipe_in):
    pusher = DummyActor(PUSHER_NAME_POWER_REPORT, dummy_pipe_in, REPORT_TYPE_TO_BE_SENT)
    pusher.start()
    pusher.connect_data()
    pusher.connect_control()
    pusher.send_control(StartMessage('test_case'))
    _ = pusher.receive_control(2000)
    yield pusher
    if pusher.is_alive():
        pusher.terminate()


@pytest.fixture
def started_dispatcher(started_fake_pusher_power_report, route_table):
    actor = DispatcherActor(name='test-integration-dispatcher',
                            formula_init_function=lambda name, pushers: DummyFormulaActor(name=name,
                                                                                          pushers=pushers, socket=0,
                                                                                          core=0),
                            route_table=route_table,
                            pushers={PUSHER_NAME_POWER_REPORT: started_fake_pusher_power_report},
                            device_id='test_device')
    actor.start()
    actor.connect_data()
    actor.connect_control()
    actor.send_control(StartMessage('test_case'))
    _ = actor.receive_control(2000)
    yield actor
    if actor.is_alive():
        actor.terminate()
    actor.socket_interface.close()
    actor.join()


def test_send_5_message_to_dispatcher_that_handle_DummyFormula_send_5_PowerReport_to_DummyPusher(started_dispatcher,
                                                                                                 dummy_pipe_out,
                                                                                                 shutdown_system):
    for report in gen_HWPCReports(5):
        started_dispatcher.send_data(report)

    for _ in range(5):
        _, msg = recv_from_pipe(dummy_pipe_out, 1)
        assert isinstance(msg, PowerReport)
