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
    """
    Abstract class of Actor.
    An actor is a process.
    """

    def __init__(self, name, verbose=False, timeout=None):
        """
        Initialization and start of the process.

        Parameters:
            @name(str): unique name that will be used to indentify the actor
                        communication socket
            @verbose(bool): allow to display log
            @timeout(int): if define, do something if no msg is recv every
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
        """
        Define actor specific processing that is run before entering the Run
        Loop
        """
        # Name process
        setproctitle.setproctitle(self.name)
        self.state.socket_interface.setup()

        self.log('I\'m ' + self.name)

        self._signal_handler_setup()

    def get_corresponding_handler(self, msg):
        """ Return the handler corresponding to the given message type
        Raise UnknowMessageTypeException if no handler could be find
        """
        for (msg_type, handler) in self.handlers:
            if isinstance(msg, msg_type):
                return handler

        raise UnknowMessageTypeException()

    def add_handler(self, message_type, handler):
        """ map a handler to a message type
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

        Parameters:
            context(zmq.Context): ZMQ context of the process that want to
                                  communicate with this actor

        """
        self.state.socket_interface.connect(context)
        self.log('connected to ' + self.name)

    def monitor(self, context):
        """
        open a monitor canal with this actor
        An actor can have only one monitor open at the same time

        Connect to the monitor socket of this actor

        open a pair socket on the process that want to monitor this actor

        parameters:
            context(zmq.Context): ZMQ context of the process that want to
                                  monitor this actor

        """
        self.state.socket_interface.monitor(context)
        self.log('monitor' + self.name)

    def send_monitor(self, msg):
        """ (PROCESS_SIDE) Send a message to this actor using monitor canal"""
        self.state.socket_interface.send_monitor(msg)

    def send(self, msg):
        """(PROCESS_SIDE) Send a msg to this actor

        This function will not be used by this actor but by process that
        want to send message to this actor
        """
        self.state.socket_interface.send(msg)
        self.log('sent ' + str(msg) + ' to ' + self.name)

    def kill(self):
        """
        (PROCESS_SIDE) kill this actor by sending a PoisonPillMessage message
        """
        self.send_monitor(PoisonPillMessage())
        self.log('send kill msg to ' + str(self.name))
        self.state.socket_interface.disconnect()
