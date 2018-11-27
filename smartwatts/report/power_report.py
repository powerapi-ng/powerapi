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

from smartwatts.report import Report


class PowerReport(Report):
    """ PowerReport class """

    def __init__(self, timestamp, sensor, target, power, metadata):
        self.timestamp = timestamp
        self.sensor = sensor
        self.target = target
        self.metadata = metadata
        self.power = power

    def serialize(self):
        json = {}
        json['timestamp'] = self.timestamp
        json['sensor'] = self.sensor
        json['target'] = self.target
        json['power'] = self.power
        json['metadata'] = self.metadata
        return json

    def deserialize(self, json):
        self.timestamp = json['timestamp']
        self.sensor = json['sensor']
        self.target = json['target']
        self.power = json['power']
        self.metadata = json['metadata']
