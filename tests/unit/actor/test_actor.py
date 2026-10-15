# Copyright (c) 2026, Inria
# Copyright (c) 2026, University of Lille
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
import secrets
from unittest.mock import Mock

import pytest

from powerapi.actor import (
    Actor,
    ErrorMessage,
    Handler,
    Message,
    OKMessage,
    PoisonPillMessage,
    PoisonPillMessageHandler,
    StartMessage,
    StartMessageHandler,
    State,
)


class UnknownMessage(Message):
    """
    Unknown message class.
    Used to test the behavior of the actor when receiving an unknown message.
    """


class DummyMessage(Message):
    """
    Dummy message class.
    Used to check if the actor can process messages.
    """

    def __init__(self, value: str):
        self.value = value
        self.processed = False

    def __eq__(self, other):
        return self.value == other.value


class FailingStartMessageHandler(Handler[StartMessage]):
    """
    Failing start message handler.
    Always sends back an error message to the control channel of the actor.
    """
    ERROR_MSG = ErrorMessage('pytest-error-message')

    def handle(self, msg):
        """
        Sends an error message on the control channel of the actor.
        """
        self.state.initialized = False
        self.state.alive = False
        self.state.actor.send_control(self.ERROR_MSG)


class LoopbackMessageHandler(Handler[DummyMessage]):
    """
    Loopback message handler.
    Set the processed flag to received messages and sends them back to the control channel.
    """

    def handle(self, msg: DummyMessage) -> None:
        """
        Handle a message.
        """
        msg.processed = True
        self.state.actor.send_control(msg)


class DummyActorState(State):
    """
    Dummy actor state class.
    """

class DummyActorBase(Actor):
    """
    Dummy actor base class.
    Used to implement actors for testing.
    """

    def __init__(self):
        """
        Initialize a new dummy actor.
        """
        super().__init__(f'dummy-actor-{secrets.token_hex(6)}', level_logger=logging.DEBUG)


class LoopbackActor(DummyActorBase):
    """
    Loopback actor class.
    """

    def setup(self) -> None:
        """
        Initializes a loopback actor.
        """
        self.state = DummyActorState(self)

        self.add_handler(StartMessage, StartMessageHandler(self.state))
        self.add_handler(PoisonPillMessage, PoisonPillMessageHandler(self.state))
        self.add_handler(DummyMessage, LoopbackMessageHandler(self.state))


class CrashActor(DummyActorBase):
    """
    Crash actor class.
    Actor that always fails its initialization and shuts down.
    """

    def setup(self) -> None:
        """
        Initialized a start error actor.
        """
        self.state = DummyActorState(self)

        self.add_handler(StartMessage, FailingStartMessageHandler(self.state))
        self.add_handler(PoisonPillMessage, PoisonPillMessageHandler(self.state))


@pytest.fixture
def loopback_actor():
    """
    Fixture to create a loopback actor.
    """
    return LoopbackActor()


@pytest.fixture
def started_loopback_actor(loopback_actor):
    """
    Fixture to create a started loopback actor.
    The actor will be started by default and will be automatically killed after use.
    """
    loopback_actor.start()

    yield loopback_actor

    proxy = loopback_actor.get_proxy(connect_control=True)
    proxy.kill()
    loopback_actor.join(5.0)


def test_start_stop_actor(loopback_actor):
    """
    Test starting and stopping an actor.
    """
    loopback_actor.start()
    assert loopback_actor.is_alive() is True

    proxy = loopback_actor.get_proxy(connect_control=True)

    proxy.send_control(StartMessage())
    msg = proxy.receive_control(5000)
    assert isinstance(msg, OKMessage)

    proxy.kill()
    loopback_actor.join(5.0)
    assert loopback_actor.is_alive() is False

    proxy.disconnect()


def test_send_two_start_messages_to_actor(started_loopback_actor):
    """
    Test that sending two start messages to an actor raises an error.
    """
    proxy = started_loopback_actor.get_proxy(connect_control=True)

    proxy.send_control(StartMessage())
    msg = proxy.receive_control(5000)
    assert isinstance(msg, OKMessage)

    proxy.send_control(StartMessage())
    msg = proxy.receive_control(5000)
    assert isinstance(msg, ErrorMessage)


