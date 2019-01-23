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

import os
import signal
import multiprocessing
import setproctitle

from smartwatts.message import PoisonPillMessage
from smartwatts.message import UnknowMessageTypeException
from smartwatts.handler import HandlerException


class Actor(multiprocessing.Process):
    """
    Abstract class that exposes an interface to create, setup and handle actors

    :Method Interface:

    This table list from wich interface each methods are accessible

    +---------------------------------+--------------------------------------------------------------------------------------------+
    |  Interface type                 |                                   method name                                              |
    +=================================+============================================================================================+
    | Accessible from Client/Server   | :meth:`log <smartwatts.actor.actor.Actor.log>`                                             |
    +---------------------------------+--------------------------------------------------------------------------------------------+
    | Client interface                | :meth:`connect_data <smartwatts.actor.actor.Actor.connect_data>`                           |
    |                                 +--------------------------------------------------------------------------------------------+
    |                                 | :meth:`connect_control <smartwatts.actor.actor.Actor.connect_control>`                     |
    |                                 +--------------------------------------------------------------------------------------------+
    |                                 | :meth:`send_control <smartwatts.actor.actor.Actor.send_control>`                           |
    |                                 +--------------------------------------------------------------------------------------------+
    |                                 | :meth:`send_data <smartwatts.actor.actor.Actor.send_data>`                                 |
    |                                 +--------------------------------------------------------------------------------------------+
    |                                 | :meth:`kill <smartwatts.actor.actor.Actor.kill>`                                           |
    +---------------------------------+--------------------------------------------------------------------------------------------+
    | Server interface                | :meth:`setup <smartwatts.actor.actor.Actor.setup>`                                         |
    |                                 +--------------------------------------------------------------------------------------------+
    |                                 | :meth:`add_handler <smartwatts.actor.actor.Actor.add_handler>`                             |
    |                                 +--------------------------------------------------------------------------------------------+
    |                                 | :meth:`terminated_behaviour <smartwatts.actor.actor.Actor.terminated_behaviour>`           |
    |                                 +--------------------------------------------------------------------------------------------+
    |                                 | :meth:`send_control <smartwatts.actor.actor.Actor.send_control>`                           |
    +---------------------------------+--------------------------------------------------------------------------------------------+

    :Attributes Interface:
    
    This table list from wich interface each attributes are accessible

    +---------------------------------+--------------------------------------------------------------------------------------------+
    |  Interface type                 |                                   method name                                              |
    +---------------------------------+--------------------------------------------------------------------------------------------+
    | Accessible from Client/Server   | :attr:`verbose <smartwatts.actor.actor.Actor.verbose>`                                     |
    +---------------------------------+--------------------------------------------------------------------------------------------+
    | Server interface                | :attr:`timeout <smartwatts.actor.actor.Actor.timeout>`                                     |
    |                                 +--------------------------------------------------------------------------------------------+
    |                                 | :attr:`state <smartwatts.actor.actor.Actor.state>`                                         |
    |                                 +--------------------------------------------------------------------------------------------+
    |                                 | :attr:`timeout_handler <smartwatts.actor.actor.Actor.timeout_handler>`                     |
    +---------------------------------+--------------------------------------------------------------------------------------------+

    """

    def __init__(self, name, verbose=False, timeout=None):
        """
        Initialization and start of the process.

        :param str name: unique name that will be used to indentify the actor
                         processus
        :param bool verbose: allow to display log
        :param int timeout: if define, do something if no msg is recv every
                            timeout (in ms)
        """
        multiprocessing.Process.__init__(self, name=name)

        #: (bool): allow to display log
        self.verbose = verbose
        #: (int): time in millisecond to wait for a message before
        #: activate the `timeout_behaviour`
        self.timeout = timeout
        #: (smartwatts.actor.state.BasicState): actor's state
        self.state = None
        #: (function): function activated when no message was
        #: received since `timeout` milliseconds
        self.timeout_handler = None

    def log(self, message):
        """
        Print message if verbose mode is enable.

        :param str message: message to print
        """
        if self.verbose:
            print('[' + str(os.getpid()) + ']' + ' ' + message)

    def run(self):
        """
        Main code executed by the actor
        """
        self.setup()

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

    def setup(self):
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

        self.log('I\'m ' + self.name)

        self._signal_handler_setup()

        raise UnknowMessageTypeException()

    def add_handler(self, message_type, handler):
        """
        Map a handler to a message type

        :param type message_type: type of the message that the handler can
                                  handle
        :param handler: handler that will handle all messages of the given type
        :type handler: smartwatts.handler.Handler
        """
        self.state.add_handler(message_type, handler)

    def _initial_behaviour(self):
        """
        Initial behaviour of an actor

        Wait for a message, and handle it with the correct handler

        If the message is None, call the timout_handler otherwise find the
        handler correponding to the message type and call it on the message.
        """
        msg_list = self.state.socket_interface.receive()
        self.log('received : ' + str(msg_list))

        # Timeout
        if msg_list == []:
            self.state = self.timeout_handler.handle(None, self.state)
        # Message
        else:
            for msg in msg_list:
                handler = self.state.get_corresponding_handler(msg)
                self.state = handler.handle_message(msg, self.state)

    def _kill_process(self):
        """
        Kill the actor (close sockets)
        """
        self.terminated_behaviour()
        self.state.socket_interface.close()
        self.log("terminated")

    def terminated_behaviour(self):
        """
        Function called before closing sockets

        Can be overriden to use personal actor termination behaviour
        """
        pass

    def connect_data(self, context):
        """
        Open a canal that can be use for unidirectional communication to this
        actor

        :param context: ZMQ context of the process that want to
                        communicate with this actor
        :type context: zmq.Context
        """
        self.state.socket_interface.connect_data(context)
        self.log('connected to ' + self.name)

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
        self.log('control' + self.name)

    def send_control(self, msg):
        """
        Send a message to this actor on the control canal

        :param Object msg: the message to send to this actor
        """
        self.state.socket_interface.send_control(msg)

    def send_data(self, msg):
        """
        Send a msg to this actor using the data canal

        :param Object msg: the message to send to this actor
        """
        self.state.socket_interface.send_data(msg)
        self.log('sent ' + str(msg) + ' to ' + self.name)

    def kill(self):
        """
        Kill this actor by sending a
        :class:`PoisonPillMessage
        <smartwatts.message.message.PoisonPillMessage>`
        """
        self.send_control(PoisonPillMessage())
        self.log('send kill msg to ' + str(self.name))
        self.state.socket_interface.disconnect()
