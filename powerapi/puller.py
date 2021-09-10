# Copyright (c) 2021, INRIA
# Copyright (c) 2021, University of Lille
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
import asyncio

from thespian.actors import ActorExitRequest

from powerapi.actor import TimedActor, InitializationException
from powerapi.report import BadInputData
from powerapi.database import DBError
from powerapi.message import PullerStartMessage, EndMessage


class PullerActor(TimedActor):
    """
    Actor used to pull data from sources.

    A puller Actor is configured to pull data from one type of sources
    """
    def __init__(self):
        TimedActor.__init__(self, PullerStartMessage, 0.5)

        self.database = None
        self.report_filter = None
        self.stream_mode = None
        self.database_it = None
        self.report_modifier_list = None
        self.loop = None

        self._number_of_message_before_sleeping = 10

    def _initialization(self, start_message: PullerStartMessage):
        TimedActor._initialization(self, start_message)

        self.database = start_message.database
        self.report_filter = start_message.report_filter
        self.stream_mode = start_message.stream_mode
        self.report_modifier_list = start_message.report_modifier_list

        self._database_connection()
        if not self.report_filter.filters:
            raise InitializationException('filter without rules')

    def _database_connection(self):
        try:
            if not self.database.asynchrone:
                self.database.connect()
            else:
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
                self.loop.set_debug(enabled=True)
                logging.basicConfig(level=logging.DEBUG)
                self.loop.run_until_complete(self.database.connect())
            self.database_it = self.database.iter(self.stream_mode)
        except DBError as error:
            raise InitializationException(error.msg) from error

    def _modify_report(self, report):
        for report_modifier in self.report_modifier_list:
            report = report_modifier.modify_report(report)
        return report

    def _launch_task(self):
        """
        Initialize the database and connect all dispatcher to the
        socket_interface
        """
        for _ in range(self._number_of_message_before_sleeping):
            try:
                raw_report = self._pull_database()
                report = self._modify_report(raw_report)
                dispatchers = self.report_filter.route(report)
                for dispatcher in dispatchers:
                    self.log_debug('send report ' + str(report) + 'to ' + str(dispatcher))
                    self.send(dispatcher, report)
                self.wakeupAfter(self._time_interval)
                return
            except StopIteration:
                if self.stream_mode:
                    self.wakeupAfter(self._time_interval)
                    return
                self.log_info('input source empty, stop system')
                self._terminate()
                return
            except BadInputData as exn:
                log_line = 'BadinputData exception raised for input data' + str(exn.input_data)
                log_line += ' with message : ' + exn.msg
                self.log_warning(log_line)

    def _terminate(self):
        self.send(self.parent, EndMessage(self.name))
        for _, dispatcher in self.report_filter.filters:
            self.send(dispatcher, EndMessage(self.name))
        self.send(self.myAddress, ActorExitRequest())

    def _pull_database(self):
        if self.database.asynchrone:
            report = self.loop.run_until_complete(self.database_it.__anext__())
            if report is not None:
                return report
            else:
                raise StopIteration()
        else:
            return next(self.database_it)
