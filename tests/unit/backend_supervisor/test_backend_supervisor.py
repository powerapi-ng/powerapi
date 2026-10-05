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

from unittest.mock import Mock, call, patch

import pytest

from powerapi.actor import Actor, ActorInitializationError, Supervisor
from powerapi.backend_supervisor import BackendSupervisor
from powerapi.dispatcher import DispatcherActor
from powerapi.processor import PostProcessorActor, PreProcessorActor
from powerapi.puller import PullerActor
from powerapi.pusher import PusherActor


def test_backend_kill_actors_stops_each_stage_before_the_next():
    """
    Test that backend stages stop sequentially from pullers to pushers.
    """
    supervisor = BackendSupervisor(stream_mode=True)
    supervisor.pullers.append(Mock(name='puller'))
    supervisor.pre_processors.append(Mock(name='preprocessor'))
    supervisor.dispatchers.append(Mock(name='dispatcher'))
    supervisor.pushers.append(Mock(name='pusher'))

    with patch.object(supervisor, '_stop_stage') as stop_stage:
        supervisor.kill_actors()

    assert stop_stage.call_args_list == [
        call(supervisor.pullers, graceful=True),
        call(supervisor.pre_processors, graceful=True),
        call(supervisor.dispatchers, graceful=True),
        call(supervisor.pushers, graceful=True),
    ]


def test_backend_nonstream_join_stops_downstream_stages():
    """
    Test that non-stream mode stops downstream stages after pullers finish.
    """
    supervisor = BackendSupervisor(stream_mode=False)
    puller = Mock()
    puller.is_alive.return_value = False
    supervisor.pullers.append(puller)
    supervisor.pre_processors.append(Mock(name='preprocessor'))
    supervisor.dispatchers.append(Mock(name='dispatcher'))
    supervisor.pushers.append(Mock(name='pusher'))

    with patch.object(supervisor, '_stop_stage') as stop_stage:
        supervisor.join(timeout=2.0)

    puller.join.assert_called_once_with(timeout=2.0)
    assert stop_stage.call_args_list == [
        call(supervisor.pre_processors, graceful=True, timeout=2.0),
        call(supervisor.dispatchers, graceful=True, timeout=2.0),
        call(supervisor.pushers, graceful=True, timeout=2.0),
    ]


def test_backend_join_puller_timeout_leaves_preprocessors_running():
    """
    Test that a puller timeout leaves preprocessors running.
    """
    supervisor = BackendSupervisor(stream_mode=False)
    puller = Mock(name='puller')
    puller.name = 'pullers'
    puller.is_alive.return_value = True
    preprocessor = Mock(name='preprocessor')
    supervisor.pullers.append(puller)
    supervisor.pre_processors.append(preprocessor)

    with pytest.raises(TimeoutError, match='pullers'):
        supervisor.join(timeout=0.1)

    preprocessor.get_proxy.assert_not_called()
    preprocessor.join.assert_not_called()


def test_backend_join_preprocessor_timeout_leaves_dispatchers_running():
    """
    Test that a preprocessor timeout leaves dispatchers running.
    """
    supervisor = BackendSupervisor(stream_mode=False)
    puller = Mock()
    puller.is_alive.return_value = False
    preprocessor = Mock(name='preprocessor')
    preprocessor.name = 'pre_processors'
    preprocessor.is_alive.return_value = True
    dispatcher = Mock(name='dispatcher')
    supervisor.pullers.append(puller)
    supervisor.pre_processors.append(preprocessor)
    supervisor.dispatchers.append(dispatcher)

    with patch.object(supervisor, '_kill_actor'), pytest.raises(TimeoutError, match='pre_processors'):
        supervisor.join(timeout=0.1)

    dispatcher.get_proxy.assert_not_called()
    dispatcher.join.assert_not_called()


def test_backend_shutdown_skips_stop_request_for_exited_actor():
    """
    Test that backend shutdown does not stop an actor that has already exited.
    """
    supervisor = BackendSupervisor(stream_mode=True)
    actor = Mock()
    actor.is_alive.return_value = False
    supervisor.pullers.append(actor)

    supervisor.kill_actors()

    actor.get_proxy.assert_not_called()
    actor.join.assert_called_once_with(timeout=None)


@pytest.mark.parametrize('actor_type', [Actor, PostProcessorActor])
def test_backend_rejects_unsupported_actor_before_start(actor_type):
    """
    Test that unsupported actors are rejected before they start.
    """
    supervisor = BackendSupervisor(stream_mode=True)
    actor = Mock(spec=actor_type)

    with pytest.raises(TypeError, match='Unsupported backend actor'):
        supervisor.launch_actor(actor)

    actor.start.assert_not_called()
    assert supervisor.supervised_actors == []


def test_backend_does_not_register_actor_when_launch_fails():
    """
    Test that a failed actor launch does not register the actor.
    """
    supervisor = BackendSupervisor(stream_mode=True)
    actor = Mock(spec=PullerActor)

    with patch.object(Supervisor, 'launch_actor', side_effect=ActorInitializationError('initialization failed')):
        with pytest.raises(ActorInitializationError, match='initialization failed'):
            supervisor.launch_actor(actor)

    assert supervisor.pullers == []
    assert supervisor.supervised_actors == []


@pytest.mark.parametrize(
    ('actor_type', 'stage_name'),
    [
        (PullerActor, 'pullers'),
        (PreProcessorActor, 'pre_processors'),
        (DispatcherActor, 'dispatchers'),
        (PusherActor, 'pushers')
    ]
)
def test_backend_registers_supported_actor(actor_type, stage_name):
    """
    Test that supported actors are registered in their pipeline stage.
    """
    supervisor = BackendSupervisor(stream_mode=True)
    actor = Mock(spec=actor_type)
    stage = getattr(supervisor, stage_name)

    with patch.object(Supervisor, 'launch_actor') as launch:
        supervisor.launch_actor(actor, init_timeout=0.5)

    launch.assert_called_once_with(actor, 0.5)
    assert stage == [actor]
