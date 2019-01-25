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

import time
from smartwatts.actor import Actor, State, SocketInterface
from smartwatts.message import PoisonPillMessage, StartMessage
from smartwatts.handler import PoisonPillMessageHandler
from smartwatts.puller import StartHandler


class NoReportExtractedException(Exception):
    """
    Exception raised when we can't extract a report from the given
    database
    """


class PullerState(State):
    """
    Puller Actor State

    Contains in addition to State values :
      - the database interface
      - the Filter class
    """
    def __init__(self, behaviour, socket_interface, database, report_filter,
                 frequency, autokill):
        """
        :param func behaviour: Function that define the initial_behaviour
        :param SocketInterface socket_interface: Communication interface of the
                                                 actor
        :param BaseDB database: Allow to interact with a Database
        :param Filter report_filter: Filter of the Puller
        :param int frequency: Define (in ms) the sleep time between each
                              read in the database.
        :param bool autokill: Puller autokill himself when it finish to read
                              all the database.
        """
        State.__init__(self, behaviour, socket_interface)

        #: (BaseDB): Allow to interact with a Database
        self.database = database

        #: (Filter): Filter of the puller
        self.report_filter = report_filter

        #: (int): Define (in ms) the sleep time between each read in the
        #: database.
        self.frequency = frequency

        #: (bool): Puller autokill himself when it finish to read all the
        #: database.
        self.autokill = autokill


class PullerActor(Actor):
    """
    PullerActor class

    A Puller allow to handle the reading of a database and to dispatch report
    to many Dispatcher depending of some rules.
    """

    def __init__(self, name, database, report_filter, frequency=0,
                 verbose=False, autokill=False):
        """
        :param str name: Actor name.
        :param BaseDB database: Allow to interact with a Database.
        :param Filter report_filter: Filter of the Puller.
        :param int frequency: Define (in ms) the sleep time between each
                              read in the database.
        :param bool verbose: Allow to display log.
        :param bool autokill: Puller autokill himself when it finish to read
                              all the database.
        """
        Actor.__init__(self, name, verbose)

        #: (State): Actor State.
        self.state = PullerState(Actor._initial_behaviour,
                                 SocketInterface(name, None), database,
                                 report_filter, frequency, autokill)

    def setup(self):
        """
        Define StartMessage handler and PoisonPillMessage handler
        """
        self.add_handler(PoisonPillMessage, PoisonPillMessageHandler())
        self.add_handler(StartMessage,
                         StartHandler(PullerActor._read_behaviour))

    def _read_behaviour(self):
        """
        Puller behaviour which read all the database, then autokill or
        reconfigure behaviour with _initial_behaviour
        """

        def get_report_dispatcher(state):
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
            json = state.database.get_next()
            if json is None:
                raise NoReportExtractedException()

            # Deserialization
            report = state.database.report_model.get_type()()
            report.deserialize(json)

            # Filter the report
            dispatchers = state.report_filter.route(report)
            return (report, dispatchers)

        # Read all the database
        while True:
            try:
                (report, dispatchers) = get_report_dispatcher(self.state)
            except NoReportExtractedException:
                for _, dispatcher in self.state.report_filter.filters:
                    dispatcher.send_data(PoisonPillMessage())
                if self.state.autokill:
                    self.state.alive = False
                break

            # Send to the dispatcher if it's not None
            for dispatcher in dispatchers:
                if dispatcher is not None:
                    dispatcher.send_data(report)
            time.sleep(self.state.frequency/1000)

        # Behaviour to _initial_behaviour
        self.state.behaviour = Actor._initial_behaviour
