# Copyright (c) 2025, Inria
# Copyright (c) 2025, University of Lille
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
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

from datetime import datetime, timezone

from powerapi.database.csv.codecs import HWPCReportDecoder
from powerapi.report import HWPCReport


class TestHwPCReportDecoder:
    """
    Test class for HWPCReportDecoder.
    """

    def test_decode_valid_csv_lines_with_one_events_group(self):
        """
        Test to decode valid CSV lines with one events group.
        """
        ts = int(datetime.now(timezone.utc).timestamp() * 1000)  # milliseconds
        lines = {'testg': [
            {'timestamp': ts, 'sensor': 'pytest', 'target': 'example', 'socket': '0', 'cpu': '0', 'event1': 1, 'event2': 1},
            {'timestamp': ts, 'sensor': 'pytest', 'target': 'example', 'socket': '0', 'cpu': '1', 'event1': 2, 'event2': 2},
            {'timestamp': ts, 'sensor': 'pytest', 'target': 'example', 'socket': '1', 'cpu': '0', 'event1': 3, 'event2': 3},
            {'timestamp': ts, 'sensor': 'pytest', 'target': 'example', 'socket': '1', 'cpu': '1', 'event1': 4, 'event2': 4},
        ]}

        report = HWPCReportDecoder().decode(lines)

        assert isinstance(report, HWPCReport)
        assert report.timestamp == datetime.fromtimestamp(ts / 1000, timezone.utc)
        assert report.sensor == 'pytest'
        assert report.target == 'example'
        assert report.metadata == {}
        assert report.groups['testg']['0']['0'] == {'event1': 1, 'event2': 1}
        assert all(isinstance(v, int) for v in report.groups['testg']['0']['0'].values())
        assert report.groups['testg']['0']['1'] == {'event1': 2, 'event2': 2}
        assert all(isinstance(v, int) for v in report.groups['testg']['0']['1'].values())
        assert report.groups['testg']['1']['0'] == {'event1': 3, 'event2': 3}
        assert all(isinstance(v, int) for v in report.groups['testg']['1']['0'].values())
        assert report.groups['testg']['1']['1'] == {'event1': 4, 'event2': 4}
        assert all(isinstance(v, int) for v in report.groups['testg']['1']['1'].values())

    def test_decode_valid_csv_lines_with_multiple_events_groups(self):
        """
        Test to decode valid CSV lines with multiple events groups.
        """
        ts = int(datetime.now(timezone.utc).timestamp() * 1000)  # milliseconds
        lines = {
            'testg1': [
                {'timestamp': ts, 'sensor': 'pytest', 'target': 'example', 'socket': '0', 'cpu': '0', 'event1': 1, 'event2': 1},
                {'timestamp': ts, 'sensor': 'pytest', 'target': 'example', 'socket': '1', 'cpu': '1', 'event1': 2, 'event2': 2},
            ],
            'testg2': [
                {'timestamp': ts, 'sensor': 'pytest', 'target': 'example', 'socket': '0', 'cpu': '0', 'event1': 3, 'event2': 3},
                {'timestamp': ts, 'sensor': 'pytest', 'target': 'example', 'socket': '1', 'cpu': '1', 'event1': 4, 'event2': 4},
            ],
        }

        report = HWPCReportDecoder().decode(lines)

        assert isinstance(report, HWPCReport)
        assert report.timestamp == datetime.fromtimestamp(ts / 1000, timezone.utc)
        assert report.sensor == 'pytest'
        assert report.target == 'example'
        assert report.metadata == {}
        assert report.groups['testg1']['0']['0'] == {'event1': 1, 'event2': 1}
        assert all(isinstance(v, int) for v in report.groups['testg1']['0']['0'].values())
        assert report.groups['testg1']['1']['1'] == {'event1': 2, 'event2': 2}
        assert all(isinstance(v, int) for v in report.groups['testg1']['1']['1'].values())
        assert report.groups['testg2']['0']['0'] == {'event1': 3, 'event2': 3}
        assert all(isinstance(v, int) for v in report.groups['testg2']['0']['0'].values())
        assert report.groups['testg2']['1']['1'] == {'event1': 4, 'event2': 4}
        assert all(isinstance(v, int) for v in report.groups['testg2']['1']['1'].values())
