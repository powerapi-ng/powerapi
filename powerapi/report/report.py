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

from __future__ import annotations

from datetime import datetime
from typing import Dict
from powerapi.message import Message


class Report(Message):
    """
    Report abtract class.
    """

    def __init__(self, timestamp: datetime, sensor: str, target: str):
        """
        Initialize a report using the given parameters.
        :param datetime timestamp: Timestamp
        :param str sensor: Sensor name.
        :param str target: Target name.
        """
        self.timestamp = timestamp
        self.sensor = sensor
        self.target = target

    def __str__(self):
        return '%s(%s, %s, %s)' % (self.__class__.__name__, self.timestamp, self.sensor, self.target)

    def __repr__(self):
        return '%s(%s, %s, %s)' % (self.__class__.__name__, self.timestamp, self.sensor, self.target)

    def __eq__(self, other):
        return isinstance(other, type(self)) and (repr(other) == repr(self))

    def serialize(self) -> Dict:
        """
        Serialize the report in JSON.
        :return: A string containing the report in JSON format
        """
        return self.__dict__

    @staticmethod
    def deserialize(data: Dict) -> Report:
        """
        Generate a report using the given data.

        :param dict json_data: JSON report.
        """
        raise NotImplementedError()
