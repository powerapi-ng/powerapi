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
import signal
import multiprocessing
import setproctitle

from powerapi.actor import State, SocketInterface
from powerapi.message import PoisonPillMessage
from powerapi.message import UnknowMessageTypeException
from powerapi.handler import HandlerException


class Actor(multiprocessing.Process):
    """
    Abstract class that exposes an interface to create, setup and handle actors

    :Method Interface:

    This table list from wich interface each methods are accessible

    +---------------------------------+--------------------------------------------------------------------------------------------+
    |  Interface type                 |                                   method name                                              |
    +=================================+============================================================================================+
    | Client interface                | :meth:`connect_data <powerapi.actor.actor.Actor.connect_data>`                           |
    |                                 +--------------------------------------------------------------------------------------------+
    |                                 | :meth:`connect_control <powerapi.actor.actor.Actor.connect_control>`                     |
    |                                 +--------------------------------------------------------------------------------------------+
    |                                 | :meth:`send_control <powerapi.actor.actor.Actor.send_control>`                           |
    |                                 +--------------------------------------------------------------------------------------------+
    |                                 | :meth:`send_data <powerapi.actor.actor.Actor.send_data>`                                 |
    |                                 +--------------------------------------------------------------------------------------------+
    |                                 | :meth:`kill <powerapi.actor.actor.Actor.kill>`                                           |
    +---------------------------------+--------------------------------------------------------------------------------------------+
    | Server interface                | :meth:`setup <powerapi.actor.actor.Actor.setup>`                                         |
    |                                 +--------------------------------------------------------------------------------------------+
    |                                 | :meth:`add_handler <powerapi.actor.actor.Actor.add_handler>`                             |
    |                                 +--------------------------------------------------------------------------------------------+
    |                                 | :meth:`terminated_behaviour <powerapi.actor.actor.Actor.terminated_behaviour>`           |
    |                                 +--------------------------------------------------------------------------------------------+
    |                                 | :meth:`send_control <powerapi.actor.actor.Actor.send_control>`                           |
    +---------------------------------+--------------------------------------------------------------------------------------------+

    :Attributes Interface:
    
    This table list from wich interface each attributes are accessible

    +---------------------------------+--------------------------------------------------------------------------------------------+
    |  Interface type                 |                                   method name                                              |
    +---------------------------------+--------------------------------------------------------------------------------------------+
    | Server interface                | :attr:`state <powerapi.actor.actor.Actor.state>`                                         |
    +---------------------------------+--------------------------------------------------------------------------------------------+
    """

    def __init__(self, name, level_logger=logging.NOTSET, timeout=None):
        """
        Initialization and start of the process.

        :param str name: unique name that will be used to indentify the actor
                         processus
        :param int level_logger: Define the level of the logger
        :param int timeout: if define, do something if no msg is recv every
                            timeout (in ms)
        """
        multiprocessing.Process.__init__(self, name=name)

        #: (powerapi.actor.state.State): actor's state
        self.state = State(self._initial_behaviour,
                           SocketInterface(name, timeout))
        #: (logging.Logger): Logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level_logger)
        formatter = logging.Formatter(
            '%(asctime)s || %(levelname)s || ' +
            '%(process)d %(processName)s || %(message)s')
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def run(self):
        """
        Main code executed by the actor
        """
        self._setup()

        while self.state.alive:
            self.state.behaviour(self)

        self._kill_process()

    def _signal_handler_setup(self):
        """
        Define how to handle signal interrupts
        """
        def term_handler(_, __):
            self._kill_process()
            exit(0)

        signal.signal(signal.SIGTERM, term_handler)
        signal.signal(signal.SIGINT, term_handler)

    def _setup(self):
        """
        Set actor specific configuration:

         - set the processus name
         - setup the socket interface
         - setup the signal handler

        This method is called before entering on the behaviour loop
        """
        # Name process
        setproctitle.setproctitle(self.name)

        self.state.socket_interface.setup()

        self.logger.info(self.name + ' process created.')

        self._signal_handler_setup()

        self.setup()

    def setup(self):
        """
        Function called before entering on the behaviour loop

        Can be overriden to use personal actor setup
        """

    def add_handler(self, message_type, handler):
        """
        Map a handler to a message type

        :param type message_type: type of the message that the handler can
                                  handle
        :param handler: handler that will handle all messages of the given type
        :type handler: powerapi.handler.Handler
        """
        self.state.add_handler(message_type, handler)

    def _initial_behaviour(self):
        """
        Initial behaviour of an actor

        Wait for a message, and handle it with the correct handler

        If the message is None, call the timout_handler otherwise find the
        handler correponding to the message type and call it on the message.
        """
        msg = self.receive()

        # Timeout
        if msg is None:
            self.state = self.state.timeout_handler.handle_message(None,
                                                                   self.state)
        # Message
        else:
            try:
                handler = self.state.get_corresponding_handler(msg)
                self.state = handler.handle_message(msg, self.state)
            except UnknowMessageTypeException:
                self.logger.warning("UnknowMessageTypeException: " +
                                    repr(msg))
            except HandlerException:
                self.logger.warning("HandlerException")

    def _kill_process(self):
        """
        Kill the actor (close sockets)
        """
        self.terminated_behaviour()
        self.state.socket_interface.close()
        self.logger.info(self.name + " terminated")

    def set_timeout_handler(self, new_timeout_handler):
        """
        Set the timeout_handler
        """
        self.state.timeout_handler = new_timeout_handler

    def terminated_behaviour(self):
        """
        Function called before closing sockets

        Can be overriden to use personal actor termination behaviour
        """

    def connect_data(self, context):
        """
        Open a canal that can be use for unidirectional communication to this
        actor

        :param context: ZMQ context of the process that want to
                        communicate with this actor
        :type context: zmq.Context
        """
        self.state.socket_interface.connect_data(context)
        self.logger.info('connected data to ' + self.name)

    def connect_control(self, context):
        """
        Open a control canal with this actor. An actor can have only one
        control open at the same time. Open a pair socket on the process
        that want to control this actor

        :param context: ZMQ context of the process that want to
                        communicate with this actor
        :type context: zmq.Context
        """
        self.state.socket_interface.connect_control(context)
        self.logger.info('connected control to ' + self.name)

    def send_control(self, msg):
        """
        Send a message to this actor on the control canal

        :param Object msg: the message to send to this actor
        """
        self.state.socket_interface.send_control(msg)
        self.logger.info('send control [' + repr(msg) + '] to ' + self.name)

    def receive_control(self):
        """
        Receive a message from this actor on the control canal
        """
        msg = self.state.socket_interface.receive_control()
        self.logger.info("receive control : [" + repr(msg) + "]")
        return msg

    def send_data(self, msg):
        """
        Send a msg to this actor using the data canal

        :param Object msg: the message to send to this actor
        """
        self.state.socket_interface.send_data(msg)
        self.logger.info('send data [' + repr(msg) + '] to ' + self.name)

    def receive(self):
        """
        Block until a message was received (or until timeout) an return the
        received messages

        :return: the list of received messages or an empty list if timeout
        :rtype: a list of Object
        """
        msg = self.state.socket_interface.receive()
        self.logger.info("receive data : [" + repr(msg) + "]")
        return msg

    def kill(self, by_data=False):
        """
        Kill this actor by sending a
        :class:`PoisonPillMessage
        <powerapi.message.message.PoisonPillMessage>`

        :param bool by_data: Define if the kill msg is send in the control
                             socket or the data socket
        """
        if by_data:
            self.send_data(PoisonPillMessage())
        else:
            self.send_control(PoisonPillMessage())
        self.logger.info('send kill msg to ' + self.name)
        self.state.socket_interface.disconnect()
