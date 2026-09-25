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

from unittest.mock import Mock

import pytest

from powerapi.actor import PoisonPillMessage, PoisonPillMessageHandler, StartMessage, StartMessageHandler
from powerapi.formula import FormulaActor, FormulaState


class SpecializedFormulaState(FormulaState):
    """
    Formula state used to verify specialized state creation.
    """


class SpecializedFormulaActor(FormulaActor):
    """
    Formula actor creating a specialized state.
    """
    state: SpecializedFormulaState

    def create_state(self) -> SpecializedFormulaState:
        """
        Create the specialized formula state.
        """
        return SpecializedFormulaState(self, self.pushers)


def test_formula_state_connects_and_disconnects_pushers():
    """
    The formula state lifecycle hooks should connect and disconnect every pusher.
    """
    pushers = [Mock(), Mock()]
    state = FormulaState(Mock(), {Mock: pushers})

    state.initialize()
    state.teardown()

    for pusher in pushers:
        pusher.connect_data.assert_called_once_with()
        pusher.disconnect.assert_called_once_with()


@pytest.mark.parametrize(
    ('message', 'handler_type'),
    [
        (StartMessage(), StartMessageHandler),
        (PoisonPillMessage(), PoisonPillMessageHandler),
    ],
)
def test_formula_actor_registers_lifecycle_handlers(message, handler_type):
    """
    Formula actors should register the generic lifecycle handlers.
    """
    actor = FormulaActor('pytest-formula', {})

    actor.setup()

    assert isinstance(actor.state.get_corresponding_handler(message), handler_type)


def test_formula_actor_lifecycle_handlers_use_specialized_state():
    """
    Formula lifecycle handlers should use the state created by the specialized actor.
    """
    actor = SpecializedFormulaActor('pytest-specialized-formula', {})

    actor.setup()

    assert isinstance(actor.state, SpecializedFormulaState)
    for message in (StartMessage(), PoisonPillMessage()):
        handler = actor.state.get_corresponding_handler(message)
        assert handler.state is actor.state
