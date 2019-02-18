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

""" Test RAPL Formula utilities : Actor and Handler"""

import math
import mock
import pytest

from powerapi.formula import RAPLFormulaHWPCReportHandler
from powerapi.message import UnknowMessageTypeException
from powerapi.report import create_core_report, create_socket_report
from powerapi.report import create_group_report, create_report_root
from powerapi.report import PowerReport
from powerapi.actor import State

#####################################


def get_fake_pusher():
    """
    Return a fake pusher

    """
    fake_pusher = mock.Mock()
    fake_pusher.send = mock.Mock()
    return fake_pusher

#####################################
# Test RAPLFormulaHWPCReportHandler #
#####################################


def test_handle_no_hwpc_report():
    """
    handle a message that is not a HWPCReport, this must raise an
    UnknowMessageTypeException
    """
    with pytest.raises(UnknowMessageTypeException):
        RAPLFormulaHWPCReportHandler(
            get_fake_pusher()).handle("toto",
                                      State(None, mock.Mock(), mock.Mock()))


def test_handle_hwpc_report_with_one_rapl_event():
    """
    handle a HWPC report with a simple RAPL event

    The HWPC report contain only one RAPL event and no other groups

    The handle method must return a PowerReport containing only the RAPL event
    """
    raw_power = 10
    socket_id = '1'
    rapl_event_id = 'RAPL_1'

    hwpc_report = create_report_root(
        [create_group_report('rapl', [
            create_socket_report(socket_id, [create_core_report('1',
                                                                rapl_event_id,
                                                                raw_power)])
        ])])

    validation_report = PowerReport(hwpc_report.timestamp, hwpc_report.sensor,
                                    hwpc_report.target,
                                    math.ldexp(raw_power, -32),
                                    {'socket_id': socket_id,
                                     'rapl_event_id': rapl_event_id})

    result = RAPLFormulaHWPCReportHandler(get_fake_pusher())._process_report(
        hwpc_report)
    assert [validation_report] == result


def test_handle_hwpc_report_with_one_rapl_event_and_other_groups():
    """
    handle a HWPC report with a simple RAPL event and events from other
    groups

    The HWPC report contain one RAPL event and events from a group 'sys'
    with two cores

    The handle method must return a PowerReport containing only the RAPL event
    """
    raw_power = 10
    socket_id = '1'
    rapl_event_id = 'RAPL_1'

    hwpc_report = create_report_root(
        [create_group_report('rapl', [
            create_socket_report(socket_id, [create_core_report('1',
                                                                rapl_event_id,
                                                                raw_power)])]),
         create_group_report('sys', [
             create_socket_report(socket_id,
                                  [create_core_report('1', 'e0', 0),
                                   create_core_report('2', 'e0', 0)])
         ])])

    validation_report = PowerReport(hwpc_report.timestamp, hwpc_report.sensor,
                                    hwpc_report.target,
                                    math.ldexp(raw_power, -32),
                                    {'socket_id': socket_id,
                                     'rapl_event_id': rapl_event_id})

    result = RAPLFormulaHWPCReportHandler(get_fake_pusher())._process_report(
        hwpc_report)

    assert [validation_report] == result


def test_handle_hwpc_report_with_two_rapl_event():
    """
    handle a HWPC report with two RAPL events

    The HWPC report contain only two RAPL events and no other groups

    The handle method must return two PowerReport containing each RAPL event
    """
    socket_id = '1'
    raw_power_1 = 10
    rapl_event_id_1 = 'RAPL_1'
    raw_power_2 = 20
    rapl_event_id_2 = 'RAPL_2'

    events = {rapl_event_id_1: raw_power_1, rapl_event_id_2: raw_power_2}

    hwpc_report = create_report_root(
        [create_group_report('rapl', [
            create_socket_report(socket_id,
                                 [create_core_report('1',
                                  None, None,
                                  events=events)])
        ])])

    validation_report_1 = PowerReport(hwpc_report.timestamp,
                                      hwpc_report.sensor,
                                      hwpc_report.target,
                                      math.ldexp(raw_power_1, -32),
                                      {'socket_id': socket_id,
                                       'rapl_event_id': rapl_event_id_1})

    validation_report_2 = PowerReport(hwpc_report.timestamp,
                                      hwpc_report.sensor,
                                      hwpc_report.target,
                                      math.ldexp(raw_power_2, -32),
                                      {'socket_id': socket_id,
                                       'rapl_event_id': rapl_event_id_2})

    result = RAPLFormulaHWPCReportHandler(get_fake_pusher())._process_report(
        hwpc_report)

    assert len(result) == 2
    assert validation_report_1 in result
    assert validation_report_2 in result


def test_handle_hwpc_report_with_two_rapl_event_and_other_groups():
    """
    handle a HWPC report with two RAPL events and events from other
    groups

    The HWPC report contain two RAPL events and events from a group 'sys'
    with two cores

    The handle method must return two PowerReport containing each RAPL event
    """
    socket_id = '1'
    raw_power_1 = 10
    rapl_event_id_1 = 'RAPL_1'
    raw_power_2 = 20
    rapl_event_id_2 = 'RAPL_2'

    events = {rapl_event_id_1: raw_power_1, rapl_event_id_2: raw_power_2}

    hwpc_report = create_report_root(
        [create_group_report('rapl', [
            create_socket_report(socket_id,
                                 [create_core_report(
                                     '1',
                                     None,
                                     None,
                                     events=events)])]),

         create_group_report('sys', [
             create_socket_report(socket_id,
                                  [create_core_report('1', 'e0', 0),
                                   create_core_report('2', 'e0', 0)])])])

    validation_report_1 = PowerReport(hwpc_report.timestamp,
                                      hwpc_report.sensor,
                                      hwpc_report.target,
                                      math.ldexp(raw_power_1, -32),
                                      {'socket_id': socket_id,
                                       'rapl_event_id': rapl_event_id_1})

    validation_report_2 = PowerReport(hwpc_report.timestamp,
                                      hwpc_report.sensor,
                                      hwpc_report.target,
                                      math.ldexp(raw_power_2, -32),
                                      {'socket_id': socket_id,
                                       'rapl_event_id': rapl_event_id_2})

    result = RAPLFormulaHWPCReportHandler(get_fake_pusher())._process_report(
        hwpc_report)

    assert len(result) == 2
    assert validation_report_1 in result
    assert validation_report_2 in result
