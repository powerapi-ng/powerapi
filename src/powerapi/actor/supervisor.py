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

from powerapi.actor.message import StartMessage, ErrorMessage
from powerapi.exception import PowerAPIException

if TYPE_CHECKING:
    from powerapi.actor import Actor


class ActorAlreadySupervisedException(PowerAPIException):
    """
    Exception raised when trying to launch an actor that is already supervised.
    """


class ActorInitializationError(PowerAPIException):
    """
    Exception raised when the initialization of the actor failed.
    """

    def __init__(self, error_msg: str):
        super().__init__()

        self.error_msg = error_msg


class Supervisor:
    """
    Actor supervisor class.
    Provides basic operations to start and stop actors.
    """

    def __init__(self):
        self.supervised_actors: list[Actor] = []

    def launch_actor(self, actor: Actor, start_message: bool = True, init_timeout: float = 5.0) -> None:
        """
        Launch the actor and supervise it.
        :param actor: Actor to launch
        :param start_message: Whether to send a start message to the actor
        :param init_timeout: Maximum time in seconds to wait for an actor to initialize
        :raise ActorAlreadySupervisedException: When trying to launch an actor that is already supervised
        :raise ActorInitializationError: When the actor initialization process failed
        """
        if actor in self.supervised_actors:
            raise ActorAlreadySupervisedException()

        actor.start()

        if start_message:
            with actor.get_proxy(connect_control=True) as proxy:
                proxy.send_control(StartMessage())
                response = proxy.receive_control(timeout=int(init_timeout * 1000))
                match response:
                    case ErrorMessage():
                        proxy.kill(graceful=False)
                        actor.join()
                        raise ActorInitializationError(response.error_message)

                    case None:
                        actor.terminate()  # Actor process is expected to be dead, this is just to be sure.
                        actor.join()
                        raise ActorInitializationError('Actor process crashed during its initialization')

        self.supervised_actors.append(actor)

    def join(self, timeout: float | None = None) -> None:
        """
        Wait until all supervised actors are stopped.
        :param timeout: Maximum time in seconds to wait for an actor to be stopped
        """
        for actor in self.supervised_actors:
            actor.join(timeout=timeout)

    def kill_actors(self, graceful: bool = True) -> None:
        """
        Kill all supervised actors.
        :param graceful: If true, the actors will process pending messages before stopping; If false, stop immediately
        """
        for actor in self.supervised_actors:
            if actor.is_alive():
                with actor.get_proxy(connect_control=True) as proxy:
                    proxy.kill(graceful=graceful)
