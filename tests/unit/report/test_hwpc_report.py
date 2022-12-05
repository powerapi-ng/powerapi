# Copyright (c) 2021, INRIA
# Copyright (c) 2021, University of Lille
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import pytest

from powerapi.report import HWPCReport, BadInputData
from datetime import datetime

from powerapi.test_utils.report.hwpc import extract_rapl_reports_with_2_sockets


########
# JSON #
########
def test_create_hwpc_report_from_json_wit_str_timestamp_create_a_HWPCReport():
    json_input = extract_rapl_reports_with_2_sockets(1)[0]
    report = HWPCReport.from_json(json_input)
    assert isinstance(report, HWPCReport)


def test_create_hwpc_report_from_json_with_datetime_timestamp_format_create_a_HWPCReport():
    json_input = extract_rapl_reports_with_2_sockets(1)[0]
    json_input['timestamp'] = datetime.strptime(json_input['timestamp'], "%Y-%m-%dT%H:%M:%S.%f")
    report = HWPCReport.from_json(json_input)
    assert isinstance(report, HWPCReport)


def test_create_hwpc_report_from_json_with_str_timestamp_with_bad_format_raise_BadInputData():
    json_input = extract_rapl_reports_with_2_sockets(1)[0]
    json_input['timestamp'] = '1970-09-01T090909.543'
    with pytest.raises(BadInputData):
        _ = HWPCReport.from_json(json_input)


def test_create_hwpc_report_from_json_without_timestamp_field_raise_BadInputData():
    json_input = extract_rapl_reports_with_2_sockets(1)[0]
    del json_input['timestamp']
    with pytest.raises(BadInputData):
        _ = HWPCReport.from_json(json_input)


def test_create_hwpc_report_from_json_without_sensor_field_raise_BadInputData():
    json_input = extract_rapl_reports_with_2_sockets(1)[0]
    del json_input['sensor']
    with pytest.raises(BadInputData):
        _ = HWPCReport.from_json(json_input)


def test_create_hwpc_report_from_json_without_groups_field_raise_BadInputData():
    json_input = extract_rapl_reports_with_2_sockets(1)[0]
    del json_input['groups']
    with pytest.raises(BadInputData):
        _ = HWPCReport.from_json(json_input)


#######
# CSV #
#######
def test_create_hwpc_report_from_csv_with_one_lines_create_an_hwpc_report():
    csv_lines = [('rapl',
                  {'sensor': 'toto', 'timestamp': '1970-09-01T09:09:09.543', 'target': 'all', 'socket': '0', 'cpu': '7',
                   'RAPL_VALUE': '1234'})]
    report = HWPCReport.from_csv_lines(csv_lines)
    assert isinstance(report, HWPCReport)


def test_create_hwpc_report_from_csv_with_bad_timestamp_format_raise_BadInputData():
    csv_lines = [('rapl',
                  {'sensor': 'toto', 'timestamp': '1970-09-01T090909.543', 'target': 'all', 'socket': '0', 'cpu': '7',
                   'RAPL_VALUE': '1234'})]
    with pytest.raises(BadInputData):
        _ = HWPCReport.from_csv_lines(csv_lines)


def test_create_hwpc_report_from_csv_with_two_lines_create_an_hwpc_report():
    csv_lines = [('rapl',
                  {'sensor': 'toto', 'timestamp': '1970-09-01T09:09:09.543', 'target': 'all', 'socket': '0', 'cpu': '7',
                   'RAPL_VALUE': '1234'}),
                 ('rapl',
                  {'sensor': 'toto', 'timestamp': '1970-09-01T09:09:09.543', 'target': 'all', 'socket': '1', 'cpu': '7',
                   'RAPL_VALUE': '4321'})]
    report = HWPCReport.from_csv_lines(csv_lines)
    assert isinstance(report, HWPCReport)
    assert len(report.groups['rapl']) == 2


def test_create_hwpc_report_from_csv_with_two_lines_with_different_timestamp_raise_BadInputData():
    csv_lines = [('rapl',
                  {'sensor': 'toto', 'timestamp': '1970-09-01T09:09:10.543', 'target': 'all', 'socket': '0', 'cpu': '7',
                   'RAPL_VALUE': '1234'}),
                 ('rapl',
                  {'sensor': 'toto', 'timestamp': '1970-09-01T09:09:09.543', 'target': 'all', 'socket': '1', 'cpu': '7',
                   'RAPL_VALUE': '4321'})]
    with pytest.raises(BadInputData):
        _ = HWPCReport.from_csv_lines(csv_lines)


def test_create_hwpc_report_from_csv_with_two_lines_with_different_sensor_name_raise_BadInputData():
    csv_lines = [('rapl',
                  {'sensor': 'toto', 'timestamp': '1970-09-01T09:09:09.543', 'target': 'all', 'socket': '0', 'cpu': '7',
                   'RAPL_VALUE': '1234'}),
                 ('rapl',
                  {'sensor': 'tutu', 'timestamp': '1970-09-01T09:09:09.543', 'target': 'all', 'socket': '1', 'cpu': '7',
                   'RAPL_VALUE': '4321'})]
    with pytest.raises(BadInputData):
        _ = HWPCReport.from_csv_lines(csv_lines)


def test_create_hwpc_report_from_csv_with_two_lines_with_different_target_name_raise_BadInputData():
    csv_lines = [('rapl',
                  {'sensor': 'toto', 'timestamp': '1970-09-01T09:09:09.543', 'target': 'all', 'socket': '0', 'cpu': '7',
                   'RAPL_VALUE': '1234'}),
                 ('rapl', {'sensor': 'toto', 'timestamp': '1970-09-01T09:09:09.543', 'target': 'allall', 'socket': '1',
                           'cpu': '7', 'RAPL_VALUE': '4321'})]
    with pytest.raises(BadInputData):
        _ = HWPCReport.from_csv_lines(csv_lines)


def test_create_hwpc_report_from_csv_without_socket_field_raise_BadInputData():
    csv_lines = [('rapl', {'sensor': 'toto', 'timestamp': '1970-09-01T09:09:09.543', 'target': 'all', 'cpu': '7',
                           'RAPL_VALUE': '1234'})]
    with pytest.raises(BadInputData):
        _ = HWPCReport.from_csv_lines(csv_lines)


############
# METADATA #
############

def test_creating_report_with_metadata():
    report = HWPCReport(('1970-09-01T09:09:10.543'), 'toto', 'all', {}, {"tag": 1})
    assert report.metadata["tag"] == 1


def test_create_report_from_json_with_metadata():
    json_input = extract_rapl_reports_with_2_sockets(1)[0]
    json_input["metadata"] = {}
    json_input["metadata"]["tag"] = 1
    report = HWPCReport.from_json(json_input)
    assert report.metadata["tag"] == 1


def test_create_report_from_csv_with_metadata():
    csv_lines = [('rapl',
                  {'sensor': 'toto', 'timestamp': '1970-09-01T09:09:09.543', 'target': 'all', 'socket': '0', 'cpu': '7',
                   'RAPL_VALUE': '1234', 'tag': 1})]
    report = HWPCReport.from_csv_lines(csv_lines)
    assert report.metadata["tag"] == 1
