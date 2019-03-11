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

import logging
from powerapi.handler import InitHandler, StartHandler
from powerapi.database import DBError
from powerapi.message import ErrorMessage, OKMessage, StartMessage
from powerapi.message import PoisonPillMessage


class NoReportExtractedException(Exception):
    """
    Exception raised when the handler can't extract a report from the given
    database
    """


class PullerStartHandler(StartHandler):
    """
    Initialize the database interface
    """

    def initialization(self, state):
        """
        Initialize the database and connect all dispatcher to the
        socket_interface

        :param State state: State of the actor.
        :rtype powerapi.State: the new state of the actor
        """
        try:
            state.database.connect()
            state.database_it = iter(state.database)
        except DBError as error:
            state.socket_interface.send_control(ErrorMessage(error.msg))
            state.alive = False
            return state

        # Connect to all dispatcher
        for _, dispatcher in state.report_filter.filters:
            dispatcher.connect_data()

        return state


class TimeoutHandler(InitHandler):
    """
    Puller timeout, read the database.
    """

    def get_report_dispatcher(self, state):
        """
        read one report of the database and filter it,
        then return the tuple (report, dispatcher).

        Return:
            (Report, DispatcherActor): (extracted_report,
                                        dispatcher to sent
                                        this report)

        Raise:
            NoReportExtractedException : if the database doesn't contains
                                         report anymore

        """
        # Read one input, if it's None, it means there is not more
        # report in the database, just pass
        try:
            data = next(state.database_it)
        except StopIteration:
            raise NoReportExtractedException()

        # Deserialization
        report = state.database.report_model.get_type().deserialize(data)

        # Filter the report
        dispatchers = state.report_filter.route(report)
        return (report, dispatchers)

    def handle(self, msg, state):
        """
        Read data from Database and send it to the dispatchers.
        If there is no more data, send a kill message to every
        dispatcher.
        If stream mode is disable, kill the actor.

        :param None msg: None.
        :param smartwatts.State state: State of the actor.
        """
        try:
            (report, dispatchers) = self.get_report_dispatcher(state)
            # for sleeping mode
            state.socket_interface.timeout = state.timeout_basic
        except NoReportExtractedException:
            if not state.stream_mode:
                state.alive = False
            # for sleeping mode
            if state.counter < 10:
                state.counter += 1
            else:
                state.socket_interface.timeout = state.timeout_sleeping
            return state

        # Send to the dispatcher if it's not None
        for dispatcher in dispatchers:
            if dispatcher is not None:
                dispatcher.send_data(report)

        return state
