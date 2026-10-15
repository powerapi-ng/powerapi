# Copyright (c) 2026, Inria
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

from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from powerapi.actor import Handler, Message, State
from powerapi.report import HWPCReport, PowerReport, Report
from .test_actor import DummyMessage, LoopbackMessageHandler


class DummyMessageSubtype(DummyMessage):
    """
    Subtype of a dummy message class.
    """


class KeyErrorMessageHandler(Handler[DummyMessage]):
    """
    Handler that always raises KeyError.
    """
    def handle(self, msg: DummyMessage) -> None:
        raise KeyError('handler failure')


def test_retrieve_handler_for_known_message_type():
    """
    Test retrieving the corresponding handler for a known message type.
    """
    state = State(None)
    dummy_handler = LoopbackMessageHandler(state)
    state.add_handler(DummyMessage, dummy_handler)

    msg_handler = state.get_corresponding_handler(DummyMessage('test-dummy'))
    assert msg_handler is dummy_handler


def test_retrieve_handler_for_known_message_subtype():
    """
    Test retrieving the corresponding handler for a subtype of a known message type.
    """
    state = State(None)
    dummy_handler = LoopbackMessageHandler(state)
    state.add_handler(DummyMessage, dummy_handler)

    msg_handler = state.get_corresponding_handler(DummyMessageSubtype('test-dummy-subtype'))
    assert msg_handler is dummy_handler


def test_retrieve_handler_for_message_subtype_defined_after_registration():
    """
    Test retrieving a handler for a subtype defined after its base handler is registered.
    """
    state = State(None)
    handler = Mock()
    state.add_handler(DummyMessage, handler)

    class LateMessage(DummyMessage):
        pass

    assert state.get_corresponding_handler(LateMessage('late')) is handler


def test_retrieve_handler_for_deep_subtype_with_only_ancestor_registered():
    """
    Test retrieving a handler through multiple unregistered subclass levels.
    """
    class DeepMessage(DummyMessageSubtype):
        pass

    state = State(None)
    handler = Mock()
    state.add_handler(DummyMessage, handler)

    assert state.get_corresponding_handler(DeepMessage('deep')) is handler


def test_retrieve_handler_for_deep_subtype_uses_nearest_registered_base():
    """
    Test that a deeper subtype uses the handler of its nearest registered base class.
    """
    class DeepMessage(DummyMessageSubtype):
        pass

    state = State(None)
    subtype_handler = Mock()
    state.add_handler(DummyMessageSubtype, subtype_handler)
    state.add_handler(DummyMessage, Mock())

    assert state.get_corresponding_handler(DeepMessage('deep')) is subtype_handler


@pytest.mark.parametrize('registration_order', [(Report, HWPCReport), (HWPCReport, Report)])
def test_specific_report_handler_precedes_catch_all(registration_order: tuple[type[Report], type[Report]]):
    """
    Test that a specific report handler takes precedence regardless of registration order.
    """
    state = State(None)
    catch_all_handler = Mock()
    hwpc_handler = Mock()
    handlers = {Report: catch_all_handler, HWPCReport: hwpc_handler}
    for report_type in registration_order:
        state.add_handler(report_type, handlers[report_type])

    timestamp = datetime.now(UTC)
    hwpc_report = HWPCReport(timestamp, 'sensor', 'target', {})
    power_report = PowerReport(timestamp, 'sensor', 'target', 10.0)

    assert state.get_corresponding_handler(hwpc_report) is hwpc_handler
    assert state.get_corresponding_handler(power_report) is catch_all_handler


def test_handler_resolution_follows_multiple_inheritance_order():
    """
    Test that multiple inheritance uses Python's method resolution order.
    """
    class LeftMessage(Message):
        pass

    class RightMessage(Message):
        pass

    class CombinedMessage(LeftMessage, RightMessage):
        pass

    state = State(None)
    left_handler = Mock()
    state.add_handler(RightMessage, Mock())
    state.add_handler(LeftMessage, left_handler)

    assert state.get_corresponding_handler(CombinedMessage()) is left_handler


def test_handler_resolution_is_cached():
    """
    Test that repeated messages of the same type reuse the resolved handler.
    """
    state = State(None)
    handler = Mock()
    state.add_handler(DummyMessage, handler)
    state._resolve_handler = Mock(wraps=state._resolve_handler)

    assert state.get_corresponding_handler(DummyMessageSubtype('first')) is handler
    assert state.get_corresponding_handler(DummyMessageSubtype('second')) is handler
    state._resolve_handler.assert_called_once_with(DummyMessageSubtype)


@pytest.mark.parametrize(('message_type', 'registration_type'), [
    (DummyMessage, DummyMessage),
    (DummyMessageSubtype, DummyMessage),
    (DummyMessageSubtype, DummyMessageSubtype),
])
def test_registration_invalidates_cached_handler(message_type, registration_type):
    """
    Test that adding or replacing a registration invalidates previously resolved handlers.
    """
    state = State(None)
    original_handler = Mock()
    replacement_handler = Mock()
    state.add_handler(DummyMessage, original_handler)
    message = message_type('message')
    assert state.get_corresponding_handler(message) is original_handler

    state.add_handler(registration_type, replacement_handler)

    assert state.get_corresponding_handler(message) is replacement_handler


def test_unrelated_message_classes_with_same_name_have_separate_handlers():
    """
    Test that unrelated message classes with the same name retain separate handlers.
    """
    def make_message_type() -> type[Message]:
        class SameNameMessage(Message):
            pass

        return SameNameMessage

    first_type = make_message_type()
    second_type = make_message_type()
    state = State(None)
    first_handler = Mock()
    second_handler = Mock()
    state.add_handler(first_type, first_handler)
    state.add_handler(second_type, second_handler)

    assert state.get_corresponding_handler(first_type()) is first_handler
    assert state.get_corresponding_handler(second_type()) is second_handler


def test_retrieve_handler_for_unknown_message_type():
    """
    Test that retrieving the corresponding handler for an unknown message type raises an error.
    """
    state = State(None)

    with pytest.raises(KeyError, match='DummyMessage'):
        state.get_corresponding_handler(DummyMessage('test-dummy'))


def test_handler_key_error_is_not_mistaken_for_an_unknown_message():
    """
    Exceptions raised by handlers should not be treated as unknown messages.
    """
    state = State(None)
    handler = KeyErrorMessageHandler(state)
    state.add_handler(DummyMessage, handler)

    with pytest.raises(KeyError, match='handler failure'):
        state.handle_message(DummyMessage('test-dummy'))
