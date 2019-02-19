# Copyright (C) 2018  University of Lille
# Copyright (C) 2018  INRIA
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import logging
import pickle
import zmq
from powerapi.handler import Handler, PoisonPillMessageHandler
from powerapi.message import PoisonPillMessage
from powerapi.report import Report
from powerapi.actor import Actor, State, SocketInterface


class HWPCReportHandler(Handler):

    def __init__(self, push_socket):
        self.push_socket = push_socket

    def handle(self, msg, state):
        self.push_socket.send(pickle.dumps(msg))
        return state


class FakeDispatcherActor(Actor):
    """
    Formula abstract class. A Dispatcher is an Actor which use data
    for dispatcher them to some Formulas.
    """

    def __init__(self, name, push_socket_addr, level_logger=logging.NOTSET,
                 timeout=None):
        """
        :param str name: Actor name
        :param int level_logger: Define logger level
        :param bool timeout: Time in millisecond to wait for a message before
                             called timeout_handler.
        """
        Actor.__init__(self, name, level_logger, timeout)

        #: (powerapi.State): Basic state of the Formula.
        self.state = State(Actor._initial_behaviour,
                           SocketInterface(name, timeout),
                           self.logger)

        self.addr = push_socket_addr
        self.push_socket = None

    def setup(self):
        self.add_handler(PoisonPillMessage, PoisonPillMessageHandler())
        self.push_socket = self.state.socket_interface.context.socket(zmq.PUSH)
        self.push_socket.connect(self.addr)

        self.add_handler(Report, HWPCReportHandler(self.push_socket))
        self.push_socket.send(pickle.dumps('created'))

    def terminated_behaviour(self):
        self.push_socket.send(pickle.dumps('terminated'))
