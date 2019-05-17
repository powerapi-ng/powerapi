"""
Copyright (c) 2018, INRIA
Copyright (c) 2018, University of Lille
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import logging
from typing import Dict

from powerapi.actor import Actor, State, SocketInterface
from powerapi.pusher import PusherActor


class FormulaState(State):
    """
    State of the Formula actor.
    """

    def __init__(self, actor, pushers):
        """
        Initialize a new Formula actor state.
        :param actor: Actor linked to the state
        :param pushers: Pushers available for the actor
        """
        State.__init__(self, actor)
        self.pushers = pushers


class FormulaActor(Actor):
    """
    Formula actor abstract class.
    """

    def __init__(self, name, pushers: Dict[str, PusherActor], level_logger=logging.WARNING, timeout=None):
        """
        Initialize a new Formula actor.
        :param name: Actor name
        :param pushers: Pusher actors
        :param level_logger: Level of the logger
        :param timeout: Time in millisecond to wait for a message before calling the timeout handler
        """
        Actor.__init__(self, name, level_logger, timeout)
        self.state = FormulaState(self, pushers)

    def setup(self):
        """
        Setup the Formula actor.
        """
        for _, pusher in self.state.pushers.items():
            pusher.connect_data()

    def teardown(self):
        """
        Teardown the Formula actor.
        """
        for _, pusher in self.state.pushers.items():
            pusher.state.socket_interface.close()
