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

import os
from hashlib import blake2b
from typing import Any
from pathlib import Path

import zmq

from powerapi.exception import PowerAPIException


class NotConnectedException(PowerAPIException):
    """
    Exception raised when attempting to do an operation on a disconnected socket.
    """


class SocketInterface:
    """
    Interface to handle communication between actors.
    """

    def __init__(self, actor_name: str, timeout: int | None):
        """
        :param str actor_name: Name of the actor whose endpoint is being accessed
        :param int timeout: Maximum time, in milliseconds, to wait for an operation
        """
        self.actor_name = actor_name
        self.timeout = timeout

        self.data_socket_filepath = self._generate_socket_path(actor_name, 'data')
        self.control_socket_filepath = self._generate_socket_path(actor_name, 'control')

        self._control_socket: zmq.Socket | None = None
        self._data_socket: zmq.Socket | None = None
        self._sockets_poller: zmq.Poller | None = None
        self._is_endpoint: bool = False

    @staticmethod
    def _generate_socket_path(actor_name: str, socket_purpose: str, basedir: str = '/tmp') -> Path:
        """
        Generate a deterministic filesystem path for an IPC socket.
        :param actor_name: Name of the actor whose endpoint is being accessed
        :param socket_purpose: Purpose of the socket (control, data, etc.)
        :param basedir: Base directory used to store the socket
        """
        key = f'{actor_name}:{socket_purpose}'
        digest = blake2b(key.encode('utf-8'), digest_size=16).hexdigest()
        return Path(basedir) / f'powerapi-ipc-{digest}'

    def setup(self):
        """
        Initializes the socket interface.
        This method should only be called by the actor acting as endpoint.
        """
        self._is_endpoint = True

        self._control_socket = zmq.Context.instance().socket(zmq.DEALER)
        self._control_socket.setsockopt(zmq.LINGER, 0)
        self._control_socket.bind(f'ipc://{self.control_socket_filepath}')

        self._data_socket = zmq.Context.instance().socket(zmq.PULL)
        self._data_socket.bind(f'ipc://{self.data_socket_filepath}')

        self._sockets_poller = zmq.Poller()
        self._sockets_poller.register(self._control_socket, zmq.POLLIN)
        self._sockets_poller.register(self._data_socket, zmq.POLLIN)

    def close(self) -> None:
        """
        Closes the socket interface.
        """
        self._sockets_poller = None

        if self._control_socket is not None:
            self._control_socket.close()
            self._control_socket = None

        if self._data_socket is not None:
            self._data_socket.close()
            self._data_socket = None

        if self._is_endpoint:
            # Calling `close()` on the bound sockets doesn't remove the file when using the `ipc` transport protocol.
            # Manually unlinking files after calling `close()` is the most reliable way to fix it.
            self.control_socket_filepath.unlink(missing_ok=True)
            self.data_socket_filepath.unlink(missing_ok=True)

    @staticmethod
    def _send_serialized(socket: zmq.Socket, msg: Any) -> None:
        """
        Sends a serialized message to the given socket.
        :param socket: Socket to use
        :param msg: Message to serialize and send
        """
        socket.send_pyobj(msg)

    @staticmethod
    def _recv_serialized(socket: zmq.Socket) -> Any:
        """
        Receive, deserialize and returns a message from the given socket.
        :param socket: Socket to use
        :return: Message received
        """
        return socket.recv_pyobj()

    def connect_control(self) -> None:
        """
        Connect to the control socket of the actor.
        This method should only be called by actors that wants to communicate with another actor's endpoint.
        """
        self._control_socket = zmq.Context.instance().socket(zmq.DEALER)
        self._control_socket.setsockopt(zmq.LINGER, 0)
        self._control_socket.connect(f'ipc://{self.control_socket_filepath}')
        self._control_socket.poll(zmq.POLLIN | zmq.POLLOUT)  # Very important, prevents synchronization problems.

    def receive_control(self, timeout: int | None = None) -> Any:
        """
        Receive a message from the control socket of the actor.
        :param timeout: Timeout of the operation in milliseconds, if None block indefinitely
        :return: Message received
        """
        if self._control_socket is None:
            raise NotConnectedException()

        if self._control_socket.poll(timeout):
            return self._recv_serialized(self._control_socket)

        return None

    def send_control(self, msg: Any) -> None:
        """
        Send a message to the control socket of the actor.
        :param msg: Message to send
        """
        if self._control_socket is None:
            raise NotConnectedException()

        self._send_serialized(self._control_socket, msg)

    def connect_data(self) -> None:
        """
        Connect to the data socket of the actor.
        This method should only be called by actors that wants to communicate with another actor's endpoint.
        """
        self._data_socket = zmq.Context.instance().socket(zmq.PUSH)
        self._data_socket.setsockopt(zmq.LINGER, -1)
        self._data_socket.connect(f'ipc://{self.data_socket_filepath}')
        self._data_socket.poll(zmq.POLLOUT)  # Very important, prevents synchronization problems.

    def send_data(self, msg: Any) -> None:
        """
        Send a message to the data socket of the actor.
        :param msg: Message to send
        """
        if self._data_socket is None:
            raise NotConnectedException()

        self._send_serialized(self._data_socket, msg)

    def receive(self, timeout: int | None = None) -> Any:
        """
        Receive a message from either the control or the data sockets.
        This method should only be called by an actor acting as endpoint.
        :param timeout: Timeout of the operation in milliseconds, if None block indefinitely
        :return: The received message or None if the timeout is reached
        """
        if self._sockets_poller is None:
            raise NotConnectedException()

        for socket, _ in self._sockets_poller.poll(timeout):
            return self._recv_serialized(socket)

        return None
