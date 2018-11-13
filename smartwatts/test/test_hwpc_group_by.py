from copy import deepcopy

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


CPUA = create_core_report('1', 'e0', '0')
CPUB = create_core_report('2', 'e0', '1')
CPUC = create_core_report('1', 'e0', '2')
CPUD = create_core_report('2', 'e0', '3')
CPUE = create_core_report('1', 'e1', '0')
CPUF = create_core_report('2', 'e1', '1')
CPUG = create_core_report('1', 'e1', '2')
CPUH = create_core_report('2', 'e1', '3')

SOCKETA = create_socket_report('1', [CPUA, CPUB])
SOCKETB = create_socket_report('2', [CPUC, CPUD])
SOCKETC = create_socket_report('1', [CPUE, CPUF])
SOCKETD = create_socket_report('2', [CPUG, CPUH])

GROUPA = create_group_report('1', [SOCKETA, SOCKETB])
GROUPB = create_group_report('2', [SOCKETC, SOCKETD])

REPORT = create_report_root([GROUPA, GROUPB])


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
        assert len(reports) == len(validation_list)
        reports.sort(key=lambda x: x[0])

        validation_list.sort(key=lambda x: x[0])
        for ((key, report), (validation_key, validation_report)) in zip(
                reports, validation_list):
            print((key, validation_key))
            assert key == validation_key
            report_assert(report, validation_report)


    def test_extract_report_with_no_groups(self):
        """Test to extract report from a report with no groups

        extract function must return an emtpy list
        """
        extract = HWPCGroupBy(HWPCDepthLevel.ROOT).extract
        report = create_report_root([])

        assert extract(report) == []

    def test_extract_report_with_no_sockets(self):
        """Test to extract report from a report with no sockets

        extract function must return an emtpy list
        """
        extract = HWPCGroupBy(HWPCDepthLevel.SOCKET).extract
        report = create_report_root(
            [create_group_report('1', [])])

        assert extract(report) == []

    def test_extract_report_with_no_core(self):
        """Test to extract report from a report with no cores

        extract function must return an emtpy list
        """
        extract = HWPCGroupBy(HWPCDepthLevel.CORE).extract
        report = create_report_root(
            [create_group_report('1', [
                create_socket_report('1', [])
            ])])
        assert extract(report) == []

    def test_extract_report_with_no_events(self):
        """Test to extract report from a report with no events

        extract function must return an emtpy list
        """
        extract = HWPCGroupBy(HWPCDepthLevel.CORE).extract
        report = create_report_root(
            [create_group_report('1', [
                create_socket_report('1', [HWPCReportCore('1')])
            ])])
        assert extract(report) == []

    def test_extract_root(self):
        """ test to extract the root report from the fake HWPCReport

        extract method must return the fake report with its id
        """
        extract = HWPCGroupBy(HWPCDepthLevel.ROOT).extract
        extracted_reports = extract(REPORT)

        assert len(extracted_reports) == 1
        [(key, extracted_report)] = extracted_reports
        assert key == (REPORT.sensor,)
        report_assert(REPORT, extracted_report)

    def test_extract_socket(self):
        """
        test to extract the socket report from the fake HWPCReport

        extract method must return two HWPCReports with their id
        """
        extract = HWPCGroupBy(HWPCDepthLevel.SOCKET).extract
        extracted_reports = extract(REPORT)

        assert len(extracted_reports) == 2

        # Rapport 1
        report1 = create_report_root(
            [create_group_report('1', [SOCKETA]),
             create_group_report('2', [SOCKETC])
             ])

        report2 = create_report_root(
            [create_group_report('1', [SOCKETB]),
             create_group_report('2', [SOCKETD])
             ]
        )

        validation_report_list = [
            report1,
            report2
        ]

        validation_key_list = [
            (REPORT.sensor, SOCKETA.socket_id),
            (REPORT.sensor, SOCKETB.socket_id)
        ]
        validation_list = list(zip(validation_key_list, validation_report_list))
        self.validate_reports(extracted_reports, validation_list)

    def test_extract_core(self):
        """
        test to extract the core report from the fake HWPCReport

        extract method must return four HWPCReports with their id
        """
        extract = HWPCGroupBy(HWPCDepthLevel.CORE).extract
        extracted_reports = extract(REPORT)

        assert len(extracted_reports) == 4

        # Rapport 1
        report1 = create_report_root(
            [create_group_report('1', [
                create_socket_report('1', [CPUA])
            ]),
             create_group_report('2', [
                 create_socket_report('1', [CPUE])
             ])
            ])

        report2 = create_report_root(
            [create_group_report('1', [
                create_socket_report('1', [CPUB])
            ]),
             create_group_report('2', [
                 create_socket_report('1', [CPUF])
             ])
            ])
        report3 = create_report_root(
            [create_group_report('1', [
                create_socket_report('2', [CPUC])
            ]),
             create_group_report('2', [
                 create_socket_report('2', [CPUG])
             ])
            ])

        report4 = create_report_root(
            [create_group_report('1', [
                create_socket_report('2', [CPUD])
            ]),
             create_group_report('2', [
                 create_socket_report('2', [CPUH])
             ])
            ])

        validation_report_list = [
            report1,
            report2,
            report3,
            report4
        ]

        validation_key_list = [
            (REPORT.sensor, SOCKETA.socket_id, CPUA.core_id),
            (REPORT.sensor, SOCKETA.socket_id, CPUB.core_id),
            (REPORT.sensor, SOCKETB.socket_id, CPUC.core_id),
            (REPORT.sensor, SOCKETB.socket_id, CPUD.core_id)
        ]

        validation_list = list(zip(validation_key_list, validation_report_list))
        self.validate_reports(extracted_reports, validation_list)

    def test_extract_rapl_report(self):
        """test rapl report extraction"""

        report = create_report_root(
            [create_group_report('rapl', [
                create_socket_report('1', [create_core_report('1', 'e0', '0')])
            ])])

        validation_list = [((report.sensor,), report)]

        cp_report = deepcopy(report)
        extracted_reports = HWPCGroupBy(HWPCDepthLevel.ROOT).extract(cp_report)
        self.validate_reports(extracted_reports, validation_list)

        c_report = deepcopy(report)
        extracted_reports = HWPCGroupBy(HWPCDepthLevel.SOCKET).extract(c_report)
        self.validate_reports(extracted_reports, validation_list)

        cp_report = deepcopy(report)
        extracted_reports = HWPCGroupBy(HWPCDepthLevel.CORE).extract(cp_report)
        self.validate_reports(extracted_reports, validation_list)

    # def test_extract_rapl_one_core(self):
    #     """
    #     test extract reports from a reports which contains rapl group and hwpc
    #     group with one core
    #     """

    #     report = create_report_root(
    #         [create_group_report('rapl', [
    #             create_socket_report('1', [create_core_report('1', 'e0', '0')])
    #         ]),
    #          create_group_report('1', [
    #              create_socket_report('1', [CPUA])
    #          ])
    #     ])

    #     # ROOT test
    #     cp_report = deepcopy(report)
    #     validation_list = [((report.sensor,), cp_report)]
    #     extracted_reports = HWPCGroupBy(HWPCDepthLevel.ROOT).extract(cp_report)
    #     self.validate_reports(extracted_reports, validation_list)

    #     # SOCKET test
    #     # validation_list = [((report.sensor,), rapl_validation_report),
    #     #                    ((report.sensor, '1'), hwpc_validation_report)]
    #     c_report = deepcopy(report)
    #     validation_list = [((report.sensor, '1'), c_report)]
    #     extracted_reports = HWPCGroupBy(HWPCDepthLevel.SOCKET).extract(c_report)
    #     self.validate_reports(extracted_reports, validation_list)

    #     # # CORE test
    #     cp_report = deepcopy(report)
    #     validation_list = [((report.sensor, '1', CPUA.core_id), cp_report)]
    #     extracted_reports = HWPCGroupBy(HWPCDepthLevel.CORE).extract(cp_report)
    #     self.validate_reports(extracted_reports, validation_list)


    def test_extract_rapl_two_core(self):
        """
        test extract reports from a reports which contains rapl group and hwpc
        group with two core
        """

        report = create_report_root(
            [create_group_report('rapl', [
                create_socket_report('1', [create_core_report('1', 'e0', '0')])
            ]),
             create_group_report('1', [
                 create_socket_report('1', [CPUA, CPUB])
             ])])

        # ROOT test
        cp_report = deepcopy(report)
        validation_list = [((report.sensor,), cp_report)]
        extracted_reports = HWPCGroupBy(HWPCDepthLevel.ROOT).extract(cp_report)
        self.validate_reports(extracted_reports, validation_list)

        # SOCKET test
        # validation_list = [((report.sensor,), rapl_validation_report),
        #                    ((report.sensor, '1'), hwpc_validation_report)]
        c_report = deepcopy(report)
        validation_list = [((report.sensor, '1'), c_report)]
        extracted_reports = HWPCGroupBy(HWPCDepthLevel.SOCKET).extract(c_report)
        self.validate_reports(extracted_reports, validation_list)

        # # CORE test
        cp_report = deepcopy(report)
        report_a = create_report_root(
            [create_group_report('rapl', [
                create_socket_report('1', [create_core_report('1', 'e0', '0')])
            ]),
             create_group_report('1', [
                 create_socket_report('1', [CPUA])
             ])])

        report_b = create_report_root(
            [create_group_report('rapl', [
                create_socket_report('1', [create_core_report('1', 'e0', '0')])
            ]),
             create_group_report('1', [
                 create_socket_report('1', [CPUB])
             ])])

        validation_list = [((report.sensor, '1', CPUA.core_id), report_a),
                           ((report.sensor, '1', CPUB.core_id), report_b)]
        extracted_reports = HWPCGroupBy(HWPCDepthLevel.CORE).extract(cp_report)
        self.validate_reports(extracted_reports, validation_list)
