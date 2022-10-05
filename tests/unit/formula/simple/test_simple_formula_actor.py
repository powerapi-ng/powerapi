# Copyright (c) 2022, INRIA
# Copyright (c) 2022, University of Lille
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
import pytest

from powerapi.formula.simple.simple_formula_actor import SimpleFormulaActor
from powerapi.report import PowerReport, HWPCReport
from powerapi.test_utils.dummy_actor import DummyActor
from tests.unit.actor.abstract_test_actor import AbstractTestActor, recv_from_pipe, start_actor, stop_actor

PUSHER_NAME_POWER_REPORT = 'fake_pusher_power'
PUSHER_NAME_HWPC_REPORT = 'fake_pusher_hwpc'

REPORT_TYPE_TO_BE_SENT = PowerReport
REPORT_TYPE_TO_BE_SENT_2 = HWPCReport


class TestSimpleFormula(AbstractTestActor):

    @pytest.fixture
    def started_fake_pusher_power_report(self, dummy_pipe_in):
        pusher = DummyActor(PUSHER_NAME_POWER_REPORT, dummy_pipe_in, REPORT_TYPE_TO_BE_SENT)
        start_actor(pusher)
        yield pusher
        if pusher.is_alive():
            pusher.terminate()

    @pytest.fixture
    def actor(self, started_fake_pusher_power_report):
        actor = SimpleFormulaActor('test_simple_formula', {PUSHER_NAME_POWER_REPORT: started_fake_pusher_power_report})

        return actor

    def test_send_power_report_to_simple_formula_make_formula_send_same_report_to_pusher(self, started_actor,
                                                                                         dummy_pipe_out):
        report1 = REPORT_TYPE_TO_BE_SENT.create_empty_report()
        started_actor.send_data(report1)
        _, msg = recv_from_pipe(dummy_pipe_out, 2)
        assert msg == report1

    def test_send_hwpc_report_to_simple_formula_make_formula_send_none_to_pusher(self, started_actor,
                                                                                 dummy_pipe_out):
        report1 = REPORT_TYPE_TO_BE_SENT_2.create_empty_report()
        started_actor.send_data(report1)

        _, msg = recv_from_pipe(dummy_pipe_out, 2)
        assert msg is None
