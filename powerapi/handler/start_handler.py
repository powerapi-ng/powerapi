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

from powerapi.message import OKMessage, StartMessage, ErrorMessage
from powerapi.handler import Handler


class StartHandler(Handler):
    """
    Initialize the received state
    """

    def handle(self, msg, state):
        """
        Allow to initialize the state of the actor, then reply to the control
        socket.

        :param powerapi.StartMessage msg: Message that initialize the actor
        :param powerapi.State state: State of the actor
        :rtype powerapi.State: the new state of the actor
        """
        if state.initialized:
            state.socket_interface.send_control(
                ErrorMessage('Actor already initialized'))
            return state

        if not isinstance(msg, StartMessage):
            return state

        state = self.initialization(state)

        state.initialized = True
        state.socket_interface.send_control(OKMessage())

        return state

    def initialization(self, state):
        """
        Abstract method that initialize the actor after receiving a start msg

        :param powerapi.State state: State of the actor
        :rtype powerapi.State: the new state of the actor
        """
        return state
