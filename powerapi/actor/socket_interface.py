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

import pickle
import logging
import zmq
from powerapi.actor import SafeContext


class NotConnectedException(Exception):
    """
    Exception raised when attempting to send/receinve a message on a socket
    that is not conected
    """


class SocketInterface:
    """
    Interface to handle comunication to/from the actor

    general methods :

    - :meth:`send_control <powerapi.actor.socket_interface.SocketInterface.send_control>`

    client interface methods :

    - :meth:`connect_data <powerapi.actor.socket_interface.SocketInterface.connect_data>`
    - :meth:`connect_control <powerapi.actor.socket_interface.SocketInterface.connect_control>`
    - :meth:`send_data <powerapi.actor.socket_interface.SocketInterface.send_data>`
    - :meth:`close <powerapi.actor.socket_interface.SocketInterface.close>`

    server interface methods :

    - :meth:`setup <powerapi.actor.socket_interface.SocketInterface.setup>`
    - :meth:`receive <powerapi.actor.socket_interface.SocketInterface.receive>`
    - :meth:`close <powerapi.actor.socket_interface.SocketInterface.close>`
    """

    def __init__(self, name, timeout):
        """
        :param str name: name of the actor using this interface
        :param int timeout: time in millisecond to wait for a message
        """
        self.logger = logging.getLogger(name)

        #: (int): Time in millisecond to wait for a message before execute
        #:        timeout_handler
        self.timeout = timeout

        #: (str): Address of the pull socket
        self.pull_socket_address = 'ipc://@' + name

        #: (str): Address of the control socket
        self.control_socket_address = 'ipc://@control_' + name

        #: (zmq.Poller): ZMQ Poller for read many socket at same time
        self.poller = zmq.Poller()

        #: (zmq.Socket): ZMQ Pull socket for receiving data message
        self.pull_socket = None

        #: (zmq.Socket): ZMQ Pair socket for receiving control message
        self.control_socket = None

        # This socket is used to connect to the pull socket of this actor. It
        # won't be created on the actor's process but on the process that want
        # to connect to the pull socket of this actor
        #: (zmq.Socket): ZMQ Push socket for sending message to this actor
        self.push_socket = None

    def setup(self):
        """
        Initialize zmq context and sockets
        """
        # create the pull socket (to communicate with this actor, others
        # process have to connect a push socket to this socket)
        self.pull_socket = self._create_socket(zmq.PULL,
                                               self.pull_socket_address)

        # create the control socket (to control this actor, a process have to
        # connect a pair socket to this socket with the `control` method)
        self.control_socket = self._create_socket(zmq.PAIR,
                                                  self.control_socket_address)
        self.control_socket.set(zmq.LINGER, 0)

    def _create_socket(self, socket_type, socket_addr):
        """
        Create a socket of the given type, bind it to the given address and
        register it to the poller

        :param int socket_type: type of the socket to open
        :param str socket_addr: address of the socket to open
        :return zmq.Socket: the initialized socket
        """
        socket = SafeContext.get_context().socket(socket_type)
        socket.bind(socket_addr)
        self.poller.register(socket, zmq.POLLIN)
        self.logger.info("bind to " + str(socket_addr))
        return socket

    def receive(self):
        """
        Block until a message was received (or until timeout) an return the
        received messages

        :return: the list of received messages or None if timeout
        :rtype: a list of Object or None
        """
        events = self.poller.poll(self.timeout)

        # If there is control socket, he has the priority
        if len(events) == 2:
            return self._recv_serialized(self.control_socket)
        elif len(events) == 1:
            return self._recv_serialized(events[0][0])
        return None

    def receive_control(self, timeout):
        """
        Block until a message was received on the control canal (client side)
        (or until timeout) an return the received messages

        :return: the list of received messages or an empty list if timeout
        :rtype: a list of Object

        """
        if self.control_socket is None:
            raise NotConnectedException

        event = self.control_socket.poll(timeout)

        if event == 0:
            return None

        return self._recv_serialized(self.control_socket)

    def close(self):
        """
        Close all socket handle by this interface
        """
        if self.pull_socket is not None:
            self.pull_socket.close()

        if self.push_socket is not None:
            self.push_socket.close()

        if self.control_socket is not None:
            self.control_socket.close()

    def _send_serialized(self, socket, msg):
        """
        Send a serialized msg with pickle to the given socket

        :param zmq.Socket socket: socket used to send the message
        :param Object msg: message to send
        """
        socket.send(pickle.dumps(msg))

    def _recv_serialized(self, socket):
        """
        Wait for a message from the given socket and return its deserialized
        value (using pickle)

        :param zmq.Socket socket: socket to wait for a reception
        :return Object: the received message
        """
        msg = pickle.loads(socket.recv())
        return msg

    def connect_data(self):
        """
        Connect to the pull socket of this actor

        Open a push socket on the process that want to communicate with this
        actor
        """
        self.push_socket = SafeContext.get_context().socket(zmq.PUSH)
        self.push_socket.connect(self.pull_socket_address)

    def connect_control(self):
        """
        Connect to the control socket of this actor

        Open a pair socket on the process that want to control this actor
        """
        self.control_socket = SafeContext.get_context().socket(zmq.PAIR)
        self.control_socket.set(zmq.LINGER, 0)
        self.control_socket.connect(self.control_socket_address)

    def send_control(self, msg):
        """
        Send a message on the control canal

        :param Object msg: message to send
        """
        if self.control_socket is None:
            raise NotConnectedException()
        self._send_serialized(self.control_socket, msg)

    def send_data(self, msg):
        """
        Send a message on data canal

        :param Object msg: message to send
        """
        if self.push_socket is None:
            raise NotConnectedException()
        self._send_serialized(self.push_socket, msg)
