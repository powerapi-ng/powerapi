"""
Copyright (c) 2018, INRIA
Copyright (c) 2018, University of Lille
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

from powerapi.filter import FilterUselessError
from powerapi.handler import InitHandler, StartHandler
from powerapi.database import DBError
from powerapi.message import ErrorMessage
from powerapi.report.report import DeserializationFail
from powerapi.report_model.report_model import BadInputData


class NoReportExtractedException(Exception):
    """
    Exception raised when the handler can't extract a report from the given
    database
    """


class PullerStartHandler(StartHandler):
    """
    Initialize the database interface
    """

    def initialization(self):
        """
        Initialize the database and connect all dispatcher to the
        socket_interface
        """
        try:
            self.state.database.connect()
            self.state.database_it = iter(self.state.database)
        except DBError as error:
            self.state.actor.send_control(ErrorMessage(error.msg))
            self.state.alive = False

        # Connect to all dispatcher
        for _, dispatcher in self.state.report_filter.filters:
            dispatcher.connect_data()


class TimeoutHandler(InitHandler):
    """
    Puller timeout, read the database.
    """

    def _get_report_dispatcher(self):
        """
        read one report of the database and filter it,
        then return the tuple (report, dispatcher).

        :return (Report, DispatcherActor): extracted report and dispatcher to sent this report

        Raise:
            NoReportExtractedException : if the database doesn't contains
                                         report anymore

        """
        # Read one input, if it's None, it means there is not more
        # report in the database, just pass
        try:
            data = next(self.state.database_it)
            # Deserialization
            report = self.state.database.report_model.get_type().deserialize(data)
        except (StopIteration, BadInputData, DeserializationFail):
            raise NoReportExtractedException()

        # Filter the report
        dispatchers = self.state.report_filter.route(report)
        return (report, dispatchers)

    def handle(self, msg):
        """
        Read data from Database and send it to the dispatchers.
        If there is no more data, send a kill message to every
        dispatcher.
        If stream mode is disable, kill the actor.

        :param None msg: None.
        """
        try:
            (report, dispatchers) = self._get_report_dispatcher()
            # for sleeping mode
            self.state.actor.socket_interface.timeout = self.state.timeout_basic
        except NoReportExtractedException:
            if not self.state.database.stream_mode:
                self.state.alive = False
            # for sleeping mode
            if self.state.counter < 10:
                self.state.counter += 1
            else:
                self.state.actor.socket_interface.timeout = self.state.timeout_sleeping
            return
        except FilterUselessError:
            self.state.alive = False
            self.state.actor.send_control(ErrorMessage("FilterUselessError"))
            return

        # Send to the dispatcher if it's not None
        for dispatcher in dispatchers:
            if dispatcher is not None:
                dispatcher.send_data(report)
