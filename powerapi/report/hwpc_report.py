"""
Copyright (c) 2018, INRIA
Copyright (c) 2018, University of Lille
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict

from powerapi.report.report import Report, DeserializationFail


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
        try:
            report = HWPCReport(data['timestamp'], data['sensor'], data['target'], data['groups'])
        except KeyError:
            raise DeserializationFail()

        return report


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
