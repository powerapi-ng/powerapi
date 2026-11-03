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

import logging
from collections.abc import Iterable

from powerapi.actor import Actor, ActorProxy, PoisonPillMessageHandler, StartMessageHandler, State
from powerapi.actor.message import ErrorMessage, StartMessage, PoisonPillMessage
from powerapi.database.driver import ReadableDatabaseFactory
from powerapi.puller.database_poller import DatabasePollerThread


class PullerState(State):
    """
    Puller Actor State class.
    """

    def __init__(self, actor: Actor, database_factory: ReadableDatabaseFactory, target_actors: list[ActorProxy], stream_mode: bool):
        """
        :param actor: Puller actor instance
        :param database_factory: Factory used to create the database driver
        :param target_actors: Actors receiving every retrieved report
        :param stream_mode: If true, poll continuously from the database; otherwise, stop the poller thread on empty result
        """
        super().__init__(actor)

        self.database_factory = database_factory
        self.target_actors = target_actors
        self.stream_mode = stream_mode

        self.db_poller_thread = DatabasePollerThread(database_factory, target_actors, stream_mode)

    def initialize(self) -> None:
        """
        Start the database poller.
        """
        if not self.target_actors:
            self.actor.send_control(ErrorMessage('Puller has no target actors'))
            self.alive = False
            return

        self.db_poller_thread.start()
        self.db_poller_thread.wait_ready(timeout=5.0)
        if not self.db_poller_thread.is_alive():
            self.actor.send_control(ErrorMessage('Database poller thread failed to start'))
            self.alive = False

    def teardown(self) -> None:
        """
        Stop the database poller.
        """
        if self.db_poller_thread.ident is not None:
            self.db_poller_thread.stop()
            self.db_poller_thread.join(timeout=5.0)


class PullerActor(Actor):
    """
    Puller Actor class.
    This actor allows to retrieve reports from a database and broadcast them to its target actors.
    """
    state: PullerState

    def __init__(self, name: str, database_factory: ReadableDatabaseFactory, target_actors: Iterable[ActorProxy], stream_mode: bool = False, level_logger: int = logging.WARNING):
        """
        :param name: Name of the puller actor
        :param database_factory: Factory used to create the database driver
        :param target_actors: Actors to send every retrieved reports to
        :param level_logger: Define the level of the logger for the actor
        """
        super().__init__(name, level_logger)

        self.database_factory = database_factory
        self.target_actors = list(target_actors)
        self.stream_mode = stream_mode

    def setup(self) -> None:
        """
        Set up the Puller actor message handlers.
        """
        self.state = PullerState(self, self.database_factory, self.target_actors, self.stream_mode)

        self.add_handler(StartMessage, StartMessageHandler(self.state))
        self.add_handler(PoisonPillMessage, PoisonPillMessageHandler(self.state))
