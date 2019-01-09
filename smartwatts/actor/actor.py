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

"""
Module actors
"""

import os
import signal
import multiprocessing
import pickle
import setproctitle
import zmq

from smartwatts.message import PoisonPillMessage
from smartwatts.message import UnknowMessageTypeException
from smartwatts.actor import BasicState, SocketInterface


class Actor(multiprocessing.Process):
    """Abstract class that exposes an interface to create actor


    methods
    =========

    general methods :
    ------------------

    - :meth:~smartwatts.actor.actor.Actor.log

    client interface methods :
    -----------------------------

    - :meth:~smartwatts.actor.actor.Actor.connect
    - :meth:~smartwatts.actor.actor.Actor.monitor
    - :meth:~smartwatts.actor.actor.Actor.send_monitor
    - :meth:~smartwatts.actor.actor.Actor.send
    - :meth:~smartwatts.actor.actor.Actor.kill

    server interface methods :
    ----------------------------

    - :meth:~smartwatts.actor.actor.Actor.setup
    - :meth:~smartwatts.actor.actor.Actor.get_corresponding_handler
    - :meth:~smartwatts.actor.actor.Actor.add_handler
    - :meth:~smartwatts.actor.actor.Actor.terminated_behaviour
    - :meth:~smartwatts.actor.actor.Actor.send_monitor

    attributes
    ============

    general attributes :
    -------------------

    - :attr:~smartwatts.actor.actor.Actor.verbose

    server interface attributes :
    ----------------------------

    - :attribute int timeout: time in millisecond to wait for a message before
                              activate the `timeout_behaviour`
    - :attribute state: actor's permanent values
    - :type state: smartwatts.actor.state.BasicState
    - :attribute timeout_ha ndler: function activated when no message was
                                   received since `timeout` milliseconds
    - :type timeout_handler:function
    - :attribute handlers: list of mapings between handler and message type that
                           the maped handler must handle
    - :type handlers: list of tuple (type, smartwatts.actor.state.BasicState)

    """

    def __init__(self, name, verbose=False, timeout=None):
        """
        Initialization and start of the process.

        :param str name: unique name that will be used to indentify the actor
                         communication socket
        :param bool verbose: allow to display log
        :param int timeout: if define, do something if no msg is recv every
                            timeout (in ms)
        """
        multiprocessing.Process.__init__(self, name=name)

        self.verbose = verbose
        self.timeout = timeout
        self.state = None
        self.timeout_handler = None
        self.handlers = []

    def log(self, message):
        """
        Print message if verbose mode is enable.

        :param str message: message to print

        """
        if self.verbose:
            print('[' + str(os.getpid()) + ']' + ' ' + message)

    def run(self):
        """
        code executed by the actor
        """
        # actors specific initialisation
        self.setup()

        while self.state.alive:
            self.state.behaviour(self)

        self._kill_process()

    def _signal_handler_setup(self):
        def term_handler(_, __):
            self._kill_process()
            exit(0)

        signal.signal(signal.SIGTERM, term_handler)
        signal.signal(signal.SIGINT, term_handler)

    def setup(self):
        """Set actor specific configuration :

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

    def get_corresponding_handler(self, msg):
        """ Return the handler corresponding to the given message type
        :raises UnknowMessageTypeException: if no handler could be find

        :param Object msg: the received message
        :return: the handler corresponding to the given message type
        :rtype: smartwatts.handler.AbstractHandler

        """
        for (msg_type, handler) in self.handlers:
            if isinstance(msg, msg_type):
                return handler

        raise UnknowMessageTypeException()

    def add_handler(self, message_type, handler):
        """ map a handler to a message type

        :param type message_type: type of the message that the handler can
                                  handle
        :param handler: handler that will handle all messages of the given type
        :type handler: smartwatts.handler.AbstractHandler
        """
        self.handlers.append((message_type, handler))

    def _initial_behaviour(self):
        """initial behaviour of an actor

        wait for a message, and handle it with the correct handler

        if the message is None, call the timout_handler otherwise find the
        handler correponding to the message type and call it on the message.

        """
        msg_list = self.state.socket_interface.receive()
        self.log('received : ' + str(msg_list))

        # Timeout
        if msg_list == []:
            self.state = self.timeout_handler.handle(None, self.state)
        else:
            for msg in msg_list:
                handler = self.get_corresponding_handler(msg)
                self.state = handler.handle_message(msg, self.state)

    def _kill_process(self):
        """ Kill the actor (close the pull socket)"""
        self.terminated_behaviour()
        self.state.socket_interface.close()

        self.log("terminated")

    def terminated_behaviour(self):
        """ function called before closing the pull socket

        Can be overiden to use personal actor termination behaviour
        """
        pass

    def connect(self, context):
        """
        open a canal that can be use for unidirectional communication to this
        actor

        :param context: ZMQ context of the process that want to
                        communicate with this actor
        :type context: zmq.Context
        """
        self.state.socket_interface.connect(context)
        self.log('connected to ' + self.name)

    def monitor(self, context):
        """
        open a monitor canal with this actor
        An actor can have only one monitor open at the same time

        Connect to the monitor socket of this actor

        open a pair socket on the process that want to monitor this actor

        :param context: ZMQ context of the process that want to
                        communicate with this actor
        :type context: zmq.Context

        """
        self.state.socket_interface.monitor(context)
        self.log('monitor' + self.name)

    def send_monitor(self, msg):
        """ Send a message on the monitor canal"""
        self.state.socket_interface.send_monitor(msg)

    def send(self, msg):
        """Send a msg to this actor using the data canal

        This function will not be used by this actor but by process that
        want to send message to this actor

        :param Object msg: the message to send to this actor

        """
        self.state.socket_interface.send(msg)
        self.log('sent ' + str(msg) + ' to ' + self.name)

    def kill(self):
        """kill this actor by sending a
        :class:~smartwatts.message.message.PoisonPillMessage

        """
        self.send_monitor(PoisonPillMessage())
        self.log('send kill msg to ' + str(self.name))
        self.state.socket_interface.disconnect()
