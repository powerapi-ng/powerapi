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
from smartwatts.message import PoisonPillMessage
from smartwatts.handler import PoisonPillMessageHandler
from smartwatts.puller import TimeoutHandler


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
            self.handle_message(None)

    def setup(self):
        """
        Override

        Connect to all dispatcher in filter and define timeout_handler
        """

        # Connect to all dispatcher
        for _, dispatcher in self.filter.filters:
            dispatcher.connect(self.context)

        # Create handler
        self.timeout_handler = TimeoutHandler(self.database, self.filter,
                                              self.autokill)
        self.add_handler(PoisonPillMessage, PoisonPillMessageHandler())
