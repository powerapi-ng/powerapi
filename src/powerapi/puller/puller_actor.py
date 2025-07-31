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

from powerapi.actor import Actor, State
from powerapi.database import ReadableDatabase
from powerapi.filter import Filter
from powerapi.message import StartMessage, PoisonPillMessage
from powerapi.puller.database_poller import DatabasePollerThread
from powerapi.puller.handlers import PullerStartMessageHandler, PullerPoisonPillMessageHandler


class PullerState(State):
    """
    Puller Actor State class.
    """

    def __init__(self, actor: Actor, database: ReadableDatabase, report_filter: Filter, stream_mode: bool):
        """
        :param actor: Puller actor instance
        :param database: Database driver
        :param report_filter: Filter to use when dispatching reports
        :param stream_mode: If true, poll continuously from the database; otherwise, stop the poller thread on empty result
        """
        super().__init__(actor)

        self.database = database
        self.report_filter = report_filter
        self.stream_mode = stream_mode

        self.db_poller_thread: DatabasePollerThread | None = None


class PullerActor(Actor):
    """
    Puller Actor class.
    This actor allows to retrieve reports from a database and send them to theirs corresponding dispatcher.
    """

    def __init__(self, name: str, database: ReadableDatabase, report_filter: Filter, stream_mode: bool = False, level_logger: int = logging.WARNING):
        """
        :param name: Name of the puller actor
        :param database: Database driver to use to persist reports
        :param report_filter: Filter to use when dispatching reports
        :param level_logger: Define the level of the logger for the actor
        """
        super().__init__(name, level_logger, 1000)

        self.state = PullerState(self, database, report_filter, stream_mode)

    def setup(self):
        """
        Set up the Puller actor message handlers.
        """
        self.add_handler(StartMessage, PullerStartMessageHandler(self.state))
        self.add_handler(PoisonPillMessage, PullerPoisonPillMessageHandler(self.state))
