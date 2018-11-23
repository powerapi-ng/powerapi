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
HWPC group by rules utilities
"""

from enum import IntEnum

import smartwatts.utils as utils
from smartwatts.group_by import AbstractGroupBy
from smartwatts.report import HWPCReport, HWPCReportSocket


class HWPCDepthLevel(IntEnum):
    """
    Enumeration that specify which report level use to group by the reports
    """

    ROOT = 3
    SOCKET = 2
    CORE = 1


class HWPCGroupBy(AbstractGroupBy):
    """
    Group by rule for HWPC report
    """
    def __init__(self, depth, primary=False):
        """
        Parameters:
            depth:(HWPCDepthLevel)
        """
        AbstractGroupBy.__init__(self, primary)
        self.depth = depth
        self.fields = ['sensor', 'socket', 'core'][:((HWPCDepthLevel.ROOT+1)
                                                     - depth)]

    def extract(self, report):
        """ See AbstractGroupBy.extract """
        if not _check_report_integrity(report):
            return []

        if self.depth == HWPCDepthLevel.ROOT:
            return [((report.sensor,), report)]

        sensor_id = report.sensor
        shared_groups, normal_groups = _extract_shared_groups(report)

        # if there are only shared groups merge them into one report and report
        # it
        if normal_groups == []:
            atomic_reports = [((sensor_id,), group_id, new_report)
                              for (group_id, reports) in shared_groups
                              for new_report in reports.values()]
            return _merge_groups(report, atomic_reports)

        # otherwise split reports from normal group into atomic reports, merge
        # atomic reports from the same groups and for each merged report, append
        # values from shared groups
        atomic_reports = _split_reports(sensor_id, normal_groups, self.depth)
        atomic_shared_reports = _split_reports(sensor_id, shared_groups,
                                               self.depth)
        reports = _merge_groups(report, atomic_reports)

        # append values from shared groups
        final_reports = []
        tree = utils.Tree()
        for base_report_id, base_report in reports:
            tree.add(list(base_report_id), (base_report_id, base_report))

        for shared_report_id, group_id, socket_report in atomic_shared_reports:
            for base_report_id, base_report in tree.get(shared_report_id):
                if group_id not in base_report.groups:
                    base_report.groups[group_id] = {}

                socket_id = socket_report.socket_id
                base_report.groups[group_id][socket_id] = socket_report

        for (base_report_id, base_report) in tree.get([]):
            final_reports.append((base_report_id, base_report))
        return final_reports


def _check_report_integrity(report):
    """ Check is report is valid

    Return(boolean):
    """
    if report.groups == {}:
        # check if the report contains at least one group
        return False

    for group in report.groups.values():
        if group == {}:
            # check if report's group are not emtpy
            return False
        for socket in group.values():
            if socket.cores == {}:
                # check if report's socket are not emtpy
                return False
            for core in socket.cores.values():
                if core.events == {}:
                    # check if report's core are not emtpy
                    return False
    return True


def _number_of_core_per_socket(group):
    """compute the number of core per socket in this group

    Parameter:
        group({str:HWPCReportSocket}): group must be a valide group (composed
                                       by socket, core, event)
    Return:
        (int): the number of core per socket in this group

    """
    first_socket_report = list(group.values())[0]
    return len(first_socket_report.cores.values())


def _extract_shared_groups(report):
    """separate shared groups (like RAPL, PCU, ...) from non shared groups

    Return([(group_id, {str:HWPCReportSocket})],
           [(group_id, {str:HWPCReportSocket})]): return the list of shared
                                                  groups and the list of non
                                                  shared groups

    """
    # tag each group with its number of core per socket and record the maximum
    # number of core per socket
    taged_groups = []
    maximum_number_of_core = -1
    for group_id, group in report.groups.items():
        number_of_core = _number_of_core_per_socket(group)
        if number_of_core > maximum_number_of_core:
            maximum_number_of_core = number_of_core

        taged_groups.append((number_of_core, group_id, group))

    # each groups that doesn't have the maximum number of core per socket is a
    # shared group
    shared_groups = []
    normal_groups = []
    for number_of_core, group_id, group in taged_groups:
        if number_of_core != maximum_number_of_core:
            shared_groups.append((group_id, group))
        else:
            normal_groups.append((group_id, group))

    return shared_groups, normal_groups


def _split_reports(sensor_id, groups, depth):
    """ split each report into atomic report depending of the needed depth

    Parameters:
        sensor_id(str): id of the report's sensor the groups were extracted from
        groups((group_id, {HWPCReportSocket})): groups that contains report
        depth(HWPCDepthLevel):

    Return([(tuple, str, HWPCReportSocket)]): list of
                                              (id_report, group_id, report)
    """
    # SOCKET level
    socket_reports = []
    for group_id, reports in groups:
        for socket_id, socket_report in reports.items():
            socket_reports.append(((sensor_id, socket_id), group_id,
                                   socket_report))
    if depth == HWPCDepthLevel.SOCKET:
        return socket_reports

    # CORE level
    core_reports = []
    for ((_, socket_id), group_id, report) in socket_reports:
        for core_id, core_report in report.cores.items():
            new_report = HWPCReportSocket(socket_id)
            new_report.cores = {core_id: core_report}
            core_reports.append(((sensor_id, socket_id, core_id), group_id,
                                 new_report))
    return core_reports


def _merge_groups(root_report, atomic_reports):
    """ merge groups of a same report in one report

    Parameters:
        atomic_reports([(tuple, str, HWPCReportSocket)]):
            list of (id_report, group_id, report)

    Return([(tuple, HWPCReport)]):
    """
    timestamp = root_report.timestamp
    sensor = root_report.sensor
    target = root_report.target
    reports = {}
    for report_id, group_id, socket_report in atomic_reports:
        if report_id not in reports:
            reports[report_id] = HWPCReport(timestamp, sensor, target)
        reports[report_id].groups[group_id] = {socket_report.socket_id:
                                               socket_report}
    return list(reports.items())
