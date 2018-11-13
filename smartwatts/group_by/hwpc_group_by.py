"""HWPC group by rules utilities

"""

from enum import IntEnum
from smartwatts.group_by import AbstractGroupBy
from smartwatts.report import HWPCReport, HWPCReportSocket


class HWPCDepthLevel(IntEnum):
    """Enumeration that specify which report level use to group by the reports
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
        self.fields = ['sensor', 'socket', 'core'][:(4 - depth)]

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
        reports = _merge_groups(report, atomic_reports)

        # append values from shared groups
        final_reports = []
        for base_report_id, base_report in reports:
            for (group_id, group) in shared_groups:
                base_report.groups[group_id] = group
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


def _extract_shared_groups(report):
    """separate shared groups (like RAPL, PCU, ...) from non shared groups

    Return([(group_id, {str:HWPCReport})],
           [(group_id, {str:HWPCReport})]): return the list of shared groups and
                                            the list of non shared groups
    """
    shared_groups = []
    normal_groups = []
    for group_id, group in report.groups.items():
        if len(group) > 1:
            # if the group have more than one socket report its a non shared
            # group
            normal_groups.append((group_id, group))
        elif len(list(group.values())[0].cores) > 1:
            # if the group have more than one core report its a non shared group
            normal_groups.append((group_id, group))
        else:
            # otherwise its a shared group
            shared_groups.append((group_id, group))
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
