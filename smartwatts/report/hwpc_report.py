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
Module hwpc_sensor which define the HWPCReport class
"""
from smartwatts.report.report import Report


class HWPCReportCore(Report):
    """
    HWPCReportCore class
    Encapuslation for core report
    """

    def __init__(self, core_id=None):
        Report.__init__(self)
        self.core_id = core_id
        self.events = {}

    def __str__(self):
        display = ("  \n" +
                   '    ' + str(self.core_id) + ":\n" +
                   '    ' + self.events.__str__() + "\n")
        return display

    def serialize(self):
        """
        Return the JSON format of the report
        """
        return self.events

    def deserialize(self, json):
        """
        Feed the report with the JSON input
          @json dict of events
        """
        for event_key, event_value in json.items():
            self.events[event_key] = int(event_value)


class HWPCReportSocket(Report):
    """
    HWPCReportSocket class
    Encapsulation for Socket report
    """
    def __init__(self, socket_id):
        """
        socket:            socket id (int)
        cores:             dict of cores
        """
        Report.__init__(self)
        self.socket_id = socket_id
        self.cores = {}
        self.group_id = None

    def __str__(self):
        display = (" \n" +
                   '  ' + str(self.socket_id) + ":\n" +
                   '  ' + ''.join([self.cores[c].__str__()
                                   for c in self.cores]))
        return display

    def serialize(self):
        """
        Return the JSON format of the report
        """
        json = {}
        for key, _ in self.cores.items():
            json[key] = self.cores[key].serialize()
        return json

    def deserialize(self, json):
        """
        Feed the report with the JSON input
          @json: socket hwpc input
        """
        for core_key, core_value in json.items():
            hwpc_core = HWPCReportCore(int(core_key))
            hwpc_core.deserialize(core_value)
            self.cores[core_key] = hwpc_core


class HWPCReport(Report):
    """ HWPCReport class """

    def __init__(self, timestamp=None, sensor=None, target=None):
        """
        timestamp: when the report is done
        sensor:    sensor name
        target:    target name
        groups:    dict of group, a group is a dict of socket
        """
        Report.__init__(self, timestamp, sensor, target)
        self.groups = {}

    def __str__(self):
        display = ("\n" +
                   ' ' + str(self.timestamp) + "\n" +
                   ' ' + self.sensor + "\n" +
                   ' ' + self.target + "\n" +
                   ' '.join(['\n' + g + '\n ' +
                             ''.join([self.groups[g][s].__str__()
                                      for s in self.groups[g]])
                             for g in self.groups]) +
                   "\n")
        return display

    def serialize(self):
        """
        Return the JSON format of the report
        """
        json = {}
        json['timestamp'] = self.timestamp
        json['sensor'] = self.sensor
        json['target'] = self.target
        json['groups'] = {}
        for group_key, _ in self.groups.items():
            json['groups'][group_key] = {}
            for socket_key, socket_value in self.groups[group_key].items():
                json['groups'][group_key][
                    socket_key] = socket_value.serialize()
        return json

    def deserialize(self, json):
        """
        Feed the report with the JSON input
          @json: full hwpc input
        """
        self.timestamp = json['timestamp']
        self.sensor = json['sensor']
        self.target = json['target']
        for group_key, _ in json['groups'].items():
            self.groups[group_key] = {}
            for socket_key, socket_value in json[
                    'groups'][group_key].items():
                hwpc_sock = HWPCReportSocket(int(socket_key))
                hwpc_sock.deserialize(socket_value)
                self.groups[group_key][socket_key] = hwpc_sock


#############################
# REPORT CREATION FUNCTIONS #
#############################

def create_core_report(core_id, event_id, event_value, events=None):
    core = HWPCReportCore(core_id)
    if events is not None:
        core.events = events
        return core
    core.events = {event_id: event_value}
    return core


def create_socket_report(socket_id, core_list):
    socket = HWPCReportSocket(socket_id)
    for core in core_list:
        socket.cores[core.core_id] = core
    return socket


def create_group_report(group_id, socket_list):
    group = {}
    for socket in socket_list:
        group[socket.socket_id] = socket
    return (group_id, group)


def create_report_root(group_list):
    sensor = HWPCReport(timestamp='time0', sensor='toto', target='system')
    for (group_id, group) in group_list:
        sensor.groups[group_id] = group
    return sensor
