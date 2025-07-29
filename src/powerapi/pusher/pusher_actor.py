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

from powerapi.actor import Actor, State
from powerapi.database import WritableDatabase
from powerapi.message import PoisonPillMessage, StartMessage
from powerapi.pusher.handlers import ReportHandler, PusherStartHandler, PusherPoisonPillMessageHandler
from powerapi.report import Report


class PusherState(State):
    """
    Pusher Actor State class.
    """

    def __init__(self, actor: Actor, database: WritableDatabase):
        """
        :param actor: Pusher actor
        :param database: Database driver used to persist reports
        """
        super().__init__(actor)

        self.database: WritableDatabase = database
        self.buffer: list[Report] = []


class PusherActor(Actor):
    """
    Pusher Actor class.
    This actor allows to persist Reports sent by a Formula to a database.
    """

    def __init__(self, name: str, database: WritableDatabase, flush_interval: float = 0.100, max_buffer_size: int = 50, logger_level: int = logging.WARNING):
        """
        :param name: Name of the pusher actor
        :param database: Database driver to use to persist reports
        :param flush_interval: Maximum time in seconds to wait before flushing the buffered reports to the database
        :param max_buffer_size: Maximum number of reports that can be buffered before a forced flush to the database
        :param logger_level: Define the level of the logger for the actor
        """
        super().__init__(name, logger_level, 1000)

        self.flush_interval = flush_interval
        self.max_buffer_size = max_buffer_size

        self.state = PusherState(self, database)

    def setup(self):
        """
        Set up the Pusher actor message handlers.
        """
        self.add_handler(StartMessage, PusherStartHandler(self.state))
        self.add_handler(PoisonPillMessage, PusherPoisonPillMessageHandler(self.state))
        self.add_handler(Report, ReportHandler(self.state, self.flush_interval, self.max_buffer_size))
