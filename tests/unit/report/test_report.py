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

from powerapi.report import Report
from datetime import datetime


@pytest.fixture()
def basic_report():
    return Report(timestamp=datetime.strptime('1970-09-01T09:09:10.543', "%Y-%m-%dT%H:%M:%S.%f"), sensor='toto',
                  target='all', metadata={"tag": 1})


@pytest.fixture()
def expected_json_report(basic_report):
    return {'timestamp': basic_report.timestamp,
            'sensor': basic_report.sensor,
            'target': basic_report.target,
            'metadata': basic_report.metadata}


def test_creating_report_with_metadata():
    report = Report(timestamp=datetime.strptime('1970-09-01T09:09:10.543', "%Y-%m-%dT%H:%M:%S.%f"), sensor='toto',
                    target='all', metadata={"tag": 1})
    assert report.metadata["tag"] == 1


def test_create_two_report_without_metadata_metadata_are_different():
    """
    When using a default parameter, its value is evaluated at the instantiation of the class
    So if not used carefully, all object have the same value as attribute
    """

    a = Report(0, 'toto', 'all')
    a.metadata["test"] = "value"
    b = Report(0, 'toto', 'all')
    assert a.metadata != b.metadata


def test_to_json(basic_report, expected_json_report):

    json = Report.to_json(report=basic_report)
    assert 'sender_name' not in json
    assert 'dispatcher_report_id' not in json
    assert json == expected_json_report


def test_to_json_with_dispatcher_report_id(basic_report, expected_json_report):
    basic_report.dispatcher_report_id = 10
    
    json = Report.to_json(report=basic_report)
    assert 'sender_name' not in json
    assert 'dispatcher_report_id' not in json
    assert json == expected_json_report
