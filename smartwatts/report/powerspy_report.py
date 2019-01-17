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
Module powerspy_report which define the PowerSpyReport class
"""

from smartwatts.report import Report
from enum import Enum


def powerspy_extract_sensor(report):
    return [(str(report.sensor), report)]

class PowerSpyReport(Report):
    """ PowerSpyReport class """

    def __init__(self, timestamp, sensor, target, val1=0, val2=0):
        Report.__init__(self, timestamp, sensor, target)
        self.val1 = val1
        self.val2 = val2

    def operation(self):
        """ op """
        return self.val1 + self.val2

    def from_json(self, json):
        """
        Get PowerSpyReport from mongodb

        Format

        .. code-block:: json

            {
                val1: first value
                val2: second value
            }
        """
        self.val1 = json['val1']
        self.val2 = json['val2']
