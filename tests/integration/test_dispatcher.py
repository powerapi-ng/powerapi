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
from multiprocessing import Pipe

import pytest

from powerapi.formula.dummy import DummyFormulaActor, DummyFormulaValues
from powerapi.dispatcher import RouteTable
from powerapi.report import HWPCReport, PowerReport
from powerapi.dispatch_rule import HWPCDispatchRule, HWPCDepthLevel
from powerapi.test_utils.actor import system, dispatcher, dispatcher_start_message, started_dispatcher
from powerapi.test_utils.dummy_actor import logger
from powerapi.test_utils.report.hwpc import gen_HWPCReports
from powerapi.test_utils.abstract_test import recv_from_pipe


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
def formula_values(logger):
    return DummyFormulaValues({'logger': logger}, 0.1)

@pytest.fixture
def route_table(logger):
    route_table = RouteTable()
    route_table.dispatch_rule(HWPCReport, HWPCDispatchRule(getattr(HWPCDepthLevel, 'ROOT'), primary=True))
    return route_table


def test_send_5_message_to_dispatcher_that_handle_DummyFormula_send_5_PowerReport_to_FakePusher(system, started_dispatcher, dummy_pipe_out):
    for report in gen_HWPCReports(5):
        system.tell(started_dispatcher, report)

    for _ in range(5):
        _, msg = recv_from_pipe(dummy_pipe_out, 1)
        assert isinstance(msg, PowerReport)
