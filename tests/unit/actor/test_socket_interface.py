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

from multiprocessing import Value

import pytest
from zmq import Socket, Poller, PAIR, PULL, PUSH, TYPE, LAST_ENDPOINT

from powerapi.actor import SocketInterface
from powerapi.message import Message


class DummyMessage(Message):
    """
    Message type used for testing the socket interface.
    """

    def __init__(self, content: str):
        super().__init__('pytest')
        self.content = content

    def __repr__(self):
        return f"{self.__class__.__name__}('{self.sender_name}', '{self.content}')"

    def __eq__(self, other) -> bool:
        if isinstance(other, self.__class__):
            return self.sender_name == other.sender_name and self.content == other.content

        return False


def check_socket(socket: Socket, socket_type: int, bind_address: Value):
    """
    Check if a socket have the expected type and is connected to a specific address.
    """
    assert isinstance(socket, Socket)
    assert socket.closed is False
    assert socket.get(TYPE) == socket_type

    socket_address = socket.get(LAST_ENDPOINT).decode("utf-8")
    assert socket_address == bind_address.value


@pytest.fixture()
def socket_interface():
    """
    Return a socket interface that haven't been initialized.
    """
    return SocketInterface('test-socket-interface')


@pytest.fixture()
def initialized_socket_interface(socket_interface):
    """
    Return an initialized socket interface.
    """
    socket_interface.setup()
    yield socket_interface
    socket_interface.close()


@pytest.fixture()
def connected_interface(initialized_socket_interface):
    """
    Return an initialized socket interface where only the data socket is connected.
    """
    initialized_socket_interface.connect_data()
    yield initialized_socket_interface
    initialized_socket_interface.close()


@pytest.fixture()
def controlled_interface(initialized_socket_interface):
    """
    Return an initialized socket interface where only the control socket is connected.
    """
    initialized_socket_interface.connect_control()
    yield initialized_socket_interface
    initialized_socket_interface.close()


@pytest.fixture()
def fully_connected_interface(initialized_socket_interface):
    """
    Return an initialized socket interface where the control and data socket are connected.

    """
    initialized_socket_interface.connect_data()
    initialized_socket_interface.connect_control()
    yield initialized_socket_interface
    initialized_socket_interface.close()


def test_close(initialized_socket_interface):
    """
    Test if the close method successfully close the connected control and data sockets.
    """
    assert initialized_socket_interface.data_socket_pull.closed is False
    assert initialized_socket_interface.control_socket_pull.closed is False

    initialized_socket_interface.close()

    assert initialized_socket_interface.data_socket_pull.closed is True
    assert initialized_socket_interface.control_socket_pull.closed is True


def test_data_control_sockets_setup(initialized_socket_interface):
    """
    Test if the setup method successfully open the control and data sockets.
    """
    check_socket(initialized_socket_interface.data_socket_pull, PULL, initialized_socket_interface.data_socket_addr)
    check_socket(initialized_socket_interface.control_socket_pull, PAIR, initialized_socket_interface.control_socket_addr)
    assert isinstance(initialized_socket_interface.poller, Poller)


def test_push_socket_setup(connected_interface):
    """
    Test if the push socket is open and connected to the data socket.
    """
    check_socket(connected_interface.data_socket_push, PUSH, connected_interface.data_socket_addr)


def test_data_disconnect(connected_interface):
    """
    Test if the disconnect method successfully close the data socket.
    """
    assert connected_interface.data_socket_push.closed is False
    connected_interface.close()
    assert connected_interface.data_socket_push.closed is True


def test_send_receive_data(connected_interface):
    """
    Test to send and receive a message from the data (PUSH/PULL) socket.
    """
    msg = DummyMessage('test-data-message')

    connected_interface.send_data(msg)
    assert connected_interface.receive_data(1000) == msg


def test_control_connect(controlled_interface):
    """
    Test if the control socket is successfully open.
    """
    check_socket(controlled_interface.control_socket_pull, PAIR, controlled_interface.control_socket_addr)


def test_control_disconnect(controlled_interface):
    """
    Test if the close method successfully disconnect the control socket.
    """
    assert controlled_interface.control_socket_pull.closed is False
    controlled_interface.close()
    assert controlled_interface.control_socket_pull.closed is True


def test_control_receive(controlled_interface):
    """
    Test to send and receive a message from the control (PAIR) socket.
    """
    msg = DummyMessage('test-control-message')

    controlled_interface.send_control(msg)
    assert controlled_interface.receive_control(1000) == msg


def test_multiple_send_receive(fully_connected_interface):
    """
    Test to send and receive messages from the control (PAIR) and data (PUSH/PULL) sockets.
    """
    control_msg = DummyMessage('test-control-message')
    data_msg = DummyMessage('test-data-message')

    fully_connected_interface.send_control(control_msg)
    assert fully_connected_interface.receive(1000) == control_msg

    fully_connected_interface.send_control(data_msg)
    assert fully_connected_interface.receive(1000) == data_msg
