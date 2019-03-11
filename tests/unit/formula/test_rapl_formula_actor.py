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

import math
import mock
import pytest

from powerapi.formula import RAPLFormulaHWPCReportHandler, FormulaState
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

@pytest.fixture
def state():
    return FormulaState(None, mock.Mock(), mock.Mock(), ('toto', 'toto', '1'))


#####################################
# Test RAPLFormulaHWPCReportHandler #
#####################################


def test_handle_no_hwpc_report(state):
    """
    handle a message that is not a HWPCReport, this must raise an
    UnknowMessageTypeException
    """
    with pytest.raises(UnknowMessageTypeException):
        RAPLFormulaHWPCReportHandler(
            get_fake_pusher()).handle("toto",
                                      state)


def test_handle_hwpc_report_with_one_rapl_event(state):
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
                                    {'socket': socket_id,
                                     'event': rapl_event_id})

    result = RAPLFormulaHWPCReportHandler(get_fake_pusher())._process_report(
        hwpc_report, state)
    assert [validation_report] == result


def test_handle_hwpc_report_with_one_rapl_event_and_other_groups(state):
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
                                    {'socket': socket_id,
                                     'event': rapl_event_id})

    result = RAPLFormulaHWPCReportHandler(get_fake_pusher())._process_report(
        hwpc_report, state)

    assert [validation_report] == result


def test_handle_hwpc_report_with_two_rapl_event(state):
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
                                      {'socket': socket_id,
                                       'event': rapl_event_id_1})

    validation_report_2 = PowerReport(hwpc_report.timestamp,
                                      hwpc_report.sensor,
                                      hwpc_report.target,
                                      math.ldexp(raw_power_2, -32),
                                      {'socket': socket_id,
                                       'event': rapl_event_id_2})

    result = RAPLFormulaHWPCReportHandler(get_fake_pusher())._process_report(
        hwpc_report, state)

    assert len(result) == 2
    assert validation_report_1 in result
    assert validation_report_2 in result


def test_handle_hwpc_report_with_two_rapl_event_and_other_groups(state):
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
                                      {'socket': socket_id,
                                       'event': rapl_event_id_1})

    validation_report_2 = PowerReport(hwpc_report.timestamp,
                                      hwpc_report.sensor,
                                      hwpc_report.target,
                                      math.ldexp(raw_power_2, -32),
                                      {'socket': socket_id,
                                       'event': rapl_event_id_2})

    result = RAPLFormulaHWPCReportHandler(get_fake_pusher())._process_report(
        hwpc_report, state)

    assert len(result) == 2
    assert validation_report_1 in result
    assert validation_report_2 in result
