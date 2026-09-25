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

from __future__ import annotations

import logging

from powerapi.actor import Actor, ActorProxy, PoisonPillMessageHandler, StartMessageHandler, State
from powerapi.actor.message import PoisonPillMessage, StartMessage
from powerapi.report import Report


class FormulaState(State):
    """
    Formula actor state.
    """

    def __init__(self, actor: FormulaActor, pushers: dict[type[Report], list[ActorProxy]]):
        """
        Initialize a new Formula actor state.
        :param actor: Formula actor
        :param pushers: Mapping of report types to pusher actors
        """
        super().__init__(actor)

        self.pushers = pushers

    def initialize(self) -> None:
        """
        Connect to the pusher actors.
        """
        for pushers in self.pushers.values():
            for pusher in pushers:
                pusher.connect_data()

    def teardown(self, graceful: bool = False) -> None:
        """
        Disconnect from the pusher actors.
        :param graceful: Whether the actor is performing a graceful shutdown
        """
        for pushers in self.pushers.values():
            for pusher in pushers:
                pusher.disconnect()


class FormulaActor(Actor):
    """
    Abstract formula actor class.
    Used to implement formula actors that compute power estimations from received reports.
    """
    state: FormulaState

    def __init__(self, name: str, pushers: dict[type[Report], list[ActorProxy]], level_logger = logging.WARNING):
        """
        Initialize a new Formula actor.
        :param name: Actor name
        :param pushers: Mapping of report types to pusher actors
        :param level_logger: Level of the logger
        """
        super().__init__(name, level_logger, None)

        self.pushers = pushers

    def create_state(self) -> FormulaState:
        """
        Create the formula state inside the actor process.
        Override this method to provide a specialized formula state.
        :return: Formula actor state
        """
        return FormulaState(self, self.pushers)

    def setup(self) -> None:
        """
        Initializes the formula actor.
        """
        self.state = self.create_state()

        self.add_handler(StartMessage, StartMessageHandler(self.state))
        self.add_handler(PoisonPillMessage, PoisonPillMessageHandler(self.state))
