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

from typing import TYPE_CHECKING

from powerapi.actor import Supervisor
from powerapi.dispatcher import DispatcherActor
from powerapi.processor.processor_actor import ProcessorActor
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

        self.pullers: list[PullerActor] = []
        self.dispatchers: list[DispatcherActor] = []
        self.pre_processors: list[ProcessorActor] = []
        self.pushers: list[PusherActor] = []

    def launch_actor(self, actor: Actor, start_message: bool = True, init_timeout: int = 2000) -> None:
        """
        Launch the actor and supervise it.
        :param actor: Actor to launch
        :param start_message: Whether to send a start message to the actor
        :param init_timeout: Maximum time in milliseconds to wait for an actor to be initialized
        :raise ActorAlreadySupervisedException: When trying to launch an actor that is already supervised
        :raise ActorInitializationError: When the actor initialization process failed
        """
        super().launch_actor(actor, start_message, init_timeout)

        match actor:
            case PullerActor():
                self.pullers.append(actor)
            case DispatcherActor():
                self.dispatchers.append(actor)
            case ProcessorActor():
                self.pre_processors.append(actor)
            case PusherActor():
                self.pushers.append(actor)

    @staticmethod
    def _kill_actor(actor: Actor, graceful: bool) -> None:
        """
        Helper function for killing an actor.
        :param actor: Actor to kill
        :param graceful: Whether to gracefully kill the actor
        """
        with actor.get_proxy(connect_control=True) as proxy:
            proxy.kill(graceful=graceful)

    def _join_stream_mode_off(self, timeout: float | None = None) -> None:
        """
        Wait until the pullers actors shutdown, then triggers the shutdown of the other actors.
        :param timeout: Maximum time in seconds to wait for an actor to joined
        """
        for puller in self.pullers:
            puller.join(timeout=timeout)

        for pre_processor in self.pre_processors:
            self._kill_actor(pre_processor, graceful=True)
            pre_processor.join(timeout=timeout)

        for dispatcher in self.dispatchers:
            self._kill_actor(dispatcher, graceful=True)
            dispatcher.join(timeout=timeout)

        for pusher in self.pushers:
            self._kill_actor(pusher, graceful=True)
            pusher.join(timeout=timeout)

    def join(self, timeout: float | None = None) -> None:
        """
        Wait until all supervised actors are stopped.
        When stream mode is disabled, this method will trigger the shutdown of all actors after the pullers shutdown.
        :param timeout: Maximum time in seconds to wait for an actor to joined
        """
        if self.stream_mode:
            super().join(timeout=timeout)
        else:
            self._join_stream_mode_off(timeout=timeout)

    def kill_actors(self, graceful: bool = True) -> None:
        """
        Kill all supervised actors.
        :param graceful: If true, the actors will process pending messages before stopping; If false, stop immediately
        """
        for puller in self.pullers:
            self._kill_actor(puller, graceful=graceful)

        for pre_processor in self.pre_processors:
            self._kill_actor(pre_processor, graceful=graceful)

        for dispatcher in self.dispatchers:
            self._kill_actor(dispatcher, graceful=graceful)

        for pusher in self.pushers:
            self._kill_actor(pusher, graceful=graceful)
