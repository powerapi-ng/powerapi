# Copyright (c) 2026, Inria
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
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

from datetime import datetime
from unittest.mock import Mock

import pytest

from powerapi.actor import PoisonPillMessage, ActorProxy
from powerapi.dispatch_rule import DispatchRule
from powerapi.dispatcher import RouteTable
from powerapi.dispatcher.dispatcher_actor import DispatcherState
from powerapi.dispatcher.handlers import FormulaDispatcherReportHandler, DispatcherPoisonPillMessageHandler
from powerapi.report import Report


class DummyReport(Report):
    """
    Minimal report used by the dispatcher report handler unit tests.
    """

    def __init__(self):
        super().__init__(timestamp=datetime.now(), sensor='pytest', target='unit-tests')


class SingleFormulaDispatchRule(DispatchRule):
    """
    Dispatch rule returning a single formula ID to test the dispatcher report handler.
    """

    def __init__(self, primary: bool = False):
        super().__init__(primary=primary, fields=['sensor'])

    def get_formula_id(self, report: DummyReport) -> list[tuple]:
        return [(report.sensor,)]


class MultipleFormulaDispatchRule(DispatchRule):
    """
    Dispatch rule returning multiple formula IDs to test the dispatcher report handler.
    """

    def __init__(self, primary: bool = False):
        super().__init__(primary=primary, fields=['sensor', 'scope'])

    def get_formula_id(self, report: DummyReport) -> list[tuple]:
        return [(report.sensor, 'scope1'), (report.sensor, 'scope2')]


@pytest.fixture
def dispatcher_report_handler():
    """
    Factory fixture for creating a report handler with a mocked dispatcher actor.
    """

    def _create_handler(route_table: RouteTable) -> FormulaDispatcherReportHandler:
        actor = Mock(name='dispatcher-actor')
        actor.name = 'dispatcher-actor'

        def _formula_factory(actor_name: str, pushers: dict[type[Report], list[ActorProxy]]):
            return Mock(name=actor_name, pushers=pushers)

        actor.formula_factory = _formula_factory
        actor.pushers = {}
        actor.route_table = route_table

        state = DispatcherState(actor)
        state.alive = True
        state.supervisor = Mock(name='supervisor')

        handler = FormulaDispatcherReportHandler(state)
        return handler

    return _create_handler


@pytest.fixture
def dispatcher_poison_pill_handler():
    """
    Factory fixture for creating a poison-pill message handler with a mocked dispatcher actor.
    """

    def _create_handler() -> DispatcherPoisonPillMessageHandler:
        actor = Mock(name='dispatcher-actor')
        actor.pushers = {}
        actor.route_table = RouteTable()
        actor.socket_interface.receive.return_value = None  # Prevents an infinite loop when triggering a graceful shutdown.

        state = DispatcherState(actor)
        state.supervisor = Mock(name='supervisor')

        handler = DispatcherPoisonPillMessageHandler(state)
        return handler

    return _create_handler


@pytest.mark.parametrize('dispatch_rule', [SingleFormulaDispatchRule(), MultipleFormulaDispatchRule()])
def test_report_handler_forwards_report_to_formula(dispatcher_report_handler, dispatch_rule):
    """
    Report handler should forward the report to its corresponding formula actor.
    """
    route_table = RouteTable()
    route_table.add_dispatch_rule(DummyReport, dispatch_rule)
    handler = dispatcher_report_handler(route_table)

    report = DummyReport()
    handler.handle(report)

    assert handler.state.formula_proxy
    for formula in handler.state.formula_proxy.values():
        formula.send_data.assert_called_once_with(report)


@pytest.mark.parametrize('graceful_flag', [True, False])
def test_poison_pill_handler_disconnects_proxies_and_stops_formula_actors(dispatcher_poison_pill_handler, graceful_flag):
    """
    Poison-Pill handler should disconnect proxies and stop supervised formula actors before shutting down the dispatcher.
    """
    handler = dispatcher_poison_pill_handler()
    proxy_a = Mock(name='formula-a-proxy')
    proxy_b = Mock(name='formula-b-proxy')
    handler.state.formula_proxy = {('formula-a',): proxy_a, ('formula-b',): proxy_b}

    handler.handle(PoisonPillMessage(soft=graceful_flag))

    proxy_a.disconnect.assert_called_once()
    proxy_b.disconnect.assert_called_once()
    handler.state.supervisor.kill_actors.assert_called_once_with(graceful=graceful_flag)
    handler.state.supervisor.join.assert_called_once()
    assert handler.state.alive is False
