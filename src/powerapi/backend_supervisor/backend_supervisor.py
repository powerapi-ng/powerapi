# Copyright (c) 2018, Inria
# Copyright (c) 2018, University of Lille
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

from __future__ import annotations

from typing import TYPE_CHECKING

from powerapi.actor import Supervisor
from powerapi.dispatcher import DispatcherActor
from powerapi.processor.processor_actor import PreProcessorActor
from powerapi.puller import PullerActor
from powerapi.pusher import PusherActor

if TYPE_CHECKING:
    from powerapi.actor import Actor


class BackendSupervisor(Supervisor):
    """
    Backend Supervisor class.
    Provides basic operations to start and stop a backend of actors.
    """

    def __init__(self, stream_mode: bool):
        """
        Initialize a new backend supervisor.
        :param stream_mode: True for stream mode, False otherwise
        """
        super().__init__()

        self.stream_mode = stream_mode

        self.pullers: list[Actor] = []
        self.dispatchers: list[Actor] = []
        self.pre_processors: list[Actor] = []
        self.pushers: list[Actor] = []

    def launch_actor(self, actor: Actor, init_timeout: float = 2.0) -> None:
        """
        Launch the actor and register its pipeline stage after successful initialization.
        :param actor: Actor to launch
        :param init_timeout: Maximum time in seconds to wait for an actor to be initialized
        :raise TypeError: When the actor does not belong to a supported pipeline stage
        :raise ValueError: When trying to launch an actor that is already supervised
        :raise ActorInitializationError: When the actor initialization process failed
        """
        match actor:
            case PullerActor():
                stage = self.pullers
            case DispatcherActor():
                stage = self.dispatchers
            case PreProcessorActor():
                stage = self.pre_processors
            case PusherActor():
                stage = self.pushers
            case _:
                raise TypeError(f'Unsupported backend actor: {type(actor).__name__}')

        super().launch_actor(actor, init_timeout)
        stage.append(actor)

    @staticmethod
    def _kill_actor(actor: Actor, graceful: bool) -> None:
        """
        Request cooperative shutdown of an actor without waiting for it to stop.
        :param actor: Actor to stop
        :param graceful: Whether to drain pending messages before cleanup and exit
        """
        with actor.get_proxy(connect_control=True) as proxy:
            proxy.kill(graceful=graceful)

    def _stop_stage(self, actors: list[Actor], graceful: bool, timeout: float | None = None) -> None:
        """
        Request shutdown for the whole stage, then wait before proceeding downstream.
        :param actors: Actors in the pipeline stage
        :param graceful: Whether actors should process pending messages before stopping
        :param timeout: Maximum wait in seconds per actor; None waits indefinitely
        :raises TimeoutError: An actor did not stop; downstream stages must remain running
        """
        for actor in actors:
            if actor.is_alive():
                self._kill_actor(actor, graceful=graceful)

        for actor in actors:
            actor.join(timeout=timeout)
            if actor.is_alive():
                raise TimeoutError(f'Actor "{actor.name}" did not stop before timeout')

    def _join_stream_mode_off(self, timeout: float | None = None) -> None:
        """
        Wait for pullers to finish naturally, then stop and wait for downstream stages.
        Stages are stopped in order: preprocessors, dispatchers, then pushers.
        :param timeout: Maximum wait in seconds per actor; None waits indefinitely
        :raises TimeoutError: An actor did not stop; subsequent stages are left running
        """
        for puller in self.pullers:
            puller.join(timeout=timeout)
            if puller.is_alive():
                raise TimeoutError(f'Actor "{puller.name}" did not stop before timeout')

        for stage in (self.pre_processors, self.dispatchers, self.pushers):
            self._stop_stage(stage, graceful=True, timeout=timeout)

    def join(self, timeout: float | None = None) -> None:
        """
        Wait for supervised actors to stop.
        In stream mode, only wait; actors may still be running when a timeout expires.
        In non-stream mode, wait for pullers to finish naturally, then stop and wait for downstream stages.
        :param timeout: Maximum wait in seconds per actor; None waits indefinitely
        :raises TimeoutError: In non-stream mode, an actor did not stop; subsequent stages are left running
        """
        if self.stream_mode:
            super().join(timeout=timeout)
        else:
            self._join_stream_mode_off(timeout=timeout)

    def kill_actors(self, graceful: bool = True) -> None:
        """
        Stop and wait for each pipeline stage before stopping the next one.
        Stages are stopped in order: pullers, pre-processors, dispatchers, then pushers.
        This method blocks until all stages have stopped.
        :param graceful: If true, drain pending messages before cleanup and exit; if false, skip draining
        """
        for stage in (self.pullers, self.pre_processors, self.dispatchers, self.pushers):
            self._stop_stage(stage, graceful=graceful)
