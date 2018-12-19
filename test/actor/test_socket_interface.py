"""Test smartwatts.actor.SocketInterface

"""

import pytest
import zmq

from smartwatts.actor import SocketInterface


ACTOR_NAME = 'dummy_actor'
PULL_SOCKET_ADDRESS = 'ipc://@' + ACTOR_NAME
MONITOR_SOCKET_ADDRESS = 'ipc://@' + 'monitor_' + ACTOR_NAME


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
n
    """
    context = zmq.Context()
    initialized_socket_interface.connect(context)
    yield initialized_socket_interface
    initialized_socket_interface.disconnect()


@pytest.fixture()
def monitored_interface(initialized_socket_interface):
    """ Return an initialized socket interface with an open connection to the
    monitor socket

    """
    context = zmq.Context()
    initialized_socket_interface.monitor(context)
    yield initialized_socket_interface
    initialized_socket_interface.disconnect()


@pytest.fixture()
def fully_connected_interface(initialized_socket_interface):
    """ Return an initialized socket interface with an open connection to the
    monitor and the push socket

    """
    context = zmq.Context()
    initialized_socket_interface.connect(context)
    initialized_socket_interface.monitor(context)
    yield initialized_socket_interface
    initialized_socket_interface.disconnect()


def test_socket_initialisation(socket_interface):
    """ test socket interface attribute initialisation
    """
    assert socket_interface.pull_socket_address == PULL_SOCKET_ADDRESS
    assert socket_interface.monitor_socket_address == MONITOR_SOCKET_ADDRESS


def test_close(initialized_socket_interface):
    """ test if the close method close the monitor and pull socket
    """
    assert initialized_socket_interface.pull_socket.closed is False
    assert initialized_socket_interface.monitor_socket.closed is False

    initialized_socket_interface.close()

    assert initialized_socket_interface.pull_socket.closed is True
    assert initialized_socket_interface.monitor_socket.closed is True


def test_setup(initialized_socket_interface):
    """ test if the setup method open the monitor and pull socket
    """
    assert isinstance(initialized_socket_interface.context, zmq.Context)
    assert isinstance(initialized_socket_interface.poller, zmq.Poller)

    check_socket(initialized_socket_interface.pull_socket, zmq.PULL,
                 PULL_SOCKET_ADDRESS)
    check_socket(initialized_socket_interface.monitor_socket, zmq.PAIR,
                 MONITOR_SOCKET_ADDRESS)


def test_push_connection(connected_interface):
    """test if the push socket is open

    """
    check_socket(connected_interface.push_socket, zmq.PUSH, PULL_SOCKET_ADDRESS)


def test_push_disconnection(connected_interface):
    """test if the disconnect method close the push socket

    """
    assert connected_interface.push_socket.closed is False
    connected_interface.disconnect()
    assert connected_interface.push_socket.closed is True


def test_push_receive(connected_interface):
    """test to send and receive a message from the push/pull socket

    """
    msg = 'toto'
    connected_interface.send(msg)
    assert connected_interface.receive() == [msg]


def test_monitor_connection(monitored_interface):
    """test if the monitor socket is open

    """
    check_socket(monitored_interface.monitor_socket, zmq.PAIR,
                 MONITOR_SOCKET_ADDRESS)


def test_monitor_disconnection(monitored_interface):
    """test if the disconnect method close the monitor socket

    """
    assert monitored_interface.monitor_socket.closed is False
    monitored_interface.disconnect()
    assert monitored_interface.monitor_socket.closed is True


def test_monitor_receive(monitored_interface):
    """test to send and receive a message from the monitor socket

    """
    msg = 'toto'
    monitored_interface.send_monitor(msg)
    assert monitored_interface.receive() == [msg]


def test_multiple_receive(fully_connected_interface):
    """test to send and receive a message from the monitor and the push/pull
    socket

    """
    monitored_msg = 'monitored_msg'
    push_msg = 'push_msg'
    fully_connected_interface.send_monitor(monitored_msg)
    assert fully_connected_interface.receive() == [monitored_msg]

    fully_connected_interface.send_monitor(push_msg)
    assert fully_connected_interface.receive() == [push_msg]
