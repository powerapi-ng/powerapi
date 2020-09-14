# Copyright (c) 2018, INRIA
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
import time
import asyncio
import logging
import threading
from threading import Thread

from powerapi.actor import NotConnectedException
from powerapi.message import UnknowMessageTypeException, StartMessage, OKMessage, ErrorMessage
from powerapi.handler import HandlerException
from powerapi.exception import PowerAPIException
from powerapi.filter import FilterUselessError
from powerapi.handler import InitHandler, StartHandler, PoisonPillMessageHandler
from powerapi.database import DBError, SocketDB
from powerapi.message import ErrorMessage, PoisonPillMessage
from powerapi.report.report import DeserializationFail
from powerapi.report_model.report_model import BadInputData

class NoReportExtractedException(PowerAPIException):
    """
    Exception raised when the handler can't extract a report from the given
    database
    """

class DBPullerThread(Thread):

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
            self.state.database_it = self.state.database.iter(self.state.report_model, self.state.stream_mode)

        except DBError as error:
            self.state.actor.send_control(ErrorMessage(error.msg))
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

        except (StopIteration, BadInputData, DeserializationFail):
            raise NoReportExtractedException()

    def _get_dispatchers(self, report):
        return self.state.report_filter.route(report)

    def run(self):
        """
        Read data from Database and send it to the dispatchers.
        If there is no more data, send a kill message to every
        dispatcher.
        If stream mode is disable, kill the actor.

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
                report = self._pull_database()
                dispatchers = self._get_dispatchers(report)
                for dispatcher in dispatchers:
                    dispatcher.send_data(report)

            except NoReportExtractedException:
                time.sleep(self.state.timeout_puller/1000)
                if not self.state.stream_mode:
                    self.handler.handle_internal_msg(PoisonPillMessage(soft=False))
                    return

            except FilterUselessError:
                self.handler.handle_internal_msg(PoisonPillMessage(soft=False))
                return

            except StopIteration:
                continue



class PullerPoisonPillMessageHandler(PoisonPillMessageHandler):
    def teardown(self, soft=False):
        for _, dispatcher in self.state.report_filter.filters:
            dispatcher.socket_interface.close()

class InitiatizationException(Exception):

    def __init__(self, msg):
        self.msg = msg


class PullerStartHandler(StartHandler):
    """
    Initialize the database interface
    """

    def __init__(self, state, timeout):
        StartHandler.__init__(self, state)

        self.timeout = timeout

    def handle_internal_msg(self, msg):
        try:
            handler = self.state.get_corresponding_handler(msg)
            handler.handle_message(msg)
        except UnknowMessageTypeException:
            self.state.actor.logger.warning("UnknowMessageTypeException: " + str(msg))
        except HandlerException:
            self.state.actor.logger.warning("HandlerException")

    def initialization(self):

        self._database_connection()

        if not self.state.report_filter.filters:
            raise InitiatizationException('No filters')
        # Connect to all dispatcher
        for _, dispatcher in self.state.report_filter.filters:
            dispatcher.connect_data()

    def handle(self, msg):
        if self.state.initialized:
            self.state.actor.send_control(
                ErrorMessage('Actor already initialized'))
            return

        if not isinstance(msg, StartMessage):
            return

        try:
            self.initialization()
        except InitiatizationException as e:
            self.state.actor.send_control(ErrorMessage(e.msg))

        if self.state.alive:
            self.state.initialized = True
            self.state.actor.send_control(OKMessage())

        self.pull_db()

    def pull_db(self):
        """
        Initialize the database and connect all dispatcher to the
        socket_interface
        """
        # db_puller_thread = DBPullerThread(self.state, self.timeout, loop=asyncio.get_event_loop())
        db_puller_thread = DBPullerThread(self.state, self.timeout, self)
        db_puller_thread.start()
        # while db_puller_thread.is_alive() and self.state.alive:
        while self.state.alive:
            time.sleep(0.4)
            msg = self.state.actor.receive_control(0.1)
            if msg is not None:
                self.handle_internal_msg(msg)

        # self.handle_internal_msg(PoisonPillMessage(soft=False))

    def _database_connection(self):
        try:
            if not self.state.asynchrone:
                self.state.database.connect()
                self.state.database_it = self.state.database.iter(self.state.report_model, self.state.stream_mode)

        except DBError as error:
            self.state.actor.send_control(ErrorMessage(error.msg))
            self.state.alive = False
