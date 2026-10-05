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

from powerapi.actor.message import ErrorMessage, OKMessage, StartMessage

if TYPE_CHECKING:
    from powerapi.actor import Actor


class ActorInitializationError(RuntimeError):
    """
    Exception raised when the initialization of the actor failed.
    """


class Supervisor:
    """
    Actor supervisor class.
    Provides basic operations to start and stop actors.
    """

    def __init__(self):
        self.supervised_actors: list[Actor] = []

    @staticmethod
    def _initialize_actor(actor: Actor, timeout: float) -> None:
        """
        Request actor initialization and check its response.
        :param actor: Started actor to initialize
        :param timeout: Maximum wait in seconds for the response
        :raise ActorInitializationError: Initialization fails or no valid response is received
        """
        with actor.get_proxy(connect_control=True) as proxy:
            proxy.send_control(StartMessage())
            response = proxy.receive_control(timeout=int(timeout * 1000))
            match response:
                case OKMessage():
                    return

                case ErrorMessage():
                    raise ActorInitializationError(response.error_message)

                case _:
                    raise ActorInitializationError('Actor did not return a valid initialization response')

    def launch_actor(self, actor: Actor, init_timeout: float = 5.0) -> None:
        """
        Launch the actor and supervise it after successful initialization.
        Exceptions during the initialization handshake trigger termination and
        joining before they are re-raised. The actor is registered only on success.
        :param actor: Actor to launch
        :param init_timeout: Maximum wait in seconds for the initialization response, excluding sends and cleanup
        :raise ValueError: When trying to launch an actor that is already supervised
        :raise ActorInitializationError: When the actor initialization process failed
        """
        if actor in self.supervised_actors:
            raise ValueError(f'Actor "{actor.name}" is already supervised')

        actor.start()
        try:
            self._initialize_actor(actor, init_timeout)
        except (Exception, KeyboardInterrupt):
            actor.terminate()
            actor.join()
            raise
        else:
            self.supervised_actors.append(actor)

    def join(self, timeout: float | None = None) -> None:
        """
        Wait until all supervised actors are stopped.
        :param timeout: Maximum time in seconds to wait for an actor to be stopped
        """
        for actor in self.supervised_actors:
            actor.join(timeout=timeout)

    def kill_actors(self) -> None:
        """
        Request all supervised actors to drain pending messages and stop.
        """
        for actor in self.supervised_actors:
            if actor.is_alive():
                with actor.get_proxy(connect_control=True) as proxy:
                    proxy.kill()
