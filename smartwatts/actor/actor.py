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
from smartwatts.actor import BasicState


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

        # Value used
        # This socket is used to connect to the pull socket of this actor. It
        # won't be created on the actor's process but on the process that want
        # to connect to the pull socket of this actor
        self.push_socket = None

        self.verbose = verbose
        self.state = BasicState(self._initial_behaviour)
        self.timeout = timeout

        self.pull_socket_address = 'ipc://@' + self.name
        self.monitor_socket_address = 'ipc://@monitor_' + self.name

        self.context = None
        self.pull_socket = None
        self.monitor_socket = None
        self.poller = None

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

        self._communication_setup()

        self._signal_handler_setup()
        # actors specific initialisation
        self.setup()

        while self.state.alive:
            self.state.behaviour(self)

        self._kill_process()

    def __create_socket(self, socket_type, socket_addr):
        """create a socket of the given type, bind it to the given address and
        register it to the poller

        Return:
            (zmq.Socket): the initialized socket
        """
        socket = self.context.socket(socket_type)
        socket.bind(socket_addr)
        self.poller.register(socket, zmq.POLLIN)
        return socket

    def _communication_setup(self):
        """ Initialize zmq context and sockets """
        # Name process
        setproctitle.setproctitle(self.name)

        # Basic initialization for ZMQ.
        self.context = zmq.Context()
        self.poller = zmq.Poller()

        # create the pull socket (to communicate with this actor, others
        # process have to connect a push socket to this socket)
        self.pull_socket = self.__create_socket(zmq.PULL,
                                                self.pull_socket_address)

        # create the monitor socket (to monitor this actor, a process have to
        # connect a pair socket to this socket with the `monitor` method)
        self.monitor_socket = self.__create_socket(zmq.PAIR,
                                                   self.monitor_socket_address)

        self.log('I\'m ' + self.name)
        self.log("running on address " + self.pull_socket_address)

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
        raise NotImplementedError

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

    def receive(self):
        """ Wait for messages and return them

        Return: a list of received messages since the last receive call
                or [] if timeout
        """
        events = self.poller.poll(self.timeout)

        return [self._recv_serialized(socket) for socket, event in events
                if event == zmq.POLLIN]

    def _initial_behaviour(self):
        """initial behaviour of an actor

        wait for a message, and handle it with the correct handler

        if the message is None, call the timout_handler otherwise find the
        handler correponding to the message type and call it on the message.

        """
        msg_list = self.receive()

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
        if self.pull_socket is not None:
            self.pull_socket.close()

        if self.monitor_socket is not None:
            self.monitor_socket.close()

        self.log("terminated")

    def terminated_behaviour(self):
        """ function called before closing the pull socket

        Can be overiden to use personal actor termination behaviour
        """
        pass

    def _send_serialized(self, socket, msg):
        """
        Allow to send a serialized msg with pickle
        """
        socket.send(pickle.dumps(msg))
        self.log('sent ' + str(msg) + ' to ' + self.name)

    def _recv_serialized(self, socket):
        """
        Allow to recv a serialized msg with pickle
        """
        msg = pickle.loads(socket.recv())
        self.log('received : ' + str(msg))
        return msg

    def connect(self, context):
        """
        Connect to the pull socket of this actor

        open a push socket on the process that want to communicate with this
        actor

        parameters:
            context(zmq.Context): ZMQ context of the process that want to
                                  communicate with this actor

        """
        self.push_socket = context.socket(zmq.PUSH)
        self.push_socket.connect(self.pull_socket_address)
        self.log('connected to ' + self.pull_socket_address)

    def monitor(self, context):
        """
        Connect to the monitor socket of this actor

        open a pair socket on the process that want to monitor this actor

        parameters:
            context(zmq.Context): ZMQ context of the process that want to
                                  monitor this actor

        """
        self.monitor_socket = context.socket(zmq.PAIR)
        self.monitor_socket.connect(self.monitor_socket_address)
        self.log('monitor' + self.name)

    def send_monitor(self, msg):
        """ Send a msg to using monitor communication"""
        self._send_serialized(self.monitor_socket, msg)

    def send(self, msg):
        """(PROCESS_SIDE) Send a msg to this actor

        This function will not be used by this actor but by process that
        want to send message to this actor
        """
        self._send_serialized(self.push_socket, msg)

    def kill(self):
        """
        kill this actor by sending a PoisonPillMessage message
        """
        self.send(PoisonPillMessage())
        self.log('send kill msg to ' + str(self.name))
        self.push_socket.close()
