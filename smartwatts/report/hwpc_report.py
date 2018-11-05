"""
Module hwpc_sensor which define the HWPCReport class
"""

from copy import deepcopy
from enum import IntEnum
from smartwatts.report.report import Report
from smartwatts.message import HWPCReportMessage
import smartwatts.utils as utils


class DepthLevel(IntEnum):
    ROOT = 3
    SOCKET = 2
    CORE = 1


def extract(report, depth):
    def extract_aux(report, current_depth):
        if current_depth == depth:
            return [((report.hw_id,), report)]

        extracted_reports = []
        for packed_report in report.get_child_reports():

            extracted_reports += extract_aux(packed_report,
                                             current_depth - 1)

        final_reports = []
        if current_depth == DepthLevel.ROOT:
            # merge group
            final_reports = {}
            for (report_id, socket_report) in extracted_reports:
                if report_id not in final_reports:
                    final_reports[report_id] = report.cut_child()
                key = socket_report.hw_id
                final_reports[report_id].set_child_report(key,
                                                          socket_report)
            return list(final_reports.items())

        for (report_id, extracted_report) in extracted_reports:
            final_report = report.cut_child()
            final_report.set_child_report(extracted_report.hw_id,
                                          extracted_report)
            final_reports.append(
                ((final_report.hw_id,) + report_id, final_report)
            )
        return final_reports
    return extract_aux(report, DepthLevel.ROOT)


class HWPCReportCore(Report):
    """
    HWPCReportCore class
    Encapuslation for core report
    """

    def __init__(self, core_id=None):
        Report.__init__(self, core_id)
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
        Report.__init__(self, socket_id)
        self.socket_id = socket_id
        self.cores = {}
        self.group_id = None

    def get_child_reports(self):
        return [report for report in self.cores.values()]

    def set_child_report(self, key, val):
        self.cores[key] = val

    def cut_child(self):
        socket_report = HWPCReportSocket(self.socket_id)
        # socket_report.hw_id = self.hw_id
        socket_report.group_id = self.group_id
        return socket_report

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
        Report.__init__(self, sensor)
        self.timestamp = timestamp
        self.sensor = sensor
        self.target = target
        self.groups = {}

    def get_child_reports(self):

        reports = []
        for (group_id, sockets) in self.groups.items():
            for (_, socket_report) in sockets.items():
                socket_report.group_id = group_id
                reports.append(socket_report)
        return reports

    def set_child_report(self, key, val):
        socket_id = key
        socket_report = val

        if socket_report.group_id not in self.groups:
            self.groups[socket_report.group_id] = {}
        self.groups[socket_report.group_id][socket_id] = socket_report

    def cut_child(self):
        return HWPCReport(self.timestamp, self.sensor, self.target)

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
