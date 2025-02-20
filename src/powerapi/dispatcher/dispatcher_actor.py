# Copyright (c) 2022, INRIA
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

import logging
from collections.abc import Callable
from typing import Literal

from powerapi.actor import Actor, State
from powerapi.dispatcher.handlers import FormulaDispatcherReportHandler, DispatcherPoisonPillMessageHandler
from powerapi.dispatcher.route_table import RouteTable
from powerapi.formula import FormulaActor
from powerapi.handler import StartHandler
from powerapi.message import PoisonPillMessage, StartMessage
from powerapi.pusher import PusherActor
from powerapi.report import Report


class DispatcherState(State):
    """
    Dispatcher actor state.
    """

    def __init__(self, actor, pushers: dict[str, PusherActor], route_table: RouteTable):
        """
        :param actor: Dispatcher actor instance
        :param pushers: List of pushers
        :param route_table: Route table to use for reports
        """
        super().__init__(actor)

        self.formula_dict = {}

        self.pushers = pushers
        self.route_table = route_table

    def add_formula(self, formula_id: tuple) -> FormulaActor:
        """
        Create a new formula corresponding to the given ID.
        :param formula_id: The formula ID
        :return: The new formula actor
        """
        formula = self.actor.formula_init_function(name=str((self.actor.name, *formula_id)), pushers=self.pushers)
        self.supervisor.launch_actor(formula, False)
        self.formula_dict[formula_id] = formula
        return formula

    def get_formula(self, formula_id: tuple) -> FormulaActor:
        """
        Get the formula corresponding to the given formula id.
        The formula will be created if it does not exist.
        :param formula_id: The formula id
        :return: The formula actor
        """
        if formula_id not in self.formula_dict:
            return self.add_formula(formula_id)

        return self.formula_dict[formula_id]


class DispatcherActor(Actor):
    """
    Dispatcher actor.
    This actor process the reports coming from the pullers and dispatches them to the formula actors according the
    provided routing table. When a report doesn't have any formula assigned, the dispatcher will create a new formula.
    """

    def __init__(self, name: str, formula_init_function: Callable, pushers: [], route_table: RouteTable,
                 level_logger: Literal = logging.WARNING, timeout=None):
        """
        :param name: Actor name
        :param formula_init_function: Factory function for creating Formula
        :param route_table: Routing table to use for dispatching the reports
        :param level_logger: Logging level
        :param timeout: Time in millisecond to wait for a message before running the timeout handler
        """
        Actor.__init__(self, name, level_logger, timeout)

        # (func): Function for creating Formula
        self.formula_init_function = formula_init_function

        # (powerapi.DispatcherState): Actor state
        self.state = DispatcherState(self, pushers, route_table)

    def setup(self):
        """
        Setup Dispatcher actor report handlers.
        """
        super().setup()

        self.add_handler(Report, FormulaDispatcherReportHandler(self.state))
        self.add_handler(PoisonPillMessage, DispatcherPoisonPillMessageHandler(self.state))
        self.add_handler(StartMessage, StartHandler(self.state))
