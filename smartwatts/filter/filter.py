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


class FilterUselessError(Exception):
    """
    Exception raised when a filter route with 0 filters
    """


class Filter:
    """
    Filter abstract class

    A filter allow the Puller to route Report of the database to Dispatchers
    by fixing some rules.
    """

    def __init__(self):
        self.filters = []

    def get_type(self):
        """
        Return the report type for a filter.

        .. note::

            Need to be overrided
        """
        raise NotImplementedError()

    def filter(self, rule, dispatcher):
        """
        Define a rule for a kind of report, and send it to the dispatcher
        if the rule accept it.

        :param (func(report) -> bool) rule:      Function which return if
                                                 the report has to be send to
                                                 this dispatcher
        :param smartwatts.Dispatcher dispatcher: Dispatcher we want to send the
                                                 report
        """
        self.filters.append((rule, dispatcher))

    def route(self, report):
        """
        Get the list of dispatchers to whom send the report, or None

        :param smartwatts.Report report: Message to send
        """
        # Error if filters is empty
        if not self.filters:
            raise FilterUselessError()

        dispatchers = []
        for rule, dispatcher in self.filters:
            if rule(report):
                dispatchers.append(dispatcher)

        return dispatchers
