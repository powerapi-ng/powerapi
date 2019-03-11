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

from powerapi.handler import InitHandler, Handler, StartHandler
from powerapi.report import PowerReport
from powerapi.message import ErrorMessage
from powerapi.message import OKMessage, StartMessage
from powerapi.database import DBError


class PusherStartHandler(StartHandler):
    """
    Handle Start Message
    """

    def initialization(self, state):
        """
        Initialize the output database

        :param powerapi.State state: State of the actor.
        :rtype powerapi.State: the new state of the actor
        """
        try:
            state.database.connect()
        except DBError as error:
            state.socket_interface.send_control(ErrorMessage(error.msg))
            return state

        return state


class PowerHandler(InitHandler):
    """
    Allow to save the PowerReport received.
    """

    def handle(self, msg, state):
        """
        Save the msg in the database

        :param powerapi.PowerReport msg: PowerReport to save.
        :param powerapi.State state: State of the actor.
        """
        if not isinstance(msg, PowerReport):
            return state

        state.buffer.append(msg.serialize())

        return state


class PusherPoisonPillHandler(Handler):
    """
    Set a timeout for the pusher for the timeout_handler. If he didn't
    read any input during the timeout, the actor end.
    """
    def handle(self, msg, state):
        """
        :param powerapi.PoisonPillMessage msg: PoisonPillMessage.
        :param powerapi.pusher.PusherState state: State of the actor.
        :return powerapi.State: new State
        """
        state.timeout_handler = TimeoutKillHandler()
        state.socket_interface.timeout = 2000
        return state


class TimeoutBasicHandler(InitHandler):
    """
    Pusher timeout flush the buffer
    """

    def handle(self, msg, state):
        """
        Flush the buffer in the database
        :param msg: None
        :param state: State of the actor
        :return powerapi.PusherState: new State
        """
        if len(state.buffer) > 0:
            state.database.save_many(state.buffer)
        state.buffer = []
        return state


class TimeoutKillHandler(InitHandler):
    """
    Pusher timeout kill the actor
    """
    def handle(self, msg, state):
        """
        Kill the actor by setting alive to False
        :param msg: None
        :param state: State of the actor
        :return powerapi.PusherState: new State
        """
        state.alive = False
        return state
