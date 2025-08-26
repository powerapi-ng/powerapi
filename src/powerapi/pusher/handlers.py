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

import time

from powerapi.actor import State
from powerapi.database import DBError
from powerapi.handler import InitHandler, StartHandler, PoisonPillMessageHandler
from powerapi.message import ErrorMessage
from powerapi.report import Report


class PusherStartHandler(StartHandler):
    """
    Start Message Handler for the Pusher actor.
    """

    def initialization(self) -> None:
        """
        Initialize the Pusher actor.
        """
        try:
            self.state.database.connect()
        except DBError as exn:
            self.state.logger.error('Failed to connect the database driver: %s', exn.msg)
            self.state.actor.send_control(ErrorMessage('Database connection failed'))
            self.state.alive = False


class PusherPoisonPillMessageHandler(PoisonPillMessageHandler):
    """
    Poison Pill Message Handler for the Pusher actor.
    """

    def teardown(self, soft: bool = False) -> None:
        """
        Teardown the Pusher actor.
        Flushes the reports buffer before disconnecting the database driver.
        :param soft: Toggle soft-kill mode for the actor
        """
        if self.state.buffer:
            try:
                self.state.database.write(self.state.buffer)
                self.state.buffer = []
            except DBError as exn:
                self.state.actor.logger.error('The reports could not be saved before shutting down actor: %s', exn.msg)

        self.state.database.disconnect()


class ReportHandler(InitHandler):
    """
    Generic Report Handler class.
    Stores the received reports into a buffer before sending them to be persisted in batch by the database.
    """

    def __init__(self, state: State, flush_interval: float, max_buffer_size: int):
        """
        :param state: Actor state
        :param flush_interval: Maximum time in seconds to wait before flushing the buffered reports to the database
        :param max_buffer_size: Maximum number of reports that can be buffered before a forced flush to the database
        """
        super().__init__(state)

        self.flush_interval = flush_interval
        self.max_buffer_size = max_buffer_size

        self._last_write_ts: float = 0.0

    def handle(self, msg: Report) -> None:
        """
        Buffers a report and flushes the buffer to the database when needed.
        Incoming reports are stored in a buffer instead of being written to the database immediately.
        The buffer is flushed in batch when it exceeds the maximum size or the flush interval has elapsed.
        :param msg: Report to be buffered and eventually persisted
        """
        self.state.buffer.append(msg)

        if (time.monotonic() - self._last_write_ts) > self.flush_interval or len(self.state.buffer) >= self.max_buffer_size:
            try:
                self.state.database.write(self.state.buffer)
                self.state.buffer = []
            except DBError as exn:
                self.state.actor.logger.error('The reports could not be saved: %s', exn.msg)
            finally:
                self._last_write_ts = time.monotonic()
