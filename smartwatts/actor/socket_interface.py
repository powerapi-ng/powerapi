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
import zmq


class SocketInterface:
    """
    Interface to handle comunication to/from the actor

    methods
    =======

    general methods :

    - :meth:`send_monitor <smartwatts.actor.socket_interface.SocketInterface.send_monitor>`

    client interface methods :

    - :meth:`connect <smartwatts.actor.socket_interface.SocketInterface.connect>`
    - :meth:`disconnect <smartwatts.actor.socket_interface.SocketInterface.disconnect>`
    - :meth:`monitor <smartwatts.actor.socket_interface.SocketInterface.monitor>`
    - :meth:`send <smartwatts.actor.socket_interface.SocketInterface.send>`

    server interface methods :

    - :meth:`setup <smartwatts.actor.socket_interface.SocketInterface.setup>`
    - :meth:`receive <smartwatts.actor.socket_interface.SocketInterface.receive>`
    - :meth:`close <smartwatts.actor.socket_interface.SocketInterface.close>`
    """

    def __init__(self, name, timeout):
        """
        :param str name: name of the actor using this interface
        :param int timeout: time in millisecond to wait for a message
        """
        self.timeout = timeout
        self.pull_socket_address = 'ipc://@' + name
        self.monitor_socket_address = 'ipc://@monitor_' + name

        self.context = None
        self.poller = None

        self.pull_socket = None
        self.monitor_socket = None

        # This socket is used to connect to the pull socket of this actor. It
        # won't be created on the actor's process but on the process that want
        # to connect to the pull socket of this actor
        self.push_socket = None

    def setup(self):
        """
        Initialize zmq context and sockets
        """
        # Basic initialization for ZMQ.
        self.context = zmq.Context()
        self.poller = zmq.Poller()

        # create the pull socket (to communicate with this actor, others
        # process have to connect a push socket to this socket)
        self.pull_socket = self._create_socket(zmq.PULL,
                                               self.pull_socket_address)

        # create the monitor socket (to monitor this actor, a process have to
        # connect a pair socket to this socket with the `monitor` method)
        self.monitor_socket = self._create_socket(zmq.PAIR,
                                                  self.monitor_socket_address)

    def _create_socket(self, socket_type, socket_addr):
        """
        Create a socket of the given type, bind it to the given address and
        register it to the poller

        :param int socket_type: type of the socket to open
        :param str socket_addr: address of the socket to open
        :return zmq.Socket: the initialized socket
        """
        socket = self.context.socket(socket_type)
        socket.bind(socket_addr)
        self.poller.register(socket, zmq.POLLIN)
        return socket

    def receive(self):
        """
        Block until a message was received (or until timeout) an return the
        received messages

        :return: the list of received messages or an empty list if timeout
        :rtype: a list of Object
        """
        events = self.poller.poll(self.timeout)

        return [self._recv_serialized(socket) for socket, event in events
                if event == zmq.POLLIN]

    def close(self):
        """
        Close all socket handle by this interface
        """
        if self.pull_socket is not None:
            self.pull_socket.close()

        if self.monitor_socket is not None:
            self.monitor_socket.close()

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

    def connect(self, context):
        """
        Connect to the pull socket of this actor

        Open a push socket on the process that want to communicate with this
        actor

        :param zmq.Context context: ZMQ context of the process that want to
                                    communicate with this actor
        """
        self.push_socket = context.socket(zmq.PUSH)
        self.push_socket.connect(self.pull_socket_address)

    def disconnect(self):
        """
        Close connection to the pull socket and monitor socket of this actor
        """
        if self.push_socket is not None:
            self.push_socket.close()

        if self.monitor_socket is not None:
            self.monitor_socket.close()

    def monitor(self, context):
        """
        Connect to the monitor socket of this actor

        Open a pair socket on the process that want to monitor this actor

        :param zmq.Context context: ZMQ context of the process that want to
                                    monitor this actor
        """
        self.monitor_socket = context.socket(zmq.PAIR)
        self.monitor_socket.connect(self.monitor_socket_address)

    def send_monitor(self, msg):
        """
        Send a message on the monitor canal

        :param Object msg: message to send
        """
        self._send_serialized(self.monitor_socket, msg)

    def send(self, msg):
        """
        Send a message on data canal

        :param Object msg: message to send
        """
        self._send_serialized(self.push_socket, msg)
