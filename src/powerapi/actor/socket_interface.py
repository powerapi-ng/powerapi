# Copyright (c) 2018, Inria
# Copyright (c) 2018, University of Lille
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import logging
from ctypes import c_wchar_p
from multiprocessing import Value, Event

from zmq import Context, Socket, Poller, PULL, PUSH, PAIR, POLLIN

from powerapi.exception import PowerAPIException
from powerapi.message import Message


class NotConnectedException(PowerAPIException):
    """
    Exception raised when attempting to send/receive a message on a socket that is not connected.
    """


class SocketInterface:
    """
    Socket Interface class.
    Handles the inter-actor (multiprocessing) communication using ZeroMQ sockets.
    """

    def __init__(self, actor_name: str):
        """
        :param str actor_name: name of the actor using this interface
        """
        self.actor_name = actor_name

        # Socket used to send/receive control messages to an actor.
        self.control_socket: Socket | None = None

        # Shared memory value used to store the control socket listen address.
        self.control_socket_addr = Value(c_wchar_p)

        # Socket used to receive data messages from other actors.
        self.pull_socket: Socket | None = None

        # Shared memory used to store the pull socket listen address.
        self.pull_socket_addr = Value(c_wchar_p)

        # Socket used to send data messages to the actor.
        self.push_socket: Socket | None = None

        # Sockets poller used to know when either (control/data) sockets have message(s) waiting.
        self.poller: Poller | None = None

        # Event used to know when a socket interface have been initialized and should be operational.
        self._is_setup_event = Event()

    def __repr__(self):
        return f"{self.__class__.__name__}('{self.actor_name}')"

    @staticmethod
    def _bind_socket_random_port(socket_type: int, address: str = 'tcp://localhost') -> tuple[Socket, str]:
        """
        Create a socket of the given type and bind it to the given address and a random port.
        :param socket_type: Type of socket to create
        :param address: Address to bind the socket to
        :return: Initialized socket and the address (proto://addr:port) it is listening to.
        """
        ctx = Context.instance()

        socket: Socket = ctx.socket(socket_type)
        port_number = socket.bind_to_random_port(address)

        return socket, f'{address}:{port_number}'

    @staticmethod
    def _connect_socket(socket_type: int, address: str) -> Socket:
        """
        Create a socket of the given type and connect it to the given address.
        :param socket_type: Type of socket to create
        :param address: Address to connect the socket to
        :return: Initialized socket
        """
        ctx = Context.instance()

        socket: Socket = ctx.socket(socket_type)
        socket.connect(address)

        return socket

    def setup(self):
        """
        Initialize the socket interface.
        """
        if self._is_setup_event.is_set():
            logging.warning('The socket interface of "%s" is already initialized.', self.actor_name)
            return

        logging.debug('Setting up "%s" socket interface...', self.actor_name)

        # Create the PULL socket used to receive data messages from other actors.
        # Other actors needs to connect a PUSH socket to do so.
        self.pull_socket, self.pull_socket_addr.value = self._bind_socket_random_port(PULL)
        logging.debug('Bound "%s" pull socket to : %s', self.actor_name, self.pull_socket_addr.value)

        # Create the PAIR socket used to receive control messages from other actors.
        # Other actors needs to connect a PAIR socket to do so.
        self.control_socket, self.control_socket_addr.value = self._bind_socket_random_port(PAIR)
        logging.debug('Bound "%s" control socket to : %s', self.actor_name, self.control_socket_addr.value)

        # Register the "data" and "control" sockets to the poller. (order *IS* important)
        self.poller = Poller()
        self.poller.register(self.control_socket, POLLIN)
        self.poller.register(self.pull_socket, POLLIN)

        self._is_setup_event.set()

    def close(self):
        """
        Close the socket interface.
        """
        if not self._is_setup_event.is_set():
            logging.warning('The socket interface of "%s" is already closed.', self.actor_name)
            return

        logging.debug('Closing "%s" socket interface...', self.actor_name)

        if self.push_socket is not None:
            self.push_socket.close()

        if self.pull_socket is not None:
            self.pull_socket.close()

        if self.control_socket is not None:
            self.control_socket.close()

    def receive(self, timeout: int | None = None) -> Message | None:
        """
        Receive a message from either the control or the data socket.
        :param timeout: Time in millisecond to wait for a message (None for waiting forever)
        :return: Received message or None when timeout is reached
        """
        events = dict(self.poller.poll(timeout))
        if len(events) == 0:
            return None

        socket: Socket = next(iter(events))
        return socket.recv_pyobj()

    def connect_control(self):
        """
        Connect to the control socket of the interface.
        This channel should be used to send lifecycle messages to the actor.
        """
        if not self._is_setup_event.is_set():
            logging.error('Socket interface of "%s" is not initialized', self.actor_name)
            raise NotConnectedException

        self.control_socket = self._connect_socket(PAIR, self.control_socket_addr.value)
        logging.debug('Connected to "%s" control socket (%s)', self.actor_name, self.control_socket_addr.value)

    def receive_control(self, timeout: int | None = None) -> Message | None:
        """
        Receive a message from the control socket.
        :param timeout: Time in millisecond to wait for a message (None for waiting forever)
        :return: Received message or None when timeout is reached
        """
        if self.control_socket is None:
            raise NotConnectedException

        event = self.control_socket.poll(timeout)
        if event == 0:
            return None

        return self.control_socket.recv_pyobj()

    def send_control(self, msg: Message):
        """
        Send a message to the control socket.
        :param msg: Message to send
        """
        if self.control_socket is None:
            raise NotConnectedException

        self.control_socket.send_pyobj(msg)

    def connect_data(self):
        """
        Connect to the data socket of the interface.
        This channel should be used to send data messages to be processed by the actor.
        """
        if not self._is_setup_event.is_set():
            logging.error('Socket interface of "%s" is not initialized', self.actor_name)
            raise NotConnectedException

        self.push_socket = self._connect_socket(PUSH, self.pull_socket_addr.value)
        logging.debug('Connected to "%s" data socket (%s)', self.actor_name, self.pull_socket_addr.value)

    def receive_data(self, timeout: int | None = None) -> Message | None:
        """
        Receive a message from the data socket.
        :param timeout: Time in millisecond to wait for a message (None for waiting forever)
        :return: Received message or None when timeout is reached
        """
        if self.pull_socket is None:
            raise NotConnectedException

        event = self.pull_socket.poll(timeout)
        if event == 0:
            return None

        return self.pull_socket.recv_pyobj()

    def send_data(self, msg: Message):
        """
        Send a message to the data socket.
        :param msg: Message to send
        """
        if self.push_socket is None:
            raise NotConnectedException

        self.push_socket.send_pyobj(msg)
