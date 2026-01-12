# Copyright (c) 2022, Inria
# Copyright (c) 2022, University of Lille
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

import secrets
from pathlib import Path

import pytest
import zmq

from powerapi.actor import SocketInterface, NotConnectedException


def check_socket(socket: zmq.Socket, socket_type: int, socket_filepath: Path) -> None:
    """
    Checks if the given socket is open, bound to the correct address and have the correct type.
    :param socket: Socket instance to check
    :param socket_type: Expected socket type
    :param socket_filepath: Expected filepath of the IPC socket
    """
    assert isinstance(socket, zmq.Socket)
    assert socket.closed is False
    assert socket.get(zmq.TYPE) == socket_type

    socket_address = socket.getsockopt_string(zmq.LAST_ENDPOINT)
    assert socket_address == f'ipc://{socket_filepath}'


@pytest.fixture
def socket_interface():
    """
    Returns an uninitialized socket interface.
    """
    actor_name = f'pytest-{secrets.token_hex()}'  # Prevent collisions on IPC files between runs.
    return SocketInterface(actor_name, 100)


@pytest.fixture
def endpoint_interface(socket_interface):
    """
    Returns a socket interface acting as endpoint.
    """
    socket_interface.setup()
    yield socket_interface
    socket_interface.close()


@pytest.fixture
def data_peer_interface(socket_interface):
    """
    Returns a socket interface connected to the data socket.
    """
    socket_interface.connect_data()
    yield socket_interface
    socket_interface.close()


@pytest.fixture
def control_peer_interface(socket_interface):
    """
    Returns a socket interface connected to the control socket.
    """
    socket_interface.connect_control()
    yield socket_interface
    socket_interface.close()


@pytest.fixture
def peer_interface(socket_interface):
    """
    Returns a socket interface connected to both control and data sockets.
    """
    socket_interface.connect_data()
    socket_interface.connect_control()
    yield socket_interface
    socket_interface.close()


def test_close(endpoint_interface):
    """
    Test if the close method close both the control and data sockets.
    """
    assert endpoint_interface._data_socket is not None
    assert endpoint_interface._data_socket.closed is False
    assert endpoint_interface._control_socket is not None
    assert endpoint_interface._control_socket.closed is False

    endpoint_interface.close()

    assert endpoint_interface._data_socket is None
    assert endpoint_interface._control_socket is None


def test_setup(endpoint_interface):
    """
    Test if the setup method opens the control and data sockets.
    """
    assert isinstance(endpoint_interface._sockets_poller, zmq.Poller)

    check_socket(endpoint_interface._data_socket, zmq.PULL, endpoint_interface.data_socket_filepath)
    check_socket(endpoint_interface._control_socket, zmq.DEALER, endpoint_interface.control_socket_filepath)


def test_data_connect(endpoint_interface, data_peer_interface):
    """
    Test if the data socket is open.
    """
    check_socket(data_peer_interface._data_socket, zmq.PUSH, data_peer_interface.data_socket_filepath)


def test_data_disconnect(endpoint_interface, data_peer_interface):
    """
    Test if the disconnect method closes the data socket.
    """
    assert data_peer_interface._data_socket is not None
    assert data_peer_interface._data_socket.closed is False

    data_peer_interface.close()

    assert data_peer_interface._data_socket is None


def test_data_receive(endpoint_interface, data_peer_interface):
    """
    Test to send and receive a message from the data socket.
    """
    msg = 'test-data-msg'
    data_peer_interface.send_data(msg)
    recv_msg = data_peer_interface.receive()
    assert recv_msg == msg


def test_data_send_not_connected(socket_interface):
    """
    Test that sending a message to a disconnected data socket raises an error.
    """
    with pytest.raises(NotConnectedException):
        socket_interface.send_data('test-data-msg')


def test_control_connect(endpoint_interface, control_peer_interface):
    """
    Test if the control socket is open.
    """
    check_socket(control_peer_interface._control_socket, zmq.DEALER, control_peer_interface.control_socket_filepath)


def test_control_disconnect(endpoint_interface, control_peer_interface):
    """
    Test if the disconnect method closes the control socket.
    """
    assert control_peer_interface._control_socket is not None
    assert control_peer_interface._control_socket.closed is False

    control_peer_interface.close()

    assert control_peer_interface._control_socket is None


def test_control_send_not_connected(socket_interface):
    """
    Test that sending a message to a disconnected control socket raises an error.
    """
    with pytest.raises(NotConnectedException):
        socket_interface.send_control('test-control-msg')


def test_control_receive(endpoint_interface, control_peer_interface):
    """
    Test to send and receive a message from the control socket.
    """
    msg = 'test-control-msg'
    control_peer_interface.send_control(msg)
    recv_msg = control_peer_interface.receive()
    assert recv_msg == msg


def test_control_receive_not_connected(socket_interface):
    """
    Test that trying to receive a message from a disconnected control socket raises an error.
    """
    with pytest.raises(NotConnectedException):
        socket_interface.receive_control()


def test_control_receive_timeout(control_peer_interface):
    """
    Test reaching the timeout when trying to receive a message from the control socket.
    """
    msg = control_peer_interface.receive_control(timeout=100)
    assert msg is None


def test_multiple_receive(endpoint_interface, peer_interface):
    """
    Test to send and receive a message from both the control and the data sockets.
    """
    control_msg = 'test-control-msg'
    peer_interface.send_control(control_msg)
    recv_control_msg = endpoint_interface.receive()
    assert recv_control_msg == control_msg

    data_msg = 'test-data-msg'
    peer_interface.send_data(data_msg)
    recv_data_msg = peer_interface.receive()
    assert recv_data_msg == data_msg


def test_multiple_receive_not_connected(socket_interface):
    """
    Test that trying to receive a message from a disconnected socket interface raises an error.
    """
    with pytest.raises(NotConnectedException):
        socket_interface.receive()


def test_multiple_receive_timeout(endpoint_interface):
    """
    Test reaching the timeout when trying to receive a message from both the control and the data sockets.
    """
    msg = endpoint_interface.receive()
    assert msg is None
