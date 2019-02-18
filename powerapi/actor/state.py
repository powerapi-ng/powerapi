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

from powerapi.message import UnknowMessageTypeException
from powerapi.handler import Handler
from powerapi.actor import Supervisor


class TimeoutHandler(Handler):
    """
    Handler used when a timeout occurs
    """

    def handle(self, msg, state):
        """
        ignore the timeout and return the actual actor state
        """
        return state



class State:
    """
    A basic state class that encapsulate basic actor values :

    :attr:`initialized <powerapi.actor.state.State.initialized>`
    :attr:`alive <powerapi.actor.state.State.alive>`
    :attr:`behaviour <powerapi.actor.state.State.behaviour>`
    :attr:`socket_interface <powerapi.actor.state.State.socket_interface>`
    :attr:`handlers <powerapi.actor.state.State.handlers>`
    :attr:`timeout_handler <powerapi.actor.state.State.timeout_handler>`
    :attr:`supervisor <powerapi.actor.state.State.supervisor>`
    """

    def __init__(self, behaviour, socket_interface, logger):
        """
        :param behaviour: function that implement the basic behaviour
        :type behaviour: (fun (actor) -> None)
        :param socket_interface: communication interface of the actor
        :type socket_interface: powerapi.actor.socket_interface.SocketInterface
        """
        #: (bool): True if the actor is initialized and can handle all
        #: message, False otherwise
        self.initialized = False
        #: (bool): True if the actor is alive, False otherwise
        self.alive = True
        #: (powerapi.SocketInterface): Communication interface of the actor
        self.socket_interface = socket_interface
        #: (func): Function that implement the current behaviour
        self.behaviour = behaviour
        #: ([(type, powerapi.handler.abstract_handler.AbstractHandler)]):
        #: mapping between message type and handler that the mapped handler
        #: must handle
        self.handlers = []
        #: (func): function activated when no message was
        #: received since `timeout` milliseconds
        self.timeout_handler = TimeoutHandler()
        #: (powerapi.actor.supervisor.Supervisor): object that supervise actors
        #: that are handle by this actor
        self.supervisor = Supervisor()
        #: (logging.Logger): Logger
        self.logger = logger

    def get_corresponding_handler(self, msg):
        """
        Return the handler corresponding to the given message type

        :param Object msg: the received message
        :return: the handler corresponding to the given message type
        :rtype: powerapi.handler.AbstractHandler

        :raises UnknowMessageTypeException: if no handler could be find
        """
        for (msg_type, handler) in self.handlers:
            if isinstance(msg, msg_type):
                return handler

        raise UnknowMessageTypeException()

    def add_handler(self, message_type, handler):
        """
        Map a handler to a message type

        :param type message_type: type of the message that the handler can
                                  handle
        :param handler: handler that will handle all messages of the given type
        :type handler: powerapi.handler.AbstractHandler
        """
        self.handlers.append((message_type, handler))
