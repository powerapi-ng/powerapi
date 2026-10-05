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


class DummyMessageSubtype(DummyMessage):
    """
    Subtype of a dummy message class.
    """


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

    def handle(self, message: DummyMessage) -> None:
        """
        Handle a message.
        """
        message.processed = True
        self.state.actor.send_control(message)


class KeyErrorMessageHandler(Handler[DummyMessage]):
    def handle(self, message: DummyMessage) -> None:
        raise KeyError('handler failure')


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


def test_retrieve_handler_for_known_message_type():
    """
    Test retrieving the corresponding handler for a known message type.
    """
    state = DummyActorState(None)
    dummy_handler = LoopbackMessageHandler(state)
    state.add_handler(DummyMessage, dummy_handler)

    msg_handler = state.get_corresponding_handler(DummyMessage('test-dummy'))
    assert msg_handler is dummy_handler


def test_retrieve_handler_for_known_message_subtype():
    """
    Test retrieving the corresponding handler for a subtype of a known message type.
    """
    state = DummyActorState(None)
    dummy_handler = LoopbackMessageHandler(state)
    state.add_handler(DummyMessage, dummy_handler, include_subclasses=True)

    msg_handler = state.get_corresponding_handler(DummyMessageSubtype('test-dummy-subtype'))
    assert msg_handler is dummy_handler


def test_retrieve_handler_for_known_message_with_subtype_excluded():
    """
    Test that retrieving the corresponding handler for an excluded subtype of a known message type raises an error.
    """
    state = DummyActorState(None)
    dummy_handler = LoopbackMessageHandler(state)
    state.add_handler(DummyMessage, dummy_handler, include_subclasses=False)

    with pytest.raises(KeyError, match='DummyMessageSubtype'):
        state.get_corresponding_handler(DummyMessageSubtype('test-dummy-subtype'))


def test_retrieve_handler_for_unknown_message_type():
    """
    Test that retrieving the corresponding handler for an unknown message type raises an error.
    """
    state = DummyActorState(None)

    with pytest.raises(KeyError, match='DummyMessage'):
        state.get_corresponding_handler(DummyMessage('test-dummy'))


def test_handler_key_error_is_not_mistaken_for_an_unknown_message():
    """
    Exceptions raised by handlers should not be treated as unknown messages.
    """
    actor = Actor('pytest')
    state = DummyActorState(actor)
    actor.state = state
    handler = KeyErrorMessageHandler(state)
    state.add_handler(DummyMessage, handler)

    with pytest.raises(KeyError, match='handler failure'):
        state.dispatch_message(DummyMessage('test-dummy'))


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


def test_soft_poison_pill_dispatches_pending_messages_before_state_teardown():
    """
    A soft shutdown should dispatch pending messages and defer state teardown.
    """
    pending_message = DummyMessage('pending')
    actor = Mock()
    actor.socket_interface.receive.side_effect = [pending_message, None]
    state = Mock(actor=actor, alive=True)
    handler = PoisonPillMessageHandler(state)

    handler.handle(PoisonPillMessage(soft=True))

    state.dispatch_message.assert_called_once_with(pending_message)
    state.teardown.assert_not_called()
    assert state.graceful_shutdown is True
    assert state.alive is False


@pytest.mark.parametrize('graceful', [True, False])
def test_actor_finalizes_once_after_poison_pill(graceful):
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
    actor._process_received_messages = Mock(side_effect=lambda: handler.handle(PoisonPillMessage(soft=graceful)))

    actor.run()

    state.teardown.assert_called_once_with(graceful=graceful)
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

    handler.handle(PoisonPillMessage(soft=True))

    actor.socket_interface.receive.assert_not_called()
    assert state.graceful_shutdown is False


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
