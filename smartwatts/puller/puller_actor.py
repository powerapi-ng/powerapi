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

from smartwatts.actor import Actor, BasicState, SocketInterface
from smartwatts.message import PoisonPillMessage, StartMessage
from smartwatts.handler import PoisonPillMessageHandler
from smartwatts.puller import TimeoutHandler, StartHandler


class PullerState(BasicState):
    """ Puller Actor State

    Contains in addition to BasicState values :
      - the database interface
      - the Filter class
    """
    def __init__(self, behaviour, socket_interface, database, report_filter):
        BasicState.__init__(self, behaviour, socket_interface)

        self.database = database
        self.report_filter = report_filter


class PullerActor(Actor):
    """ PullerActor class """

    def __init__(self, name, database, report_filter, timeout,
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
        self.timeout_handler = TimeoutHandler(self.autokill)

        timeout_null_behaviour = ((lambda actor:
                                   actor.timeout_handler.handle(None,
                                                                actor.state))
                                  if timeout == 0 else Actor._initial_behaviour)

        self.state = PullerState(timeout_null_behaviour,
                                 SocketInterface(name, timeout), database,
                                 report_filter)
        self.autokill = autokill

    def setup(self):
        """
        Override

        Connect to all dispatcher in filter and define timeout_handler
        """
        self.add_handler(PoisonPillMessage, PoisonPillMessageHandler())
        self.add_handler(StartMessage, StartHandler())
