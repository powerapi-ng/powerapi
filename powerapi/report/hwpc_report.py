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

from powerapi.report.report import Report


class HWPCReport(Report):
    """
    HWPCReport class

    JSON HWPC format

    .. code-block:: json

        {
         'timestamp': $int,
         'sensor': '$str',
         'target': '$str',
         'groups' : {
            '$group_name': {
               '$socket_id': {
                   '$core_id': {
                       '$event_name': '$int',
                       ...
                   }
                   ...
               }
               ...
            }
            ...
         }
        }
    """

    def __init__(self, timestamp: datetime, sensor: str, target: str, groups: Dict[str, Dict]):
        """
        Initialize an HWPC report using the given parameters.
        :param datetime timestamp: Timestamp of the report
        :param str sensor: Sensor name
        :param str target: Target name
        :param Dict groups: Events groups
        """
        Report.__init__(self, timestamp, sensor, target)

        #: (dict): Events groups
        self.groups = groups

    def __repr__(self) -> str:
        return 'HWCPReport(%s, %s, %s, %s)' % (self.timestamp, self.sensor, self.target, self.groups.keys())

    @staticmethod
    def deserialize(data: Dict) -> HWPCReport:
        """
        Generate a report using the given data.
        :param data: Dictionary containing the report attributes
        :return: The HWPC report initialized with the given data
        """
        return HWPCReport(data['timestamp'], data['sensor'], data['target'], data['groups'])


#############################
# REPORT CREATION FUNCTIONS #
#############################


def create_core_report(core_id, event_id, event_value, events=None):
    id_str = str(core_id)
    data = {id_str: {}}
    if events is not None:
        data[id_str] = events
        return data
    data[id_str] = {event_id: event_value}
    return data


def create_socket_report(socket_id, core_list):
    id_str = str(socket_id)
    data = {id_str: {}}
    for core in core_list:
        data[id_str].update(core)
    return data


def create_group_report(group_id, socket_list):
    group = {}
    for socket in socket_list:
        group.update(socket)
    return (group_id, group)


def create_report_root(group_list, timestamp=datetime.fromtimestamp(0), sensor='toto', target='system'):
    sensor = HWPCReport(timestamp=timestamp, sensor=sensor, target=target, groups={})
    for (group_id, group) in group_list:
        sensor.groups[group_id] = group
    return sensor
