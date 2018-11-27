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
        print('(key, validation key)')
        for ((key, report), (validation_key, validation_report)) in zip(
                reports, validation_list):
            print(report)
            print('---------')
            print(validation_report)
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

    ############################
    # RAPL & HWPC EVENT REPORT #
    ############################

    def test_extract_rapl_with_hwpc_report_for_one_socket_one_core(self):
        """ test rapl report extraction for two socket

        The report contains a RAPL group, and an event group with one socket
        and one core

        The extracted report must be equal to the initial report regardless of
        the group_by rule
        """
        report = create_report_root(
            [create_group_report('rapl', [
                create_socket_report('1', [create_core_report('1', 'e0', '0')]),
            ]), create_group_report('hwpc', [
                create_socket_report('1', [create_core_report('1', 'e0', '0')])
            ])])

        # ROOT test
        validation_list = [((report.sensor,), report)]
        extracted_reports = HWPCGroupBy(HWPCDepthLevel.ROOT).extract(report)
        self.validate_reports(extracted_reports, validation_list)

        # SOCKET and CORE test
        validation_list = [((report.sensor, '1'), report)]
        extracted_reports = HWPCGroupBy(HWPCDepthLevel.SOCKET).extract(report)
        self.validate_reports(extracted_reports, validation_list)

        validation_list = [((report.sensor, '1', '1'), report)]
        extracted_reports = HWPCGroupBy(HWPCDepthLevel.CORE).extract(report)
        self.validate_reports(extracted_reports, validation_list)

    def test_extract_rapl_hwpc_report_for_two_socket_one_core(self):
        """ test rapl report extraction for two socket

        The report contains a RAPL group, and an event group with two socket
        and one core

        The extracted report must be equal to the initial report when grouping
        by sensor.
        When grouping by core or socket, the extract function must return one
        report per socket with hwpc and RAPL events

        """
        report = create_report_root(
            [create_group_report('rapl', [
                create_socket_report('1', [create_core_report('1', 'e0', '0')]),
                create_socket_report('2', [create_core_report('2', 'e0', '0')])
            ]), create_group_report('hwpc', [
                create_socket_report('1', [create_core_report('1', 'e0', '0')]),
                create_socket_report('2', [create_core_report('2', 'e0', '0')])
            ])])

        # ROOT test
        validation_list = [((report.sensor,), report)]
        extracted_reports = HWPCGroupBy(HWPCDepthLevel.ROOT).extract(report)
        self.validate_reports(extracted_reports, validation_list)

        # SOCKET and CORE test
        validation_report1 = create_report_root(
            [create_group_report('rapl', [
                create_socket_report('1', [create_core_report('1', 'e0', '0')])
            ]), create_group_report('hwpc', [
                create_socket_report('1', [create_core_report('1', 'e0', '0')])
            ])])

        validation_report2 = create_report_root(
            [create_group_report('rapl', [
                create_socket_report('2', [create_core_report('2', 'e0', '0')])
            ]), create_group_report('hwpc', [
                create_socket_report('2', [create_core_report('2', 'e0', '0')])
            ])])

        validation_list = [((report.sensor, '1'), validation_report1),
                           ((report.sensor, '2'), validation_report2)]
        extracted_reports = HWPCGroupBy(HWPCDepthLevel.SOCKET).extract(report)
        self.validate_reports(extracted_reports, validation_list)

        validation_list = [((report.sensor, '1', '1'), validation_report1),
                           ((report.sensor, '2', '2'), validation_report2)]
        extracted_reports = HWPCGroupBy(HWPCDepthLevel.CORE).extract(report)
        self.validate_reports(extracted_reports, validation_list)

    def test_extract_rapl_hwpc_report_for_one_socket_two_core(self):
        """test rapl report extraction for two socket

        The report contains a RAPL group, and an event group with one socket
        and two core

        The extracted report must be equal to the initial report when grouping
        by sensor and socket.
        When grouping by core, the extract function must return one report per
        core with hwpc and RAPL events

        """
        report = create_report_root(
            [create_group_report('rapl', [
                create_socket_report('1', [create_core_report('1', 'e0', '0')]),
            ]), create_group_report('hwpc', [
                create_socket_report('1', [create_core_report('1', 'e0', '0'),
                                           create_core_report('2', 'e0', '0')]),
            ])])

        # ROOT and SOCKET test
        validation_list = [((report.sensor,), report)]
        extracted_reports = HWPCGroupBy(HWPCDepthLevel.ROOT).extract(report)
        self.validate_reports(extracted_reports, validation_list)

        validation_list = [((report.sensor, '1'), report)]
        extracted_reports = HWPCGroupBy(HWPCDepthLevel.SOCKET).extract(report)
        self.validate_reports(extracted_reports, validation_list)

        # CORE test
        validation_report1 = create_report_root(
            [create_group_report('rapl', [
                create_socket_report('1', [create_core_report('1', 'e0', '0')])
            ]), create_group_report('hwpc', [
                create_socket_report('1', [create_core_report('1', 'e0', '0')])
            ])])

        validation_report2 = create_report_root(
            [create_group_report('rapl', [
                create_socket_report('1', [create_core_report('1', 'e0', '0')])
            ]), create_group_report('hwpc', [
                create_socket_report('1', [create_core_report('2', 'e0', '0')])
            ])])

        validation_list = [((report.sensor, '1', '1'), validation_report1),
                           ((report.sensor, '1', '2'), validation_report2)]
        extracted_reports = HWPCGroupBy(HWPCDepthLevel.CORE).extract(report)
        self.validate_reports(extracted_reports, validation_list)

    def test_extract_rapl_hwpc_report_for_two_socket_two_core(self):
        """test rapl report extraction for two socket

        The report contains a RAPL group, and an event group with two socket
        and two core

        The extracted report must be equal to the initial report when grouping
        by sensor.

        When grouping by socket, the extract function must return one report per
        socket with hwpc and RAPL event

        When grouping by core, the extract function must return one report per
        core with hwpc events, each reports also contains its socket rapl events

        """
        report = create_report_root(
            [create_group_report('rapl', [
                create_socket_report('1', [create_core_report('1', 'e0', '0')]),
                create_socket_report('2', [create_core_report('3', 'e0', '0')])
            ]), create_group_report('hwpc', [
                create_socket_report('1', [create_core_report('1', 'e0', '0'),
                                           create_core_report('2', 'e0', '0')]),
                create_socket_report('2', [create_core_report('3', 'e0', '0'),
                                           create_core_report('4', 'e0', '0')])
            ])])

        # ROOT test
        validation_list = [((report.sensor,), report)]
        extracted_reports = HWPCGroupBy(HWPCDepthLevel.ROOT).extract(report)
        self.validate_reports(extracted_reports, validation_list)

        # SOCKET test
        validation_report1 = create_report_root(
            [create_group_report('rapl', [
                create_socket_report('1', [create_core_report('1', 'e0', '0')])
            ]), create_group_report('hwpc', [
                create_socket_report('1', [create_core_report('1', 'e0', '0'),
                                           create_core_report('2', 'e0', '0')])
            ])])
        validation_report2 = create_report_root(
            [create_group_report('rapl', [
                create_socket_report('2', [create_core_report('3', 'e0', '0')])
            ]), create_group_report('hwpc', [
                create_socket_report('2', [create_core_report('3', 'e0', '0'),
                                           create_core_report('4', 'e0', '0')])
            ])])

        validation_list = [((report.sensor, '1'), validation_report1),
                           ((report.sensor, '2'), validation_report2)]
        extracted_reports = HWPCGroupBy(HWPCDepthLevel.SOCKET).extract(report)
        self.validate_reports(extracted_reports, validation_list)

        # CORE test
        validation_report1 = create_report_root(
            [create_group_report('rapl', [
                create_socket_report('1', [create_core_report('1', 'e0', '0')])
            ]), create_group_report('hwpc', [
                create_socket_report('1', [create_core_report('1', 'e0', '0')])
            ])])

        validation_report2 = create_report_root(
            [create_group_report('rapl', [
                create_socket_report('1', [create_core_report('1', 'e0', '0')])
            ]), create_group_report('hwpc', [
                create_socket_report('1', [create_core_report('2', 'e0', '0')])
            ])])

        validation_report3 = create_report_root(
            [create_group_report('rapl', [
                create_socket_report('2', [create_core_report('3', 'e0', '0')])
            ]), create_group_report('hwpc', [
                create_socket_report('2', [create_core_report('3', 'e0', '0')])
            ])])

        validation_report4 = create_report_root(
            [create_group_report('rapl', [
                create_socket_report('2', [create_core_report('3', 'e0', '0')])
            ]), create_group_report('hwpc', [
                create_socket_report('2', [create_core_report('4', 'e0', '0')])
            ])])

        validation_list = [((report.sensor, '1', '1'), validation_report1),
                           ((report.sensor, '1', '2'), validation_report2),
                           ((report.sensor, '2', '3'), validation_report3),
                           ((report.sensor, '2', '4'), validation_report4)]
        extracted_reports = HWPCGroupBy(HWPCDepthLevel.CORE).extract(report)
        self.validate_reports(extracted_reports, validation_list)
