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

from powerapi.actor import Actor, ActorProxy, State
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

    def connect_to_pushers(self):
        """
        Connect to the pusher actors.
        """
        for pushers in self.pushers.values():
            for pusher in pushers:
                pusher.connect_data()

    def disconnect_from_pushers(self):
        """
        Disconnect from the pusher actors.
        """
        for pushers in self.pushers.values():
            for pusher in pushers:
                pusher.disconnect()


class FormulaActor(Actor):
    """
    Abstract formula actor class.
    Used to implement formula actors that compute power estimations from received reports.
    """

    def __init__(self, name: str, pushers: dict[type[Report], list[ActorProxy]], level_logger = logging.WARNING, timeout = None):
        """
        Initialize a new Formula actor.
        :param name: Actor name
        :param pushers: Mapping of report types to pusher actors
        :param level_logger: Level of the logger
        :param timeout: Time in millisecond to wait for a message before calling the timeout handler
        """
        super().__init__(name, level_logger, timeout)

        self.state: FormulaState | None = None
        self.pushers = pushers

    def setup(self):
        """
        Initializes the formula actor.
        """
        self.state = FormulaState(self, self.pushers)
        self.state.connect_to_pushers()

    def teardown(self):
        """
        Teardown the formula actor.
        """
        self.state.disconnect_from_pushers()
