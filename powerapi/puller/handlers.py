# Copyright (C) 2018  University of Lille
# Copyright (C) 2018  INRIA
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
        except NoReportExtractedException:
            if not state.stream_mode:
                state.alive = False
            return state

        # Send to the dispatcher if it's not None
        for dispatcher in dispatchers:
            if dispatcher is not None:
                dispatcher.send_data(report)

        return state
