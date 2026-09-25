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

from powerapi.actor import Actor, PoisonPillMessageHandler, StartMessageHandler, State
from powerapi.actor.message import ErrorMessage, PoisonPillMessage, StartMessage
from powerapi.database.driver import WritableDatabaseFactory, WritableDatabase
from powerapi.database.exceptions import DatabaseError
from powerapi.pusher.handlers import ReportHandler
from powerapi.report import Report


class PusherState(State):
    """
    Pusher Actor State class.
    """

    def __init__(self, actor: Actor, database_factory: WritableDatabaseFactory):
        """
        :param actor: Pusher actor
        :param database_factory: Factory used to create the database driver
        """
        super().__init__(actor)

        self.database_factory = database_factory
        self.database_driver: WritableDatabase | None = None
        self.buffer: list[Report] = []

    def initialize(self) -> None:
        """
        Create and connect the database driver.
        """
        try:
            database_driver = self.database_factory.create()
            database_driver.connect()
            self.database_driver = database_driver
        except ValueError as exn:
            logging.error('Failed to create the database driver: %s', exn)
            self.actor.send_control(ErrorMessage('Database driver creation failed'))
            self.alive = False
        except DatabaseError as exn:
            logging.error('Failed to initialize the database driver: %s', exn)
            self.actor.send_control(ErrorMessage('Database initialization failed'))
            self.alive = False

    def teardown(self, graceful: bool = False) -> None:
        """
        Flush buffered reports and disconnect the database driver.
        :param graceful: Whether the actor is performing a graceful shutdown
        """
        if self.database_driver is None:
            return

        if self.buffer:
            try:
                self.database_driver.write(self.buffer)
                self.buffer.clear()
            except DatabaseError as exn:
                logging.error('The reports could not be saved before shutting down actor: %s', exn)

        self.database_driver.disconnect()


class PusherActor(Actor):
    """
    Pusher Actor class.
    This actor allows to persist Reports sent by a Formula to a database.
    """
    state: PusherState

    def __init__(self, name: str, database_factory: WritableDatabaseFactory, flush_interval: float = 0.100, max_buffer_size: int = 50, logger_level: int = logging.WARNING):
        """
        :param name: Name of the pusher actor
        :param database_factory: Factory used to create the database driver
        :param flush_interval: Maximum time in seconds to wait before flushing the buffered reports to the database
        :param max_buffer_size: Maximum number of reports that can be buffered before a forced flush to the database
        :param logger_level: Define the level of the logger for the actor
        """
        super().__init__(name, logger_level, 1000)

        self.database_factory = database_factory
        self.flush_interval = flush_interval
        self.max_buffer_size = max_buffer_size

    def setup(self) -> None:
        """
        Set up the Pusher actor message handlers.
        """
        self.state = PusherState(self, self.database_factory)

        self.add_handler(StartMessage, StartMessageHandler(self.state))
        self.add_handler(PoisonPillMessage, PoisonPillMessageHandler(self.state))
        self.add_handler(Report, ReportHandler(self.state, self.flush_interval, self.max_buffer_size))
