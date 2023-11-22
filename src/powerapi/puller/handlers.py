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

import time
import asyncio
import logging
from threading import Thread

from powerapi.actor import State
from powerapi.message import Message
from powerapi.exception import PowerAPIException, BadInputData
from powerapi.filter import FilterUselessError
from powerapi.handler import StartHandler, PoisonPillMessageHandler
from powerapi.database import DBError
from powerapi.message import ErrorMessage, PoisonPillMessage
from powerapi.report.report import DeserializationFail


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
        Thread.__init__(self)
        self.timeout = timeout
        self.state = state
        self.loop = None
        self.handler = handler

    def _connect(self):
        try:
            self.state.database.connect()
            self.loop.run_until_complete(self.state.database.connect())
            self.state.database_it = self.state.database.iter(self.state.stream_mode)
        except DBError as error:
            self.state.actor.send_control(ErrorMessage(sender_name='system', error_message=error.msg))
            self.state.alive = False

    def _pull_database(self):
        try:
            if self.state.asynchrone:
                report = self.loop.run_until_complete(self.state.database_it.__anext__())
                if report is not None:
                    return report
                else:
                    raise StopIteration()
            else:
                return next(self.state.database_it)

        except (StopIteration, BadInputData, DeserializationFail) as database_problem:
            raise NoReportExtractedException() from database_problem

    def _get_dispatchers(self, report):
        return self.state.report_filter.route(report)

    def run(self):
        """
        Read data from Database and send it to the dispatchers.
        If there is no more data, send a kill message to every
        dispatcher.
        If stream mode is disabled, kill the actor.

        :param None msg: None.
        """
        if self.state.asynchrone:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.state.loop = self.loop
            self.loop.set_debug(enabled=True)
            logging.basicConfig(level=logging.DEBUG)

            self._connect()

        while self.state.alive:
            try:
                raw_report = self._pull_database()

                dispatchers = self._get_dispatchers(raw_report)
                for dispatcher in dispatchers:
                    dispatcher.send_data(raw_report)

            except NoReportExtractedException:
                time.sleep(self.state.timeout_puller / 1000)
                self.state.actor.logger.debug('NoReportExtractedException with stream mode ' +
                                              str(self.state.stream_mode))
                if not self.state.stream_mode:
                    self.handler.handle_internal_msg(PoisonPillMessage(soft=False, sender_name='system'))
                    return

            except FilterUselessError:
                self.handler.handle_internal_msg(PoisonPillMessage(soft=False, sender_name='system'))
                return

            except StopIteration:
                continue


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

        self._database_connection()

        if not self.state.report_filter.filters:
            raise PullerInitializationException('No filters')
        # Connect to all dispatcher
        for _, dispatcher in self.state.report_filter.filters:
            dispatcher.connect_data()

    def handle(self, msg: Message):
        try:
            StartHandler.handle(self, msg)
        except PullerInitializationException as e:
            self.state.actor.send_control(ErrorMessage(self.state.actor.name, e.msg))

        self.pull_db()

        self.handle_internal_msg(PoisonPillMessage(soft=False, sender_name='system'))

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

    def _database_connection(self):
        try:
            if not self.state.asynchrone:
                self.state.database.connect()
                self.state.database_it = self.state.database.iter(stream_mode=self.state.stream_mode)

        except DBError as error:
            self.state.actor.send_control(ErrorMessage(self.state.actor.name, error.msg))
            self.state.alive = False
