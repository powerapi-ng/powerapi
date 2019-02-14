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

from powerapi.report import Report


class PowerReport(Report):
    """
    PowerReport class
    """

    def __init__(self, timestamp, sensor, target, power, metadata):
        """
        :param time.Datetime timestamp: Report timestamp.
        :param str sensor: Sensor name.
        :param str target: Target name.
        :param float power: Power value.
        :param dict metadata: Metadata values, can be anything that add
                              useful informations.
        """
        Report.__init__(self, timestamp, sensor, target)

        #: (dict): Metadate values, can be anything that add useful
        #: informations.
        self.metadata = metadata

        #: (float): Power value.
        self.power = power

    def serialize(self):
        """
        Return the JSON format of the report
        """
        json = {}
        json['timestamp'] = self.timestamp
        json['sensor'] = self.sensor
        json['target'] = self.target
        json['power'] = self.power
        json['metadata'] = self.metadata
        return json

    def deserialize(self, json):
        """
        Feed the report with the JSON input
        :param dict json: JSON data.
        """
        self.timestamp = json['timestamp']
        self.sensor = json['sensor']
        self.target = json['target']
        self.power = json['power']
        self.metadata = json['metadata']

    def __eq__(self, other):
        if not isinstance(other, PowerReport):
            return False

        return (self.timestamp == other.timestamp or
                self.sensor == other.sensor or
                self.target == other.target or
                self.metadata == other.metadata or
                self.power == other.power)
