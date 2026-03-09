# Copyright (c) 2022, Inria
# Copyright (c) 2022, University of Lille
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

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Protocol

from powerapi.actor import Actor, State
from powerapi.actor.message import PoisonPillMessage, StartMessage
from powerapi.dispatcher.handlers import FormulaDispatcherReportHandler, DispatcherPoisonPillMessageHandler
from powerapi.handler import StartHandler
from powerapi.report import Report

if TYPE_CHECKING:
    from powerapi.actor import ActorProxy
    from powerapi.formula import FormulaActor
    from powerapi.dispatcher.route_table import RouteTable


class FormulaFactory(Protocol):
    """
    Abstract formula factory class.
    Used to define the factory method that will be called by the dispatcher to create a new formula actor.
    """

    def __call__(self, actor_name: str, pushers: dict[type[Report], list[ActorProxy]]) -> FormulaActor: ...


class DispatcherState(State):
    """
    Dispatcher actor state.
    """

    def __init__(self, actor: DispatcherActor):
        """
        Initialize a new dispatcher actor state.
        :param actor: Dispatcher actor instance
        """
        super().__init__(actor)

        self.formula_factory = actor.formula_factory
        self.pushers = actor.pushers
        self.route_table = actor.route_table

        self.formula_proxy: dict[tuple, ActorProxy] = {}

    def add_formula(self, formula_id: tuple) -> ActorProxy:
        """
        Create and start a new formula actor.
        :param formula_id: The formula ID
        :return: Formula actor proxy
        """
        formula_name = str((self.actor.name, *formula_id))
        formula_actor = self.formula_factory(formula_name, self.pushers)
        self.supervisor.launch_actor(formula_actor)

        formula_proxy = formula_actor.get_proxy(connect_data=True)
        self.formula_proxy[formula_id] = formula_proxy
        return formula_proxy

    def get_formula(self, formula_id: tuple) -> ActorProxy:
        """
        Get the formula corresponding to the given formula id.
        A new formula actor will be created if it does not exist.
        :param formula_id: The formula id
        :return: Formula actor proxy
        """
        if formula_id not in self.formula_proxy:
            return self.add_formula(formula_id)

        return self.formula_proxy[formula_id]


class DispatcherActor(Actor):
    """
    Dispatcher actor.
    This actor process the reports coming from the pullers and dispatches them to the formula actors according the
    provided routing table. When a report doesn't have any formula assigned, the dispatcher will create a new formula.
    """

    def __init__(self, name: str, formula_factory: FormulaFactory, pushers: dict[type[Report], list[ActorProxy]],
                 route_table: RouteTable, level_logger: int = logging.WARNING, timeout=None):
        """
        Initialize a new dispatcher actor.
        :param name: Actor name
        :param formula_factory: Factory function for Formula actors
        :param route_table: Routing table to use for dispatching the reports between formulas
        :param level_logger: Logging level of the actor
        :param timeout: Maximum time to wait for a message (in milliseconds)
        """
        super().__init__(name, level_logger, timeout)

        self.formula_factory = formula_factory
        self.pushers = pushers
        self.route_table = route_table

    def setup(self):
        """
        Setup dispatcher actor.
        """
        self.state = DispatcherState(self)

        self.add_handler(StartMessage, StartHandler(self.state))
        self.add_handler(PoisonPillMessage, DispatcherPoisonPillMessageHandler(self.state))
        self.add_handler(Report, FormulaDispatcherReportHandler(self.state))
