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
Module filter
"""


class FilterUselessError(Exception):
    """ Raise when a filter route with 0 filters """
    pass


class Filter:
    """ Filter abstract class """

    def __init__(self):
        self.filters = []

    def get_type(self):
        """
        Need to be overrided.

        Return the report type for a filter.
        """
        raise NotImplementedError()

    def filter(self, rule, dispatcher):
        """
        Define a rule for a new report, and send it to the dispatcher
        if the rule accept it.

        Parameters:
            @rule: function which return true of false
            @dispatcher: Actor we want to send the report
        """
        self.filters.append((rule, dispatcher))

    def route(self, msg):
        """
        Return the dispatcher to whom
        send the msg, or None

        Parameters:
            @msg: msg to send
        """
        # Error if filters is empty
        if not self.filters:
            raise FilterUselessError()

        dispatchers = []
        for rule, dispatcher in self.filters:
            if rule(msg):
                dispatchers.append(dispatcher)

        return dispatchers
