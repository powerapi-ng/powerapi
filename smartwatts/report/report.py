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


class Report:
    """
    Report abtract class.
    """

    def __init__(self, timestamp, sensor, target):
        """
        :param time.Datetime timestamp: Timestamp of the report.
        :param str sensor: Report sensor name.
        :param str target: Report target name.
        """
        self.timestamp = timestamp
        self.sensor = sensor
        self.target = target

    def serialize(self):
        """
        Return the JSON format of the report
        """
        raise NotImplementedError()

    def deserialize(self, json):
        """
        Feed the report with the JSON input

        :param dict json: JSON report.
        """
        raise NotImplementedError()
