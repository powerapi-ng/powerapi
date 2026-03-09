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

import logging

import pytest

from powerapi.actor import Actor, Supervisor, ActorInitializationError, ActorAlreadySupervisedException
from .test_actor import LoopbackActor, CrashActor, DummyMessage


@pytest.fixture
def supervisor():
    """
    Returns an actor supervisor.
    """
    return Supervisor()


def test_launch_kill_actor(supervisor):
    """
    Tests launching an actor with the supervisor.
    """
    actor = LoopbackActor()
    supervisor.launch_actor(actor)

    assert actor.is_alive() is True

    with actor.get_proxy(connect_control=True, connect_data=True) as proxy:
        msg = DummyMessage('test-dummy')
        proxy.send_data(msg)
        response = proxy.receive_control(2000)

        assert isinstance(response, DummyMessage)
        assert msg == response
        assert response.processed is True

    supervisor.kill_actors()
    supervisor.join(timeout=5.0)
    assert actor.is_alive() is False


def test_launch_actor_already_supervised(supervisor):
    """
    Test that launching an actor that is already supervised raises an error.
    """
    actor = LoopbackActor()
    supervisor.launch_actor(actor)

    with pytest.raises(ActorAlreadySupervisedException):
        supervisor.launch_actor(actor)

    supervisor.kill_actors()
    supervisor.join(timeout=5.0)


def test_launch_actor_with_failed_initialization(supervisor):
    """
    Test launching an actor that fails to initialize raises an error.
    """
    actor = Actor('test-actor-1', level_logger=logging.DEBUG)

    with pytest.raises(ActorInitializationError):
        supervisor.launch_actor(actor, init_timeout=0.5)

    supervisor.join(timeout=5.0)
    assert actor.is_alive() is False


def test_launch_actor_failed_with_error_message(supervisor):
    """
    Test launching an actor that fails to initialize and sends an error message back.
    """
    actor = CrashActor()

    with pytest.raises(ActorInitializationError):
        supervisor.launch_actor(actor)

    actor.join(timeout=5.0)
    assert actor.is_alive() is False
