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
import pickle
import zmq
from powerapi.handler import Handler, PoisonPillMessageHandler
from powerapi.message import PoisonPillMessage
from powerapi.report import Report
from powerapi.actor import Actor, State, SocketInterface, SafeContext


class HWPCReportHandler(Handler):

    def __init__(self, state, push_socket):
        Handler.__init__(self, state)
        self.push_socket = push_socket

    def handle(self, msg):
        self.push_socket.send(pickle.dumps(msg))


class FakeFormulaActor(Actor):
    """
    Formula abstract class. A Formula is an Actor which use data
    for computing some new useful power estimation.

    A Formula is design to be handle by a Dispatcher, and to send
    result to a Pusher.
    """

    def __init__(self, name, push_socket_addr, level_logger=logging.WARNING,
                 timeout=None):
        """
        :param str name: Actor name
        :param int level_logger: Define logger level
        :param bool timeout: Time in millisecond to wait for a message before
                             called timeout_handler.

        """
        Actor.__init__(self, name, level_logger, timeout)

        #: (powerapi.State): Basic state of the Formula.
        self.state = State(self)

        self.addr = push_socket_addr
        self.push_socket = None


    def setup(self):
        self.add_handler(PoisonPillMessage, PoisonPillMessageHandler(self.state))
        self.push_socket = SafeContext.get_context().socket(zmq.PUSH)
        self.push_socket.connect(self.addr)

        self.add_handler(Report, HWPCReportHandler(self.state, self.push_socket))

        self.push_socket.send(pickle.dumps('created'))


    def teardown(self):
        self.push_socket.send(pickle.dumps('terminated'))
