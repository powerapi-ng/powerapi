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

from powerapi.dispatcher.dispatcher_actor import DispatcherState


@pytest.fixture
def dispatcher_actor_state():
    """
    Factory fixture for creating a dispatcher actor state.
    """

    def _create_state() -> DispatcherState:
        actor = Mock(name='dispatcher-actor')
        actor.name = 'dispatcher-actor'
        actor.formula_factory = Mock(name='formula-factory')
        actor.pushers = {}
        actor.route_table = Mock(name='route-table')

        state = DispatcherState(actor)
        state.supervisor = Mock(name='supervisor')
        return state

    return _create_state


def test_state_getting_unknown_formula_id_creates_a_new_formula(dispatcher_actor_state):
    """
    Tests that getting an unknown formula ID creates a new formula.
    """
    state = dispatcher_actor_state()
    formula_id = ('pytest-formula',)

    formula_proxy = state.get_formula(formula_id)
    assert formula_id in state.formula_proxy
    assert formula_proxy is state.formula_proxy[formula_id]
    state.supervisor.launch_actor.assert_called_once()


def test_state_getting_known_formula_id_returns_existing_formula(dispatcher_actor_state):
    """
    Tests that getting a known formula ID returns the existing formula.
    """
    state = dispatcher_actor_state()
    formula_id = ('pytest-formula',)
    formula_proxy = state.add_formula(formula_id)

    fetched_formula_proxy = state.get_formula(formula_id)
    assert fetched_formula_proxy is formula_proxy
    state.supervisor.launch_actor.assert_called_once()
