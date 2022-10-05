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
import time
from typing import Dict

import pytest

from powerapi.actor import Actor
from powerapi.cli.generator import SimplePusherGenerator, SimplePullerGenerator
from powerapi.dispatch_rule.simple_dispatch_rule import SimpleDispatchRule
from powerapi.dispatcher import DispatcherActor, RouteTable
from powerapi.dispatcher.simple.simple_dispatcher_actor import SimpleDispatcherActor
from powerapi.filter import Filter
from powerapi.formula import FormulaState
from powerapi.formula.simple.simple_formula_actor import SimpleFormulaActor
from powerapi.message import DispatcherStartMessage, SimplePullerSendReportsMessage, \
    GetReceivedReportsSimplePusherMessage, StartMessage, PoisonPillMessage
from powerapi.report import HWPCReport
from tests.unit.actor.abstract_test_actor import start_actor, stop_actor

FORMULA_NAME = "simple-formula-test"
REPORTS_TO_SEND = 10


def filter_rule(_):
    """
    Rule of filter. Here none
    """
    return True

class TestSimplePullerFormulaPusher:

    @pytest.fixture
    def config(self) -> Dict:
        return {
            "input": {
                "puller": {
                    "type": "SimplePuller",
                    "model": "HWPCReport",
                    "number_of_reports_to_send": REPORTS_TO_SEND
                }
            },
            "output": {
                "pusher": {
                    "type": "SimplePusher",
                    "model": "HWPCReport",
                    "number_of_reports_to_store": REPORTS_TO_SEND + 1
                }
            }
        }

    @pytest.fixture
    def formula_pushers(self, config):

        pusher_generator = SimplePusherGenerator()
        pushers = pusher_generator.generate(config)

        for pusher_name in pushers:
            pusher = pushers[pusher_name]
            start_actor(pusher)

        yield pushers

        for _, pusher in pushers.items():
            stop_actor(pusher)

    @pytest.fixture
    def report_filter(self):
        return Filter()

    @pytest.fixture
    def route_table(self):
        route_table = RouteTable()
        route_table.dispatch_rule(HWPCReport, SimpleDispatchRule(FORMULA_NAME))
        return route_table

    @pytest.fixture
    def setup_simple_pullers_formula_actors(self, route_table, report_filter, formula_pushers, config):
        """
        Setup CPU formula actor.
        :param route_table: Reports routing table
        :param report_filter: Reports filter
        :param formula_pushers: Reports pushers
        :param config: Config
        """
        dispatcher = SimpleDispatcherActor(name='test-simple-dispatcher-test', formula_init_function=SimpleFormulaActor,
                                           route_table=route_table, pushers=formula_pushers)
        start_actor(dispatcher)

        report_filter.filter(filter_rule, dispatcher)

        pullers = SimplePullerGenerator(report_filter).generate(config)
        for puller_name in pullers:
            puller = pullers[puller_name]
            start_actor(puller)

        yield pullers

        for _, puller in pullers.items():
            stop_actor(puller)

        stop_actor(dispatcher)

    def test_sending_x_messages(self, setup_simple_pullers_formula_actors, formula_pushers, config):

        # Exercise
        setup_simple_pullers_formula_actors[list(config['input'].keys())[0]]. \
            send_data(SimplePullerSendReportsMessage('system', 'test-integration'))

        time.sleep(REPORTS_TO_SEND)

        formula_pushers[list(config['output'].keys())[0]]. \
            send_control(GetReceivedReportsSimplePusherMessage('system'))
        reports_message = formula_pushers[list(config['output'].keys())[0]].receive_control(2000)
        assert len(reports_message.reports) == config['input']['puller']['number_of_reports_to_send']
