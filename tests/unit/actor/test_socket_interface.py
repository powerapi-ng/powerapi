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

import pytest

from powerapi.actor.socket_interface import NotBoundException, NotConnectedException
from powerapi.message import Message

TIMEOUT = 1000


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


def test_connect_to_not_bound_socket_interface(socket_interface):
    """
    Test connecting to a non-bound socket interface.
    """
    with pytest.raises(NotBoundException):
        socket_interface.connect()


def test_connect_control_to_not_bound_socket_interface(socket_interface):
    """
    Test connecting the control socket of a non-bound socket interface.
    """
    with pytest.raises(NotBoundException):
        socket_interface.connect_control()


def test_connect_data_to_not_bound_socket_interface(socket_interface):
    """
    Test connecting the data socket of a non-bound socket interface.
    """
    with pytest.raises(NotBoundException):
        socket_interface.connect_data()


def test_disconnect_to_not_bound_socket_interface(socket_interface):
    """
    Test disconnecting from a non-bound socket interface.
    """
    with pytest.raises(NotBoundException):
        socket_interface.disconnect()


def test_send_control_message_to_not_connected_socket_interface(socket_interface):
    """
    Test sending a control message to a non-connected socket interface.
    """
    with pytest.raises(NotConnectedException):
        socket_interface.send_control(DummyMessage('test-control-message'))


def test_receive_control_message_from_not_connected_socket_interface(socket_interface):
    """
    Test receiving a control message from a non-connected socket interface.
    """
    with pytest.raises(NotConnectedException):
        socket_interface.receive_control(TIMEOUT)


def test_send_data_message_to_not_connected_socket_interface(socket_interface):
    """
    Test sending a data message to a non-connected socket interface.
    """
    with pytest.raises(NotConnectedException):
        socket_interface.send_data(DummyMessage('test-data-message'))


def test_receive_data_message_from_not_connected_socket_interface(socket_interface):
    """
    Test receiving a data message from a non-connected socket interface.
    """
    with pytest.raises(NotConnectedException):
        socket_interface.receive_data(TIMEOUT)


def test_send_control_message_to_not_bound_socket_interface(socket_interface):
    """
    Test sending a control message to a non-bound socket interface.
    """
    with pytest.raises(NotConnectedException):
        socket_interface.send_control(DummyMessage('test-control-message'))


def test_receive_from_not_bound_socket_interface(socket_interface):
    """
    Test receiving a message from a not bound socket interface.
    """
    with pytest.raises(NotBoundException):
        socket_interface.receive(100)


def test_bind_socket_interface(socket_interface):
    """
    Test binding an unbound socket interface.
    """
    socket_interface.bind()

    assert socket_interface.is_bound_event.is_set()
    assert socket_interface.control_socket is not None
    assert socket_interface.control_socket_addr.get_obj().value
    assert socket_interface.data_socket is not None
    assert socket_interface.data_socket_addr.get_obj().value


def test_unbind_socket_interface(socket_interface):
    """
    Test unbinding a bound socket interface.
    """
    socket_interface.bind()
    assert socket_interface.is_bound_event.is_set()
    assert socket_interface.control_socket is not None
    assert len(socket_interface.control_socket_addr.get_obj().value) > 0
    assert socket_interface.data_socket is not None
    assert len(socket_interface.data_socket_addr.get_obj().value) > 0

    socket_interface.unbind()
    assert not socket_interface.is_bound_event.is_set()
    assert socket_interface.control_socket is None
    assert len(socket_interface.control_socket_addr.get_obj().value) == 0
    assert socket_interface.data_socket is None
    assert len(socket_interface.data_socket_addr.get_obj().value) == 0


def test_bind_already_bound_socket_interface(bound_socket_interface):
    """
    Test binding an already bound socket interface.
    """
    control_socket = bound_socket_interface.control_socket
    control_socket_addr = bound_socket_interface.control_socket_addr.get_obj().value
    data_socket = bound_socket_interface.data_socket
    data_socket_addr = bound_socket_interface.data_socket_addr.get_obj().value

    bound_socket_interface.bind()

    # Calling `bind()` again should not have side effects in order to not break communication with other actors.
    assert bound_socket_interface.is_bound_event.is_set()
    assert bound_socket_interface.control_socket_addr.get_obj().value == control_socket_addr
    assert bound_socket_interface.control_socket == control_socket
    assert bound_socket_interface.data_socket_addr.get_obj().value == data_socket_addr
    assert bound_socket_interface.data_socket == data_socket


