# Copyright (c) 2025, Inria
# Copyright (c) 2025, University of Lille
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

import os
import signal
from threading import Thread, Event
from time import sleep

from powerapi.actor import Actor
from powerapi.database import ReadableDatabase, ConnectionFailed, ReadFailed
from powerapi.filter import Filter


class DatabasePollerThread(Thread):
    """
    Database Poller Thread.
    Fetches reports from a database and forward it to theirs corresponding dispatcher.
    """

    def __init__(self, actor: Actor, database: ReadableDatabase, report_filter: Filter, stream_mode: bool, poll_interval: float = 1.0):
        """
        :param actor: Puller actor instance
        :param database: Database to retrieve the reports from
        :param report_filter: Report filter used to dispatch the received reports
        :param stream_mode: If true, poll continuously from the database; otherwise, stop the poller thread on empty result
        :param poll_interval: Interval in seconds between database polls
        """
        super().__init__(name='database-poller-thread', daemon=True)

        self.actor = actor
        self.database = database
        self.report_filter = report_filter
        self.stream_mode = stream_mode
        self.poll_interval = poll_interval

        self._stop_event = Event()

    @staticmethod
    def kill_parent_actor_on_exit(func):
        """
        Decorator that kills the parent actor when the wrapped function exits.
        """
        def wrapper(self, *args, **kwargs):
            try:
                func(self, *args, **kwargs)
            finally:
                # Don't send a signal to the parent actor if the stop was requested by the actor itself.
                if not self._stop_event.is_set():
                    os.kill(os.getpid(), signal.SIGINT)

        return wrapper

    @kill_parent_actor_on_exit
    def run(self) -> None:
        """
        Entrypoint of the database poller thread.
        """
        try:
            self.database.connect()
        except ConnectionFailed as exn:
            self.actor.logger.error('Failed to connect the database driver: %s', exn.msg)
            return

        self.actor.logger.info('Database poller thread started')

        while not self._stop_event.is_set():
            try:
                for report in self.database.read(self.stream_mode):
                    for dispatcher in self.report_filter.route(report):
                        dispatcher.send_data(report)

                if not self.stream_mode:
                    self.actor.logger.info('No reports available from database, shutting down poller thread')
                    break
            except ReadFailed as exn:
                self.actor.logger.error('Failed to fetch reports from database: %s', exn.msg)

            sleep(self.poll_interval)

        self.database.disconnect()
        self.actor.logger.info('Database poller thread stopped')

    def stop(self) -> None:
        """
        Shutdown the database poller thread.
        """
        self._stop_event.set()
