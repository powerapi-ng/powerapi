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

import json
from datetime import datetime
from typing import Dict, Any

from powerapi.report import Report


class PowerReport(Report):
    """
    PowerReport stores the power estimation information.
    """

    def __init__(self, timestamp: datetime, sensor: str, target: str, power: float, metadata: Dict[str, Any]):
        """
        Initialize a Power report using the given parameters.
        :param datetime timestamp: Report timestamp
        :param str sensor: Sensor name
        :param str target: Target name
        :param float power: Power value
        :param dict metadata: Metadata values, can be anything that add useful information
        """
        Report.__init__(self, timestamp, sensor, target)

        #: (dict): Metadate values, can be anything that add useful information.
        self.metadata = metadata

        #: (float): Power value.
        self.power = power

    def __repr__(self) -> str:
        return 'PowerReport(%s, %s, %s, %f, %s)' % (self.timestamp, self.sensor, self.target, self.power, self.metadata)

    @staticmethod
    def deserialize(data: Dict) -> PowerReport:
        """
        Generate a report using the given data.
        :param Dict data: Dictionary containing the report attributes
        :return: The Power report initialized with the given data
        """
        return PowerReport(data['timestamp'], data['sensor'], data['target'], data['power'], data['metadata'])