def test_unbind_already_unbound_socket_interface(socket_interface):
    """
    Test unbinding an already unbound socket interface.
    """
    socket_interface.unbind()

    # Calling `unbind()` on an already unbound socket interface should be a no-op.
    assert not socket_interface.is_bound_event.is_set()
    assert socket_interface.control_socket_addr.get_obj().value == ''
    assert socket_interface.control_socket is None
    assert socket_interface.data_socket_addr.get_obj().value == ''
    assert socket_interface.data_socket is None


def test_send_receive_control_message(bound_socket_interface, connected_socket_interface):
    """
    Test sending a control message to a bound socket interface.
    """
    control_msg = DummyMessage('test-control-message')
    connected_socket_interface.send_control(control_msg)
    received_msg = bound_socket_interface.receive_control(TIMEOUT)

    assert received_msg == control_msg


def test_receive_control_message_timeout(bound_socket_interface):
    """
    Test reaching the timeout when receiving a control message.
    """
    received_msg = bound_socket_interface.receive_control(100)

    assert received_msg is None


def test_send_receive_data_message(bound_socket_interface, connected_socket_interface):
    """
    Test sending a data message to a bound socket interface.
    """
    data_msg = DummyMessage('test-data-message')
    connected_socket_interface.send_data(data_msg)
    received_msg = bound_socket_interface.receive_data(TIMEOUT)

    assert received_msg == data_msg


def test_receive_data_message_timeout(bound_socket_interface):
    """
    Test reaching the timeout when receiving a data message.
    """
    received_msg = bound_socket_interface.receive_data(100)

    assert received_msg is None


def test_receive_both_messages(bound_socket_interface, connected_socket_interface):
    """
    Test sending and receiving control/data messages to a bound socket interface.
    """
    control_msg = DummyMessage('test-control-message')
    data_msg = DummyMessage('test-data-message')

    connected_socket_interface.send_control(control_msg)
    connected_socket_interface.send_data(data_msg)

    # Waiting for messages to arrive, prevents flaky tests
    bound_socket_interface.poller.poll(TIMEOUT)

    received_msg1 = bound_socket_interface.receive(TIMEOUT)
    received_msg2 = bound_socket_interface.receive(TIMEOUT)

    assert received_msg1 == control_msg
    assert received_msg2 == data_msg


def test_receive_priority_and_ordering(bound_socket_interface, connected_socket_interface):
    """
    Test that control messages are received before data messages and in the correct order.
    """
    control_msg1 = DummyMessage('test-control-message1')
    control_msg2 = DummyMessage('test-control-message2')
    data_msg1 = DummyMessage('test-data-message1')
    data_msg2 = DummyMessage('test-data-message2')

    connected_socket_interface.send_control(control_msg1)
    connected_socket_interface.send_data(data_msg1)
    connected_socket_interface.send_control(control_msg2)
    connected_socket_interface.send_data(data_msg2)

    # Waiting for messages to arrive, prevents flaky tests
    bound_socket_interface.poller.poll(TIMEOUT)

    received_msg1 = bound_socket_interface.receive(TIMEOUT)
    received_msg2 = bound_socket_interface.receive(TIMEOUT)
    received_msg3 = bound_socket_interface.receive(TIMEOUT)
    received_msg4 = bound_socket_interface.receive(TIMEOUT)

    assert received_msg1 == control_msg1
    assert received_msg2 == control_msg2
    assert received_msg3 == data_msg1
    assert received_msg4 == data_msg2


def test_receive_timeout(bound_socket_interface):
    """
    Test reaching the timeout when receiving a message.
    """
    received_msg = bound_socket_interface.receive(100)

    assert received_msg is None
