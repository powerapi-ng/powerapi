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
from thespian.actors import ActorExitRequest

from powerapi.cli.generator import SimplePusherGenerator, SimplePullerGenerator
from powerapi.dispatch_rule.simple_dispatch_rule import SimpleDispatchRule
from powerapi.dispatcher import DispatcherActor, RouteTable
from powerapi.filter import Filter
from powerapi.formula import FormulaValues
from powerapi.formula.simple_formula_actor import SimpleFormulaActor
from powerapi.message import DispatcherStartMessage, SimplePullerSendReportsMessage, \
    GetReceivedReportsSimplePusherMessage
from powerapi.report import HWPCReport
from powerapi.test_utils.actor import system

FORMULA_NAME = "simple-formula-test"
REPORTS_TO_SEND = 10

def filter_rule(_):
    """
    Rule of filter. Here none
    """
    return True


class TestSimplePullerFormulaPusher():

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
                    "model": "HWPCReport"
                }
            }
        }

    @pytest.fixture
    def formula_pushers(self, system, config):

        pusher_generator = SimplePusherGenerator()
        pushers_info = pusher_generator.generate(config)

        pushers = {}

        for pusher_name in pushers_info:
            pusher_cls, pusher_start_message = pushers_info[pusher_name]
            pushers[pusher_name] = system.createActor(pusher_cls)
            system.ask(pushers[pusher_name], pusher_start_message)

        return pushers

    @pytest.fixture
    def report_filter(self):
        return Filter()

    @pytest.fixture
    def route_table(self):
        route_table = RouteTable()
        route_table.dispatch_rule(HWPCReport, SimpleDispatchRule(FORMULA_NAME))
        return route_table

    @pytest.fixture
    def setup_simple_pullers_formula_actors(self, system, route_table, report_filter, formula_pushers, config):
        """
        Setup CPU formula actor.
        :param system: Actor supervisor
        :param route_table: Reports routing table
        :param report_filter: Reports filter
        :param formula_pushers: Reports pushers
        :param config: Config
        """
        dispatcher_start_message = DispatcherStartMessage('system', 'simple-dispatcher-test', SimpleFormulaActor,
                                                          FormulaValues(formula_pushers), route_table, 'simple-test')
        dispatcher = system.createActor(DispatcherActor)
        system.ask(dispatcher, dispatcher_start_message)
        report_filter.filter(filter_rule, dispatcher)

        pullers_info = SimplePullerGenerator(report_filter).generate(config)
        pullers = {}
        for puller_name in pullers_info:
            puller_cls, puller_start_message = pullers_info[puller_name]
            pullers[puller_name] = system.createActor(puller_cls)
            system.ask(pullers[puller_name], puller_start_message)

        yield pullers

        for _, puller in pullers.items():
            system.tell(puller, ActorExitRequest())

    def test_sending_x_messages(self, system, setup_simple_pullers_formula_actors, formula_pushers, config):

        # Exercise
        system.tell(setup_simple_pullers_formula_actors[list(config['input'].keys())[0]],
                    SimplePullerSendReportsMessage('system', 'test-integration'))

        time.sleep(REPORTS_TO_SEND)

        reports_message = system.ask(formula_pushers[list(config['output'].keys())[0]],
                                     GetReceivedReportsSimplePusherMessage('system'))

        assert len(reports_message.reports) == config['input']['puller']['number_of_reports_to_send']
