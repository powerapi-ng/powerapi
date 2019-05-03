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
import typing

from powerapi.actor import Actor, State, SocketInterface
from powerapi.pusher import PusherActor


class FormulaState(State):
    """
    Formula Actor State
    """

    def __init__(self, behaviour, socket_interface, logger, formula_id, pusher_actors, model):
        State.__init__(self, behaviour, socket_interface, logger)
        self.formula_id = formula_id
        self.pusher_actors = pusher_actors
        self.model = model


class FormulaActor(Actor):
    """
    Formula abstract class. A Formula is an Actor which use data
    for computing some new useful power estimation.

    A Formula is design to be handle by a Dispatcher, and to send
    result to a Pusher.
    """

    def __init__(self, name, pusher_actors: typing.Dict[str, PusherActor],
                 level_logger=logging.WARNING, timeout=None):
        """
        :param str name:                                       Actor name
        :param Dict[str, powerapi.PusherActor] pusher_actors:  Pusher actors whom send
                                                               results
        :param int level_logger:                               Define logger level
        :param bool timeout:                                   Time in millisecond to wait
                                                               for a message before called
                                                               timeout_handler.
        """
        Actor.__init__(self, name, level_logger, timeout)

        #: (powerapi.State): Basic state of the Formula.
        self.state = FormulaState(Actor._initial_behaviour,
                                  SocketInterface(name, timeout),
                                  self.logger, None, pusher_actors,
                                  None)

    def setup(self):
        """
        Formula basic setup, Connect the formula to the pusher
        """
        for _, actor_pusher in self.state.pusher_actors.items():
            actor_pusher.connect_data()

    def terminated_behaviour(self):
        """
        Allow to close actor_pusher socket
        """
        for _, actor_pusher in self.state.pusher_actors.items():
            actor_pusher.state.socket_interface.close()
