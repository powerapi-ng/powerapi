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
Test powerapi.actor.SocketInterface
"""

import pytest
import zmq

from powerapi.actor import SocketInterface


ACTOR_NAME = 'dummy_actor'
PULL_SOCKET_ADDRESS = 'ipc://@' + ACTOR_NAME
CONTROL_SOCKET_ADDRESS = 'ipc://@' + 'control_' + ACTOR_NAME


def check_socket(socket, socket_type, bind_address):
    """check if the given socket is open, binded to the correct address and have
    the correct type

    """
    assert isinstance(socket, zmq.Socket)
    assert socket.closed is False
    assert socket.get(zmq.TYPE) == socket_type

    socket_address = socket.get(zmq.LAST_ENDPOINT).decode("utf-8")
    assert socket_address == bind_address


@pytest.fixture()
def socket_interface():
    """Return a socket interface not initialized

    """
    return SocketInterface(ACTOR_NAME, 100)

@pytest.fixture()
def initialized_socket_interface(socket_interface):
    """Return an initialized socket interface

    close the socket interface after testing

    """
    socket_interface.setup()
    yield socket_interface
    socket_interface.close()


@pytest.fixture()
def connected_interface(initialized_socket_interface):
    """ Return an initialized socket interface with an open connection to the
    push socket

    """
    initialized_socket_interface.connect_data()
    yield initialized_socket_interface
    initialized_socket_interface.close()


@pytest.fixture()
def controlled_interface(initialized_socket_interface):
    """ Return an initialized socket interface with an open connection to the
    control socket

    """
    initialized_socket_interface.connect_control()
    yield initialized_socket_interface
    initialized_socket_interface.close()


@pytest.fixture()
def fully_connected_interface(initialized_socket_interface):
    """ Return an initialized socket interface with an open connection to the
    control and the push socket

    """
    initialized_socket_interface.connect_data()
    initialized_socket_interface.connect_control()
    yield initialized_socket_interface
    initialized_socket_interface.close()


def test_socket_initialisation(socket_interface):
    """ test socket interface attribute initialisation
    """
    assert socket_interface.pull_socket_address == PULL_SOCKET_ADDRESS
    assert socket_interface.control_socket_address == CONTROL_SOCKET_ADDRESS


def test_close(initialized_socket_interface):
    """ test if the close method close the control and pull socket
    """
    assert initialized_socket_interface.pull_socket.closed is False
    assert initialized_socket_interface.control_socket.closed is False

    initialized_socket_interface.close()

    assert initialized_socket_interface.pull_socket.closed is True
    assert initialized_socket_interface.control_socket.closed is True


def test_setup(initialized_socket_interface):
    """ test if the setup method open the control and pull socket
    """
    assert isinstance(initialized_socket_interface.poller, zmq.Poller)

    check_socket(initialized_socket_interface.pull_socket, zmq.PULL,
                 PULL_SOCKET_ADDRESS)
    check_socket(initialized_socket_interface.control_socket, zmq.PAIR,
                 CONTROL_SOCKET_ADDRESS)


def test_push_connection(connected_interface):
    """test if the push socket is open

    """
    check_socket(connected_interface.push_socket, zmq.PUSH, PULL_SOCKET_ADDRESS)


def test_push_disconnection(connected_interface):
    """test if the disconnect method close the push socket

    """
    assert connected_interface.push_socket.closed is False
    connected_interface.close()
    assert connected_interface.push_socket.closed is True


def test_push_receive(connected_interface):
    """test to send and receive a message from the push/pull socket

    """
    msg = 'toto'
    connected_interface.send_data(msg)
    assert connected_interface.receive() == msg


def test_control_connection(controlled_interface):
    """test if the control socket is open

    """
    check_socket(controlled_interface.control_socket, zmq.PAIR,
                 CONTROL_SOCKET_ADDRESS)


def test_control_disconnection(controlled_interface):
    """test if the disconnect method close the control socket

    """
    assert controlled_interface.control_socket.closed is False
    controlled_interface.close()
    assert controlled_interface.control_socket.closed is True


def test_control_receive(controlled_interface):
    """test to send and receive a message from the control socket

    """
    msg = 'toto'
    controlled_interface.send_control(msg)
    assert controlled_interface.receive() == msg


def test_multiple_receive(fully_connected_interface):
    """test to send and receive a message from the control and the push/pull
    socket

    """
    controlled_msg = 'controlled_msg'
    push_msg = 'push_msg'
    fully_connected_interface.send_control(controlled_msg)
    assert fully_connected_interface.receive() == controlled_msg

    fully_connected_interface.send_control(push_msg)
    assert fully_connected_interface.receive() == push_msg
