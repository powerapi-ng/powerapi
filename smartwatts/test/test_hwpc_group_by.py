import pytest
from smartwatts.report import HWPCReportCore, HWPCReportSocket, HWPCReport
from smartwatts.group_by import HWPCGroupBy, HWPCDepthLevel


"""
When testing on HWPC report, we test to extrat reports from this fake HWPC
report :

                    sensor

         groupA                 groupB
         id:1                   id:2

     SA         SB          SC          SD
     id:1      id:2        id:1        id:2

 CPUA  CPUB  CPUC  CPUD  CPUE  CPUF  CPUG  CPUH
 id:1  id:2  id:1  id:2  id:1  id:2  id:1  id:2
 e0:0  e0:1  e0:2  e0:3  e1:0  e1:1  e1:2  e1:3
"""



############################
# REPORT CREATION FUNCTION #
############################

def create_core_report(core_id, event_id, event_value):
    core = HWPCReportCore(core_id)
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


def core_report_assert(r1, r2):
    assert (r1.core_id == r2.core_id) and (r1.events == r2.events)


def socket_report_assert(r1, r2):
    assert r1.socket_id == r2.socket_id

    for (core_id, core_report) in r1.cores.items():
        assert core_id in r2.cores
        core_report_assert(core_report, r2.cores[core_id])

    for core_id in r2.cores:
        assert core_id in r1.cores


def report_assert(r_1, r_2):
    """assert that two report are HWPC_equals"""
    assert (r_1.timestamp == r_2.timestamp and r_1.sensor == r_2.sensor and
            r_1.target == r_2.target)

    for (group_id, _) in r_1.groups.items():
        assert group_id in r_2.groups
        for (socket_id, socket_report) in (r_1.groups[group_id]).items():
            assert socket_id in r_2.groups[group_id]
            socket_report_assert(socket_report,
                                 r_2.groups[group_id][socket_id])

        for socket_id in r_2.groups[group_id]:
            assert socket_id in r_1.groups[group_id]

    for group_id in r_2.groups:
        assert group_id in r_2.groups


cpuA = create_core_report('1', 'e0', '0')
cpuB = create_core_report('2', 'e0', '1')
cpuC = create_core_report('1', 'e0', '2')
cpuD = create_core_report('2', 'e0', '3')
cpuE = create_core_report('1', 'e1', '0')
cpuF = create_core_report('2', 'e1', '1')
cpuG = create_core_report('1', 'e1', '2')
cpuH = create_core_report('2', 'e1', '3')

socketA = create_socket_report('1', [cpuA, cpuB])
socketB = create_socket_report('2', [cpuC, cpuD])
socketC = create_socket_report('1', [cpuE, cpuF])
socketD = create_socket_report('2', [cpuG, cpuH])

groupA = create_group_report('1', [socketA, socketB])
groupB = create_group_report('2', [socketC, socketD])

report = create_report_root([groupA, groupB])


class TestHWPCGroupBy():

    def test_init_fields_name_test(self):
        """
        test if the field's names of the group_by identifier tuple are correctly
        initialized
        """
        assert HWPCGroupBy(HWPCDepthLevel.ROOT).fields == ['sensor']
        assert HWPCGroupBy(HWPCDepthLevel.SOCKET).fields == ['sensor', 'socket']
        assert HWPCGroupBy(HWPCDepthLevel.CORE).fields == ['sensor', 'socket',
                                                           'core']

    def validate_reports(self, reports, validation_list):
        """function used when testing the extract method

        extract method return a list of tuple (report_id, report), validate
        report test if this list of tuple is equal to validation_list that
        contains the tuple that extract method must return
        """
        reports.sort(key=lambda x: x[0])

        validation_list.sort(key=lambda x: x[0])
        for ((key, report), (validation_key, validation_report)) in zip(
                reports, validation_list):
            assert key == validation_key
            report_assert(report, validation_report)

    def test_extract_root(self):
        """ test to extract the root report from the fake HWPCReport

        extract method must return the fake report with its id
        """
        extract = HWPCGroupBy(HWPCDepthLevel.ROOT).extract
        extracted_reports = extract(report)

        assert len(extracted_reports) == 1
        [(key, extracted_report)] = extracted_reports
        assert key == (report.sensor,)
        report_assert(report, extracted_report)

    def test_extract_socket(self):
        """
        test to extract the socket report from the fake HWPCReport

        extract method must return two HWPCReports with their id
        """
        extract = HWPCGroupBy(HWPCDepthLevel.SOCKET).extract
        extracted_reports = extract(report)

        assert len(extracted_reports) == 2

        # Rapport 1
        report1 = create_report_root(
            [create_group_report('1', [socketA]),
             create_group_report('2', [socketC])
             ])

        report2 = create_report_root(
            [create_group_report('1', [socketB]),
             create_group_report('2', [socketD])
             ]
        )

        validation_report_list = [
            report1,
            report2
        ]

        validation_key_list = [
            (report.sensor, socketA.socket_id),
            (report.sensor, socketB.socket_id)
        ]
        validation_list = list(zip(validation_key_list, validation_report_list))
        self.validate_reports(extracted_reports, validation_list)

    def test_extract_core(self):
        """
        test to extract the core report from the fake HWPCReport

        extract method must return four HWPCReports with their id
        """
        extract = HWPCGroupBy(HWPCDepthLevel.CORE).extract
        extracted_reports = extract(report)

        assert len(extracted_reports) == 4

        # Rapport 1
        report1 = create_report_root(
            [create_group_report('1', [
                create_socket_report('1', [cpuA])
            ]),
             create_group_report('2', [
                 create_socket_report('1', [cpuE])
             ])
            ])

        report2 = create_report_root(
            [create_group_report('1', [
                create_socket_report('1', [cpuB])
            ]),
             create_group_report('2', [
                 create_socket_report('1', [cpuF])
             ])
            ])
        report3 = create_report_root(
            [create_group_report('1', [
                create_socket_report('2', [cpuC])
            ]),
             create_group_report('2', [
                 create_socket_report('2', [cpuG])
             ])
            ])

        report4 = create_report_root(
            [create_group_report('1', [
                create_socket_report('2', [cpuD])
            ]),
             create_group_report('2', [
                 create_socket_report('2', [cpuH])
             ])
            ])

        validation_report_list = [
            report1,
            report2,
            report3,
            report4
        ]

        validation_key_list = [
            (report.sensor, socketA.socket_id, cpuA.core_id),
            (report.sensor, socketA.socket_id, cpuB.core_id),
            (report.sensor, socketB.socket_id, cpuC.core_id),
            (report.sensor, socketB.socket_id, cpuD.core_id)
        ]

        validation_list = list(zip(validation_key_list, validation_report_list))
        self.validate_reports(extracted_reports, validation_list)
