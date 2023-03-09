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

# pylint: disable=arguments-differ,redefined-outer-name,unused-argument,no-self-use,unused-import

import pytest

from powerapi.formula.simple.simple_formula_actor import SimpleFormulaActor
from powerapi.test_utils.unit import shutdown_system
from tests.unit.actor.abstract_test_actor import AbstractTestActor, recv_from_pipe, REPORT_TYPE_TO_BE_SENT, \
    REPORT_TYPE_TO_BE_SENT_2, PUSHER_NAME_POWER_REPORT


class TestSimpleFormula(AbstractTestActor):
    """
        Class for testing the SimpleFormulaActor
    """

    @pytest.fixture
    def actor(self, started_fake_pusher_power_report):
        actor = SimpleFormulaActor(name='test_simple_formula',
                                   pushers={PUSHER_NAME_POWER_REPORT: started_fake_pusher_power_report})

        return actor

    def test_send_power_report_to_simple_formula_make_formula_send_same_report_to_pusher(self, started_actor,
                                                                                         dummy_pipe_out,
                                                                                         shutdown_system):
        """
            Check that a power report sent to the formula is the same one received by the pusher
        """
        report1 = REPORT_TYPE_TO_BE_SENT.create_empty_report()
        started_actor.send_data(report1)
        _, msg = recv_from_pipe(dummy_pipe_out, 2)
        assert msg == report1

    def test_send_empty_hwpc_report_to_simple_formula_make_formula_send_none_to_pusher(self, started_actor,
                                                                                       dummy_pipe_out,
                                                                                       shutdown_system):
        """
            Check that a hwpc report is ignored by the pusher, i.e., it is not forwarded to the output (pipe)
        """
        report1 = REPORT_TYPE_TO_BE_SENT_2.create_empty_report()
        started_actor.send_data(report1)

        _, msg = recv_from_pipe(dummy_pipe_out, 2)
        assert msg is None
