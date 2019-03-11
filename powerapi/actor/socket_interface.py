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

import pickle
import logging
import multiprocessing
import ctypes

import zmq
from powerapi.actor import SafeContext

LOCAL_ADDR = 'tcp://127.0.0.1'


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
        self.pull_socket_address = None

        #: (str): Address of the control socket
        self.control_socket_address = None

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

        # Shared memory used to communicate the port used to bind sockets
        self._pull_port = multiprocessing.Value(ctypes.c_int)
        self._ctrl_port = multiprocessing.Value(ctypes.c_int)
        self._values_available = multiprocessing.Event()

        self._pull_port.value = -1
        self._ctrl_port.value = -1

    def setup(self):
        """
        Initialize sockets and send the selected port number to the father
        process with a Pipe
        """
        # create the pull socket (to communicate with this actor, others
        # process have to connect a push socket to this socket)
        self.pull_socket, pull_port = self._create_socket(zmq.PULL, -1)

        # create the control socket (to control this actor, a process have to
        # connect a pair socket to this socket with the `control` method)
        self.control_socket, ctrl_port = self._create_socket(zmq.PAIR, 0)

        self.pull_socket_address = LOCAL_ADDR + ':' + str(pull_port)
        self.control_socket_address = LOCAL_ADDR + ':' + str(ctrl_port)

        self._pull_port.value = pull_port
        self._ctrl_port.value = ctrl_port
        self._values_available.set()

    def _create_socket(self, socket_type, linger_value):
        """
        Create a socket of the given type, bind it to a random port and
        register it to the poller

        :param int socket_type: type of the socket to open
        :param int linger_value: -1 mean wait for receive all msg and block
                                 closing 0 mean hardkill the socket even if msg
                                 are still here.
        :return (zmq.Socket, int): the initialized socket and the port where the
                                   socket is bound
        """
        socket = SafeContext.get_context().socket(socket_type)
        socket.setsockopt(zmq.LINGER, linger_value)
        socket.set_hwm(0)
        port_number = socket.bind_to_random_port(LOCAL_ADDR)
        self.poller.register(socket, zmq.POLLIN)
        self.logger.info("bind to " + LOCAL_ADDR + ':' + str(port_number))
        return (socket, port_number)

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
        if self.push_socket is not None:
            self.push_socket.close()

        if self.pull_socket is not None:
            self.pull_socket.close()

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

        this method shouldn't be called if socket interface was not initialized
        with the setup method
        """

        if self.pull_socket_address is None:
            self._values_available.wait()
            self.pull_socket_address = LOCAL_ADDR + ':' + str(self._pull_port.value)
            self.control_socket_address = LOCAL_ADDR + ':' + str(self._ctrl_port.value)

        self.push_socket = SafeContext.get_context().socket(zmq.PUSH)
        self.push_socket.setsockopt(zmq.LINGER, -1)
        self.push_socket.set_hwm(0)
        self.push_socket.connect(self.pull_socket_address)
        self.logger.info("connected data to %s" % (self.pull_socket_address))

    def connect_control(self):
        """
        Connect to the control socket of this actor

        Open a pair socket on the process that want to control this actor
        this method shouldn't be called if socket interface was not initialized
        with the setup method
        """
        if self.pull_socket_address is None:
            self._values_available.wait()
            self.pull_socket_address = LOCAL_ADDR + ':' + str(self._pull_port.value)
            self.control_socket_address = LOCAL_ADDR + ':' + str(self._ctrl_port.value)

        self.control_socket = SafeContext.get_context().socket(zmq.PAIR)
        self.control_socket.setsockopt(zmq.LINGER, 0)
        self.control_socket.set_hwm(0)
        self.control_socket.connect(self.control_socket_address)
        self.logger.info("connected control to %s" % (self.control_socket_address))

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
