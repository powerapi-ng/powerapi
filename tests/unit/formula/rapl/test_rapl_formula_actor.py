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
import math

from powerapi.formula.rapl.rapl_formula_actor import RAPLFormulaActor, RAPLFormulaConfig, RAPLFormulaScope
from powerapi.report import PowerReport, HWPCReport

from tests.unit.actor.abstract_test_actor import PUSHER_NAME_POWER_REPORT, AbstractTestActor, recv_from_pipe


class TestRAPLFormula(AbstractTestActor):
    @pytest.fixture
    def actor(self, started_fake_pusher_power_report):
        actor = RAPLFormulaActor(name='test_rapl_formula',
                                 pushers={PUSHER_NAME_POWER_REPORT: started_fake_pusher_power_report},
                                 socket=0,
                                 core=0,
                                 sensor='test_sensor',
                                 config=RAPLFormulaConfig(RAPLFormulaScope.CPU, 1000, 'RAPL_ENERGY_PKG'))
        return actor

    def test_send_hwpc_report_to_rapl_formula_return_correct_result(self, started_actor, dummy_pipe_out):
        report = HWPCReport.from_json(
            {"timestamp": "2021-10-05T09:14:58.226",
             "sensor": "toto",
             "target": "all",
             "groups":
                 {"rapl":
                      {"0":
                           {"7":
                                {"RAPL_ENERGY_PKG": 5558763520.0,
                                 "time_enabled": 1000770053.0,
                                 "time_running": 1000770053.0
                                 }
                            }
                       }
                  }
             }
        )

        started_actor.send_data(report)

        _, msg = recv_from_pipe(dummy_pipe_out, 1)

        assert isinstance(msg, PowerReport)
        assert msg.power == math.ldexp(5558763520.0, -32)