def test_send_data_message_to_actor(started_loopback_actor):
    """
    Test sending a message to the data channel of an actor.
    """
    proxy = started_loopback_actor.get_proxy(connect_control=True, connect_data=True)

    data_msg = DummyMessage('test-data')
    proxy.send_data(data_msg)

    ack_msg = proxy.receive_control(5000)
    assert isinstance(ack_msg, DummyMessage)
    assert data_msg == ack_msg
    assert ack_msg.processed is True


def test_start_message_handler_initializes_state():
    """
    The start-message handler should initialize the actor state.
    """
    state = Mock(initialized=False, alive=True)
    handler = StartMessageHandler(state)

    handler.handle(StartMessage())

    state.initialize.assert_called_once_with()
    state.actor.send_control.assert_called_once()
    assert isinstance(state.actor.send_control.call_args.args[0], OKMessage)
    assert state.initialized is True


def test_poison_pill_dispatches_pending_messages_before_state_teardown():
    """
    Test that a poison pill dispatches pending messages and defers state teardown.
    """
    pending_message = DummyMessage('pending')
    actor = Mock()
    actor.socket_interface.receive.side_effect = [pending_message, None]
    state = Mock(actor=actor, alive=True)
    handler = PoisonPillMessageHandler(state)

    handler.handle(PoisonPillMessage())

    state.handle_message.assert_called_once_with(pending_message)
    state.teardown.assert_not_called()
    assert state.alive is False


def test_actor_finalizes_once_after_poison_pill():
    """
    Test that actor resources are finalized once after receiving a poison pill.
    """
    actor = Actor('lifecycle-test')
    state = State(actor)
    state.teardown = Mock()
    handler = PoisonPillMessageHandler(state)
    actor.state = state
    actor.teardown = Mock()
    actor.socket_interface = Mock()
    actor.socket_interface.receive.return_value = None
    actor._setup_actor = Mock()
    actor._process_received_messages = Mock(side_effect=lambda: handler.handle(PoisonPillMessage()))

    actor.run()

    state.teardown.assert_called_once_with()
    actor.teardown.assert_called_once()
    actor.socket_interface.close.assert_called_once()


def test_poison_pill_handler_ignores_message_when_state_is_stopped():
    """
    Test that another poison pill is ignored after actor shutdown starts.
    """
    actor = Mock()
    state = State(actor)
    state.alive = False
    handler = PoisonPillMessageHandler(state)

    handler.handle(PoisonPillMessage())

    actor.socket_interface.receive.assert_not_called()
    assert state.alive is False


def test_actor_teardown_runs_when_setup_fails_before_state_exists():
    """
    Test that actor teardown runs when setup fails before creating the state.
    """
    actor = Actor('setup-failure-test')
    actor.socket_interface = Mock()
    actor.teardown = Mock()
    actor._setup_actor = Mock(side_effect=RuntimeError('setup failed'))

    with pytest.raises(RuntimeError, match='setup failed'):
        actor.run()

    actor.teardown.assert_called_once()
    actor.socket_interface.close.assert_called_once()


def test_actor_teardown_continues_when_state_teardown_fails():
    """
    Test that actor teardown continues when state teardown fails.
    """
    actor = Actor('teardown-failure-test')
    state = State(actor)
    state.alive = False
    state.teardown = Mock(side_effect=RuntimeError('teardown failed'))
    actor.state = state
    actor.teardown = Mock()
    actor.socket_interface = Mock()
    actor._setup_actor = Mock()

    with pytest.raises(RuntimeError, match='teardown failed'):
        actor.run()

    state.teardown.assert_called_once()
    actor.teardown.assert_called_once()
    actor.socket_interface.close.assert_called_once()


def test_actor_tears_down_and_propagates_processing_error():
    """
    Test that processing errors trigger actor teardown and propagate.
    """
    actor = Actor('processing-error-test')
    state = State(actor)
    actor.state = state
    actor._setup_actor = Mock()
    actor._process_received_messages = Mock(side_effect=RuntimeError('processing failed'))
    actor._teardown_actor = Mock()

    with pytest.raises(RuntimeError, match='processing failed'):
        actor.run()

    actor._teardown_actor.assert_called_once()
