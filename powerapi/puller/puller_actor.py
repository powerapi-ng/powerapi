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
from powerapi.actor import Actor, State, SocketInterface
from powerapi.message import PoisonPillMessage, StartMessage
from powerapi.handler import PoisonPillMessageHandler
from powerapi.puller import PullerStartHandler, TimeoutHandler


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
    def __init__(self, behaviour, socket_interface, logger,
                 database, report_filter, stream_mode):
        """
        :param func behaviour: Function that define the initial_behaviour
        :param SocketInterface socket_interface: Communication interface of the
                                                 actor
        :param BaseDB database: Allow to interact with a Database
        :param Filter report_filter: Filter of the Puller
        :param bool stream_mode: Puller stream_mode database.
        """
        State.__init__(self, behaviour, socket_interface, logger)

        #: (BaseDB): Allow to interact with a Database
        self.database = database

        #: (it BaseDB): Allow to browse the database
        self.database_it = None

        #: (Filter): Filter of the puller
        self.report_filter = report_filter

        #: (bool): Puller stream_mode database.
        self.stream_mode = stream_mode


class PullerActor(Actor):
    """
    PullerActor class

    A Puller allow to handle the reading of a database and to dispatch report
    to many Dispatcher depending of some rules.
    """

    def __init__(self, name, database, report_filter,
                 level_logger=logging.WARNING, stream_mode=False, timeout=0):
        """
        :param str name: Actor name.
        :param BaseDB database: Allow to interact with a Database.
        :param Filter report_filter: Filter of the Puller.
        :param int level_logger: Define the level of the logger
        :param bool stream_mode: Puller stream_mode himself when it finish to
                                 read all the database.
        """

        Actor.__init__(self, name, level_logger, timeout)
        #: (State): Actor State.
        self.state = PullerState(Actor._initial_behaviour,
                                 SocketInterface(name, timeout),
                                 self.logger,
                                 database,
                                 report_filter, stream_mode)

    def setup(self):
        """
        Define StartMessage handler and PoisonPillMessage handler
        """
        self.add_handler(PoisonPillMessage, PoisonPillMessageHandler())
        self.add_handler(StartMessage, PullerStartHandler())
        self.set_timeout_handler(TimeoutHandler())

    def terminated_behaviour(self):
        """
        Allow to end some socket connection properly
        """
        # Connect to all dispatcher
        for _, dispatcher in self.state.report_filter.filters:
            dispatcher.state.socket_interface.close()
