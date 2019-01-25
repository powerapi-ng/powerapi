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

from smartwatts.actor import Actor, State, SocketInterface
from smartwatts.pusher import PowerHandler, StartHandler, TimeoutHandler
from smartwatts.message import PoisonPillMessage, StartMessage
from smartwatts.handler import PoisonPillMessageHandler


class PusherState(State):
    """
    Pusher Actor State

    Contains in addition to State values :
      - The database interface
    """
    def __init__(self, behaviour, socket_interface, database):
        """
        :param func behaviour: Function that define the initial_behaviour.
        :param SocketInterface socket_interface: Communication interface of the
                                                 actor.
        :param BaseDB database: Database for saving data.
        """
        State.__init__(self, behaviour, socket_interface)

        #: (BaseDB): Database for saving data.
        self.database = database


class PusherActor(Actor):
    """
    PusherActor class

    The Pusher allow to save Report sent by Formula.
    """

    def __init__(self, name, report_type, database, verbose=False):
        """
        :param str name: Pusher name.
        :param Report report_type: Type of the report that the pusher
                                   handle.
        :param BaseDB database: Database use for saving data.
        :param bool verbose: Allow to display log.
        """
        timeout = 3000
        Actor.__init__(self, name, verbose, timeout)

        #: (Report): Type of the report that the pusher handle.
        self.report_type = report_type

        #: (State): State of the actor.
        self.state = PusherState(Actor._initial_behaviour,
                                 SocketInterface(name, timeout), database)

    def setup(self):
        """
        Define StartMessage, PoisonPillMessage handlers and a handler for
        each report type
        """
        self.add_handler(PoisonPillMessage, PoisonPillMessageHandler())
        self.add_handler(self.report_type, PowerHandler())
        self.add_handler(StartMessage, StartHandler())
        self.set_timeout_handler(TimeoutHandler())
