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
import pytest

from thespian.actors import ActorExitRequest

from powerapi.formula.dummy import DummyFormulaActor, DummyFormulaValues
from powerapi.formula import CpuDramDomainValues
from powerapi.message import StartMessage, FormulaStartMessage, ErrorMessage, EndMessage, OKMessage
from powerapi.report import Report, PowerReport
from powerapi.test_utils.abstract_test import AbstractTestActor, recv_from_pipe
from powerapi.test_utils.actor import system
from powerapi.test_utils.dummy_actor import logger


class TestDummyFormula(AbstractTestActor):
    @pytest.fixture
    def actor(self, system):
        actor = system.createActor(DummyFormulaActor)
        yield actor
        system.tell(actor, ActorExitRequest())

    @pytest.fixture
    def actor_start_message(self, logger):
        values = DummyFormulaValues({'logger': logger}, 1)
        return FormulaStartMessage('system', 'test_dummy_formula', values, CpuDramDomainValues('test_device', ('test_sensor', 0, 0)))

    def test_starting_dummy_formula_without_DummyFormulaStartMessage_answer_ErrorMessage(self, system, actor):
        answer = system.ask(actor, StartMessage('system', 'test'))
        assert isinstance(answer, ErrorMessage)
        assert answer.error_message == 'use FormulaStartMessage instead of StartMessage'

    def test_send_Report_to_dummy_formula_make_formula_send_power_report_to_logger_with_42_as_power_value_after_1_second(self, system, started_actor, dummy_pipe_out):
        report1 = Report(1, 2, 3)
        system.tell(started_actor, report1)

        _, msg = dummy_pipe_out.recv()
        assert isinstance(msg, PowerReport)
        assert msg.power == 42
