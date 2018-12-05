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

"""
Module actor_puller
"""

from smartwatts.actor import Actor
from smartwatts.handler import AbstractHandler, PoisonPillMessageHandler
from smartwatts.message import PoisonPillMessage


class NoReportExtractedException(Exception):
    """ Exception raised when the handler can't extract a report from the given
    database

    """
    pass


class _TimeoutHandler(AbstractHandler):
    """
    TimeoutHandler class
    """

    def __init__(self, database, filt, autokill=False):
        self.database = database
        self.filter = filt
        self.database.load()
        self.autokill = autokill

    def _get_report_dispatcher(self):
        """
        read one report of the database and filter it,
        then return the tuple (report, dispatcher).

        Return:
            (Report, DispatcherActor): (extracted_report, dispatcher to sent
                                        this report)

        Raise:
            NoReportExtractedException : if the database doesn't contains
                                         report anymore

        """
        # Read one input, if it's None, it means there is not more
        # report in the database, just pass
        json = self.database.get_next()
        if json is None:
            raise NoReportExtractedException()

        # Deserialization
        report = self.filter.get_type()()
        report.deserialize(json)

        # Filter the report
        dispatcher = self.filter.route(report)
        return (report, dispatcher)

    def handle(self, msg, state):
        """
        Handle the send of the report to the good dispatcher
        """
        try:
            (report, dispatcher) = self._get_report_dispatcher()

        except NoReportExtractedException:
            if self.autokill:
                state.alive = False
            return state

        # Send to the dispatcher if it's not None
        if dispatcher is not None:
            dispatcher.send(report)

        return state


class PullerActor(Actor):
    """ PullerActor class """

    def __init__(self, name, database, filt, timeout,
                 verbose=False, autokill=False):
        """
        Initialization

        Parameters:
            @database: BaseDB object
            @filter:   Filter object
            @timeout:  define the time to wait for a msg, else it
                       run timeout_handler
            @autokill: if True, kill himself if timeout_handler
                       return None (it means that all the db has been read)
        """
        Actor.__init__(self, name, verbose, timeout=timeout)
        self.database = database
        self.filter = filt
        self.autokill = autokill

        # If timeout is 0, define new behaviour and doesn't recv message
        if timeout == 0:
            self.behaviour = self._behaviour_timeout_null

    def _behaviour_timeout_null(self):
        """
        Never read socket message, just run the timeout_handler
        """
        while self.state.alive:
            self._handle_message(None)

    def setup(self):
        """
        Override

        Connect to all dispatcher in filter and define timeout_handler
        """

        # Connect to all dispatcher
        for _, dispatcher in self.filter.filters:
            dispatcher.connect(self.context)

        # Create handler
        self.timeout_handler = _TimeoutHandler(self.database, self.filter,
                                               self.autokill)
        self.handlers.append((PoisonPillMessage, PoisonPillMessageHandler))
