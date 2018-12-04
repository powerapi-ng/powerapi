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

from smartwatts.actor import Actor, Handler


class _TimeoutHandler(Handler):
    """
    TimeoutHandler class
    """

    def __init__(self, database, filt):
        self.database = database
        self.filter = filt
        self.database.load()

    def handle(self, msg):
        """
        Override

        This handler read one report of the database and filter it,
        then return the tuple (report, dispatcher).
        """
        # Read one input, if it's None, it means there is not more
        # report in the database, just pass
        json = self.database.get_next()
        if json is None:
            return None

        # Deserialization
        report = self.filter.get_type()()
        report.deserialize(json)

        # Filter the report
        dispatcher = self.filter.route(report)
        return (report, dispatcher)


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
        while self.alive:
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
        self.timeout_handler = _TimeoutHandler(self.database, self.filter)

    def _post_handle(self, result):
        """
        Override

        Handle the send of the report to the good dispatcher
        """
        # Test if result is None
        if result is None:
            if self.autokill:
                self.alive = False
            return

        # Extract report & dispatcher
        # TODO: ugly, and unsafe
        report = result[0]
        dispatcher = result[1]

        # Send to the dispatcher if it's not None
        if dispatcher is not None:
            dispatcher.send(report)
