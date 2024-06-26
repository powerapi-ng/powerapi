# Copyright (c) 2022, INRIA
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
import time
from threading import Thread

from powerapi.actor import State
from powerapi.database import DBError
from powerapi.exception import PowerAPIException
from powerapi.filter import FilterUselessError
from powerapi.handler import StartHandler, PoisonPillMessageHandler
from powerapi.message import ErrorMessage, PoisonPillMessage
from powerapi.message import Message
from powerapi.report import BadInputData


class NoReportExtractedException(PowerAPIException):
    """
    Exception raised when the handler can't extract a report from the given
    database
    """


class DBPullerThread(Thread):
    """
    Thread for pulling data from source
    """

    def __init__(self, state, timeout, handler):
        super().__init__(daemon=True)
        self.timeout = timeout
        self.state = state
        self.handler = handler

    def run(self):
        """
        Read data from Database and send it to the dispatchers.
        If there is no more data, send a kill message to every
        dispatcher.
        If stream mode is disabled, kill the actor.

        :param None msg: None.
        """
        while self.state.alive:
            try:
                raw_report = next(self.state.database_it)
                dispatchers = self.state.report_filter.route(raw_report)
                for dispatcher in dispatchers:
                    dispatcher.send_data(raw_report)

            except FilterUselessError:
                self.handler.handle_internal_msg(PoisonPillMessage(False, self.name))
                return

            except BadInputData as exn:
                logging.error('Received malformed report from database: %s', exn.msg)
                logging.debug('Raw report value: %s', exn.input_data)

            except StopIteration:
                time.sleep(self.state.timeout_puller / 1000)
                if not self.state.stream_mode:
                    self.handler.handle_internal_msg(PoisonPillMessage(False, self.name))
                    return


class PullerPoisonPillMessageHandler(PoisonPillMessageHandler):
    """
    Default handler PoisonPillMessage
    """

    def teardown(self, soft=False):
        for _, dispatcher in self.state.report_filter.filters:
            dispatcher.socket_interface.close()


class PullerInitializationException(Exception):
    """
    Exception related to puller initialization
    """

    def __init__(self, msg):
        Exception.__init__(self)
        self.msg = msg


class PullerStartHandler(StartHandler):
    """
    Initialize the database interface
    """

    def __init__(self, state: State, timeout: int):
        StartHandler.__init__(self, state)

        self.timeout = timeout

    def handle_internal_msg(self, msg):
        """
        Deal with the given message
        :param msg: Message to handle
        """
        StartHandler.delegate_message_handling(self, msg)

    def initialization(self):
        if not self.state.report_filter.filters:
            raise PullerInitializationException('No filters')

        # Connect to all dispatcher
        for _, dispatcher in self.state.report_filter.filters:
            dispatcher.connect_data()

        self._connect_database()

    def handle(self, msg: Message):
        try:
            StartHandler.handle(self, msg)
        except PullerInitializationException as e:
            self.state.actor.send_control(ErrorMessage(self.state.actor.name, e.msg))

        self.pull_db()

        self.handle_internal_msg(PoisonPillMessage(False, self.state.actor.name))

    def pull_db(self):
        """
        Initialize the database and connect all dispatcher to the
        socket_interface
        """
        db_puller_thread = DBPullerThread(self.state, self.timeout, self)
        db_puller_thread.start()

        while self.state.alive:
            msg = self.state.actor.receive_control(self.timeout)
            if msg is not None:
                self.handle_internal_msg(msg)

    def _connect_database(self):
        try:
            self.state.database.connect()
            self.state.database_it = self.state.database.iter(self.state.stream_mode)
        except DBError as error:
            self.state.alive = False
            self.state.actor.send_control(ErrorMessage(self.state.actor.name, error.msg))
