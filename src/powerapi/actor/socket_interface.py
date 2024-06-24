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
import pickle
from ctypes import c_wchar
from multiprocessing import Array, Event

from zmq import Context, Socket, Poller, PULL, PUSH, PAIR, POLLIN, LAST_ENDPOINT

from powerapi.exception import PowerAPIException
from powerapi.message import Message


class NotBoundException(PowerAPIException):
    """
    Exception raised when trying to connect to a socket that has not been bound.
    """


class NotConnectedException(PowerAPIException):
    """
    Exception raised when attempting to send/receive a message on a socket that is not connected.
    """


class AlreadyConnectedException(PowerAPIException):
    """
    Exception raised when attempting to connect to a socket that has already been connected.
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

        # Socket used to receive control messages from an actor.
        self.control_socket: Socket | None = None

        # Shared memory value used to store the control socket listen address. ('proto://addr:port')
        self.control_socket_addr = Array(c_wchar, 255)

        # Socket used to receive data messages from other actors.
        self.data_socket: Socket | None = None

        # Shared memory used to store the pull socket listen address. ('proto://addr:port')
        self.data_socket_addr = Array(c_wchar, 255)

        # Sockets poller used to know when either (control/data) sockets have message(s) waiting.
        self.poller: Poller | None = None

        # Event used to know when the control and data sockets have been bound and should be able to receive data.
        self.is_bound_event = Event()

    def __repr__(self):
        return f"{self.__class__.__name__}('{self.actor_name}')"

    @staticmethod
    def _bind_socket_random_port(socket_type: int, address: str = 'tcp://127.0.0.1') -> Socket:
        """
        Create a socket of the given type and bind it to the given address and a random port.
        :param socket_type: Type of socket to create
        :param address: Address to bind the socket to
        :return: Initialized socket listening to the given address
        """
        ctx = Context.instance()

        socket: Socket = ctx.socket(socket_type)
        socket.bind_to_random_port(address)
        return socket

    @staticmethod
    def _connect_socket(socket_type: int, address: str) -> Socket:
        """
        Create a socket of the given type and connect it to the given address.
        :param socket_type: Type of socket to create
        :param address: Address to connect the socket to
        :return: Initialized socket connected to the given address
        """
        ctx = Context.instance()

        socket: Socket = ctx.socket(socket_type)
        socket.connect(address)
        return socket

    def bind(self):
        """
        Bind the control and data sockets of the actor.
        This method should only be called when the actor is initializing.
        :return: True if successful, False otherwise.
        """
        if self.is_bound_event.is_set():
            return

        logging.debug('Setting up "%s" actor control and data sockets...', self.actor_name)

        # Create the PAIR socket used to receive control messages from other actors.
        # Other actors needs to connect a PAIR socket to do so.
        self.control_socket = self._bind_socket_random_port(PAIR)
        self.control_socket_addr.get_obj().value = self.control_socket.get(LAST_ENDPOINT).decode('utf-8')
        logging.debug('Bound "%s" actor control socket to: %s', self.actor_name, self.control_socket_addr.get_obj().value)

        # Create the PULL socket used to receive data messages from other actors.
        # Other actors needs to connect a PUSH socket to do so.
        self.data_socket = self._bind_socket_random_port(PULL)
        self.data_socket_addr.get_obj().value = self.data_socket.get(LAST_ENDPOINT).decode('utf-8')
        logging.debug('Bound "%s" actor data socket to: %s', self.actor_name, self.data_socket_addr.get_obj().value)

        # Register the sockets to the poller. (order *IS* important, control socket should have priority)
        self.poller = Poller()
        self.poller.register(self.control_socket, POLLIN)
        self.poller.register(self.data_socket, POLLIN)

        self.is_bound_event.set()

    def unbind(self):
        """
        Unbind the control and data sockets of the actor.
        This method should only be called when the actor is terminated.
        """
        if not self.is_bound_event.is_set():
            return

        logging.debug('Unbinding "%s" actor control and data sockets...', self.actor_name)

        self.control_socket.close()
        self.control_socket = None
        self.control_socket_addr.get_obj().value = ''

        self.data_socket.close()
        self.data_socket = None
        self.data_socket_addr.get_obj().value = ''

        self.is_bound_event.clear()

    def connect(self):
        """
        Connect to the control and data sockets of the actor.
        This method should be called by other actors wanting to communicate with this actor.
        :raises NotBoundException: When attempting to connect to sockets that are not bound.
        """
        if not self.is_bound_event.is_set():
            raise NotBoundException

        logging.debug('Connecting sockets to "%s" actor...', self.actor_name)
        self.connect_control()
        self.connect_data()

    def disconnect(self):
        """
        Disconnect from the control and data sockets of the actor.
        This method should be called by other actors wanting to close their sockets connected to the actor.
        """
        if not self.is_bound_event.is_set():
            raise NotBoundException

        self.disconnect_control()
        self.disconnect_data()

    def receive(self, timeout: int | None = None) -> Message | None:
        """
        Receive a message from either the control or the data socket.
        :param timeout: Time in millisecond to wait for a message (None for waiting forever)
        :return: Received message or None when timeout is reached
        """
        if self.poller is None:
            raise NotBoundException

        events = dict(self.poller.poll(timeout))
        if len(events) == 0:
            return None

        socket: Socket = next(iter(events))
        return pickle.loads(socket.recv())

    def connect_control(self):
        """
        Connect to the control socket of the interface.
        This channel should be used to send lifecycle messages to the actor.
        """
        if not self.is_bound_event.is_set():
            raise NotBoundException

        dst_address = self.control_socket_addr.get_obj().value
        self.control_socket = self._connect_socket(PAIR, dst_address)
        logging.debug('Connected control socket (%s) to "%s" actor', dst_address, self.actor_name)

    def disconnect_control(self):
        """
        Disconnect from the control socket of the interface.
        """
        if self.control_socket is None:
            return

        self.control_socket.close()
        self.control_socket = None
        logging.debug('Disconnected control socket to "%s" actor', self.actor_name)

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

        return pickle.loads(self.control_socket.recv())

    def send_control(self, msg: Message):
        """
        Send a message to the control socket.
        :param msg: Message to send
        """
        if self.control_socket is None:
            raise NotConnectedException

        self.control_socket.send(pickle.dumps(msg, pickle.HIGHEST_PROTOCOL))

    def connect_data(self):
        """
        Connect to the data socket of the interface.
        This channel should be used to send data messages to be processed by the actor.
        """
        if not self.is_bound_event.is_set():
            raise NotBoundException

        dst_address = self.data_socket_addr.get_obj().value
        self.data_socket = self._connect_socket(PUSH, dst_address)
        logging.debug('Connected data socket (%s) to "%s" actor', dst_address, self.actor_name)

    def disconnect_data(self):
        """
        Disconnect from the data socket of the interface.
        """
        if self.data_socket is None:
            return

        self.data_socket.close()
        self.data_socket = None
        logging.debug('Disconnected data socket to "%s" actor', self.actor_name)

    def receive_data(self, timeout: int | None = None) -> Message | None:
        """
        Receive a message from the data socket.
        :param timeout: Time in millisecond to wait for a message (None for waiting forever)
        :return: Received message or None when timeout is reached
        """
        if self.data_socket is None or self.data_socket.type is not PULL:
            raise NotConnectedException

        event = self.data_socket.poll(timeout)
        if event == 0:
            return None

        return pickle.loads(self.data_socket.recv())

    def send_data(self, msg: Message):
        """
        Send a message to the data socket.
        :param msg: Message to send
        """
        if self.data_socket is None or self.data_socket.type is not PUSH:
            raise NotConnectedException

        self.data_socket.send(pickle.dumps(msg, pickle.HIGHEST_PROTOCOL))
