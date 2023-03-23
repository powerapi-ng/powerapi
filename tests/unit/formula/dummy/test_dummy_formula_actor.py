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

# pylint: disable=arguments-differ,redefined-outer-name,unused-argument,unused-import,no-self-use
import pytest

from powerapi.formula.dummy import DummyFormulaActor
from powerapi.report import Report
# noinspection PyUnresolvedReferences
from tests.utils.unit import shutdown_system
from tests.unit.actor.abstract_test_actor import PUSHER_NAME_POWER_REPORT, AbstractTestActor, recv_from_pipe


class TestDummyFormula(AbstractTestActor):
    """
        Class for testing the DummyFormulaActor
    """
    @pytest.fixture
    def actor(self, started_fake_pusher_power_report):
        actor = DummyFormulaActor(name='test_dummy_formula',
                                  pushers={PUSHER_NAME_POWER_REPORT: started_fake_pusher_power_report},
                                  socket=0,
                                  core=0)

        return actor

    def test_send_Report_to_dummy_formula_make_formula_send_power_report_with_42_as_power_value_after_1_second(
            self, started_actor, dummy_pipe_out, shutdown_system):
        """
            Check that a sent report is processed by the actor formula
        """
        report1 = Report(1, 2, 3)
        started_actor.send_data(report1)

        _, msg = recv_from_pipe(dummy_pipe_out, 2)
        assert msg.power == 42
